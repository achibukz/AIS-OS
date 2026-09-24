"""Bounded, scoped recall of learned preferences and saved notes for one turn.

A topic reads its own domain. General reads achiMem, and reads schoolMem only
when the request is about school. Revoked and superseded preference revisions
never appear, and notes older than NOTE_MAX_AGE are left out. The block is
capped at MAX_TOKENS. Every matched record is logged as retrieved, and the ones
that fit are logged as selected, keyed by the turn's source so later uses and
corrections can be joined to them.
"""

from __future__ import annotations

import datetime as dt
import re
import sqlite3
from pathlib import Path
from typing import Any

MAX_TOKENS = 1500
CHARS_PER_TOKEN = 4
NOTE_MAX_AGE = dt.timedelta(days=180)
TOPIC_SCOPES = {
    "general": ("achimem",),
    "achimem": ("achimem",),
    "schoolmem": ("schoolmem",),
}
SCHOOL_RE = re.compile(
    r"\b(school|class|course|assignment|exam|quiz|lab|lecture|dlsu|canvas|schoolmem|[A-Z]{4,7}\d{0,3})\b"
)


def scopes_for(topic: str | None, query: str) -> tuple[str, ...]:
    scopes = TOPIC_SCOPES.get(topic or "", ())
    # Cross-domain recall needs the request itself to point at the other domain.
    if topic == "general" and SCHOOL_RE.search(query or ""):
        scopes = scopes + ("schoolmem",)
    return scopes


def _preferences(db: Path) -> list[dict[str, Any]]:
    connection = sqlite3.connect(db)
    connection.row_factory = sqlite3.Row
    try:
        rows = connection.execute(
            """SELECT p.preference_id, p.kind, p.scope_type, p.scope_value, p.value, p.revision,
                      p.exceptions_json, e.evidence
               FROM semantic_preferences p
               JOIN semantic_preference_events e ON e.event_id = p.evidence_event_id
               WHERE p.status = 'active'
               ORDER BY CASE p.scope_type WHEN 'item' THEN 0 WHEN 'category' THEN 1 ELSE 2 END,
                        p.updated_at DESC"""
        ).fetchall()
    finally:
        connection.close()
    return [dict(row) for row in rows]


def _preference_line(row: dict) -> str:
    scope = f"{row['scope_type']}:{row['scope_value']}" if row["scope_value"] else row["scope_type"]
    return (
        f"- pref {row['preference_id']} r{row['revision']}: {row['kind']}={row['value']} "
        f"({scope}), from Aki: \"{row['evidence']}\""
    )


def _note_line(note: dict) -> str:
    where = note.get("viewer_link") or note["path"]
    return f"- note \"{note['title']}\" ({note['scope']}): {where}"


def recall(
    db: Path,
    notes,
    *,
    topic: str | None,
    query: str,
    source_id: str,
    now: dt.datetime | None = None,
) -> dict[str, Any]:
    now = now or dt.datetime.now(dt.UTC)
    scopes = scopes_for(topic, query)
    if not scopes:
        return {"topic": topic, "scopes": [], "text": "", "selected": 0, "dropped": 0}
    candidates: list[tuple[str, str, int, str]] = [
        ("preference", row["preference_id"], row["revision"], _preference_line(row))
        for row in _preferences(db)
    ]
    for scope in scopes:
        for note in notes.recall(scope, query) if notes is not None else []:
            if now - dt.datetime.fromtimestamp(Path(note["path"]).stat().st_mtime, dt.UTC) > NOTE_MAX_AGE:
                continue
            candidates.append(("note", note["path"], 1, _note_line({**note, "scope": scope})))
    budget = MAX_TOKENS * CHARS_PER_TOKEN
    selected, used = [], 0
    for candidate in candidates:
        if used + len(candidate[3]) + 1 > budget:
            continue
        selected.append(candidate)
        used += len(candidate[3]) + 1
    chosen = {(kind, record_id) for kind, record_id, _, _ in selected}
    stamp = now.isoformat()
    connection = sqlite3.connect(db)
    try:
        with connection:
            connection.executemany(
                "INSERT OR IGNORE INTO learning_retrievals VALUES(?,?,?,?,?,?,NULL)",
                [
                    (kind, record_id, revision, source_id, int((kind, record_id) in chosen), stamp)
                    for kind, record_id, revision, _ in candidates
                ],
            )
    finally:
        connection.close()
    text = ""
    if selected:
        text = "\n".join(line for _, _, _, line in selected)
    return {
        "topic": topic,
        "scopes": list(scopes),
        "text": text,
        "selected": len(selected),
        "dropped": len(candidates) - len(selected),
    }
