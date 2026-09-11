"""Queue deadline reminders, weekly and daily digests and the one-time catch-up.

Each notice claims a key in `notices` in the same transaction as its events, so
a notice is queued once. Only current windows are considered, which means a run
after downtime never replays a missed day or an elapsed reminder window.
"""
from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone

from canvas_events import enqueue
from canvas_store import MANILA, parse_time, unfinished

HOUR = timedelta(hours=1)


def load(db):
    courses = {row["id"]: row["code"] for row in db.execute("SELECT id,code FROM courses WHERE active=1")}
    items = {"assignments": [], "announcements": [], "grades": []}
    for row in db.execute("SELECT course_id,category,data FROM records WHERE active=1 ORDER BY course_id,id"):
        if row["course_id"] in courses and row["category"] in items:
            items[row["category"]].append({**json.loads(row["data"]), "course_id": row["course_id"],
                                           "subject": courses[row["course_id"]]})
    as_of = db.execute("""SELECT min(success_at) FROM coverage JOIN courses ON courses.id=coverage.course_id
        WHERE courses.active=1 AND category='assignments'""").fetchone()[0]
    return items, as_of


def deadline(item):
    return {key: item.get(key) for key in ("subject", "name", "due_at", "source_url")}


def announcement(item):
    return {key: item.get(key) for key in ("subject", "title", "posted_at", "source_url")}


def grade(item):
    return {key: item.get(key) for key in ("subject", "current_grade", "current_score", "source_url")}


def between(items, start, end, field="due_at"):
    return [item for item in items if item.get(field) and start <= parse_time(item[field]) < end]


def soonest(items):
    return sorted(items, key=lambda item: (parse_time(item["due_at"]), item["subject"]))


def remind(db, now=None):
    now = now or datetime.now(timezone.utc)
    at = now.isoformat()
    local = now.astimezone(MANILA)
    items, as_of = load(db)
    open_work = [item for item in items["assignments"] if item.get("due_at") and unfinished(item)]
    grades = [grade(item) for item in items["grades"]]
    queued = {}

    def queue(key, events):
        with db:
            claimed = db.execute("INSERT OR IGNORE INTO notices(key,created_at) VALUES(?,?)", (key, at)).rowcount
            if claimed:
                for course_id, kind, data in events:
                    enqueue(db, course_id, kind, data, at)
                    queued[kind] = queued.get(kind, 0) + 1
        return claimed

    def deadlines(title, empty, rows):
        return None, "deadline_digest", {"title": title, "empty": empty, "as_of": as_of,
                                         "items": [deadline(item) for item in soonest(rows)]}

    def announcements(title, empty, rows):
        rows = sorted(rows, key=lambda item: item.get("posted_at") or "", reverse=True)
        return None, "announcement_digest", {"title": title, "empty": empty,
                                             "items": [announcement(item) for item in rows]}

    latest = {}
    for item in items["announcements"]:
        current = latest.get(item["course_id"])
        if current is None or (item.get("posted_at") or "") > (current.get("posted_at") or ""):
            latest[item["course_id"]] = item
    # The catch-up already covers today, so its run claims today's digest silently.
    caught_up = queue("catchup:v1", [
        deadlines("Due from now", "Nothing due from now", between(open_work, now, datetime.max.replace(tzinfo=timezone.utc))),
        announcements("Latest announcements", "No announcements yet", list(latest.values())),
        (None, "grade_digest", {"title": "Course grades", "items": grades}),
    ])

    if local.hour >= 8:
        midnight = local.replace(hour=0, minute=0, second=0, microsecond=0)
        if local.weekday() == 0:
            year, week, _ = local.isocalendar()
            queue(f"weekly:{year}-W{week:02d}", [] if caught_up else [
                deadlines("Due this week", f"📅 Week of {local:%a %d %b}: nothing due",
                          between(open_work, midnight, midnight + timedelta(days=7))),
                announcements("Announcements this past week", "No announcements this past week",
                               between(items["announcements"], now - timedelta(days=7), now, "posted_at")),
                (None, "grade_digest", {"title": "Course grades", "items": grades}),
            ])
        else:
            recent = between(items["announcements"], now - timedelta(days=1), now, "posted_at")
            events = [deadlines("Due today", "Nothing due today",
                                between(open_work, now, midnight + timedelta(days=1, hours=8)))]
            if recent:
                events.append(announcements("New announcements today", "", recent))
            queue(f"daily:{local.date().isoformat()}", [] if caught_up else events)

    for item in open_work:
        left = parse_time(item["due_at"]) - now
        tag = "1h" if timedelta(0) < left <= HOUR else "3h" if HOUR < left <= 3 * HOUR else None
        if tag:
            queue(f"reminder:{item['course_id']}:{item['id']}:{item['due_at']}:{tag}",
                  [(item["course_id"], "deadline_reminder", deadline(item))])
    return {"queued": queued}
