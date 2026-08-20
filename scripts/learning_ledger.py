#!/usr/bin/env python3
"""Append-only audit trail for the self-learning loop.

Every candidate the loop considers gets a record here, whether it was written to
memory or rejected. This is the instrument the 2026-08-27 trial audit reads; without
it, judging whether autonomous writes are safe is guesswork.

Records are never mutated in place. A state change appends a new record carrying the
same id, and readers take the latest. That keeps every write atomic (a single
O_APPEND line) and preserves the full decision history for the audit.
"""

from __future__ import annotations

import json
import os
import uuid
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Optional
from zoneinfo import ZoneInfo

try:
    import fcntl
except ImportError:  # pragma: no cover - POSIX only in practice
    fcntl = None

LOCAL_TZ = ZoneInfo("Asia/Manila")
DEFAULT_PATH = Path.home() / ".local" / "state" / "achios" / "learning_ledger.jsonl"

PENDING = "pending"
WRITTEN = "written"
REJECTED = "rejected"
FAILED = "failed"


@dataclass
class Candidate:
    record_id: str
    chat_id: int
    turn_index: int
    raw: str


def _resolve(path: Optional[Path]) -> Path:
    target = Path(path) if path else DEFAULT_PATH
    target.parent.mkdir(parents=True, exist_ok=True)
    return target


@contextmanager
def _locked(path: Path):
    """Exclusive lock on a sidecar file, mirroring memory_engine's pattern."""
    lock_path = path.with_suffix(path.suffix + ".lock")
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    handle = open(lock_path, "a+", encoding="utf-8")
    try:
        if fcntl is not None:
            fcntl.flock(handle, fcntl.LOCK_EX)
        yield
    finally:
        try:
            if fcntl is not None:
                fcntl.flock(handle, fcntl.LOCK_UN)
        finally:
            handle.close()


def _append(record: dict[str, Any], path: Optional[Path]) -> None:
    target = _resolve(path)
    with _locked(target):
        with open(target, "a", encoding="utf-8") as handle:
            handle.write(json.dumps(record, ensure_ascii=False) + "\n")


def _read_all(path: Optional[Path]) -> list[dict[str, Any]]:
    target = _resolve(path)
    if not target.exists():
        return []
    records = []
    for line in target.read_text(encoding="utf-8", errors="replace").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            records.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return records


def _latest_by_id(path: Optional[Path]) -> dict[str, dict[str, Any]]:
    latest: dict[str, dict[str, Any]] = {}
    for record in _read_all(path):
        rid = record.get("id")
        if rid:
            latest[rid] = record
    return latest


def append_candidate(
    chat_id: int,
    raw: str,
    turn_index: int,
    path: Optional[Path] = None,
) -> str:
    record_id = uuid.uuid4().hex
    _append(
        {
            "id": record_id,
            "ts": datetime.now(LOCAL_TZ).isoformat(),
            "chat_id": chat_id,
            "turn_index": turn_index,
            "raw": raw,
            "state": PENDING,
            "verdict": None,
            "reason": None,
            "rule": None,
            "action": None,
            "target": None,
        },
        path,
    )
    return record_id


def _transition(record_id: str, path: Optional[Path], **fields: Any) -> None:
    base = _latest_by_id(path).get(record_id)
    if base is None:
        return
    updated = dict(base)
    updated.update(fields)
    updated["ts"] = datetime.now(LOCAL_TZ).isoformat()
    _append(updated, path)


def mark_written(
    record_id: str,
    rule: str,
    action: str,
    target: str,
    path: Optional[Path] = None,
) -> None:
    _transition(
        record_id,
        path,
        state=WRITTEN,
        verdict="durable",
        rule=rule,
        action=action,
        target=target,
    )


def mark_rejected(record_id: str, reason: str, path: Optional[Path] = None) -> None:
    _transition(record_id, path, state=REJECTED, reason=reason, action="none")


def mark_failed(record_id: str, reason: str, path: Optional[Path] = None) -> None:
    _transition(record_id, path, state=FAILED, reason=reason, action="none")


def latest(record_id: str, path: Optional[Path] = None) -> Optional[dict[str, Any]]:
    return _latest_by_id(path).get(record_id)


def pending(chat_id: int, limit: int = 25, path: Optional[Path] = None) -> list[Candidate]:
    out = []
    for record in _latest_by_id(path).values():
        if record.get("state") != PENDING or record.get("chat_id") != chat_id:
            continue
        out.append(
            Candidate(
                record_id=record["id"],
                chat_id=record["chat_id"],
                turn_index=record.get("turn_index", 0),
                raw=record.get("raw", ""),
            )
        )
    out.sort(key=lambda c: c.turn_index)
    return out[:limit]


def writes_today(path: Optional[Path] = None) -> int:
    # Manila date, not date.today(). The box runs UTC, and records are stamped in
    # Asia/Manila — comparing the two makes the daily cap read zero for the eight
    # hours the dates disagree, silently disabling it.
    today = datetime.now(LOCAL_TZ).date().isoformat()
    return sum(
        1
        for record in _latest_by_id(path).values()
        if record.get("state") == WRITTEN and str(record.get("ts", "")).startswith(today)
    )


def stats(path: Optional[Path] = None) -> dict[str, int]:
    counts: dict[str, int] = {PENDING: 0, WRITTEN: 0, REJECTED: 0, FAILED: 0}
    for record in _latest_by_id(path).values():
        state = record.get("state")
        if state in counts:
            counts[state] += 1
    return counts
