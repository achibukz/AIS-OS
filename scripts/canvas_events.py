"""Persist observed Canvas transitions and retry unconfirmed deliveries."""
from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from html import escape
from zoneinfo import ZoneInfo

from canvas_client import CONFIG, CanvasError, timestamp


SEPARATOR = "---------------------------------"


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


def link(url):
    return f'<a href="{escape(url, quote=True)}">[link]</a>'


def card(header, *lines):
    """Telegram HTML in the cron layout: separator, bold header, body."""
    return "\n".join([SEPARATOR, f"<b>{escape(header)}</b>", *lines])


def item_line(subject, title, url, detail=""):
    return f"{escape(subject or '')}  {escape(title or '(untitled)')}{detail} {link(url)}"


def format_digest(kind, data, now):
    items = data["items"]
    if not items:
        return card(data["empty"])
    rows = []
    for item in items:
        if kind == "deadline_digest":
            when = f" ({manila(item['due_at']):%a %I:%M %p})"
            rows.append(f"• {countdown(parse(item['due_at']), now):<7} "
                        + item_line(item["subject"], item["name"], item["source_url"], when))
        else:
            posted = f" ({manila(item['posted_at']):%a %d %b})" if item["posted_at"] else " (no date)"
            rows.append("• " + item_line(item["subject"], item["title"], item["source_url"], posted))
    header = f"{data['title']} ({len(items)})"
    if kind == "deadline_digest":
        as_of = f"{manila(data['as_of']):%a %d %b, %I:%M %p}" if data["as_of"] else "unknown"
        return card(header, f"Data as of {as_of}", "", *rows)
    return card(header, "", *rows)


def format_reminder(data, now):
    due = manila(data["due_at"])
    when = f"{due:%I:%M %p} today" if due.date() == now.astimezone(due.tzinfo).date() else f"{due:%a %d %b, %I:%M %p}"
    return card("Deadline reminder",
                f"{countdown(due, now)}  " + item_line(data["subject"], data["name"], data["source_url"]),
                f"Due {when}")


def format_event(event, now=None):
    kind = event["kind"]
    data = json.loads(event["data"])
    now = now or datetime.now(timezone.utc)
    if kind in ("deadline_digest", "announcement_digest"):
        return format_digest(kind, data, now)
    if kind == "deadline_reminder":
        return format_reminder(data, now)
    if kind == "authentication_expired":
        return card("Canvas session expired",
                    "Saved facts remain available. Restore the private Ubuntu session before refreshing.")
    if kind == "authentication_restored":
        return card("Canvas authentication restored",
                    "Check each category's fetch time before relying on saved facts.")
    title = (data.get("name") or data.get("title") or "Course grades")[:160]
    line = item_line(event["subject"], title, data["source_url"])
    if kind == "new_assignment":
        return card("New assignment", line, f"Due: {local_date(data['due_at'])}")
    if kind == "due_date_changed":
        return card("Due date changed", line, f"Previous: {local_date(data['previous_due_at'])}",
                    f"Now: {local_date(data['due_at'])}")
    if kind == "new_announcement":
        return card("New announcement", line)
    if kind == "assignment_grade_changed":
        return card("Grade updated", line, f"Grade: {escape(grade_value(data['grade']))}",
                    f"Score: {escape(grade_value(data['score']))}")
    return card("Course grades updated", line,
                f"Current: {escape(grade_value(data['current_grade']))}, score {escape(grade_value(data['current_score']))}",
                f"Final: {escape(grade_value(data['final_grade']))}, score {escape(grade_value(data['final_score']))}")


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
        sender = lambda message: send(message, env_path=env_path, html=True)
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
