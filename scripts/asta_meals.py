"""Compute meal nutrients and keep the original estimate through corrections."""
from __future__ import annotations

import copy
import json
import uuid
from datetime import datetime
from pathlib import Path

from asta_store import AstaError, MANILA, encoded, now

DEFAULT_CONFIG = Path(__file__).resolve().parents[1] / 'config/asta.example.json'


def thresholds(path=None):
    from asta import number, obj
    defaults = json.loads(DEFAULT_CONFIG.read_text())
    if path is not None and path.exists():
        patch = json.loads(path.read_text())
        obj(patch, defaults)
        defaults.update(patch)
    for key, value in defaults.items():
        number(value, key, 0, 1 if key.endswith(('identity', 'fraction')) else 10000)
    return defaults


def calculate(db, payload, config=None):
    from asta import MACROS, number, obj, text
    obj(payload, ('schema_version', 'occurred_at', 'meal_type', 'source', 'photo_path',
                  'original_text', 'model_id', 'effort', 'prompt_version', 'items'),
        ('schema_version', 'occurred_at', 'meal_type', 'source', 'model_id', 'effort', 'prompt_version', 'items'))
    if type(payload['schema_version']) is not int or payload['schema_version'] != 1:
        raise AstaError('unsupported_meal_schema')
    for key in ('meal_type', 'model_id', 'effort', 'prompt_version'):
        text(payload[key], key, 200)
    if payload['source'] not in ('text', 'photo'):
        raise AstaError('invalid_meal_source')
    if 'original_text' in payload and not isinstance(payload['original_text'], str):
        raise AstaError('invalid_original_text')
    try:
        at = datetime.fromisoformat(payload['occurred_at'])
        if at.tzinfo is None:
            raise ValueError
    except (ValueError, TypeError):
        raise AstaError('invalid_meal_timestamp') from None
    items = payload['items']
    if not isinstance(items, list) or not 1 <= len(items) <= 100:
        raise AstaError('invalid_items')
    totals = {k: {bound: 0.0 for bound in ('min', 'estimate', 'max')} for k in MACROS}
    calculated = []
    density_used, low_identity = False, False
    config = config or thresholds()
    for raw in items:
        obj(raw, ('label', 'preparation', 'food_id', 'density_estimate', 'grams',
                  'identity_confidence', 'portion_confidence', 'hidden_ingredient_risk', 'assumptions'),
            ('label', 'grams', 'identity_confidence', 'portion_confidence', 'hidden_ingredient_risk', 'assumptions'))
        text(raw['label'], 'label', 500)
        if 'preparation' in raw:
            text(raw['preparation'], 'preparation', 500)
        for key in ('identity_confidence', 'portion_confidence'):
            number(raw[key], key, 0, 1)
        if raw['hidden_ingredient_risk'] not in ('low', 'medium', 'high'):
            raise AstaError('invalid_hidden_ingredient_risk')
        if not isinstance(raw['assumptions'], list) or any(not isinstance(a, str) for a in raw['assumptions']):
            raise AstaError('invalid_assumptions')
        grams = obj(raw['grams'], ('min', 'estimate', 'max'), ('min', 'estimate', 'max'))
        for key, value in grams.items():
            number(value, 'grams_' + key, 0, 10000)
        if not grams['min'] <= grams['estimate'] <= grams['max'] or grams['estimate'] <= 0:
            raise AstaError('invalid_grams_range')
        if ('food_id' in raw) == ('density_estimate' in raw):
            raise AstaError('choose_food_or_density')
        if 'food_id' in raw:
            text(raw['food_id'], 'food_id', 500)
            row = db.execute('SELECT data FROM foods WHERE id=?', (raw['food_id'],)).fetchone()
            if not row:
                raise AstaError('unknown_food_id')
            food = json.loads(row['data'])
            nutrients = food['per_100g']
            source = {'source': food['source'], 'source_id': food['source_id'],
                      'estimated': bool(food.get('estimated'))}
            density_used |= source['estimated']
        else:
            nutrients = obj(raw['density_estimate'], MACROS, MACROS)
            source = {'source': 'density_estimate', 'source_id': None}
            density_used = True
        for key in MACROS:
            number(nutrients[key], key, 0, 1000 if key == 'kcal' else 100)
        item_totals = {k: {b: nutrients[k] * grams[b] / 100 for b in grams} for k in MACROS}
        for key in MACROS:
            for bound in grams:
                totals[key][bound] += item_totals[key][bound]
        low_identity |= raw['identity_confidence'] < config['needs_answer_identity']
        calculated.append({**copy.deepcopy(raw), 'nutrient_source': source,
                           'per_100g': nutrients, 'totals': item_totals})
    point = totals['kcal']['estimate']
    width = totals['kcal']['max'] - totals['kcal']['min']
    if low_identity or width > max(config['needs_answer_kcal'], config['needs_answer_fraction'] * point):
        uncertain = max(calculated, key=lambda i: max(i['totals']['kcal']['max'] - i['totals']['kcal']['min'],
                        i['totals']['kcal']['estimate'] * (1 - i['identity_confidence'])))
        return {'status': 'needs_answer', 'question': 'Can you confirm the food and amount of ' + uncertain['label'] + '?'}
    tier = 'flagged' if density_used or width > max(config['flagged_kcal'], config['flagged_fraction'] * point) else 'committed'
    return {**copy.deepcopy(payload), 'status': tier, 'confidence': 'medium' if tier == 'flagged' else 'high',
            'date': at.astimezone(MANILA).date().isoformat(), 'items': calculated,
            'totals': {k: {b: round(v, 4) for b, v in bounds.items()} for k, bounds in totals.items()}}


def add(db, payload, config=None, attachments=None, meals_root=None):
    result = calculate(db, payload, config)
    if result['status'] == 'needs_answer':
        return result
    photo = None
    if payload.get('photo_path') or payload['source'] == 'photo':
        from asta_media import inspect_photo
        from gcal import user_home
        home = user_home()
        attachments = attachments or home / '.local/state/achicore-hub/attachments'
        meals_root = meals_root or home / 'Documents/Files/training/asta/meals'
        photo = inspect_photo(payload.get('photo_path'), attachments)
    meal_id = uuid.uuid4().hex
    with db:
        db.execute('BEGIN IMMEDIATE')
        if photo:
            from asta_media import retain
            result['media'] = retain(db, photo, meals_root, result['date'])
            result['image_hash'] = photo['hash']
            result.pop('photo_path', None)
        db.execute('INSERT INTO meals VALUES(?,?,?,?,?,?)',
                   (meal_id, result['date'], now(), encoded(result), encoded(result), result['status']))
    if photo:
        from asta_media import finish
        try:
            finish(photo)
        except OSError:
            result['warnings'] = ['attachment_cleanup_pending']
    return {'id': meal_id, **result}


def show(db, meal_id):
    row = db.execute('SELECT * FROM meals WHERE id=?', (meal_id,)).fetchone()
    if not row:
        raise AstaError('meal_not_found')
    corrections = [{**dict(r), 'old': json.loads(r['old']), 'new': json.loads(r['new'])}
                   for r in db.execute('SELECT * FROM corrections WHERE meal_id=? ORDER BY id', (meal_id,))]
    return {'status': 'ok', 'id': meal_id, 'meal': json.loads(row['current']),
            'original': json.loads(row['original']), 'corrections': corrections}


def listing(db, on=None, flagged=False):
    from asta import day
    if on:
        day(on)
    rows = db.execute('SELECT * FROM meals WHERE (? IS NULL OR date=?) AND (?=0 OR tier=?) ORDER BY date,at',
                      (on, on, int(flagged), 'flagged'))
    return {'status': 'ok', 'meals': [{'id': r['id'], **json.loads(r['current'])} for r in rows]}


def correct(db, meal_id, patch, config=None):
    from asta import obj, text
    obj(patch, ('items', 'reason'), ('items', 'reason'))
    text(patch['reason'], 'reason')
    with db:
        db.execute('BEGIN IMMEDIATE')
        previous = show(db, meal_id)['meal']
        payload = {k: v for k, v in previous.items() if k in ('schema_version', 'occurred_at', 'meal_type',
                   'source', 'photo_path', 'original_text', 'model_id', 'effort', 'prompt_version')}
        payload['items'] = patch['items']
        result = calculate(db, payload, config)
        if result['status'] == 'needs_answer':
            return result
        for key in ('media', 'image_hash'):
            if key in previous:
                result[key] = previous[key]
        db.execute('INSERT INTO corrections(meal_id,at,field,old,new,reason) VALUES(?,?,?,?,?,?)',
                   (meal_id, now(), 'items', encoded(previous['items']), encoded(result['items']), patch['reason']))
        db.execute('UPDATE meals SET current=?,tier=? WHERE id=?', (encoded(result), result['status'], meal_id))
    return {'id': meal_id, **result}


def delete(db, meal_id):
    with db:
        result = db.execute('DELETE FROM meals WHERE id=?', (meal_id,))
        if not result.rowcount:
            raise AstaError('meal_not_found')
    return {'status': 'ok', 'deleted': meal_id}
