#!/usr/bin/env python3
"""Read daily Asta totals and deliver the scheduled summary to its topic."""
from __future__ import annotations

import argparse
import json
import sys
import subprocess
from datetime import date, datetime
from pathlib import Path

import gcal
from asta import day, weight_trend
from asta_meals import listing
from asta_store import AstaError, MANILA, latest, now, open_reader


def sessions(on):
    config = gcal.load_config()
    entry = gcal.find_calendar(config, 'workouts')
    return gcal.read_events([entry], date.fromisoformat(on), date.fromisoformat(on))


def today(db, on, calendar_reader=None):
    day(on)
    meals = listing(db, on)['meals']
    totals = {key: {bound: round(sum(m['totals'][key][bound] for m in meals), 4)
                    for bound in ('min', 'estimate', 'max')}
              for key in ('kcal', 'protein', 'carbs', 'fat')} if meals else None
    warnings = []
    try:
        calendar = (calendar_reader or sessions)(on)
        if calendar.get('status') != 'ok' or calendar.get('errors'):
            warnings.append('calendar_unavailable_or_partial')
    except (gcal.GcalError, OSError, ValueError, TimeoutError, subprocess.TimeoutExpired):
        calendar = {'events': []}
        warnings.append('calendar_unavailable')
    calendar_sessions = calendar.get('events', [])
    event_ids = [event.get('event_id') for event in calendar_sessions
                 if isinstance(event, dict) and event.get('event_id')]
    if event_ids:
        placeholders = ','.join('?' for _ in event_ids)
        adherence = [dict(row) for row in db.execute(
            f'SELECT * FROM adherence WHERE event_id IN ({placeholders})', event_ids,
        )]
    else:
        adherence = []
    return {'status': 'ok', 'date': on, 'totals': totals, 'meal_count': len(meals),
            'flagged_count': sum(m['status'] == 'flagged' for m in meals),
            'targets': latest(db, 'targets'), 'weight': weight_trend(db, on),
            'sessions': calendar_sessions, 'warnings': warnings,
            'adherence': adherence,
            'latest_meal_at': max((m['occurred_at'] for m in meals), default=None)}


def adherence_set(db, event, state):
    from asta import text
    text(event, 'event_id', 500)
    if state not in ('done', 'skipped', 'moved'):
        raise AstaError('invalid_adherence')
    with db:
        db.execute('INSERT INTO adherence VALUES(?,?,?,?) ON CONFLICT(event_id) DO UPDATE SET state=excluded.state,at=excluded.at',
                   (event, state, 'manual', now()))
    return {'status': 'ok', 'event_id': event, 'state': state, 'source': 'manual'}


def render(data):
    lines = ['Asta, ' + data['date']]
    if data['totals'] is None:
        lines.append('No meals logged today. Food intake is unknown.')
    else:
        total = data['totals']['kcal']
        lines.append(f"Logged {total['estimate']:g} kcal, range {total['min']:g} to {total['max']:g}.")
        lines.append(f"{data['meal_count']} meals, {data['flagged_count']} flagged. Unlogged food is not included.")
        lines.append('Protein: ' + str(data['totals']['protein']['estimate']) + ' g.')
        if data['targets']:
            lines.append(f"Saved target: {data['targets']['kcal']['value']:g} kcal.")
    avg = data['weight']['seven_day_average']
    if avg is not None:
        lines.append(f'Weight average over recorded days this week: {avg:g} kg.')
    if data['warnings']:
        lines.append('Calendar data is unavailable or incomplete.')
    adherence = {r['event_id']: r['state'] for r in data['adherence']}
    for event in data['sessions']:
        title = event.get('summary', event.get('title', 'Scheduled session'))
        state = adherence.get(event.get('event_id'))
        lines.append(f"{title}: {state or 'done, skipped or moved?'}")
    return '\n'.join(lines)


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--dry-run', action='store_true')
    p.add_argument('--date', default=datetime.now(MANILA).date().isoformat())
    args = p.parse_args(argv)
    home = gcal.user_home()
    with open_reader(home / '.local/state/achios/asta/asta.sqlite3') as db:
        message = render(today(db, args.date))
    if args.dry_run:
        print(message)
        return 0
    import telegram_notify
    config = json.loads((home / '.config/achios/asta/delivery.json').read_text())
    if type(config.get('thread_id')) is not int or config['thread_id'] <= 0:
        raise AstaError('invalid_asta_thread')
    values = telegram_notify.read_env(config['env_path'])
    if not values.get('TELEGRAM_BOT_TOKEN') or not values.get('TELEGRAM_CHAT_ID'):
        raise AstaError('asta_delivery_credentials_missing')
    bindings_path = home / '.local/state/achicore-hub/topics.json'
    bindings = json.loads(bindings_path.read_text())
    key = str(values['TELEGRAM_CHAT_ID']) + ':' + str(config['thread_id'])
    if not isinstance(bindings, dict) or bindings.get(key) != 'asta':
        raise AstaError('asta_topic_binding_mismatch')
    telegram_notify.send(message, env_path=config['env_path'], thread_id=config['thread_id'])
    return 0


if __name__ == '__main__':
    sys.exit(main())
