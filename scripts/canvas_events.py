"""Persist observed Canvas transitions and retry unconfirmed deliveries."""
from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

from canvas_client import CONFIG, CanvasError, timestamp


def enqueue(db, course_id, kind, data, at):
    db.execute("INSERT INTO events(course_id,kind,data,observed_at) VALUES(?,?,?,?)",
               (course_id, kind, json.dumps(data, ensure_ascii=False), at))


def record_changes(db, course_id, category, records, at, previous=None):
    coverage = db.execute("SELECT baseline FROM coverage WHERE course_id=? AND category=?",
                          (course_id, category)).fetchone()
    if not coverage or not coverage["baseline"]:
        return
    if previous is None:
        previous = {row["id"]: json.loads(row["data"]) for row in db.execute(
            "SELECT id,data FROM records WHERE course_id=? AND category=?", (course_id, category))}
    for record in records:
        old = previous.get(record["id"])
        if category == "assignments":
            if old is None:
                enqueue(db, course_id, "new_assignment", record, at)
                continue
            if old["due_at"] != record["due_at"]:
                enqueue(db, course_id, "due_date_changed", {**record, "previous_due_at": old["due_at"]}, at)
            grade_available = record.get("grade_available", True)
            became_available = grade_available and not old.get("grade_available", True)
            grade_changed = (old["grade"], old["score"]) != (record["grade"], record["score"])
            if grade_available and grade_changed and (old.get("grade_success_at") is not None or became_available):
                enqueue(db, course_id, "assignment_grade_changed", record, at)
        elif category == "announcements" and old is None:
            enqueue(db, course_id, "new_announcement", record, at)
        elif category == "grades":
            keys = ("current_grade", "current_score", "final_grade", "final_score")
            if old is None:
                if any(record[key] is not None for key in keys):
                    enqueue(db, course_id, "course_grade_changed", record, at)
            elif any(old[key] != record[key] for key in keys):
                enqueue(db, course_id, "course_grade_changed", record, at)


def local_date(value):
    if value is None:
        return "no due date"
    return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(ZoneInfo("Asia/Manila")).strftime("%a %d %b, %I:%M %p Manila")


def grade_value(value):
    return "unavailable" if value is None else str(value)


def parse(value):
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def manila(value):
    return parse(value).astimezone(ZoneInfo("Asia/Manila"))


def countdown(due, now):
    left = due - now
    if left <= timedelta(0):
        return "overdue"
    if left < timedelta(hours=1):
        return f"in {max(1, int(left.total_seconds() // 60))}m"
    if left < timedelta(hours=48):
        return f"in {int(left.total_seconds() // 3600)}h"
    return f"in {left.days}d"


def format_digest(kind, data, now):
    items = data["items"]
    if kind == "grade_digest":
        lines = [data["title"]] if items else ["Course grades: none saved"]
        for item in items:
            posted = item["current_grade"] is not None or item["current_score"] is not None
            value = f"{grade_value(item['current_grade'])}, {grade_value(item['current_score'])}" if posted else "not posted"
            lines += [f"• {item['subject']}  {value}", f"  {item['source_url']}"]
        return "\n".join(lines)
    if not items:
        return data["empty"]
    lines = [f"{data['title']} ({len(items)})"]
    for item in items:
        if kind == "deadline_digest":
            due = parse(item["due_at"])
            lines.append(f"• {countdown(due, now):<7} {item['subject']}  {item['name'] or '(untitled)'} "
                         f"({manila(item['due_at']):%a %I:%M %p})")
        else:
            posted = f"{manila(item['posted_at']):%a %d %b}" if item["posted_at"] else "no date"
            lines.append(f"• {item['subject']}  {item['title'] or '(untitled)'} ({posted})")
        lines.append(f"  {item['source_url']}")
    if kind == "deadline_digest":
        as_of = f"{manila(data['as_of']):%a %d %b, %I:%M %p}" if data["as_of"] else "unknown"
        lines.append(f"Data as of {as_of}")
    return "\n".join(lines)


def format_reminder(data, now):
    due = manila(data["due_at"])
    when = f"{due:%I:%M %p} today" if due.date() == now.astimezone(due.tzinfo).date() else f"{due:%a %d %b, %I:%M %p}"
    return (f"⏰ {countdown(due, now)}  {data['subject']}  {data['name'] or '(untitled)'}\n"
            f"Due {when}\n{data['source_url']}")


def format_event(event, now=None):
    kind = event["kind"]
    data = json.loads(event["data"])
    now = now or datetime.now(timezone.utc)
    if kind in ("deadline_digest", "announcement_digest", "grade_digest"):
        return format_digest(kind, data, now)
    if kind == "deadline_reminder":
        return format_reminder(data, now)
    if kind == "authentication_expired":
        return "Canvas session expired. Saved facts remain available. Restore the private Ubuntu session before refreshing."
    if kind == "authentication_restored":
        return "Canvas authentication restored. Check each category's fetch time before relying on saved facts."
    subject = event["subject"]
    title = (data.get("name") or data.get("title") or "Course grades")[:160]
    if kind == "new_assignment":
        body = f"New assignment: {title}\nDue: {local_date(data['due_at'])}"
    elif kind == "due_date_changed":
        body = f"Due date changed: {title}\nPrevious: {local_date(data['previous_due_at'])}\nNow: {local_date(data['due_at'])}"
    elif kind == "new_announcement":
        body = f"New announcement: {title}"
    elif kind == "assignment_grade_changed":
        body = f"Grade updated: {title}\nGrade: {grade_value(data['grade'])}\nScore: {grade_value(data['score'])}"
    else:
        body = (f"Course grades updated\nCurrent: {grade_value(data['current_grade'])}, score {grade_value(data['current_score'])}"
                f"\nFinal: {grade_value(data['final_grade'])}, score {grade_value(data['final_score'])}")
    return f"{subject}\n{body}\n{data['source_url']}"


def pending(db, limit=50):
    return list(db.execute("""SELECT events.*,courses.code AS subject FROM events
        LEFT JOIN courses ON events.course_id=courses.id
        WHERE state IN ('pending','uncertain') ORDER BY events.attempts,events.id LIMIT ?""", (limit,)))


def preview(db):
    events = pending(db)
    return {"messages": [{"event_id": event["id"], "state": event["state"], "text": format_event(event)} for event in events],
            "remaining": db.execute("SELECT count(*) FROM events WHERE state!='sent'").fetchone()[0]}


def deliver(db, sender=None):
    if sender is None:
        from telegram_notify import read_env, send
        env_path = CONFIG.parent / "telegram_school.env"
        values = read_env(env_path)
        if not values.get("TELEGRAM_BOT_TOKEN") or not values.get("TELEGRAM_CHAT_ID"):
            raise CanvasError("notification_config_unavailable")
        sender = lambda message: send(message, env_path=env_path)
    sent = 0
    failed = []
    for event in pending(db):
        message = format_event(event)
        with db:
            db.execute("UPDATE events SET state='uncertain',attempts=attempts+1,last_attempt_at=? WHERE id=?",
                       (timestamp(), event["id"]))
        try:
            count = sender(message)
            if type(count) is not int or count < 1:
                raise CanvasError("unconfirmed_delivery")
        except (Exception, SystemExit):
            with db:
                db.execute("UPDATE events SET error='delivery_unconfirmed' WHERE id=?", (event["id"],))
            failed.append(event["id"])
            continue
        with db:
            db.execute("UPDATE events SET state='sent',sent_at=?,error=NULL WHERE id=?", (timestamp(), event["id"]))
        sent += 1
    result = {"sent": sent, "remaining": db.execute("SELECT count(*) FROM events WHERE state!='sent'").fetchone()[0]}
    if failed:
        result.update({"error": "delivery_unconfirmed", "event_id": failed[0], "failed_event_ids": failed})
    return result
