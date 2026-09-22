from __future__ import annotations

import json
import sqlite3
from pathlib import Path

import pytest

import asta
from asta_store import AstaError, open_store


@pytest.fixture
def db(tmp_path):
    with open_store(tmp_path / 'private/asta.sqlite3') as store:
        yield store


PROFILE = {'sex': 'male', 'age': 30, 'height_cm': 180, 'weight_kg': 80,
           'activity_factor': 1.5, 'goal': 'maintain'}


def test_private_store_and_reopen(tmp_path):
    path = tmp_path / 'private/asta.sqlite3'
    with open_store(path) as db:
        assert db.execute('PRAGMA user_version').fetchone()[0] == 1
        asta.profile_set(db, {'age': 30})
    assert path.stat().st_mode & 0o777 == 0o600
    assert path.parent.stat().st_mode & 0o777 == 0o700
    with open_store(path) as db:
        assert asta.profile_show(db)['profile']['age'] == 30


@pytest.mark.parametrize('parent', [False, True])
def test_symlinks_refused(tmp_path, parent):
    target = tmp_path / 'target'
    target.mkdir()
    link = tmp_path / 'link'
    link.symlink_to(target if parent else target / 'db')
    with pytest.raises(AstaError, match='unsafe_symlink'):
        with open_store(link / 'db' if parent else link):
            pass
    assert not (target / 'db').exists()


def test_future_schema_untouched(tmp_path):
    path = tmp_path / 'db'
    with sqlite3.connect(path) as db:
        db.execute('PRAGMA user_version=99')
    with pytest.raises(AstaError, match='unsupported_schema'):
        with open_store(path):
            pass
    with sqlite3.connect(path) as db:
        assert db.execute('PRAGMA user_version').fetchone()[0] == 99


def test_profile_versions_and_skipped_fields(db):
    asta.profile_set(db, {'age': 30, 'sex': 'male'})
    asta.profile_set(db, {'age': 31, 'height_cm': None, 'eating_habits': 'varies'})
    state = asta.profile_show(db)
    assert state['profile']['version'] == 2
    assert state['profile']['sex'] == 'male'
    assert 'height_cm' in state['missing']
    assert json.loads(db.execute('SELECT data FROM profiles WHERE id=1').fetchone()[0])['age'] == 30


@pytest.mark.parametrize('bad', [{'age': -1}, {'age': True}, {'age': float('nan')},
                                 {'surprise': 1}, {'sex': []}, {'goal': {}}, {'age': '30'}])
def test_invalid_profile_writes_nothing(db, bad):
    with pytest.raises(AstaError):
        asta.profile_set(db, bad)
    assert db.execute('SELECT count(*) FROM profiles').fetchone()[0] == 0


@pytest.mark.parametrize(('goal', 'percent', 'kcal'), [('maintain', 5, 2670), ('cut', 5, 2269.5),
                                                      ('lean_gain', 5, 2803.5), ('lean_gain', 10, 2937)])
def test_targets_hand_calculated(db, goal, percent, kcal):
    asta.profile_set(db, {**PROFILE, 'goal': goal, 'gain_percent': percent})
    result = asta.targets_suggest(db)
    assert result['bmr'] == 1780
    assert result['targets'] == {'kcal': kcal, 'protein': 144, 'fat': 64,
                                  'carbs': round((kcal - 576 - 576) / 4, 2)}
    assert db.execute('SELECT count(*) FROM targets').fetchone()[0] == 0


def test_missing_profile_never_guessed(db):
    assert asta.targets_suggest(db)['missing'] == list(asta.REQUIRED)
    asta.profile_set(db, PROFILE)
    asta.profile_set(db, {'activity_factor': None})
    assert asta.targets_suggest(db)['missing'] == ['activity_factor']


def test_target_provenance(db):
    asta.profile_set(db, PROFILE)
    suggestion = asta.targets_suggest(db)['targets']
    payload = {k: {'value': v, 'source': 'computed'} for k, v in suggestion.items()}
    payload['kcal'] = {'value': 2500, 'source': 'overridden'}
    result = asta.targets_set(db, payload)['targets']
    assert result['kcal']['source'] == 'overridden'
    assert result['protein']['source'] == 'computed'
    payload['kcal']['source'] = 'computed'
    with pytest.raises(AstaError, match='mismatch'):
        asta.targets_set(db, payload)
    assert db.execute('SELECT count(*) FROM targets').fetchone()[0] == 1


def test_weight_window_gaps_and_replacement(db):
    for on, kg in [('2026-09-01', 80), ('2026-09-14', 75), ('2026-09-15', 70),
                   ('2026-09-20', 72), ('2026-09-22', 99)]:
        asta.weight_add(db, kg, on)
    asta.weight_add(db, 74, '2026-09-20')
    trend = asta.weight_trend(db, '2026-09-21')
    assert trend['seven_day_average'] == 72
    assert trend['sample_count'] == 2
    assert len(trend['entries']) == 4


def test_cli_bad_json_does_not_create_db(tmp_path, monkeypatch, capsys):
    import io
    path = tmp_path / 'db'
    monkeypatch.setattr('sys.stdin', io.StringIO('{'))
    assert asta.main(['--db', str(path), 'profile', 'set', '--json', '-']) == 1
    assert json.loads(capsys.readouterr().out)['status'] == 'error'
    assert not path.exists()


@pytest.fixture
def food(db):
    value = {'id': 'fixture:rice', 'source': 'fixture', 'source_id': 'rice', 'label': 'rice',
             'per_100g': {'kcal': 100, 'protein': 2, 'carbs': 20, 'fat': 1}}
    with db:
        db.execute('INSERT INTO foods VALUES(?,?)', (value['id'], json.dumps(value)))
    return value


def meal(minimum=200, estimate=200, maximum=200):
    return {'schema_version': 1, 'occurred_at': '2026-09-20T17:00:00+00:00',
            'meal_type': 'dinner', 'source': 'text', 'model_id': 'fixture', 'effort': 'medium',
            'prompt_version': 'fixture-1', 'items': [
                {'label': 'rice', 'food_id': 'fixture:rice',
                 'grams': {'min': minimum, 'estimate': estimate, 'max': maximum},
                 'identity_confidence': .9, 'portion_confidence': .8,
                 'hidden_ingredient_risk': 'low', 'assumptions': []}]}


@pytest.mark.parametrize(('low', 'high', 'tier'), [(140, 260, 'committed'),
    (139, 260, 'flagged'), (75, 325, 'flagged'), (74, 325, 'needs_answer')])
def test_meal_thresholds_and_no_write_for_question(db, food, low, high, tier):
    import asta_meals
    result = asta_meals.add(db, meal(low, 200, high))
    assert result['status'] == tier
    assert db.execute('SELECT count(*) FROM meals').fetchone()[0] == (tier != 'needs_answer')
    if tier != 'needs_answer':
        assert result['date'] == '2026-09-21'
        assert result['totals']['protein']['estimate'] == 4


def test_density_always_flagged_and_unknown_food_rejected(db, food):
    import asta_meals
    payload = meal()
    payload['items'][0].pop('food_id')
    payload['items'][0]['density_estimate'] = food['per_100g']
    assert asta_meals.add(db, payload)['status'] == 'flagged'
    payload['items'][0]['food_id'] = 'missing'
    payload['items'][0].pop('density_estimate')
    with pytest.raises(AstaError, match='unknown_food'):
        asta_meals.add(db, payload)


def test_correction_keeps_original_and_delete_cascades(db, food):
    import asta_meals
    original = asta_meals.add(db, meal(139, 200, 260))
    result = asta_meals.correct(db, original['id'], {'items': meal(100, 100, 100)['items'], 'reason': 'weighed'})
    assert result['totals']['kcal']['estimate'] == 100
    record = asta_meals.show(db, original['id'])
    assert record['original']['totals']['kcal']['estimate'] == 200
    assert record['corrections'][0]['reason'] == 'weighed'
    assert asta_meals.listing(db, flagged=True)['meals'] == []
    asta_meals.delete(db, original['id'])
    assert db.execute('SELECT count(*) FROM corrections').fetchone()[0] == 0


def test_config_override_and_identity_boundary(db, food, tmp_path):
    import asta_meals
    path = tmp_path / 'config.json'
    path.write_text(json.dumps({'needs_answer_identity': .95}))
    assert asta_meals.add(db, meal(), asta_meals.thresholds(path))['status'] == 'needs_answer'
    payload = meal()
    payload['items'][0]['identity_confidence'] = .6
    assert asta_meals.add(db, payload)['status'] == 'committed'
    payload['items'][0]['identity_confidence'] = .599
    assert asta_meals.add(db, payload)['status'] == 'needs_answer'


@pytest.mark.parametrize('mutate', [lambda p: p.update(kcal=10),
    lambda p: p['items'][0].update(kcal=10), lambda p: p['items'][0].pop('grams'),
    lambda p: p['items'][0]['grams'].update(estimate=float('inf')),
    lambda p: p.update(occurred_at='2026-09-21T10:00:00'),
    lambda p: p['items'][0].update(identity_confidence=True)])
def test_meal_validation_atomic(db, food, mutate):
    import asta_meals
    payload = meal()
    mutate(payload)
    with pytest.raises(AstaError):
        asta_meals.add(db, payload)
    assert db.execute('SELECT count(*) FROM meals').fetchone()[0] == 0


def test_question_targets_largest_impact(db, food):
    import asta_meals
    payload = meal(0, 200, 600)
    other = meal(10, 10, 10)['items'][0]
    other['label'] = 'small side'
    payload['items'].insert(0, other)
    assert 'rice' in asta_meals.add(db, payload)['question']


def test_template_roundtrip(db, food):
    import asta_food
    import asta_meals
    stored = asta_meals.add(db, meal())
    asta_food.template_save(db, stored['id'], 'usual rice')
    result = asta_food.template_search(db, 'usual')[0]
    assert result['food']['per_100g'] == food['per_100g']
    assert result['sample_count'] == 1


def test_food_search_order_cache_and_local_fallback(db, food, tmp_path):
    import asta_food
    import asta_meals
    from datetime import datetime, timezone, timedelta
    stored = asta_meals.add(db, meal())
    asta_food.template_save(db, stored['id'], 'rice bowl')
    seed = tmp_path / 'staples.json'
    seed.write_text(json.dumps([{**food, 'id': 'philfct:R', 'source': 'philfct',
                                 'source_id': 'R', 'copied_at': '2026-09-21'}, {'bad': True}]))
    key = tmp_path / 'key'
    key.write_text('fixture-key')
    calls = []
    class Response:
        def raise_for_status(self):
            pass
        def json(self):
            return {'foods': [{'fdcId': 1, 'description': 'rice', 'foodNutrients': [
                {'nutrientId': n, 'value': food['per_100g'][k]} for k, n in asta_food.NUTRIENTS.items()]}]}
    def fetch(*args, **kwargs):
        calls.append(kwargs)
        return Response()
    at = datetime(2026, 9, 21, tzinfo=timezone.utc)
    result = asta_food.search(db, 'rice', seed, key, at, fetch)
    assert [f['source'] for f in result['foods']] == ['template', 'philfct', 'usda']
    assert result['warnings'] == ['malformed_staple_row']
    asta_food.search(db, 'rice', seed, key, at, fetch)
    assert len(calls) == 1
    asta_food.search(db, 'rice', seed, key, at + timedelta(days=8), fetch)
    assert len(calls) == 2
    key.unlink()
    result = asta_food.search(db, 'rice', seed, key, at + timedelta(days=16), fetch)
    assert 'usda_key_missing' in result['warnings']
    assert len(result['foods']) == 2


@pytest.mark.parametrize('energy_id', [2047, 2048])
def test_food_search_accepts_alternate_usda_energy_nutrients(db, food, tmp_path, energy_id):
    import asta_food
    key = tmp_path / 'key'
    key.write_text('fixture-key')
    class Response:
        def raise_for_status(self):
            pass
        def json(self):
            nutrients = [
                {'nutrientId': nutrient_id, 'value': food['per_100g'][name]}
                for name, nutrient_id in asta_food.NUTRIENTS.items()
                if name != 'kcal'
            ]
            nutrients.append({'nutrientId': energy_id, 'value': food['per_100g']['kcal']})
            return {'foods': [{'fdcId': energy_id, 'description': 'rice',
                               'foodNutrients': nutrients}]}
    result = asta_food.search(
        db, 'rice', tmp_path / 'absent', key, transport=lambda *args, **kwargs: Response(),
    )
    assert result['foods'][0]['per_100g']['kcal'] == food['per_100g']['kcal']
    assert result['warnings'] == []


@pytest.mark.parametrize('error', ['timeout', 'http', 'malformed'])
def test_food_network_failure_is_visible(db, tmp_path, error):
    import asta_food
    import requests
    key = tmp_path / 'key'
    key.write_text('secret')
    def fetch(*args, **kwargs):
        if error == 'timeout':
            raise requests.Timeout('secret')
        if error == 'http':
            raise requests.HTTPError('secret')
        raise ValueError('secret')
    result = asta_food.search(db, 'rice', tmp_path / 'absent', key, transport=fetch)
    assert result == {'status': 'ok', 'foods': [], 'warnings': ['usda_unavailable']}


def test_photo_move_dedupe_and_provenance(db, food, tmp_path):
    import asta_meals
    from PIL import Image
    attachments, root = tmp_path / 'attachments', tmp_path / 'meals'
    attachments.mkdir()
    source = attachments / 'photo.jpg'
    Image.new('RGB', (10, 20), 'red').save(source)
    content = source.read_bytes()
    payload = {**meal(), 'source': 'photo', 'photo_path': str(source)}
    result = asta_meals.add(db, payload, attachments=attachments, meals_root=root)
    assert not source.exists()
    assert Path(result['media']['path']).read_bytes() == content
    assert result['media']['width'] == 10
    assert result['media']['height'] == 20
    assert result['image_hash'] == result['media']['hash']
    source.write_bytes(content)
    second = asta_meals.add(db, payload, attachments=attachments, meals_root=root)
    assert second['media']['path'] == result['media']['path']
    assert db.execute('SELECT count(*) FROM media').fetchone()[0] == 1
    corrected = asta_meals.correct(db, result['id'], {'items': meal(100, 100, 100)['items'], 'reason': 'weighed'})
    assert corrected['image_hash'] == result['image_hash']


@pytest.mark.parametrize('kind', ['outside', 'missing', 'nonimage', 'symlink'])
def test_invalid_photos_do_not_commit(db, food, tmp_path, kind):
    import asta_meals
    attachments = tmp_path / 'attachments'
    attachments.mkdir()
    source = attachments / 'photo.jpg'
    if kind == 'outside':
        source = tmp_path / 'outside.jpg'
        source.write_text('not a photo')
    elif kind == 'nonimage':
        source.write_text('not a photo')
    elif kind == 'symlink':
        target = tmp_path / 'target'
        target.write_text('private')
        source.symlink_to(target)
    with pytest.raises(AstaError):
        asta_meals.add(db, {**meal(), 'source': 'photo', 'photo_path': str(source)},
                       attachments=attachments, meals_root=tmp_path / 'meals')
    assert db.execute('SELECT count(*) FROM meals').fetchone()[0] == 0
    assert not (tmp_path / 'meals').exists()


def test_question_leaves_attachment(db, food, tmp_path):
    import asta_meals
    photo = tmp_path / 'photo.jpg'
    photo.write_bytes(b'unchanged')
    result = asta_meals.add(db, {**meal(0, 200, 600), 'source': 'photo', 'photo_path': str(photo)},
                           attachments=tmp_path, meals_root=tmp_path / 'meals')
    assert result['status'] == 'needs_answer'
    assert photo.read_bytes() == b'unchanged'


def test_rollup_and_adherence(db, food):
    import asta_daily
    import asta_meals
    import gcal
    asta_meals.add(db, meal())
    asta_meals.add(db, meal(139, 200, 260))
    asta_daily.adherence_set(db, 'session1', 'skipped')
    asta_daily.adherence_set(db, 'session1', 'done')
    asta_daily.adherence_set(db, 'old-session', 'skipped')
    calendar = {'name': 'workouts', 'id': 'workouts@example.test', 'profile': 'personal'}
    def event(event_id, title, hour):
        return gcal.normalize_event(calendar, {
            'id': event_id,
            'summary': title,
            'start': {'dateTime': f'2026-09-21T{hour:02d}:00:00+08:00'},
            'end': {'dateTime': f'2026-09-21T{hour + 1:02d}:00:00+08:00'},
        })
    result = asta_daily.today(db, '2026-09-21', lambda _: {'status': 'ok', 'events': [
        event('session1', 'Lifting', 8), event('session2', 'Climbing', 10)]})
    assert result['totals']['kcal']['estimate'] == 400
    assert result['flagged_count'] == 1
    assert len(result['adherence']) == 1
    output = asta_daily.render(result)
    assert 'Lifting: done' in output
    assert 'Climbing: done, skipped or moved?' in output
    assert '2 meals, 1 flagged' in output


def test_empty_day_and_calendar_failure(db):
    import asta_daily
    import gcal
    def fail(_):
        raise gcal.GcalError('fixture', 'failure')
    result = asta_daily.today(db, '2026-09-21', fail)
    assert result['totals'] is None
    output = asta_daily.render(result)
    assert 'No meals logged' in output
    assert 'Calendar data is unavailable' in output
    assert '0 kcal' not in output


def test_backup_retention_and_failure(tmp_path):
    from asta_backup import backup
    source = tmp_path / 'asta.sqlite3'
    with open_store(source) as db:
        asta.profile_set(db, PROFILE)
    target = tmp_path / 'backups'
    copies = [backup(source, target) for _ in range(15)]
    assert not copies[0].exists()
    assert all(p.exists() for p in copies[1:])
    with sqlite3.connect(copies[-1]) as db:
        assert db.execute('PRAGMA integrity_check').fetchone()[0] == 'ok'
        assert db.execute('SELECT count(*) FROM profiles').fetchone()[0] == 1
    with pytest.raises(AstaError, match='source_missing'):
        backup(tmp_path / 'missing', target)
    assert len(list(target.glob('*.sqlite3'))) == 14


def test_backup_during_writes(tmp_path):
    import threading
    from asta_backup import backup
    source = tmp_path / 'db'
    with open_store(source):
        pass
    entered, finish = threading.Event(), threading.Event()
    def writer():
        with open_store(source) as db:
            asta.profile_set(db, PROFILE)
            db.execute('BEGIN IMMEDIATE')
            db.execute('INSERT INTO weights VALUES(?,?,?)', ('2026-09-21', 80, 'now'))
            entered.set()
            finish.wait(5)
            db.commit()
    thread = threading.Thread(target=writer)
    thread.start()
    try:
        assert entered.wait(5)
        copy = backup(source, tmp_path / 'backups')
        with sqlite3.connect(copy) as db:
            assert db.execute('PRAGMA integrity_check').fetchone()[0] == 'ok'
            assert db.execute('SELECT count(*) FROM weights').fetchone()[0] == 0
    finally:
        finish.set()
        thread.join(5)


def test_backup_create_failure_preserves_existing_copy(tmp_path, monkeypatch):
    import asta_backup
    source = tmp_path / 'db'
    with open_store(source):
        pass
    target = tmp_path / 'backups'
    first = asta_backup.backup(source, target)
    def denied(*args, **kwargs):
        raise PermissionError('fixture')
    monkeypatch.setattr(asta_backup.os, 'open', denied)
    with pytest.raises(PermissionError):
        asta_backup.backup(source, target)
    assert first.exists()


def test_telegram_thread_is_optional(monkeypatch):
    import telegram_notify
    import requests
    payloads = []
    class Response:
        ok = True
    monkeypatch.setattr(telegram_notify, 'load_config', lambda **_: ('fixture', 'chat'))
    monkeypatch.setattr(requests, 'post', lambda url, **kw: (payloads.append(kw['json']) or Response()))
    telegram_notify.send('ordinary')
    telegram_notify.send('asta', thread_id=123)
    assert 'message_thread_id' not in payloads[0]
    assert payloads[1]['message_thread_id'] == 123


def test_read_commands_do_not_initialize_or_lock(tmp_path, capsys):
    from asta_store import open_reader
    path = tmp_path / 'absent' / 'db'
    assert asta.main(['--db', str(path), 'meal', 'list', '--flagged']) == 1
    assert not path.parent.exists()
    assert json.loads(capsys.readouterr().out)['error'] == 'tracking_not_initialized'
    with open_store(path) as db:
        asta.profile_set(db, PROFILE)
        db.execute('BEGIN IMMEDIATE')
        with open_reader(path) as reader:
            assert asta.profile_show(reader)['profile']['age'] == 30
            with pytest.raises(sqlite3.OperationalError):
                reader.execute('DELETE FROM profiles')
        db.rollback()


def test_null_gain_percent_is_skipped(db):
    asta.profile_set(db, {**PROFILE, 'goal': 'lean_gain', 'gain_percent': None})
    assert asta.targets_suggest(db)['targets']['kcal'] == 2803.5


def test_density_template_cannot_become_high_confidence(db, food):
    import asta_meals
    import asta_food
    payload = meal()
    payload['items'][0].pop('food_id')
    payload['items'][0]['density_estimate'] = food['per_100g']
    original = asta_meals.add(db, payload)
    saved = asta_food.template_save(db, original['id'], 'estimated rice')
    payload = meal()
    payload['items'][0]['food_id'] = saved['template']['food']['id']
    assert asta_meals.add(db, payload)['status'] == 'flagged'


def test_argument_errors_are_json(capsys):
    assert asta.main(['weight', 'add', 'not-a-number']) == 1
    assert json.loads(capsys.readouterr().out)['status'] == 'error'


@pytest.mark.parametrize('binding', ['asta', 'general'])
def test_daily_delivery_checks_current_binding(tmp_path, monkeypatch, binding):
    import asta_daily
    import telegram_notify
    home = tmp_path
    with open_store(home / '.local/state/achios/asta/asta.sqlite3'):
        pass
    private = home / '.config/achios/asta'
    private.mkdir(parents=True)
    env = private / 'delivery.env'
    env.write_text('TELEGRAM_BOT_TOKEN=fixture\nTELEGRAM_CHAT_ID=-123\n')
    (private / 'delivery.json').write_text(json.dumps({'env_path': str(env), 'thread_id': 42}))
    hub = home / '.local/state/achicore-hub'
    hub.mkdir()
    (hub / 'topics.json').write_text(json.dumps({'-123:42': binding}))
    monkeypatch.setattr(asta_daily.gcal, 'user_home', lambda: home)
    monkeypatch.setattr(asta_daily, 'sessions', lambda _: {'status': 'ok', 'events': []})
    calls = []
    monkeypatch.setattr(telegram_notify, 'send', lambda *a, **kw: calls.append((a, kw)))
    if binding == 'asta':
        assert asta_daily.main(['--date', '2026-09-21']) == 0
        assert calls[0][1]['thread_id'] == 42
    else:
        with pytest.raises(AstaError, match='binding_mismatch'):
            asta_daily.main(['--date', '2026-09-21'])
        assert calls == []
