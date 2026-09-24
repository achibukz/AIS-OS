"""Versioned semantic preferences backed by exact source evidence."""

from __future__ import annotations

import datetime as dt
import hashlib
import json
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Any

import learning_ledger

KINDS = {"viewer_delivery", "placement", "linked_completion"}
SCOPES = {"global", "category", "item", "ambiguous"}
VALUES = {
    "viewer_delivery": {"viewer_link", "paste"},
    "placement": {"tasks", "calendar", "both"},
    "linked_completion": {"linked", "single"},
}
USER_SOURCE_KINDS = {"telegram_user", "fixture_user"}


class PreferenceError(ValueError):
    pass


def _stable_id(prefix: str, value: str) -> str:
    digest = hashlib.sha256(value.encode("utf-8")).hexdigest()
    return f"{prefix}_{digest[:24]}"


class PreferenceStore:
    def __init__(self, path: Path, ledger_path: Path | None = None):
        self.path = Path(path)
        self.ledger_path = Path(ledger_path) if ledger_path else self.path.with_name(
            "learning_ledger.jsonl"
        )
        self.path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        self._initialize()

    @contextmanager
    def _connect(self):
        connection = sqlite3.connect(self.path)
        connection.row_factory = sqlite3.Row
        try:
            with connection:
                yield connection
        finally:
            connection.close()

    def _initialize(self) -> None:
        with self._connect() as connection:
            connection.executescript(
                """
                CREATE TABLE IF NOT EXISTS semantic_preference_events (
                    event_id TEXT PRIMARY KEY,
                    source_id TEXT NOT NULL,
                    source_kind TEXT NOT NULL,
                    native_id TEXT NOT NULL,
                    source_revision INTEGER NOT NULL,
                    source_timestamp TEXT NOT NULL,
                    evidence TEXT NOT NULL,
                    evidence_validated INTEGER NOT NULL,
                    kind TEXT,
                    scope_type TEXT,
                    scope_value TEXT,
                    value TEXT,
                    exceptions_json TEXT NOT NULL,
                    action TEXT NOT NULL,
                    status TEXT NOT NULL,
                    reason TEXT,
                    question TEXT,
                    created_at TEXT NOT NULL,
                    UNIQUE(source_id, kind, scope_type, scope_value, action)
                );
                CREATE TABLE IF NOT EXISTS semantic_preferences (
                    preference_id TEXT PRIMARY KEY,
                    kind TEXT NOT NULL,
                    scope_type TEXT NOT NULL,
                    scope_value TEXT NOT NULL,
                    value TEXT NOT NULL,
                    exceptions_json TEXT NOT NULL,
                    revision INTEGER NOT NULL,
                    status TEXT NOT NULL,
                    evidence_event_id TEXT NOT NULL REFERENCES semantic_preference_events(event_id),
                    updated_at TEXT NOT NULL,
                    UNIQUE(kind, scope_type, scope_value)
                );
                CREATE TABLE IF NOT EXISTS semantic_review_state (
                    singleton INTEGER PRIMARY KEY CHECK(singleton=1),
                    checkpoint INTEGER NOT NULL,
                    updated_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS semantic_review_calls (
                    call_id TEXT PRIMARY KEY,
                    manila_day TEXT NOT NULL,
                    started_at TEXT NOT NULL,
                    status TEXT NOT NULL
                );
                INSERT OR IGNORE INTO semantic_review_state(singleton,checkpoint,updated_at)
                VALUES(1,0,'1970-01-01T00:00:00+00:00');
                """
            )

    @staticmethod
    def _validate_source(source: dict[str, Any]) -> None:
        required = {"id", "kind", "native_id", "revision", "timestamp"}
        if not isinstance(source, dict) or set(source) != required:
            raise PreferenceError("source envelope is incomplete or contains extra fields")
        for field in ("id", "kind", "native_id", "timestamp"):
            if not isinstance(source[field], str) or not source[field].strip():
                raise PreferenceError(f"source.{field} must be a non-empty string")
        if not isinstance(source["revision"], int) or source["revision"] < 1:
            raise PreferenceError("source.revision must be a positive integer")
        parsed = dt.datetime.fromisoformat(source["timestamp"])
        if parsed.tzinfo is None or parsed.utcoffset() is None:
            raise PreferenceError("source.timestamp must include an offset")

    @staticmethod
    def _validate_preference(preference: dict[str, Any]) -> None:
        if not isinstance(preference, dict):
            raise PreferenceError("preference is required")
        kind = preference.get("kind")
        scope = preference.get("scope")
        action = preference.get("action", "set")
        if kind not in KINDS:
            raise PreferenceError("preference.kind is unsupported")
        if scope not in SCOPES:
            raise PreferenceError("preference.scope is unsupported")
        if action not in {"set", "revoke"}:
            raise PreferenceError("preference.action must be set or revoke")
        if scope in {"category", "item"} and not str(preference.get("scope_value") or "").strip():
            raise PreferenceError("scoped preferences require scope_value")
        value = preference.get("value")
        if action == "set" and value not in VALUES[kind]:
            raise PreferenceError("preference.value is unsupported for its kind")
        evidence = preference.get("evidence")
        if not isinstance(evidence, str) or not evidence.strip():
            raise PreferenceError("preference.evidence must quote the source")
        exceptions = preference.get("exceptions", [])
        if not isinstance(exceptions, list) or any(not isinstance(item, str) for item in exceptions):
            raise PreferenceError("preference.exceptions must be a list of strings")

    def record(self, source: dict[str, Any], preference: dict[str, Any]) -> dict[str, Any]:
        self._validate_source(source)
        self._validate_preference(preference)
        scope = preference["scope"]
        scope_value = str(preference.get("scope_value") or "")
        event_id = _stable_id(
            "prefev",
            f"{source['id']}:{preference['kind']}:{scope}:{scope_value}:{preference.get('action', 'set')}",
        )
        status = "pending"
        reason = None
        question = None
        if source["kind"] not in USER_SOURCE_KINDS:
            status = "rejected"
            reason = "assistant_or_unsupported_source"
        elif not preference.get("evidence_validated"):
            reason = "source_quote_not_validated"
        elif scope == "ambiguous":
            question = self._question(preference["kind"])
            reason = "scope_needs_clarification"
        elif preference.get("explicit") is True:
            status = "validated"
        else:
            reason = "daily_review_required"
        now = dt.datetime.now(dt.UTC).isoformat()
        with self._connect() as connection:
            cursor = connection.execute(
                """INSERT OR IGNORE INTO semantic_preference_events VALUES(
                       ?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                (
                    event_id,
                    source["id"],
                    source["kind"],
                    source["native_id"],
                    source["revision"],
                    source["timestamp"],
                    preference["evidence"].strip(),
                    int(bool(preference.get("evidence_validated"))),
                    preference["kind"],
                    scope,
                    scope_value,
                    preference.get("value"),
                    json.dumps(preference.get("exceptions", []), ensure_ascii=False),
                    preference.get("action", "set"),
                    status,
                    reason,
                    question,
                    now,
                ),
            )
        if not cursor.rowcount:
            return self._replayed(event_id)
        learning_ledger.record_semantic_event(
            event_id,
            source,
            preference["evidence"].strip(),
            preference,
            status,
            reason,
            path=self.ledger_path,
        )
        if status == "validated":
            activated = self.activate(event_id)
            return {**activated, "question": None}
        return {
            "event_id": event_id,
            "status": status,
            "reason": reason,
            "question": question,
            "activated": False,
        }

    def _replayed(self, event_id: str) -> dict[str, Any]:
        """Report a repeated source event without activating it a second time."""
        with self._connect() as connection:
            event = connection.execute(
                "SELECT status,reason,question FROM semantic_preference_events WHERE event_id=?",
                (event_id,),
            ).fetchone()
        return {
            "event_id": event_id,
            "status": event["status"],
            "reason": event["reason"],
            "question": event["question"],
            "activated": False,
        }

    @staticmethod
    def _question(kind: str) -> str:
        questions = {
            "viewer_delivery": "Should I use that file format every time, or only for this request?",
            "placement": "Should that placement apply to this category in future, or only this item?",
            "linked_completion": "Should linked records complete together for this category, or only this item?",
        }
        return questions[kind]

    def activate(self, event_id: str) -> dict[str, Any]:
        now = dt.datetime.now(dt.UTC).isoformat()
        with self._connect() as connection:
            event = connection.execute(
                "SELECT * FROM semantic_preference_events WHERE event_id=?", (event_id,)
            ).fetchone()
            if event is None:
                raise PreferenceError("preference event does not exist")
            if event["status"] == "rejected" or event["source_kind"] not in USER_SOURCE_KINDS:
                raise PreferenceError("unsupported evidence cannot activate a preference")
            if not event["evidence_validated"]:
                raise PreferenceError("unvalidated source evidence cannot activate a preference")
            if event["scope_type"] not in {"global", "category", "item"}:
                raise PreferenceError("ambiguous preferences cannot activate")
            key = f"{event['kind']}:{event['scope_type']}:{event['scope_value']}"
            preference_id = _stable_id("pref", key)
            current = connection.execute(
                """SELECT revision FROM semantic_preferences
                   WHERE kind=? AND scope_type=? AND scope_value=?""",
                (event["kind"], event["scope_type"], event["scope_value"]),
            ).fetchone()
            revision = (current["revision"] if current else 0) + 1
            status = "revoked" if event["action"] == "revoke" else "active"
            value = event["value"] or "revoked"
            connection.execute(
                """INSERT INTO semantic_preferences VALUES(?,?,?,?,?,?,?,?,?,?)
                   ON CONFLICT(kind,scope_type,scope_value) DO UPDATE SET
                   value=excluded.value,exceptions_json=excluded.exceptions_json,
                   revision=excluded.revision,status=excluded.status,
                   evidence_event_id=excluded.evidence_event_id,updated_at=excluded.updated_at""",
                (
                    preference_id,
                    event["kind"],
                    event["scope_type"],
                    event["scope_value"],
                    value,
                    event["exceptions_json"],
                    revision,
                    status,
                    event_id,
                    now,
                ),
            )
            connection.execute(
                "UPDATE semantic_preference_events SET status=?,reason=NULL WHERE event_id=?",
                ("activated" if status == "active" else "revoked", event_id),
            )
        learning_ledger.mark_semantic_event(
            event_id,
            "activated" if status == "active" else "revoked",
            path=self.ledger_path,
        )
        return {
            "event_id": event_id,
            "preference_id": preference_id,
            "status": status,
            "revision": revision,
            "activated": status == "active",
        }

    def effective(
        self,
        kind: str,
        *,
        category: str | None = None,
        item_id: str | None = None,
    ) -> dict[str, Any] | None:
        if kind not in KINDS:
            raise PreferenceError("preference kind is unsupported")
        scopes = []
        if item_id:
            scopes.append(("item", item_id))
        if category:
            scopes.append(("category", category))
        scopes.append(("global", ""))
        with self._connect() as connection:
            for scope_type, scope_value in scopes:
                row = connection.execute(
                    """SELECT * FROM semantic_preferences
                       WHERE kind=? AND scope_type=? AND scope_value=? AND status='active'""",
                    (kind, scope_type, scope_value),
                ).fetchone()
                if row:
                    result = dict(row)
                    result["exceptions"] = json.loads(result.pop("exceptions_json"))
                    return result
        return None

    def context(self, category: str | None = None) -> dict[str, Any]:
        active = {}
        for kind in sorted(KINDS):
            preference = self.effective(kind, category=category)
            if preference:
                active[kind] = {
                    key: preference[key]
                    for key in ("value", "scope_type", "scope_value", "revision", "exceptions")
                }
        with self._connect() as connection:
            pending = connection.execute(
                "SELECT COUNT(*) FROM semantic_preference_events WHERE status='pending'"
            ).fetchone()[0]
            conflicts = [
                dict(row)
                for row in connection.execute(
                    """SELECT event_id,source_id,evidence,kind,scope_type,scope_value,value,reason
                       FROM semantic_preference_events
                       WHERE status IN ('pending','rejected') ORDER BY rowid DESC LIMIT 20"""
                )
            ]
        return {"active": active, "pending_count": pending, "inspectable": conflicts}

    def pending(self, limit: int = 25, *, reviewable: bool = False) -> list[dict[str, Any]]:
        """Pending events. Reviewable ones exclude events no classifier can activate."""
        where = "status='pending'"
        if reviewable:
            where += " AND reason='daily_review_required'"
        with self._connect() as connection:
            return [
                dict(row)
                for row in connection.execute(
                    f"SELECT rowid AS sequence,* FROM semantic_preference_events "
                    f"WHERE {where} ORDER BY rowid LIMIT ?",
                    (limit,),
                )
            ]

    def mark_rejected(self, event_id: str, reason: str) -> None:
        with self._connect() as connection:
            connection.execute(
                "UPDATE semantic_preference_events SET status='rejected',reason=? WHERE event_id=?",
                (reason, event_id),
            )
        learning_ledger.mark_semantic_event(
            event_id, "rejected", reason, path=self.ledger_path
        )
