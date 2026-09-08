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
