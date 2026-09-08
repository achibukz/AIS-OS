"""Transactional Canvas snapshots and queries that never write the cache."""
from __future__ import annotations

import json
import os
import re
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
from html import unescape
from pathlib import Path
from zoneinfo import ZoneInfo

from canvas_client import CanvasError, ORIGIN, private_directory
from canvas_events import enqueue, record_changes

DATABASE = Path.home() / ".local/share/achios/canvas/canvas.sqlite3"
CATEGORIES = ("courses", "assignments", "grades", "announcements")
MANILA = ZoneInfo("Asia/Manila")
SCHEMA = """
CREATE TABLE courses (
    id INTEGER PRIMARY KEY, term TEXT NOT NULL, code TEXT NOT NULL,
    section TEXT NOT NULL, active INTEGER NOT NULL DEFAULT 1
);
CREATE TABLE coverage (
    course_id INTEGER NOT NULL REFERENCES courses(id), category TEXT NOT NULL,
    success_at TEXT, attempted_at TEXT, error TEXT, baseline INTEGER NOT NULL DEFAULT 0,
    PRIMARY KEY (course_id, category)
);
CREATE TABLE records (
    course_id INTEGER NOT NULL REFERENCES courses(id), category TEXT NOT NULL,
    id INTEGER NOT NULL, data TEXT NOT NULL, active INTEGER NOT NULL DEFAULT 1,
    PRIMARY KEY (course_id, category, id)
);
CREATE TABLE authentication (
    singleton INTEGER PRIMARY KEY CHECK (singleton = 1), state TEXT NOT NULL,
    checked_at TEXT NOT NULL
);
CREATE TABLE events (
    id INTEGER PRIMARY KEY AUTOINCREMENT, course_id INTEGER REFERENCES courses(id),
    kind TEXT NOT NULL, data TEXT NOT NULL, observed_at TEXT NOT NULL,
    state TEXT NOT NULL DEFAULT 'pending' CHECK(state IN ('pending','uncertain','sent')),
    attempts INTEGER NOT NULL DEFAULT 0, last_attempt_at TEXT, sent_at TEXT, error TEXT
);
CREATE INDEX events_delivery ON events(state,id);
PRAGMA user_version=1;
"""


@contextmanager
def open_writer(path: Path):
    private_directory(path.parent)
    if path.is_symlink():
        raise CanvasError("unsafe_database")
    fd = os.open(path, os.O_CREAT | os.O_RDWR | os.O_NOFOLLOW, 0o600)
    os.close(fd)
    path.chmod(0o600)
    db = sqlite3.connect(path, timeout=5)
    db.row_factory = sqlite3.Row
    try:
        db.execute("PRAGMA foreign_keys=ON")
        version = db.execute("PRAGMA user_version").fetchone()[0]
        if version == 0:
            db.executescript("BEGIN IMMEDIATE;\n" + SCHEMA + "COMMIT;")
        elif version != 1:
            raise CanvasError("unsupported_schema")
        if db.execute("PRAGMA journal_mode").fetchone()[0] != "delete":
            raise CanvasError("unsupported_journal")
        yield db
    finally:
        db.close()


@contextmanager
def open_reader(path: Path):
    db = sqlite3.connect(path.resolve().as_uri() + "?mode=ro", uri=True, timeout=5)
    db.row_factory = sqlite3.Row
    try:
        db.execute("PRAGMA query_only=ON")
        if db.execute("PRAGMA user_version").fetchone()[0] != 1:
            raise CanvasError("unsupported_schema")
        if db.execute("PRAGMA journal_mode").fetchone()[0] != "delete":
            raise CanvasError("unsupported_journal")
        db.execute("BEGIN")
        yield db
    finally:
        db.close()


def configure_courses(db, mapping):
    with db:
        db.execute("UPDATE courses SET active=0")
        for subject in mapping["subjects"]:
            db.execute("""INSERT INTO courses(id,term,code,section) VALUES(?,?,?,?)
                ON CONFLICT(id) DO UPDATE SET term=excluded.term,code=excluded.code,
                section=excluded.section,active=1""",
                (subject["course_id"], mapping["term"], subject["code"], subject["section"]))
            for category in CATEGORIES:
                db.execute("INSERT OR IGNORE INTO coverage(course_id,category) VALUES(?,?)",
                           (subject["course_id"], category))


def save_auth(db, state, at):
    with db:
        previous = db.execute("SELECT state FROM authentication WHERE singleton=1").fetchone()
        old = previous["state"] if previous else "unknown"
        if state == "expired" and old != "expired":
            enqueue(db, None, "authentication_expired", {}, at)
        elif state == "valid" and old == "expired":
            enqueue(db, None, "authentication_restored", {}, at)
        db.execute("""INSERT INTO authentication VALUES(1,?,?)
            ON CONFLICT(singleton) DO UPDATE SET state=excluded.state,checked_at=excluded.checked_at""",
            (state, at))


def save_failure(db, course_id, category, kind, at):
    with db:
        db.execute("UPDATE coverage SET attempted_at=?,error=? WHERE course_id=? AND category=?",
                   (at, kind, course_id, category))


def assignment_grades(row, previous, at):
    available = row.get("grade_available", True)
    return {**row, "grade_available": available,
            "grade": row["grade"] if available else previous.get("grade"),
            "score": row["score"] if available else previous.get("score"),
            "grade_success_at": at if available else previous.get("grade_success_at")}


def save_snapshot(db, course_id, category, records, at):
    if category not in CATEGORIES or len({row['id'] for row in records}) != len(records):
        raise CanvasError("malformed_response")
    with db:
        if category == "assignments":
            previous = {row["id"]: json.loads(row["data"]) for row in db.execute(
                "SELECT id,data FROM records WHERE course_id=? AND category=?", (course_id, category))}
            records = [assignment_grades(row, previous.get(row["id"], {}), at) for row in records]
        record_changes(db, course_id, category, records, at)
        db.execute("UPDATE records SET active=0 WHERE course_id=? AND category=?", (course_id, category))
        for row in records:
            db.execute("""INSERT INTO records VALUES(?,?,?,?,1)
                ON CONFLICT(course_id,category,id) DO UPDATE SET data=excluded.data,active=1""",
                (course_id, category, row["id"], json.dumps(row, ensure_ascii=False)))
        db.execute("""UPDATE coverage SET success_at=?,attempted_at=?,error=NULL,baseline=1
            WHERE course_id=? AND category=?""", (at, at, course_id, category))


def clean_text(value, limit=20000):
    if value is None:
        return None
    if not isinstance(value, str):
        raise CanvasError("malformed_response")
    text = unescape(re.sub(r"<[^>]*>", " ", value))
    text = re.sub(r"https?://\S+", "[link omitted]", text)
    return " ".join(text.split())[:limit]


def numeric(value):
    if value is not None and (type(value) not in (int, float) or not float('-inf') < value < float('inf')):
        raise CanvasError("malformed_response")
    return value


def parse_time(value):
    try:
        result = datetime.fromisoformat(value.replace("Z", "+00:00"))
        if result.tzinfo is None:
            raise ValueError
        return result
    except (ValueError, AttributeError, TypeError):
        raise CanvasError("malformed_timestamp") from None


def date_value(value):
    return parse_time(value).isoformat() if value is not None else None


def project_record(category, row, course_id, user_id):
    if not isinstance(row, dict) or type(row.get("id")) is not int or row["id"] <= 0:
        raise CanvasError("malformed_response")
    item_id = row["id"]
    base = f"{ORIGIN}/courses/{course_id}"
    if category == "courses":
        if item_id != course_id:
            raise CanvasError("malformed_response")
        return {"id": item_id, "name": clean_text(row.get("name"), 300), "source_url": base}
    if category == "assignments":
        if "due_at" not in row or "name" not in row:
            raise CanvasError("malformed_response")
        submission = row.get("submission")
        if (not isinstance(submission, dict) or submission.get("user_id") != user_id
                or "workflow_state" not in submission):
            raise CanvasError("submission_unavailable")
        return {"id": item_id, "name": clean_text(row["name"], 300),
                "description": clean_text(row.get("description")), "due_at": date_value(row["due_at"]),
                "points_possible": numeric(row.get("points_possible")),
                "submission_status": clean_text(submission.get("workflow_state"), 80),
                "submitted_at": date_value(submission.get("submitted_at")),
                "missing": submission.get("missing") if type(submission.get("missing")) is bool else None,
                "excused": submission.get("excused") if type(submission.get("excused")) is bool else None,
                "grade": clean_text(submission.get("grade"), 100), "score": numeric(submission.get("score")),
                "grade_available": "grade" in submission and "score" in submission,
                "source_url": f"{base}/assignments/{item_id}"}
    if category == "grades":
        if row.get("user_id") != user_id or row.get("type") != "StudentEnrollment":
            raise CanvasError("unexpected_enrollment")
        grades = row.get("grades")
        if not isinstance(grades, dict) or any(key not in grades for key in ("current_score", "final_score")):
            raise CanvasError("grades_unavailable")
        return {"id": item_id, "current_grade": clean_text(grades.get("current_grade"), 100),
                "current_score": numeric(grades.get("current_score")),
                "final_grade": clean_text(grades.get("final_grade"), 100),
                "final_score": numeric(grades.get("final_score")), "source_url": f"{base}/grades"}
    if category == "announcements":
        if "title" not in row or "message" not in row:
            raise CanvasError("malformed_response")
        return {"id": item_id, "title": clean_text(row["title"], 300),
                "message": clean_text(row["message"]), "posted_at": date_value(row.get("posted_at")),
                "source_url": f"{base}/discussion_topics/{item_id}"}
    raise CanvasError("invalid_category")


def query_record(record, course, command, item, unfinished, start):
    value = json.loads(record["data"])
    value.update({"subject": course["code"], "category": record["category"]})
    if item is not None and value["id"] != item:
        return None
    if unfinished and (value.get("submitted_at") or value.get("excused")
                       or value.get("submission_status") in ("submitted", "pending_review", "graded")):
        return None
    if command == "due":
        if value.get("due_at") is None or not start <= parse_time(value["due_at"]) < start + timedelta(days=7):
            return None
    if command == "courses":
        value.update({"term": course["term"], "section": course["section"]})
    if command not in ("detail", "announcements"):
        value.pop("description", None)
    if command == "grades" and value["category"] == "assignments":
        return {key: value[key] for key in ("id", "subject", "category", "name", "grade", "score", "points_possible", "source_url", "grade_available", "grade_success_at")}
    if command == "announcements" and item is None and value.get("message"):
        value["message_truncated"] = len(value["message"]) > 1000
        value["message"] = value["message"][:1000]
    return value


def query(db, command, *, course=None, item=None, period="week", unfinished=False, now=None, limit=50, offset=0):
    if not 1 <= limit <= 200 or offset < 0:
        raise CanvasError("invalid_query_page")
    now = now or datetime.now(timezone.utc)
    categories = {"status": CATEGORIES, "courses": ("courses",), "due": ("assignments",),
                  "assignments": ("assignments",), "detail": ("assignments",),
                  "grades": ("grades", "assignments"), "announcements": ("announcements",)}[command]
    courses = [dict(row) for row in db.execute("SELECT * FROM courses WHERE active=1 ORDER BY code")]
    if course is not None:
        courses = [row for row in courses if row["code"] == course]
        if not courses:
            raise CanvasError("unknown_course")
    ids = {row["id"]: row for row in courses}
    coverage = []
    for row in db.execute("SELECT * FROM coverage ORDER BY course_id,category"):
        if row["course_id"] not in ids or row["category"] not in categories:
            continue
        value = dict(row)
        value["subject"] = ids[row["course_id"]]["code"]
        if command == "grades" and row["category"] == "assignments":
            grades = [json.loads(record[0]) for record in db.execute(
                "SELECT data FROM records WHERE course_id=? AND category='assignments' AND active=1", (row["course_id"],))]
            if grades:
                fetched = [record.get("grade_success_at") for record in grades]
                value["success_at"] = min(fetched) if all(fetched) else None
                if any(not record.get("grade_available", False) for record in grades):
                    value["error"] = "assignment_grades_unavailable"
        value["stale"] = value["success_at"] is None or now - parse_time(value["success_at"]) > timedelta(hours=4)
        value["coverage"] = "unavailable" if not row["baseline"] else ("saved_after_failure" if value["error"] else "complete")
        coverage.append(value)
    auth = db.execute("SELECT state,checked_at FROM authentication WHERE singleton=1").fetchone()
    warnings = []
    if not ids:
        warnings.append("no_mapped_courses")
    if any(row["stale"] for row in coverage):
        warnings.append("stale_data")
    if any(row["error"] or not row["baseline"] for row in coverage):
        warnings.append("incomplete_coverage")
    if auth and auth["state"] == "expired":
        warnings.append("authentication_expired")
    local = now.astimezone(MANILA)
    start = local.replace(hour=0, minute=0, second=0, microsecond=0) - timedelta(days=local.weekday()) if period == "week" else local
    rows = []
    if command != "status":
        for record in db.execute("SELECT * FROM records WHERE active=1 ORDER BY course_id,id"):
            if record["course_id"] not in ids or record["category"] not in categories:
                continue
            value = query_record(record, ids[record["course_id"]], command, item, unfinished, start)
            if value is not None:
                rows.append(value)
    if command == "due":
        rows.sort(key=lambda row: (parse_time(row["due_at"]), row["subject"], row["id"]))
    course_grades = [row for row in rows if row["category"] == "grades"] if command == "grades" else []
    if command == "grades":
        rows = [row for row in rows if row["category"] == "assignments"]
    total = len(rows)
    result = {"data": rows[offset:offset + limit], "total": total,
            "next_offset": offset + limit if offset + limit < total else None, "coverage": coverage, "authentication": dict(auth) if auth else {"state": "unknown"},
            "warnings": warnings, "timezone": "Asia/Manila", "queried_at": now.isoformat()}
    if command == "grades":
        result["course_grades"] = course_grades
    return result
