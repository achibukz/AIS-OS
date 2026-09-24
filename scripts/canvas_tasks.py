"""Turn eligible Canvas facts into durable cohesion operations."""
from __future__ import annotations

import hashlib
import json
import re
from datetime import datetime, timedelta, timezone
from typing import Any
from zoneinfo import ZoneInfo

from canvas_client import CanvasError
from canvas_store import MANILA, parse_time
from cohesion import CohesionService
from owned_persist import Persister

MAX_PREVIEW = 25
MAX_RECONCILE = 50
ACTION_WORDS = re.compile(
    r"\b(submit|complete|finish|upload|prepare|bring|read|answer|register|attend|fill(?:\s+out)?)\b",
    re.IGNORECASE,
)
DEADLINE_WORDS = re.compile(r"\b(due|deadline|by|before)\b", re.IGNORECASE)
ISO_DATE = re.compile(r"\b(20\d{2}-\d{2}-\d{2})\b")
MONTH_DATE = re.compile(
    r"\b(January|February|March|April|May|June|July|August|September|October|November|December)"
    r"\s+(\d{1,2})(?:,\s*(20\d{2}))?\b",
    re.IGNORECASE,
)
MONTHS = {
    name.lower(): index
    for index, name in enumerate(
        "January February March April May June July August September October November December".split(),
        1,
    )
}


def _stable_item_id(course_id: int, source_kind: str, source_id: int) -> str:
    digest = hashlib.sha256(f"canvas:{course_id}:{source_kind}:{source_id}".encode()).hexdigest()
    return f"canvas_{digest[:24]}"


def assignment_state(record: dict[str, Any]) -> str:
    if record.get("excused") is True:
        return "excused"
    status = str(record.get("submission_status") or "").strip().lower()
    if record.get("grade") is not None or record.get("score") is not None or status == "graded":
        return "graded"
    if status in {"completed", "complete"}:
        return "completed"
    if status in {"submitted", "pending_review"} or record.get("submitted_at"):
        return "submitted"
    if status in {"unsubmitted", "not_submitted"}:
        return "active"
    return "unknown"


def _due_date(value: str | None) -> str | None:
    return parse_time(value).astimezone(MANILA).date().isoformat() if value else None


def _course(db, code: str):
    rows = db.execute(
        "SELECT * FROM courses WHERE active=1 AND lower(code)=lower(?)", (code,)
    ).fetchall()
    if len(rows) != 1:
        raise CanvasError("course_not_found_or_ambiguous")
    return rows[0]


def _active(db, course_id: int) -> bool:
    return db.execute(
        "SELECT 1 FROM canvas_task_activation WHERE course_id=?", (course_id,)
    ).fetchone() is not None


def _next_revision(db, course_id: int, source_kind: str, source_id: int) -> int:
    row = db.execute(
        """SELECT max(source_revision) FROM canvas_task_ops
           WHERE course_id=? AND source_kind=? AND source_id=?""",
        (course_id, source_kind, source_id),
    ).fetchone()
    return (row[0] or 0) + 1


def _was_created(db, course_id: int, source_kind: str, source_id: int) -> bool:
    return db.execute(
        """SELECT 1 FROM canvas_task_ops
           WHERE course_id=? AND source_kind=? AND source_id=?
             AND json_extract(intent,'$.action')='upsert' LIMIT 1""",
        (course_id, source_kind, source_id),
    ).fetchone() is not None


def _insert_op(
    db,
    *,
    course_id: int,
    source_kind: str,
    source_id: int,
    change_kind: str,
    source_state: str,
    snapshot: dict[str, Any],
    intent: dict[str, Any] | None,
    at: str,
) -> int:
    revision = _next_revision(db, course_id, source_kind, source_id)
    cursor = db.execute(
        """INSERT INTO canvas_task_ops(
               course_id,source_kind,source_id,source_revision,change_kind,
               source_state,snapshot,intent,observed_at,state,error
           ) VALUES(?,?,?,?,?,?,?,?,?,?,?)""",
        (
            course_id,
            source_kind,
            source_id,
            revision,
            change_kind,
            source_state,
            json.dumps(snapshot, ensure_ascii=False, sort_keys=True),
            json.dumps(intent, ensure_ascii=False, sort_keys=True) if intent else None,
            at,
            "pending" if intent else "conflict",
            None if intent else f"unsupported_or_incomplete_{source_state}",
        ),
    )
    return cursor.lastrowid


def _assignment_intent(course, record: dict[str, Any], state: str) -> dict[str, Any] | None:
    due = _due_date(record.get("due_at"))
    if state == "unknown" or due is None:
        return None
    item_id = _stable_item_id(course["id"], "assignment", record["id"])
    if state in {"submitted", "graded", "completed", "excused"}:
        return {"action": "complete", "item_id": item_id}
    return {
        "action": "upsert",
        "category": "school_deadline",
        "title": f"{course['code']} {record.get('name') or 'Assignment'}",
        "item_id": item_id,
        "area": "school",
        "due": due,
        "calendar": "DLSU",
        "tags": [course["code"]],
    }


def _announcement_due(record: dict[str, Any]) -> str | None:
    text = " ".join(str(record.get(key) or "") for key in ("title", "message"))
    if not ACTION_WORDS.search(text) or not DEADLINE_WORDS.search(text):
        return None
    match = ISO_DATE.search(text)
    if match:
        try:
            return datetime.fromisoformat(match.group(1)).date().isoformat()
        except ValueError:
            return None
    match = MONTH_DATE.search(text)
    if not match:
        return None
    posted = parse_time(record["posted_at"]).astimezone(MANILA) if record.get("posted_at") else None
    year = int(match.group(3)) if match.group(3) else (posted.year if posted else None)
    if year is None:
        return None
    try:
        value = datetime(year, MONTHS[match.group(1).lower()], int(match.group(2))).date()
    except ValueError:
        return None
    if posted and not match.group(3) and value < posted.date():
        try:
            value = value.replace(year=value.year + 1)
        except ValueError:
            return None
    return value.isoformat()


def announcement_intent(course, record: dict[str, Any]) -> dict[str, Any] | None:
    due = _announcement_due(record)
    if due is None:
        return None
    title = str(record.get("title") or "Announcement task").strip()
    return {
        "action": "upsert",
        "category": "school_deadline",
        "title": f"{course['code']} {title}",
        "item_id": _stable_item_id(course["id"], "announcement", record["id"]),
        "area": "school",
        "due": due,
        "calendar": "DLSU",
        "tags": [course["code"], "announcement"],
    }


def record_changes(db, course_id, category, records, at, previous=None):
    """Queue changes only after explicit course activation."""
    if not _active(db, course_id):
        return
    course = db.execute("SELECT * FROM courses WHERE id=?", (course_id,)).fetchone()
    previous = previous or {}
    for record in records:
        old = previous.get(record["id"])
        if category == "announcements":
            if old == record:
                continue
            old_intent = announcement_intent(course, old) if old else None
            intent = announcement_intent(course, record)
            if old_intent is None and intent is None:
                continue
            _insert_op(
                db,
                course_id=course_id,
                source_kind="announcement",
                source_id=record["id"],
                change_kind="new_announcement_task" if old_intent is None else "announcement_changed",
                source_state="active" if intent else "unknown",
                snapshot=record,
                intent=intent,
                at=at,
            )
            continue
        state = assignment_state(record)
        changed = old is None or any(
            old.get(key) != record.get(key)
            for key in (
                "name",
                "due_at",
                "submission_status",
                "submitted_at",
                "excused",
                "grade",
                "score",
            )
        )
        if not changed:
            continue
        intent = _assignment_intent(course, record, state)
        # An assignment already done before activation never became a task, so a
        # later grade has nothing to complete and would stay pending forever.
        if (
            intent
            and intent["action"] == "complete"
            and not _was_created(db, course_id, "assignment", record["id"])
        ):
            continue
        _insert_op(
            db,
            course_id=course_id,
            source_kind="assignment",
            source_id=record["id"],
            change_kind="new_assignment" if old is None else "assignment_changed",
            source_state=state,
            snapshot=record,
            intent=intent,
            at=at,
        )


def _coverage_ready(db, course_id: int, category: str, now: datetime) -> None:
    row = db.execute(
        "SELECT success_at,error,baseline FROM coverage WHERE course_id=? AND category=?",
        (course_id, category),
    ).fetchone()
    if not row or not row["baseline"] or not row["success_at"]:
        raise CanvasError("assignment_data_unavailable")
    if row["error"]:
        raise CanvasError("assignment_data_failed")
    if now - parse_time(row["success_at"]).astimezone(timezone.utc) > timedelta(hours=4):
        raise CanvasError("stale_assignment_data")


def activation_preview(db, course_code: str, *, now: datetime | None = None, limit=MAX_PREVIEW):
    now = (now or datetime.now(timezone.utc)).astimezone(timezone.utc)
    course = _course(db, course_code)
    _coverage_ready(db, course["id"], "assignments", now)
    assignments = [json.loads(row[0]) for row in db.execute(
        "SELECT data FROM records WHERE course_id=? AND category='assignments' AND active=1 ORDER BY id",
        (course["id"],),
    )]
    announcements_ready = True
    try:
        _coverage_ready(db, course["id"], "announcements", now)
    except CanvasError:
        announcements_ready = False
    announcements = []
    if announcements_ready:
        announcements = [json.loads(row[0]) for row in db.execute(
            """SELECT data FROM records
               WHERE course_id=? AND category='announcements' AND active=1 ORDER BY id""",
            (course["id"],),
        )]
    eligible = []
    blocked = []
    for record in assignments:
        state = assignment_state(record)
        intent = _assignment_intent(course, record, state)
        item = {"id": record["id"], "name": record.get("name"), "state": state,
                "due": _due_date(record.get("due_at"))}
        if state == "active" and intent:
            eligible.append(item)
        else:
            blocked.append(item)
    extracted = [
        {"id": record["id"], "title": record.get("title"), "due": intent["due"]}
        for record in announcements
        if (intent := announcement_intent(course, record)) is not None
    ]
    preview = (eligible + [{"announcement": item} for item in extracted])[:limit]
    return {
        "course": course["code"],
        "active": _active(db, course["id"]),
        "eligible_assignments": len(eligible),
        "blocked_assignments": len(blocked),
        "announcement_tasks": len(extracted),
        "announcements_ready": announcements_ready,
        "preview": preview,
        "remaining": max(0, len(eligible) + len(extracted) - len(preview)),
    }


def activate(db, course_code: str, *, at: str, now: datetime | None = None):
    report = activation_preview(db, course_code, now=now)
    course = _course(db, course_code)
    if _active(db, course["id"]):
        return {**report, "activated": False, "queued": 0}
    assignments = [json.loads(row[0]) for row in db.execute(
        "SELECT data FROM records WHERE course_id=? AND category='assignments' AND active=1 ORDER BY id",
        (course["id"],),
    )]
    announcements = []
    if report["announcements_ready"]:
        announcements = [json.loads(row[0]) for row in db.execute(
            """SELECT data FROM records
               WHERE course_id=? AND category='announcements' AND active=1 ORDER BY id""",
            (course["id"],),
        )]
    queued = 0
    with db:
        db.execute(
            "INSERT INTO canvas_task_activation(course_id,activated_at) VALUES(?,?)",
            (course["id"], at),
        )
        for record in assignments:
            state = assignment_state(record)
            intent = _assignment_intent(course, record, state)
            if state != "active" or intent is None:
                continue
            _insert_op(db, course_id=course["id"], source_kind="assignment",
                       source_id=record["id"], change_kind="activation", source_state=state,
                       snapshot=record, intent=intent, at=at)
            queued += 1
        for record in announcements:
            intent = announcement_intent(course, record)
            if intent is None:
                continue
            _insert_op(db, course_id=course["id"], source_kind="announcement",
                       source_id=record["id"], change_kind="activation", source_state="active",
                       snapshot=record, intent=intent, at=at)
            queued += 1
    return {**report, "active": True, "activated": True, "queued": queued}


def reconcile(db, *, service: CohesionService | None = None, limit=MAX_RECONCILE):
    rows = db.execute(
        """SELECT canvas_task_ops.*,courses.code FROM canvas_task_ops
           JOIN courses ON courses.id=canvas_task_ops.course_id
           WHERE canvas_task_ops.state='pending' ORDER BY canvas_task_ops.id LIMIT ?""",
        (limit,),
    ).fetchall()
    if rows and service is None:
        service = CohesionService(persister=Persister())
    applied = pending = 0
    destination_applied = {"tasks": 0, "calendar": 0}
    receipts = []
    for row in rows:
        intent = json.loads(row["intent"]) if row["intent"] else None
        if intent is None:
            raise RuntimeError("pending Canvas task operation has no intent")
        source_id = (
            f"canvas:{row['course_id']}:{row['source_kind']}:{row['source_id']}:"
            f"r{row['source_revision']}"
        )
        if service is None:
            raise RuntimeError("cohesion service was not initialized")
        receipt = service.submit({
            "version": 1,
            "source": {
                "id": source_id,
                "kind": f"canvas_{row['source_kind']}",
                "native_id": f"{row['course_id']}:{row['source_id']}",
                "revision": row["source_revision"],
                "timestamp": row["observed_at"],
            },
            "intent": intent,
        })
        has_pending = bool(receipt.get("pending"))
        prior_receipt = json.loads(row["receipt"]) if row["receipt"] else {}
        prior_destinations = {
            item.get("destination") for item in prior_receipt.get("applied") or []
        }
        for item in receipt.get("applied") or []:
            destination = item.get("destination")
            if destination in destination_applied and destination not in prior_destinations:
                destination_applied[destination] += 1
        state = "pending" if has_pending else "applied"
        error = "; ".join(
            str(item.get("error")) for item in receipt.get("pending") or [] if item.get("error")
        ) or None
        with db:
            db.execute(
                "UPDATE canvas_task_ops SET state=?,receipt=?,error=? WHERE id=?",
                (state, json.dumps(receipt, ensure_ascii=False, sort_keys=True), error, row["id"]),
            )
            if receipt.get("item_id"):
                db.execute(
                    """INSERT INTO canvas_task_links VALUES(?,?,?,?,?,?)
                       ON CONFLICT(course_id,source_kind,source_id) DO UPDATE SET
                       item_id=excluded.item_id,last_revision=excluded.last_revision,
                       updated_at=excluded.updated_at""",
                    (row["course_id"], row["source_kind"], row["source_id"],
                     receipt["item_id"], row["source_revision"], row["observed_at"]),
                )
        receipts.append({"operation_id": row["id"], "receipt": receipt})
        if has_pending:
            pending += 1
        else:
            applied += 1
    remaining = db.execute("SELECT count(*) FROM canvas_task_ops WHERE state='pending'").fetchone()[0]
    conflicts = db.execute("SELECT count(*) FROM canvas_task_ops WHERE state='conflict'").fetchone()[0]
    return {
        "applied": applied,
        "task_applied": destination_applied["tasks"],
        "calendar_applied": destination_applied["calendar"],
        "pending": pending,
        "conflicts": conflicts,
        "remaining": remaining,
        "receipts": receipts,
    }
