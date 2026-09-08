import json

import pytest

import canvas
from canvas_store import configure_courses, open_writer, save_auth, save_snapshot
from test_canvas_store import AT, MAPPING, assignment


def test_read_commands_and_preview_never_open_client(tmp_path, monkeypatch, capsys):
    path = tmp_path / "cache.sqlite3"
    with open_writer(path) as db:
        configure_courses(db, MAPPING)
        save_snapshot(db, 42, "assignments", [assignment()], AT)
        save_auth(db, "expired", AT)
    monkeypatch.setattr(canvas, "CanvasClient", lambda *a: pytest.fail("cached read opened credentials"))
    before = path.read_bytes()
    for command in ("status", "courses", "due", "assignments", "grades", "announcements", "deliver"):
        assert canvas.main(["--db", str(path), command]) == 0
        assert isinstance(json.loads(capsys.readouterr().out), dict)
    assert path.read_bytes() == before
    assert not (tmp_path / "writer.lock").exists()


def test_invalid_detail_and_missing_database_are_json_errors(tmp_path, capsys):
    assert canvas.main(["detail"]) == 1
    assert json.loads(capsys.readouterr().err)["error"] == "detail_requires_course_and_id"
    path = tmp_path / "missing.sqlite3"
    assert canvas.main(["--db", str(path), "status"]) == 1
    assert json.loads(capsys.readouterr().err)["error"] == "invalid_or_unavailable_local_data"
    assert not path.exists()


def test_send_is_explicit_and_uses_writer_lock(tmp_path, monkeypatch, capsys):
    path = tmp_path / "cache.sqlite3"
    config = tmp_path / "config"
    with open_writer(path) as db:
        configure_courses(db, MAPPING)
        save_auth(db, "expired", AT)
    calls = []
    def deliver(db):
        from canvas_client import writer_lock, CanvasError
        with pytest.raises(CanvasError, match="busy"):
            with writer_lock(config):
                pytest.fail("delivery is not serialized")
        calls.append(1)
        return {"sent": 1}
    monkeypatch.setattr(canvas, "deliver", deliver)
    assert canvas.main(["--config", str(config), "--db", str(path), "deliver"]) == 0
    assert not calls
    assert canvas.main(["--config", str(config), "--db", str(path), "deliver", "--send"]) == 0
    assert calls == [1]
    assert canvas.main(["sync", "--send"]) == 1
    assert json.loads(capsys.readouterr().err)["error"] == "send_requires_deliver"


@pytest.fixture
def online(tmp_path, monkeypatch):
    from canvas_client import writer_lock
    manifest = {"term": "AY2627-T1", "subjects": [
        {"code": "STDISCM", "section": "S03", "overview": "AY2627-T1/STDISCM/_overview.md"}]}
    monkeypatch.setattr(canvas, "read_subjects", lambda path: manifest)
    monkeypatch.setattr("canvas_sync.read_subjects", lambda path: manifest)
    class Client:
        error = None
        profile = {"id": 7}
        def __init__(self, config):
            self.config = config
        def __enter__(self):
            self.lock = writer_lock(self.config)
            self.lock.__enter__()
            return self
        def __exit__(self, *args):
            self.lock.__exit__(*args)
        def get(self, path):
            if self.error:
                from canvas_client import CanvasError
                raise CanvasError(self.error)
            return (self.profile if "profile" in path else {"id": 42, "name": "Distributed Computing"}), None
        def list(self, path):
            if path.startswith('/api/v1/courses?'):
                return [{"id": 42, "course_code": "STDISCM_S03", "term": {"name": "AY 2026-2027 Term 1"}}]
            return []
    monkeypatch.setattr(canvas, "CanvasClient", Client)
    config = tmp_path / "config"
    db = tmp_path / "cache/cache.sqlite3"
    return Client, config, db, ["--config", str(config), "--db", str(db)]


def test_online_commands_write_receipts_and_verified_mapping(online, capsys):
    Client, config, db, args = online
    for command in ("probe", "map", "sync"):
        assert canvas.main(args + [command]) == 0
        output = json.loads(capsys.readouterr().out)
        assert json.loads((config / 'receipt.json').read_text()) == output
    mapping = json.loads((config / 'mappings.json').read_text())
    assert mapping['subjects'][0]['course_id'] == 42 and mapping['user_id'] == 7
    assert json.loads((config / 'course-candidates.json').read_text())[0]['id'] == 42
    assert (config / 'mappings.json').stat().st_mode & 0o777 == 0o600
    assert output == {'complete_categories': 4, 'failures': []}


def test_probe_expiry_and_recovery_update_cached_state_without_freshening_facts(online, capsys):
    from canvas_store import open_reader, query
    Client, config, dbpath, args = online
    with open_writer(dbpath) as db:
        configure_courses(db, MAPPING)
        save_snapshot(db, 42, 'assignments', [assignment()], AT)
        save_auth(db, 'valid', AT)
    Client.error = 'authentication_expired'
    for _ in range(2):
        assert canvas.main(args + ['probe']) == 1
        assert json.loads(capsys.readouterr().err)['error'] == 'authentication_expired'
        assert json.loads((config / 'receipt.json').read_text())['error'] == 'authentication_expired'
    with open_reader(dbpath) as db:
        assert 'authentication_expired' in query(db, 'status')['warnings']
        assert db.execute("SELECT count(*) FROM events WHERE kind='authentication_expired'").fetchone()[0] == 1
    Client.error = None
    assert canvas.main(args + ['probe']) == 0
    with open_reader(dbpath) as db:
        assert query(db, 'status')['authentication']['state'] == 'valid'
        assert query(db, 'assignments')['coverage'][0]['success_at'] == AT
        assert db.execute("SELECT count(*) FROM events WHERE kind='authentication_restored'").fetchone()[0] == 1


def test_failed_mapping_keeps_last_verified_file_and_writes_receipt(online, capsys, monkeypatch):
    Client, config, db, args = online
    assert canvas.main(args + ['map']) == 0
    before = (config / 'mappings.json').read_bytes()
    monkeypatch.setattr(Client, 'list', lambda self, path: [])
    assert canvas.main(args + ['map']) == 1
    assert (config / 'mappings.json').read_bytes() == before
    assert json.loads((config / 'receipt.json').read_text())['error'] == 'course_mapping_missing_or_ambiguous'


def test_malformed_profile_is_a_failure_receipt(online, capsys):
    Client, config, db, args = online
    Client.profile = []
    assert canvas.main(args + ['probe']) == 1
    assert json.loads((config / 'receipt.json').read_text())['error'] == 'malformed_profile'


@pytest.mark.parametrize('change', [
    lambda m: [],
    lambda m: {**m, 'term': 'AY2526-T3'},
    lambda m: {**m, 'user_id': 0},
    lambda m: {**m, 'user_id': True},
    lambda m: {**m, 'subjects': {}},
    lambda m: {**m, 'subjects': [None]},
    lambda m: {**m, 'subjects': [{**m['subjects'][0], 'section': 'S04'}]},
    lambda m: {**m, 'subjects': [{**m['subjects'][0], 'course_id': 0}]},
])
def test_sync_rejects_invalid_mapping_and_writes_failure_receipt(online, capsys, change):
    Client, config, db, args = online
    assert canvas.main(args + ['map']) == 0
    path = config / 'mappings.json'
    mapping = json.loads(path.read_text())
    path.write_text(json.dumps(change(mapping)))
    assert canvas.main(args + ['sync']) == 1
    assert json.loads((config / 'receipt.json').read_text())['error'] == 'mapping_requires_verification'
    with open_writer(db) as connection:
        assert connection.execute('SELECT count(*) FROM courses').fetchone()[0] == 0


def test_load_mapping_rejects_duplicate_course_ids(tmp_path, monkeypatch):
    from canvas_client import CanvasError
    from canvas_sync import load_mapping
    subjects = [{'code': 'A', 'section': 'S01', 'overview': 'A.md'},
                {'code': 'B', 'section': 'S02', 'overview': 'B.md'}]
    monkeypatch.setattr('canvas_sync.read_subjects', lambda path: {'term': 'AY2627-T1', 'subjects': subjects})
    (tmp_path / 'mappings.json').write_text(json.dumps({'term': 'AY2627-T1', 'user_id': 7,
        'subjects': [{**s, 'course_id': 42} for s in subjects]}))
    with pytest.raises(CanvasError, match='mapping_requires_verification'):
        load_mapping(tmp_path, tmp_path)


@pytest.mark.parametrize('command,flags', [
    ('grades', ['--unfinished']), ('status', ['--limit', '50']), ('probe', ['--offset', '0']),
    ('announcements', ['--period', 'week']), ('sync', ['--course', 'STDISCM']),
    ('detail', ['--limit', '1']),
])
def test_irrelevant_flags_are_rejected_before_io(command, flags, monkeypatch, capsys):
    monkeypatch.setattr(canvas, 'CanvasClient', lambda *a: pytest.fail('unexpected client'))
    assert canvas.main([command, *flags]) == 1
    assert json.loads(capsys.readouterr().err)['error'].endswith('_not_supported_for_command')
