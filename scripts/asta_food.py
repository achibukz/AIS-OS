"""Resolve nutrient records without treating missing values as zero."""
from __future__ import annotations

import json
from datetime import datetime, timedelta

import requests

from asta_store import AstaError, encoded, now, safe_path

NUTRIENTS = {'kcal': 1008, 'protein': 1003, 'carbs': 1005, 'fat': 1004}
ENERGY_NUTRIENTS = (1008, 2047, 2048)


def validate_food(food):
    from asta import MACROS, day, number, obj, text
    obj(food, ('id', 'label', 'source', 'source_id', 'copied_at', 'per_100g', 'estimated'),
        ('id', 'label', 'source', 'source_id', 'per_100g'))
    for key in ('id', 'label', 'source', 'source_id'):
        text(food[key], key, 500)
    obj(food['per_100g'], MACROS, MACROS)
    for key in MACROS:
        number(food['per_100g'][key], key, 0, 1000 if key == 'kcal' else 100)
    if 'estimated' in food and type(food['estimated']) is not bool:
        raise AstaError('invalid_estimated')
    if food['source'] == 'philfct':
        day(food.get('copied_at'))
    return food


def template_search(db, query):
    return [{'name': r['name'], 'sample_count': r['samples'], **json.loads(r['data'])}
            for r in db.execute('SELECT * FROM templates ORDER BY name')
            if query.casefold() in r['name'].casefold()]


def search(db, query, seed_path, key_path, at=None, transport=None):
    from asta import text
    text(query, 'query', 200)
    at = at or datetime.fromisoformat(now())
    warnings, foods = [], []
    templates = template_search(db, query)
    for template in templates:
        foods.append(template['food'])
    seed_path = safe_path(seed_path)
    if seed_path.exists():
        try:
            seed = json.loads(seed_path.read_text())
            if not isinstance(seed, list):
                raise AstaError('invalid_seed')
            for row in seed:
                try:
                    row = validate_food(row)
                    if row['source'] != 'philfct' or row['id'] != 'philfct:' + row['source_id']:
                        raise AstaError('invalid_seed')
                    if query.casefold() in row['label'].casefold():
                        foods.append(row)
                except (AstaError, TypeError):
                    warnings.append('malformed_staple_row')
        except (OSError, ValueError):
            warnings.append('staples_unavailable')
    cache = db.execute('SELECT * FROM food_cache WHERE query=?', (query.casefold(),)).fetchone()
    remote = None
    if cache and timedelta(0) <= at - datetime.fromisoformat(cache['at']) < timedelta(days=7):
        remote = json.loads(cache['data'])
    else:
        try:
            key = safe_path(key_path).read_text().strip()
            if not key:
                raise FileNotFoundError
            response = (transport or requests.get)(
                'https://api.nal.usda.gov/fdc/v1/foods/search',
                params={'api_key': key, 'query': query, 'pageSize': 10,
                        'dataType': ['Foundation', 'SR Legacy', 'Survey (FNDDS)']}, timeout=15)
            response.raise_for_status()
            payload = response.json()
            if not isinstance(payload, dict) or not isinstance(payload.get('foods'), list):
                raise AstaError('usda_response_invalid')
            remote = []
            for food in payload['foods']:
                if not isinstance(food, dict) or not isinstance(food.get('foodNutrients'), list):
                    raise AstaError('usda_response_invalid')
                nutrients = {n['nutrientId']: n['value'] for n in food.get('foodNutrients', [])
                             if isinstance(n, dict) and 'nutrientId' in n and 'value' in n}
                energy_id = next((value for value in ENERGY_NUTRIENTS if value in nutrients), None)
                macro_ids = {value for name, value in NUTRIENTS.items() if name != 'kcal'}
                if energy_id is None or not macro_ids <= nutrients.keys():
                    warnings.append('usda_food_missing_nutrients')
                    continue
                record = {'id': 'usda:' + str(food['fdcId']), 'source_id': str(food['fdcId']),
                          'label': food['description'], 'source': 'usda',
                          'per_100g': {
                              **{name: nutrients[value] for name, value in NUTRIENTS.items()
                                 if name != 'kcal'},
                              'kcal': nutrients[energy_id],
                          }}
                remote.append(validate_food(record))
            with db:
                db.execute('INSERT OR REPLACE INTO food_cache VALUES(?,?,?)',
                           (query.casefold(), at.isoformat(), encoded(remote)))
        except FileNotFoundError:
            warnings.append('usda_key_missing')
        except (OSError, requests.RequestException, ValueError, KeyError, TypeError):
            warnings.append('usda_unavailable')
            remote = None
    foods.extend(remote or [])
    foods = list({f['id']: f for f in foods}.values())
    with db:
        for food in foods:
            db.execute('INSERT OR REPLACE INTO foods VALUES(?,?)', (food['id'], encoded(food)))
    return {'status': 'ok', 'foods': foods, 'warnings': sorted(set(warnings))}


def template_save(db, meal_id, name):
    from asta import text
    from asta_meals import show
    text(name, 'template_name', 200)
    meal = show(db, meal_id)['meal']
    items = meal['items']
    if any(i['grams']['min'] != i['grams']['max'] for i in items):
        raise AstaError('template_requires_confirmed_grams')
    grams = sum(i['grams']['estimate'] for i in items)
    if grams <= 0:
        raise AstaError('empty_template')
    food = {'id': 'template:' + name, 'source_id': name, 'source': 'template', 'label': name,
            'per_100g': {k: v['estimate'] / grams * 100 for k, v in meal['totals'].items()},
            'estimated': any(i['nutrient_source']['source'] == 'density_estimate' or
                             i['nutrient_source'].get('estimated') for i in items)}
    data = {'food': food, 'meal_id': meal_id, 'items': items}
    with db:
        db.execute('INSERT INTO templates VALUES(?,?,1) ON CONFLICT(name) DO UPDATE SET data=excluded.data,samples=templates.samples+1',
                   (name, encoded(data)))
        db.execute('INSERT OR REPLACE INTO foods VALUES(?,?)', (food['id'], encoded(food)))
    return {'status': 'ok', 'template': data}
