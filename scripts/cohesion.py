#!/usr/bin/env python3
"""Apply versioned task and Calendar operations with durable receipts."""

from __future__ import annotations

import argparse
import contextlib
import datetime as dt
import hashlib
import json
import os
import re
import sqlite3
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Protocol
from zoneinfo import ZoneInfo

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

import gcal
from task_engine import PRIMARY_AREAS

CONTRACT_VERSION = 1
SCHEMA_VERSION = 1
MANILA = ZoneInfo("Asia/Manila")
DEFAULT_DB = gcal.USER_HOME / ".local" / "state" / "achios" / "cohesion.sqlite3"
DEFAULT_TASKS = SCRIPT_DIR.parent / "tasks.md"
SEEDED_PREFERENCES = {
    "social_plan": "calendar",
    "quick_task": "tasks",
    "coding_ticket": "tasks",
    "school_deadline": "both",
}
PLACEMENTS = ("tasks", "calendar", "both")


class CohesionError(RuntimeError):
    pass


class ConcurrentEdit(CohesionError):
    pass


class CalendarTransport(Protocol):
    def insert(
        self, *, profile: str, calendar_id: str, event_id: str, body: dict
    ) -> dict: ...

    def get(self, *, profile: str, calendar_id: str, event_id: str) -> dict | None: ...

    def update(
        self,
        *,
        profile: str,
        calendar_id: str,
        event_id: str,
        body: dict,
        expected_version: str,
    ) -> dict: ...


class GwsCalendarTransport:
    def insert(self, *, profile: str, calendar_id: str, event_id: str, body: dict) -> dict:
        return gcal.insert_event(profile, calendar_id, {**body, "id": event_id})

    def get(self, *, profile: str, calendar_id: str, event_id: str) -> dict | None:
        return gcal.get_event(profile, calendar_id, event_id)

    def update(
        self,
        *,
        profile: str,
        calendar_id: str,
        event_id: str,
        body: dict,
        expected_version: str,
    ) -> dict:
        current = self.get(profile=profile, calendar_id=calendar_id, event_id=event_id)
        if current is None or current.get("etag") != expected_version:
            raise ConcurrentEdit("calendar event changed")
        return gcal.patch_event(profile, calendar_id, event_id, body)


def _canonical_hash(value: object) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(payload.encode()).hexdigest()


def _content_hash(content: str) -> str:
    return hashlib.sha256(content.encode()).hexdigest()


def _stable_id(prefix: str, value: str, length: int = 24) -> str:
    return f"{prefix}_{hashlib.sha256(value.encode()).hexdigest()[:length]}"


def _line_version(line: str | None) -> str | None:
    return _content_hash(line) if line is not None else None


def _calendar_version(event: dict) -> str:
    """Hash only the fields cohesion owns, so edits to anything else are adopted."""
    private = event.get("extendedProperties", {}).get("private", {})
    return _canonical_hash(
        {
            "summary": event.get("summary"),
            "start": event.get("start"),
            "end": event.get("end"),
            "private": {key: value for key, value in private.items() if key.startswith("achios_")},
        }
    )


def _event_id(item_id: str) -> str:
    return gcal.event_id_for(item_id)


def _source_time(value: str) -> dt.datetime:
    parsed = dt.datetime.fromisoformat(value)
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise CohesionError("source.timestamp must include an offset")
    return parsed


def _resolve_date(value: str | None, source_time: dt.datetime) -> str | None:
    if value is None:
        return None
    local_date = source_time.astimezone(MANILA).date()
    if value == "today":
        return local_date.isoformat()
    if value == "tomorrow":
        return (local_date + dt.timedelta(days=1)).isoformat()
    try:
        return dt.date.fromisoformat(value).isoformat()
    except (TypeError, ValueError) as exc:
        raise CohesionError("intent.due must be today, tomorrow, or YYYY-MM-DD") from exc


def _resolve_datetime(value: str | None) -> str | None:
    if value is None:
        return None
    parsed = dt.datetime.fromisoformat(value)
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=MANILA)
    return parsed.astimezone(MANILA).isoformat()


class CohesionService:
    def __init__(
        self,
        *,
        db_path: Path = DEFAULT_DB,
        tasks_path: Path = DEFAULT_TASKS,
        calendar: CalendarTransport | None = None,
        calendars_path: Path | None = None,
    ):
        self.db_path = Path(db_path)
        self.tasks_path = Path(tasks_path)
        self.calendars_path = calendars_path
        self.calendar = calendar or GwsCalendarTransport()
        self.db_path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        self._initialize()
        self.db_path.chmod(0o600)

    @contextlib.contextmanager
    def _connect(self):
        connection = sqlite3.connect(self.db_path)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        try:
            with connection:
                yield connection
        finally:
            connection.close()

    def _initialize(self) -> None:
        with self._connect() as connection:
            connection.executescript(
                """
                CREATE TABLE IF NOT EXISTS schema_meta (
                    version INTEGER NOT NULL
                );
                CREATE TABLE IF NOT EXISTS preferences (
                    category TEXT PRIMARY KEY,
                    placement TEXT NOT NULL,
                    revision INTEGER NOT NULL
                );
                CREATE TABLE IF NOT EXISTS sources (
                    source_id TEXT PRIMARY KEY,
                    payload_hash TEXT NOT NULL,
                    request_json TEXT NOT NULL,
                    kind TEXT NOT NULL,
                    native_id TEXT NOT NULL,
                    revision INTEGER NOT NULL,
                    source_timestamp TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS clarifications (
                    source_id TEXT PRIMARY KEY REFERENCES sources(source_id),
                    error TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS items (
                    item_id TEXT PRIMARY KEY,
                    task_id TEXT NOT NULL UNIQUE,
                    category TEXT NOT NULL,
                    title TEXT NOT NULL,
                    area TEXT,
                    tags_json TEXT NOT NULL,
                    priority TEXT NOT NULL,
                    due TEXT,
                    start_at TEXT,
                    end_at TEXT,
                    calendar_profile TEXT,
                    calendar_id TEXT,
                    placement TEXT NOT NULL,
                    state TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS operations (
                    operation_id TEXT PRIMARY KEY,
                    source_id TEXT NOT NULL REFERENCES sources(source_id),
                    item_id TEXT NOT NULL REFERENCES items(item_id),
                    action TEXT NOT NULL,
                    destination TEXT NOT NULL,
                    status TEXT NOT NULL,
                    attempts INTEGER NOT NULL,
                    snapshot_json TEXT NOT NULL,
                    result_json TEXT,
                    error TEXT,
                    destination_version TEXT
                );
                """
            )
            versions = connection.execute("SELECT version FROM schema_meta").fetchall()
            if not versions:
                connection.execute("INSERT INTO schema_meta(version) VALUES (?)", (SCHEMA_VERSION,))
            elif versions[0]["version"] != SCHEMA_VERSION:
                raise CohesionError(f"unsupported database schema {versions[0]['version']}")
            for category, placement in SEEDED_PREFERENCES.items():
                connection.execute(
                    "INSERT OR IGNORE INTO preferences(category, placement, revision) VALUES (?, ?, 1)",
                    (category, placement),
                )

    def capabilities(self) -> dict:
        return {
            "version": CONTRACT_VERSION,
            "operations": ["upsert", "complete"],
            "destinations": ["tasks", "calendar"],
            "placements": list(PLACEMENTS),
        }

    def context(self, category: str | None = None) -> dict:
        with self._connect() as connection:
            rows = connection.execute(
                "SELECT category, placement, revision FROM preferences ORDER BY category"
            ).fetchall()
            source_count = connection.execute("SELECT COUNT(*) FROM sources").fetchone()[0]
            pending_count = connection.execute(
                "SELECT COUNT(*) FROM operations WHERE status = 'pending'"
            ).fetchone()[0]
            pending_count += connection.execute("SELECT COUNT(*) FROM clarifications").fetchone()[0]
            if category is None:
                item_rows = connection.execute(
                    """SELECT item_id, category, title, state, due, placement
                       FROM items ORDER BY rowid DESC"""
                ).fetchall()
            else:
                item_rows = connection.execute(
                    """SELECT item_id, category, title, state, due, placement
                       FROM items WHERE category = ? ORDER BY rowid DESC""",
                    (category,),
                ).fetchall()
        preferences = {row["category"]: row["placement"] for row in rows}
        if category is not None:
            preferences = {category: preferences[category]} if category in preferences else {}
        return {
            "version": CONTRACT_VERSION,
            "preferences": preferences,
            "schema_version": SCHEMA_VERSION,
            "source_count": source_count,
            "pending_count": pending_count,
            "items": [dict(row) for row in item_rows],
        }

    def item_for_task(self, task_id: str) -> str | None:
        with self._connect() as connection:
            row = connection.execute(
                "SELECT item_id FROM items WHERE task_id = ?", (task_id,)
            ).fetchone()
        return row["item_id"] if row else None

    def submit(self, request: dict) -> dict:
        original_request = request
        source = self._validate_source(request)
        payload_hash = _canonical_hash(original_request)
        source_id = source["id"]

        with self._connect() as connection:
            existing_source = connection.execute(
                "SELECT payload_hash FROM sources WHERE source_id = ?", (source_id,)
            ).fetchone()
            if existing_source and existing_source["payload_hash"] != payload_hash:
                if connection.execute(
                    "SELECT 1 FROM operations WHERE source_id = ? LIMIT 1", (source_id,)
                ).fetchone():
                    return self._conflict_receipt(
                        source_id, "source ID was reused with different content"
                    )
                connection.execute("DELETE FROM clarifications WHERE source_id = ?", (source_id,))
                connection.execute("DELETE FROM sources WHERE source_id = ?", (source_id,))
                existing_source = None
            if existing_source is None:
                connection.execute(
                    "INSERT INTO sources VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                    (
                        source_id,
                        payload_hash,
                        json.dumps(original_request),
                        source["kind"],
                        source["native_id"],
                        source["revision"],
                        source["timestamp"],
                        dt.datetime.now(dt.UTC).isoformat(),
                    ),
                )

        try:
            request = self._prepare_completion(request)
            source, intent, normalized, placement = self._validate(request)
        except CohesionError as exc:
            return self._pending_receipt(source_id, str(exc))

        with self._connect() as connection:
            existing_operations = connection.execute(
                "SELECT 1 FROM operations WHERE source_id = ? LIMIT 1", (source_id,)
            ).fetchone()
            item_id = intent.get("item_id") or _stable_id("item", source_id)
            task_id = _stable_id("task", item_id)
            existing_item = connection.execute(
                "SELECT * FROM items WHERE item_id = ?", (item_id,)
            ).fetchone()
            transition_error = None
            if existing_item and existing_operations is None:
                transition_error = self._item_transition_error(
                    existing_item, normalized, intent["action"]
                )
            if existing_operations is not None and existing_item is not None:
                placement = existing_item["placement"]

            if existing_operations is None and transition_error is None:
                if existing_item:
                    connection.execute(
                        """UPDATE operations SET status = 'superseded', error = ?
                           WHERE item_id = ? AND status = 'pending'""",
                        ("operation superseded by newer item update", item_id),
                    )
                    connection.execute(
                        """UPDATE items SET category = ?, title = ?, area = ?, tags_json = ?,
                           priority = ?, due = ?,
                           start_at = ?, end_at = ?, calendar_profile = ?, calendar_id = ?,
                           placement = ?, state = ?
                           WHERE item_id = ?""",
                        (*normalized, item_id),
                    )
                else:
                    connection.execute(
                        "INSERT INTO items VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                        (item_id, task_id, *normalized),
                    )
                destinations = self._destinations(placement)
                for destination in destinations:
                    operation_id = _stable_id(
                        "op", f"{source_id}:{item_id}:{intent['action']}:{destination}"
                    )
                    prior = connection.execute(
                        """SELECT destination_version FROM operations
                           WHERE item_id = ? AND destination = ? AND status = 'applied'
                           ORDER BY rowid DESC LIMIT 1""",
                        (item_id, destination),
                    ).fetchone()
                    snapshot = {
                        "item_id": item_id,
                        "task_id": task_id,
                        "title": normalized[1],
                        "area": normalized[2],
                        "tags": json.loads(normalized[3]),
                        "priority": normalized[4],
                        "due": normalized[5],
                        "start_at": normalized[6],
                        "end_at": normalized[7],
                        "calendar_profile": normalized[8],
                        "calendar_id": normalized[9],
                        "placement": placement,
                        "state": normalized[11],
                    }
                    connection.execute(
                        """INSERT INTO operations(
                               operation_id, source_id, item_id, action, destination, status,
                               attempts, snapshot_json, destination_version
                           ) VALUES (?, ?, ?, ?, ?, 'pending', 0, ?, ?)""",
                        (
                            operation_id,
                            source_id,
                            item_id,
                            intent["action"],
                            destination,
                            json.dumps(snapshot),
                            prior["destination_version"] if prior else None,
                        ),
                    )

        if transition_error is not None:
            return self._pending_receipt(source_id, transition_error, item_id)

        self._run_pending(source_id)
        self._clear_clarifications(source, item_id)
        return self._receipt(source_id, placement)

    def _clear_clarifications(self, source: dict, item_id: str) -> None:
        with self._connect() as connection:
            connection.execute(
                """DELETE FROM clarifications WHERE source_id IN (
                       SELECT clarifications.source_id FROM clarifications
                       JOIN sources USING(source_id)
                       WHERE (sources.kind = ? AND sources.native_id = ?)
                          OR json_extract(sources.request_json, '$.intent.item_id') = ?
                   )""",
                (source["kind"], source["native_id"], item_id),
            )

    @staticmethod
    def _item_transition_error(
        existing_item: sqlite3.Row, normalized: tuple, action: str
    ) -> str | None:
        if action == "upsert" and existing_item["state"] == "completed":
            return "reopening a completed item requires clarification"
        new_calendar_profile = normalized[8]
        new_calendar_id = normalized[9]
        new_placement = normalized[10]
        if (
            existing_item["placement"] != new_placement
            or existing_item["calendar_profile"] != new_calendar_profile
            or existing_item["calendar_id"] != new_calendar_id
        ):
            return "existing item placement or Calendar target change requires clarification"
        return None

    def _pending_receipt(self, source_id: str, error: str, item_id: str | None = None) -> dict:
        with self._connect() as connection:
            connection.execute(
                "INSERT OR REPLACE INTO clarifications(source_id, error) VALUES (?, ?)",
                (source_id, error),
            )
        return self._conflict_receipt(source_id, error, item_id)

    def _prepare_completion(self, request: dict) -> dict:
        intent = request.get("intent")
        if not isinstance(intent, dict) or intent.get("action") != "complete":
            return request
        item_id = intent.get("item_id")
        if not item_id:
            raise CohesionError("completion requires intent.item_id")
        with self._connect() as connection:
            item = connection.execute("SELECT * FROM items WHERE item_id = ?", (item_id,)).fetchone()
        if item is None:
            raise CohesionError("completion target does not exist")
        prepared = {**request, "intent": {**intent}}
        prepared_intent = prepared["intent"]
        for field in ("category", "title", "area", "priority", "due"):
            prepared_intent.setdefault(field, item[field])
        prepared_intent.setdefault("tags", json.loads(item["tags_json"]))
        if item["start_at"]:
            prepared_intent.setdefault("start", item["start_at"])
            prepared_intent.setdefault("end", item["end_at"])
        if item["calendar_id"]:
            entry = gcal.calendar_by_id(self._calendars(), item["calendar_id"])
            if entry is None:
                raise CohesionError("the item's calendar is no longer in the calendar config")
            prepared_intent.setdefault("calendar", entry["name"])
        prepared_intent.setdefault("placement", item["placement"])
        return prepared

    def _validate(self, request: dict) -> tuple[dict, dict, tuple, str]:
        source = self._validate_source(request)
        intent = request.get("intent")
        if not isinstance(intent, dict):
            raise CohesionError("intent is required")
        source_time = _source_time(source["timestamp"])

        action = intent.get("action")
        if action not in {"upsert", "complete"}:
            raise CohesionError("intent.action must be upsert or complete")
        category = intent.get("category")
        if category not in SEEDED_PREFERENCES:
            raise CohesionError("intent.category is unsupported")
        title = intent.get("title")
        if not isinstance(title, str) or not title.strip():
            raise CohesionError("intent.title is required")
        if "\n" in title or "\r" in title or "<!--" in title:
            raise CohesionError("intent.title must be one plain-text line")
        placement = intent.get("placement") or self._preference(category)
        if placement not in PLACEMENTS:
            raise CohesionError("intent.placement is unsupported")

        area = intent.get("area")
        if "tasks" in self._destinations(placement) and area not in PRIMARY_AREAS:
            raise CohesionError(f"intent.area must be one of {', '.join(PRIMARY_AREAS)}")
        tags = intent.get("tags", [])
        if not isinstance(tags, list) or any(
            not isinstance(tag, str) or not re.fullmatch(r"[A-Za-z][\w-]*", tag.lstrip("#"))
            for tag in tags
        ):
            raise CohesionError("intent.tags must be a list of tag names")
        normalized_tags = [
            tag.lstrip("#") for tag in tags if tag.lstrip("#").lower() not in PRIMARY_AREAS
        ]
        priority = intent.get("priority", "med")
        if priority not in {"high", "med", "low"}:
            raise CohesionError("intent.priority must be high, med, or low")
        due = _resolve_date(intent.get("due"), source_time)
        start_at = _resolve_datetime(intent.get("start"))
        end_at = _resolve_datetime(intent.get("end"))
        if due is not None and (start_at is not None or end_at is not None):
            raise CohesionError("choose an all-day due date or a timed start and end")
        calendar = {}
        if "calendar" in self._destinations(placement):
            calendar = self._resolve_calendar(intent.get("calendar"))
            if due is None and (start_at is None or end_at is None):
                raise CohesionError("calendar operations need due or start and end")
        if start_at and end_at and end_at <= start_at:
            raise CohesionError("intent.end must be after intent.start")

        normalized = (
            category,
            title.strip(),
            area,
            json.dumps(normalized_tags),
            priority,
            due,
            start_at,
            end_at,
            calendar.get("profile"),
            calendar.get("id"),
            placement,
            "completed" if action == "complete" else "active",
        )
        return source, intent, normalized, placement

    def _calendars(self) -> list[dict]:
        try:
            return gcal.load_config(self.calendars_path)
        except gcal.GcalError as exc:
            raise CohesionError(str(exc)) from exc

    def _resolve_calendar(self, name: object) -> dict:
        """Callers name a calendar; its profile and ID come only from the calendar config."""
        if not isinstance(name, str) or not name.strip():
            raise CohesionError("intent.calendar must name a configured calendar")
        try:
            entry = gcal.find_calendar(self._calendars(), name)
        except gcal.GcalError as exc:
            raise CohesionError(str(exc)) from exc
        if "cohesion" not in entry["write_owner"]:
            raise CohesionError(f"calendar {name!r} is not written by cohesion")
        return entry

    def _preference(self, category: str) -> str:
        with self._connect() as connection:
            row = connection.execute(
                "SELECT placement FROM preferences WHERE category = ?", (category,)
            ).fetchone()
        if row is None:
            raise CohesionError("intent.category has no placement preference")
        return row["placement"]

    @staticmethod
    def _validate_source(request: dict) -> dict:
        if request.get("version") != CONTRACT_VERSION:
            raise CohesionError(f"version must be {CONTRACT_VERSION}")
        source = request.get("source")
        if not isinstance(source, dict):
            raise CohesionError("source is required")
        for field in ("id", "kind", "native_id", "revision", "timestamp"):
            if field not in source:
                raise CohesionError(f"source.{field} is required")
        for field in ("id", "kind", "native_id", "timestamp"):
            if not isinstance(source[field], str) or not source[field].strip():
                raise CohesionError(f"source.{field} must be a non-empty string")
        if not isinstance(source["revision"], int) or source["revision"] < 1:
            raise CohesionError("source.revision must be a positive integer")
        _source_time(source["timestamp"])
        return source

    @staticmethod
    def _destinations(placement: str) -> tuple[str, ...]:
        if placement == "both":
            return "tasks", "calendar"
        return (placement,)

    def _run_pending(self, source_id: str) -> None:
        with self._connect() as connection:
            operations = connection.execute(
                """SELECT operations.*, sources.request_json AS source_request_json
                   FROM operations
                   JOIN sources USING(source_id)
                   WHERE source_id = ? AND status = 'pending'
                   ORDER BY destination DESC""",
                (source_id,),
            ).fetchall()
        for operation in operations:
            operation_data = dict(operation)
            operation_data.update(json.loads(operation["snapshot_json"]))
            try:
                if operation["destination"] == "tasks":
                    result, version = self._apply_task(operation_data)
                else:
                    result, version = self._apply_calendar(operation_data)
            except (CohesionError, gcal.GcalError, subprocess.TimeoutExpired) as exc:
                self._finish_operation(operation["operation_id"], "pending", None, None, str(exc))
            else:
                self._finish_operation(operation["operation_id"], "applied", result, version, None)

    def _finish_operation(
        self,
        operation_id: str,
        status: str,
        result: dict | None,
        version: str | None,
        error: str | None,
    ) -> None:
        with self._connect() as connection:
            connection.execute(
                """UPDATE operations SET status = ?, attempts = attempts + 1,
                   result_json = ?,
                   destination_version = CASE WHEN ? = 'applied' THEN ?
                                              ELSE COALESCE(?, destination_version) END,
                   error = ?
                   WHERE operation_id = ?""",
                (
                    status,
                    json.dumps(result) if result is not None else None,
                    status,
                    version,
                    version,
                    error,
                    operation_id,
                ),
            )

    def _apply_task(self, operation: dict) -> tuple[dict, str]:
        content = self.tasks_path.read_text(encoding="utf-8")
        task_id = operation["task_id"]
        marker = f"<!-- task-id: {task_id} -->"
        metadata = f"#{operation['area']} !{operation['priority']}"
        if operation["tags"]:
            metadata += " " + " ".join(f"#{tag}" for tag in operation["tags"])
        if operation["due"]:
            metadata += f" @{operation['due']}"
        lines = content.splitlines()
        matches = [index for index, current in enumerate(lines) if marker in current]
        if len(matches) > 1:
            raise CohesionError(f"duplicate task identity {task_id}")
        current = lines[matches[0]] if matches else None
        if operation["action"] == "complete":
            if current is None:
                raise CohesionError(f"task identity {task_id} does not exist")
            recorded = re.search(r"\(done (\d{4}-\d{2}-\d{2})\) <!--", current)
            if current.startswith("- [x] ") and recorded:
                completed_on = recorded.group(1)
            else:
                source_request = json.loads(operation["source_request_json"])
                completed_on = (
                    _source_time(source_request["source"]["timestamp"])
                    .astimezone(MANILA)
                    .date()
                    .isoformat()
                )
            line = f"- [x] {operation['title']} {metadata} (done {completed_on}) {marker}"
        else:
            line = f"- [ ] {operation['title']} {metadata} {marker}"
        if current == line:
            return {"task_id": task_id}, _content_hash(line)
        if _line_version(current) != operation["destination_version"]:
            raise ConcurrentEdit("the task line changed after the last applied operation")
        if operation["action"] == "complete":
            lines.pop(matches[0])
            try:
                done_index = lines.index("## Done")
            except ValueError as exc:
                raise CohesionError("tasks.md has no Done section") from exc
            lines.insert(done_index + 1, line)
        elif matches:
            lines[matches[0]] = line
        else:
            try:
                active_index = lines.index("## Active")
            except ValueError as exc:
                raise CohesionError("tasks.md has no Active section") from exc
            lines.insert(active_index + 1, line)
        updated = "\n".join(lines) + ("\n" if content.endswith("\n") else "")
        self._write_tasks(updated)
        return {"task_id": task_id}, _content_hash(line)

    def _write_tasks(self, content: str) -> None:
        descriptor, temporary_name = tempfile.mkstemp(
            dir=self.tasks_path.parent, prefix=f".{self.tasks_path.name}.", text=True
        )
        try:
            os.fchmod(descriptor, self.tasks_path.stat().st_mode & 0o777)
            with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
                handle.write(content)
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(temporary_name, self.tasks_path)
        finally:
            if os.path.exists(temporary_name):
                os.unlink(temporary_name)

    def _calendar_body(self, operation: dict) -> dict:
        private = {"achios_owner": gcal.OWNER_COHESION, "achios_item_id": operation["item_id"]}
        if operation.get("placement") != "calendar":
            private["achios_task_id"] = operation["task_id"]
        private["achios_item_state"] = operation["state"]
        if operation["due"]:
            day = dt.date.fromisoformat(operation["due"])
            # Google stores useDefault false on all-day events whatever is sent, checked live.
            body = gcal.all_day_body(operation["title"], day)
        else:
            body = {
                "summary": operation["title"],
                "start": {"dateTime": operation["start_at"], "timeZone": "Asia/Manila"},
                "end": {"dateTime": operation["end_at"], "timeZone": "Asia/Manila"},
            }
        body["extendedProperties"] = {"private": private}
        return body

    def _apply_calendar(self, operation: dict) -> tuple[dict, str | None]:
        profile = operation["calendar_profile"]
        calendar_id = operation["calendar_id"]
        event_id = _event_id(operation["item_id"])
        body = self._calendar_body(operation)
        existing = self.calendar.get(
            profile=profile, calendar_id=calendar_id, event_id=event_id
        )
        if existing and existing.get("status") == "cancelled":
            raise CohesionError("owned calendar event no longer exists")
        if existing:
            private = gcal.private_properties(existing)
            # Events created before achios_owner existed carry only the item ID.
            if private.get("achios_item_id") != operation["item_id"] or private.get(
                "achios_owner", gcal.OWNER_COHESION
            ) != gcal.OWNER_COHESION:
                raise CohesionError("calendar event ownership is unknown")
            if (
                operation["destination_version"] is not None
                and _calendar_version(existing) != operation["destination_version"]
            ):
                raise ConcurrentEdit("calendar event changed since the last applied operation")
            completion_note = "achiOS item state: completed"
            previous_description = (
                existing.get("description", "").replace(completion_note, "").strip()
            )
            if operation["action"] == "complete":
                body["description"] = (
                    f"{previous_description}\n\n{completion_note}"
                    if previous_description
                    else completion_note
                )
            elif previous_description:
                body["description"] = previous_description
            if _calendar_version(existing) == _calendar_version(body) and existing.get(
                "description", ""
            ) == body.get("description", ""):
                event = existing
            else:
                event = self.calendar.update(
                    profile=profile,
                    calendar_id=calendar_id,
                    event_id=event_id,
                    body=body,
                    expected_version=existing.get("etag"),
                )
        else:
            if operation["action"] == "complete":
                raise CohesionError("owned calendar event no longer exists")
            try:
                event = self.calendar.insert(
                    profile=profile, calendar_id=calendar_id, event_id=event_id, body=body
                )
            except subprocess.TimeoutExpired:
                event = self.calendar.get(
                    profile=profile, calendar_id=calendar_id, event_id=event_id
                )
                if event is None:
                    raise
        return {
            "event_id": event_id,
            "profile": profile,
            "calendar_id": calendar_id,
        }, _calendar_version(event)

    def _receipt(self, source_id: str, placement: str) -> dict:
        with self._connect() as connection:
            rows = connection.execute(
                """SELECT operation_id, item_id, destination, status, attempts, result_json, error
                   FROM operations WHERE source_id = ? ORDER BY destination""",
                (source_id,),
            ).fetchall()
        operations = [
            {
                "operation_id": row["operation_id"],
                "destination": row["destination"],
                "status": row["status"],
                "attempts": row["attempts"],
                "result": json.loads(row["result_json"]) if row["result_json"] else None,
                "error": row["error"],
            }
            for row in rows
        ]
        return {
            "version": CONTRACT_VERSION,
            "source_id": source_id,
            "item_id": rows[0]["item_id"] if rows else None,
            "placement": placement,
            "applied": [op for op in operations if op["status"] == "applied"],
            "pending": [op for op in operations if op["status"] == "pending"],
            "superseded": [op for op in operations if op["status"] == "superseded"],
        }

    @staticmethod
    def _conflict_receipt(source_id: str, error: str, item_id: str | None = None) -> dict:
        return {
            "version": CONTRACT_VERSION,
            "source_id": source_id,
            "item_id": item_id,
            "placement": None,
            "applied": [],
            "pending": [{"destination": None, "status": "pending", "error": error}],
            "superseded": [],
        }


def _read_request(path: str) -> dict:
    if path == "-":
        return json.load(sys.stdin)
    return json.loads(Path(path).read_text(encoding="utf-8"))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--db", type=Path, default=DEFAULT_DB)
    parser.add_argument("--tasks", type=Path, default=DEFAULT_TASKS)
    parser.add_argument("--calendars", type=Path, default=None, help="calendar config path")
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("capabilities")
    context_parser = subparsers.add_parser("context")
    context_parser.add_argument("--category")
    submit_parser = subparsers.add_parser("submit")
    submit_parser.add_argument("--input", default="-", help="JSON file or - for stdin")
    args = parser.parse_args(argv)

    service = CohesionService(db_path=args.db, tasks_path=args.tasks, calendars_path=args.calendars)
    try:
        if args.command == "capabilities":
            result = service.capabilities()
        elif args.command == "context":
            result = service.context(args.category)
        else:
            result = service.submit(_read_request(args.input))
    except (CohesionError, ValueError, json.JSONDecodeError) as exc:
        print(json.dumps({"version": CONTRACT_VERSION, "error": str(exc)}))
        return 2
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
