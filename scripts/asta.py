#!/usr/bin/env python3
"""Asta's JSON interface for profiles, nutrition and training records."""
from __future__ import annotations

import argparse
import json
import math
import sqlite3
import sys
from datetime import date, datetime, timedelta
from pathlib import Path

from asta_store import AstaError, MANILA, encoded, latest, now, open_reader, open_store
from gcal import user_home

PROFILE_NUMBERS = {'age': (18, 120), 'height_cm': (100, 250), 'weight_kg': (25, 400),
                   'activity_factor': (1.1, 2.5), 'proactivity': (0, 10)}
PROFILE_TEXT = {'goal_description', 'training_experience', 'current_activity', 'schedule',
                'session_length', 'equipment', 'locations', 'exercise_preferences',
                'limitations', 'injuries', 'nutrition_goal', 'tracking_precision',
                'common_meals', 'dietary_restrictions', 'portion_habits', 'meal_times',
                'coaching_tone', 'check_in_preferences', 'eating_habits', 'allergies'}
REQUIRED = ('sex', 'age', 'height_cm', 'weight_kg', 'activity_factor', 'goal')
MACROS = ('kcal', 'protein', 'carbs', 'fat')


def number(value, field, low=0, high=100000):
    if type(value) not in (int, float) or not math.isfinite(value) or not low <= value <= high:
        raise AstaError('invalid_' + field)
    return value


def obj(value, allowed, required=()):
    if not isinstance(value, dict) or set(value) - set(allowed) or set(required) - set(value):
        raise AstaError('invalid_fields')
    return value


def text(value, field, limit=10000):
    if not isinstance(value, str) or not value.strip() or len(value) > limit:
        raise AstaError('invalid_' + field)
    return value


def day(value):
    try:
        parsed = date.fromisoformat(value)
        if parsed.isoformat() != value:
            raise ValueError
        return value
    except (ValueError, TypeError):
        raise AstaError('invalid_date') from None


def profile_show(db):
    profile = latest(db, 'profiles')
    return {'status': 'ok', 'profile': profile,
            'missing': [key for key in REQUIRED if not profile or profile.get(key) is None]}


def profile_set(db, patch):
    obj(patch, set(PROFILE_NUMBERS) | PROFILE_TEXT | {'sex', 'goal', 'gain_percent'})
    if not patch:
        raise AstaError('empty_profile')
    for key, value in patch.items():
        if value is None:
            continue
        if key in PROFILE_NUMBERS:
            number(value, key, *PROFILE_NUMBERS[key])
        elif key in PROFILE_TEXT:
            text(value, key)
        elif key == 'sex' and value not in ('male', 'female'):
            raise AstaError('invalid_sex')
        elif key == 'goal' and value not in ('cut', 'maintain', 'lean_gain'):
            raise AstaError('invalid_goal')
        elif key == 'gain_percent':
            number(value, key, 5, 10)
    with db:
        db.execute('BEGIN IMMEDIATE')
        old = latest(db, 'profiles') or {}
        merged = {k: v for k, v in old.items() if k not in ('version', 'at')}
        merged.update(patch)
        db.execute('INSERT INTO profiles(at,data) VALUES(?,?)', (now(), encoded(merged)))
    return profile_show(db)


def targets_suggest(db):
    state = profile_show(db)
    if state['missing']:
        return {'status': 'needs_answer', 'missing': state['missing']}
    p = state['profile']
    bmr = 10 * p['weight_kg'] + 6.25 * p['height_cm'] - 5 * p['age'] + (5 if p['sex'] == 'male' else -161)
    adjustment = {'cut': -.15, 'maintain': 0, 'lean_gain': (p.get('gain_percent') or 5) / 100}[p['goal']]
    kcal = bmr * p['activity_factor'] * (1 + adjustment)
    protein, fat = 1.8 * p['weight_kg'], .8 * p['weight_kg']
    carbs = (kcal - protein * 4 - fat * 9) / 4
    if carbs < 0:
        return {'status': 'needs_answer', 'missing': [], 'question': 'Review the profile before setting targets.'}
    values = dict(zip(MACROS, (kcal, protein, carbs, fat)))
    return {'status': 'ok', 'profile_version': p['version'], 'bmr': round(bmr, 2),
            'maintenance_kcal': round(bmr * p['activity_factor'], 2),
            'targets': {key: round(value, 2) for key, value in values.items()}}


def targets_set(db, data):
    obj(data, MACROS, MACROS)
    result = {}
    with db:
        db.execute('BEGIN IMMEDIATE')
        suggestion = targets_suggest(db)
        for key in MACROS:
            entry = obj(data[key], ('value', 'source'), ('value', 'source'))
            number(entry['value'], key, 0 if key != 'kcal' else 1, 20000 if key == 'kcal' else 2000)
            if entry['source'] not in ('computed', 'overridden'):
                raise AstaError('invalid_target_source')
            if entry['source'] == 'computed' and (suggestion['status'] != 'ok' or
                    abs(entry['value'] - suggestion['targets'][key]) > .01):
                raise AstaError('computed_target_mismatch')
            result[key] = dict(entry)
        result['profile_version'] = (latest(db, 'profiles') or {}).get('version')
        db.execute('INSERT INTO targets(at,data) VALUES(?,?)', (now(), encoded(result)))
    return {'status': 'ok', 'targets': latest(db, 'targets')}


def weight_add(db, kg, on):
    number(kg, 'weight_kg', 25, 400)
    day(on)
    with db:
        db.execute('INSERT INTO weights VALUES(?,?,?) ON CONFLICT(date) DO UPDATE SET kg=excluded.kg,at=excluded.at',
                   (on, kg, now()))
    return {'status': 'ok', 'date': on, 'kg': kg}


def weight_trend(db, on=None):
    on = day(on or datetime.now(MANILA).date().isoformat())
    start = (date.fromisoformat(on) - timedelta(days=6)).isoformat()
    rows = [dict(row) for row in db.execute('SELECT date,kg FROM weights WHERE date<=? ORDER BY date DESC LIMIT 30', (on,))]
    current = [r['kg'] for r in rows if r['date'] >= start]
    return {'status': 'ok', 'entries': rows, 'seven_day_average': round(sum(current) / len(current), 3) if current else None,
            'sample_count': len(current), 'from': start, 'to': on}


class JsonParser(argparse.ArgumentParser):
    def error(self, message):
        raise AstaError('invalid_arguments: ' + message)


def parser():
    p = JsonParser(description=__doc__)
    p.add_argument('--db', type=Path)
    commands = p.add_subparsers(dest='command', required=True)
    commands.add_parser('status')
    for group, actions in [('profile', ('show', 'set')), ('targets', ('show', 'suggest', 'set'))]:
        subs = commands.add_parser(group).add_subparsers(dest='action', required=True)
        for action in actions:
            sub = subs.add_parser(action)
            if action == 'set':
                sub.add_argument('--json', required=True)
    subs = commands.add_parser('weight').add_subparsers(dest='action', required=True)
    add = subs.add_parser('add')
    add.add_argument('kg', type=float)
    add.add_argument('--date', default=datetime.now(MANILA).date().isoformat())
    subs.add_parser('trend')
    for group in ('food', 'template'):
        subs = commands.add_parser(group).add_subparsers(dest='action', required=True)
        search = subs.add_parser('search')
        search.add_argument('query')
        if group == 'template':
            save = subs.add_parser('save')
            save.add_argument('--from-meal', required=True)
            save.add_argument('--name', required=True)
    subs = commands.add_parser('meal').add_subparsers(dest='action', required=True)
    for action in ('add', 'list', 'show', 'correct', 'delete'):
        sub = subs.add_parser(action)
        if action in ('show', 'correct', 'delete'):
            sub.add_argument('id')
        if action in ('add', 'correct'):
            sub.add_argument('--json', required=True)
        if action == 'list':
            sub.add_argument('--date')
            sub.add_argument('--flagged', action='store_true')
    today = commands.add_parser('today')
    today.add_argument('--date', default=datetime.now(MANILA).date().isoformat())
    adherence = commands.add_parser('adherence').add_subparsers(dest='action', required=True).add_parser('set')
    adherence.add_argument('--event', required=True)
    adherence.add_argument('state', choices=('done', 'skipped', 'moved'))
    return p


def main(argv=None):
    try:
        args = parser().parse_args(argv)
        path = args.db or user_home() / '.local/state/achios/asta/asta.sqlite3'
        data = None
        if getattr(args, 'json', None):
            data = json.loads(sys.stdin.read() if args.json == '-' else Path(args.json).read_text())
        action = getattr(args, 'action', None)
        read_only = (args.command == 'today' or
                     args.command in ('profile', 'targets') and action in ('show', 'suggest') or
                     args.command == 'weight' and action == 'trend' or
                     args.command == 'meal' and action in ('list', 'show') or
                     args.command == 'template' and action == 'search')
        with (open_reader(path) if read_only else open_store(path)) as db:
            if args.command == 'status':
                freshness = {}
                for table in ('profiles', 'targets', 'weights', 'meals', 'corrections', 'adherence'):
                    freshness[table] = db.execute(f'SELECT MAX(at) FROM {table}').fetchone()[0]
                result = {'status': 'ok', 'schema_version': 1, 'missing_setup': profile_show(db)['missing'],
                          'freshness': freshness,
                          'last_write': max((value for value in freshness.values() if value), default=None)}
            elif args.command == 'profile':
                result = profile_set(db, data) if args.action == 'set' else profile_show(db)
            elif args.command == 'targets':
                result = targets_set(db, data) if args.action == 'set' else targets_suggest(db) if args.action == 'suggest' else {'status': 'ok', 'targets': latest(db, 'targets')}
            elif args.command == 'today':
                from asta_daily import today
                result = today(db, args.date)
            elif args.command == 'adherence':
                from asta_daily import adherence_set
                result = adherence_set(db, args.event, args.state)
            elif args.command == 'food':
                from asta_food import search
                result = search(db, args.query, path.parent / 'staples.json',
                                user_home() / '.config/achios/asta/usda.key')
            elif args.command == 'template':
                from asta_food import template_save, template_search
                result = template_save(db, args.from_meal, args.name) if args.action == 'save' else {
                    'status': 'ok', 'templates': template_search(db, args.query)}
            elif args.command == 'meal':
                import asta_meals
                config = asta_meals.thresholds(user_home() / '.config/achios/asta/config.json')
                if args.action == 'add':
                    result = asta_meals.add(db, data, config)
                elif args.action == 'correct':
                    result = asta_meals.correct(db, args.id, data, config)
                elif args.action == 'list':
                    result = asta_meals.listing(db, args.date, args.flagged)
                elif args.action == 'show':
                    result = asta_meals.show(db, args.id)
                else:
                    result = asta_meals.delete(db, args.id)
            else:
                result = weight_add(db, args.kg, args.date) if args.action == 'add' else weight_trend(db)
        print(encoded(result))
        return 0
    except (AstaError, OSError, sqlite3.Error, json.JSONDecodeError) as exc:
        print(encoded({'status': 'error', 'error': str(exc) if isinstance(exc, AstaError) else type(exc).__name__}))
        return 1


if __name__ == '__main__':
    sys.exit(main())
