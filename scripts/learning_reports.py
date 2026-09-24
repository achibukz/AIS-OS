#!/usr/bin/env python3
"""Daily learning receipts, weekly evidence debriefs and learning health.

The daily receipt follows the 03:00 semantic review. The weekly debrief covers
the Manila week that ends Sunday 20:00 by default. Both go through the durable
outbox under stable IDs, so a restart catch-up cannot send a second report.
Every count reads stored records. Nothing here calls a model.

Usage:
    python scripts/learning_reports.py weekly
    python scripts/learning_reports.py health
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import sqlite3
import subprocess
import sys
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

import agy_classify
import notify_outbox
import owned_persist
import sync_completed_tickets

MANILA = ZoneInfo("Asia/Manila")
COHESION_DB = Path.home() / ".local" / "state" / "achios" / "cohesion.sqlite3"
VAULTS = (
    Path.home() / "Documents" / "Obsidian" / "achiMem",
    Path.home() / "Documents" / "Obsidian" / "schoolMem",
)
WEEKLY_DAY = int(os.environ.get("ACHIOS_WEEKLY_DAY", "6"))  # Monday is 0, Sunday is 6
WEEKLY_TIME = dt.time.fromisoformat(os.environ.get("ACHIOS_WEEKLY_TIME", "20:00"))
MAX_CALLS_PER_DAY = 24


def _read(path: Path, query: str, params: tuple = ()) -> list[sqlite3.Row]:
    if not path.is_file():
        return []
    connection = sqlite3.connect(f"file:{path}?mode=ro", uri=True)
    connection.row_factory = sqlite3.Row
    try:
        return connection.execute(query, params).fetchall()
    except sqlite3.OperationalError:
        return []  # the table arrives with a later release
    finally:
        connection.close()


def _iso(value: dt.datetime) -> str:
    return value.astimezone(dt.UTC).isoformat()


def week_window(now: dt.datetime) -> tuple[dt.datetime, dt.datetime]:
    """The latest completed report week. A late catch-up still reports that week."""
    local = now.astimezone(MANILA)
    days_back = (local.weekday() - WEEKLY_DAY) % 7
    end = dt.datetime.combine(local.date() - dt.timedelta(days=days_back), WEEKLY_TIME, MANILA)
    if end > local:
        end -= dt.timedelta(days=7)
    return end - dt.timedelta(days=7), end


def daily_id(now: dt.datetime) -> str:
    return f"learning-daily:{now.astimezone(MANILA).date().isoformat()}"


def weekly_id(end: dt.datetime) -> str:
    return f"learning-weekly:{end.astimezone(MANILA).date().isoformat()}"


def _accepted(db: Path, start: dt.datetime, end: dt.datetime) -> list[dict]:
    rows = _read(
        db,
        """SELECT p.preference_id, p.kind, p.scope_type, p.scope_value, p.value, p.revision,
                  p.status, e.evidence, e.source_kind
           FROM semantic_preferences p
           JOIN semantic_preference_events e ON e.event_id = p.evidence_event_id
           WHERE p.updated_at > ? AND p.updated_at <= ? ORDER BY p.updated_at""",
        (_iso(start), _iso(end)),
    )
    return [dict(row) for row in rows]


def _questions(db: Path) -> list[dict]:
    return [
        dict(row)
        for row in _read(
            db,
            """SELECT event_id, kind, question, evidence FROM semantic_preference_events
               WHERE status='pending' AND question IS NOT NULL ORDER BY rowid""",
        )
    ]


def daily_data(review: dict, now: dt.datetime, *, db: Path | None = None) -> dict:
    db = Path(db) if db else COHESION_DB
    accepted = _accepted(db, now - dt.timedelta(days=1), now)
    return {
        "id": daily_id(now),
        "date": now.astimezone(MANILA).date().isoformat(),
        "idle": review.get("status") == "idle" and not accepted,
        "model_calls": review.get("calls", 0),
        "accepted": [row for row in accepted if row["status"] == "active" and row["revision"] == 1],
        "updated": [row for row in accepted if row["status"] == "active" and row["revision"] > 1],
        "revoked": [row for row in accepted if row["status"] == "revoked"],
        "rejected": review.get("rejected", 0),
        "deferred": review.get("pending", 0),
        "questions": _questions(db),
        "error": review.get("error"),
    }


def weekly_data(now: dt.datetime, *, db: Path | None = None) -> dict:
    db = Path(db) if db else COHESION_DB
    start, end = week_window(now)
    window = (_iso(start), _iso(end))
    captured = _read(
        db,
        """SELECT status, reason, count(*) AS n FROM semantic_preference_events
           WHERE created_at > ? AND created_at <= ? GROUP BY status, reason""",
        window,
    )
    uses = _read(
        db,
        """SELECT p.kind, p.scope_type, p.scope_value, p.value, count(*) AS n
           FROM semantic_preference_uses u JOIN semantic_preferences p USING(preference_id)
           WHERE u.used_at > ? AND u.used_at <= ?
           GROUP BY u.preference_id ORDER BY n DESC""",
        window,
    )
    completions = sync_completed_tickets.DEFAULT_DB
    tickets = _read(
        completions,
        """SELECT repo, kind, number, title, outcome FROM work_items
           WHERE at > ? AND at <= ? AND outcome IN ('completed','merged') ORDER BY at""",
        tuple(value.astimezone(dt.UTC).strftime("%Y-%m-%dT%H:%M:%SZ") for value in (start, end)),
    )
    conflicts = _read(
        completions,
        "SELECT reason, count(*) AS n FROM conflicts WHERE at > ? AND at <= ? GROUP BY reason",
        window,
    )
    persistence = _read(
        owned_persist.DEFAULT_DB,
        """SELECT state, error FROM persistence_receipts
           WHERE updated_at > ? AND updated_at <= ?""",
        window,
    )
    persistence_errors: dict[str, int] = {}
    for row in persistence:
        if row["error"]:
            reason = row["error"].split(":", 1)[0]
            persistence_errors[reason] = persistence_errors.get(reason, 0) + 1
    counts: dict[str, int] = {}
    for row in captured:
        key = row["status"] if row["status"] != "pending" else (
            "awaiting_review" if row["reason"] == "daily_review_required" else "needs_aki"
        )
        counts[key] = counts.get(key, 0) + row["n"]
    return {
        "id": weekly_id(end),
        "start": start.isoformat(),
        "end": end.isoformat(),
        "states": {
            "captured": sum(row["n"] for row in captured),
            "awaiting_review": counts.get("awaiting_review", 0),
            "needs_aki": counts.get("needs_aki", 0),
            "accepted": counts.get("activated", 0),
            "rejected": counts.get("rejected", 0),
            "applied": sum(row["n"] for row in uses),
            "committed": sum(1 for row in persistence if row["state"] in {"committed", "pushed"}),
            "pushed": sum(1 for row in persistence if row["state"] == "pushed"),
        },
        "learned": _accepted(db, start, end),
        "reuse": [dict(row) for row in uses],
        "pain_points": {
            **{f"completion {row['reason']}": row["n"] for row in conflicts},
            **{f"persistence {reason}": n for reason, n in persistence_errors.items()},
        },
        "tickets_closed": [dict(row) for row in tickets if row["kind"] == "issue"],
        "prs_merged": [dict(row) for row in tickets if row["kind"] == "pull"],
        "decisions": _questions(db),
    }


def _vault_state(path: Path) -> dict:
    def git(*args: str) -> subprocess.CompletedProcess:
        return subprocess.run(["git", "-C", str(path), *args], capture_output=True, text=True, check=False)

    if not (path / ".git").exists():
        return {"path": str(path), "available": False}
    dirty = [line for line in git("status", "--porcelain").stdout.splitlines() if line.strip()]
    counts = git("rev-list", "--left-right", "--count", "HEAD...@{u}").stdout.split()
    fetch_head = path / ".git" / "FETCH_HEAD"
    fetched = (
        dt.datetime.fromtimestamp(fetch_head.stat().st_mtime, dt.UTC).isoformat()
        if fetch_head.exists() else None
    )
    return {
        "path": str(path),
        "available": True,
        "dirty_files": len(dirty),
        "ahead": int(counts[0]) if len(counts) == 2 else None,
        "behind": int(counts[1]) if len(counts) == 2 else None,
        # Upstream counts come from the last fetch; no network call is made here.
        "upstream_as_of": fetched,
    }


def health(now: dt.datetime | None = None, *, db: Path | None = None, outbox=None,
           vaults=None) -> dict:
    now = now or dt.datetime.now(dt.UTC)
    vaults = VAULTS if vaults is None else vaults
    db = Path(db) if db else COHESION_DB
    day = now.astimezone(MANILA).date().isoformat()
    calls = _read(db, "SELECT status, count(*) AS n FROM semantic_review_calls WHERE manila_day=? GROUP BY status", (day,))
    review_queue = _read(
        db,
        """SELECT count(*) AS n, min(created_at) AS oldest FROM semantic_preference_events
           WHERE status='pending' AND reason='daily_review_required'""",
    )
    oldest = review_queue[0]["oldest"] if review_queue else None
    persistence = _read(
        owned_persist.DEFAULT_DB, "SELECT state, count(*) AS n FROM persistence_receipts GROUP BY state"
    )
    return {
        "review_queue": {
            "pending": review_queue[0]["n"] if review_queue else 0,
            "oldest_seconds": int((now - dt.datetime.fromisoformat(oldest)).total_seconds()) if oldest else 0,
        },
        "budget": {
            "manila_day": day,
            "used": sum(row["n"] for row in calls),
            "failed": sum(row["n"] for row in calls if row["status"] == "failed"),
            "limit": MAX_CALLS_PER_DAY,
        },
        "classifier": {"engine": "agy", "installed": agy_classify.AGY_BIN.is_file()},
        "persistence": {row["state"]: row["n"] for row in persistence},
        "delivery": (outbox or notify_outbox.Outbox()).health(now),
        "vaults": [_vault_state(Path(path)) for path in vaults],
    }


def send_daily(review: dict, now: dt.datetime | None = None, *, db: Path | None = None, outbox=None) -> dict:
    now = now or dt.datetime.now(dt.UTC)
    data = daily_data(review, now, db=db)
    box = outbox or notify_outbox.Outbox()
    queued = box.enqueue(data["id"], render_daily(data), now=now)
    return {"id": data["id"], "queued": queued, "delivery": box.deliver(now)}


def send_weekly(now: dt.datetime | None = None, *, db: Path | None = None, outbox=None) -> dict:
    now = now or dt.datetime.now(dt.UTC)
    data = weekly_data(now, db=db)
    box = outbox or notify_outbox.Outbox()
    queued = box.enqueue(data["id"], render_weekly(data), now=now)
    return {"id": data["id"], "queued": queued, "delivery": box.deliver(now)}


SEPARATOR = "-" * 33


def _day_label(value: str | dt.date) -> str:
    day = dt.date.fromisoformat(value) if isinstance(value, str) else value
    return f"{day:%b} {day.day}"


def _needs_you(questions: list[dict]) -> list[str]:
    if not questions:
        return []
    lines = ["", "Needs you:"]
    for question in questions[:5]:
        lines.append(f"- {question['question']}")
        lines.append(f'  ("{question["evidence"]}")')
    if len(questions) > 5:
        lines.append(f"- and {len(questions) - 5} more")
    return lines


def render_daily(data: dict) -> str:
    lines = [SEPARATOR, f"Learning receipt, {_day_label(data['date'])}", ""]
    if data["idle"] and not data["questions"] and not data["error"]:
        lines.append("No new learning. No model call.")
    else:
        lines.append(
            f"Accepted {len(data['accepted'])} · Updated {len(data['updated'])} · "
            f"Revoked {len(data['revoked'])}"
        )
        lines.append(f"Rejected {data['rejected']} · Awaiting review {data['deferred']}")
        lines.append(f"Model calls {data['model_calls']} of {MAX_CALLS_PER_DAY}")
        if data["error"]:
            lines.append(f"Failed: {data['error']}")
        lines.extend(_needs_you(data["questions"]))
    lines.extend(["", data["id"]])
    return "\n".join(lines)


def _ticket(row: dict) -> str:
    return f"{row['repo'].split('/')[-1]} {'PR ' if row['kind'] == 'pull' else ''}#{row['number']}"


def render_weekly(data: dict) -> str:
    start = dt.datetime.fromisoformat(data["start"]).astimezone(MANILA).date()
    end = dt.datetime.fromisoformat(data["end"]).astimezone(MANILA).date()
    states = data["states"]
    lines = [
        SEPARATOR,
        f"Learning week, {_day_label(start)} to {_day_label(end)}",
        "",
        f"Captured {states['captured']} · Accepted {states['accepted']} · Applied {states['applied']}",
        f"Rejected {states['rejected']} · Awaiting review {states['awaiting_review']} · "
        f"Needs you {states['needs_aki']}",
        f"Committed {states['committed']} · Pushed {states['pushed']}",
    ]
    if not data["learned"]:
        lines.append("No verified learning this week.")
    for row in data["learned"][:5]:
        scope = row["scope_value"] or row["scope_type"]
        lines.append(f'Learned: {row["kind"]}={row["value"]} ({scope}) from "{row["evidence"]}"')
    for row in data["reuse"][:5]:
        scope = row["scope_value"] or row["scope_type"]
        lines.append(f"Reused: {row['kind']}={row['value']} ({scope}) x{row['n']}")
    if data["pain_points"]:
        points = sorted(data["pain_points"].items(), key=lambda item: -item[1])
        lines.append("Pain points: " + ", ".join(f"{name} x{n}" for name, n in points[:5]))
    closed = ", ".join(_ticket(row) for row in data["tickets_closed"][:8]) or "none"
    merged = ", ".join(_ticket(row) for row in data["prs_merged"][:8]) or "none"
    lines.append(f"Closed: {closed} · Merged: {merged}")
    lines.append("Deployed and live-verified: not tracked")
    lines.extend(_needs_you(data["decisions"]))
    lines.extend(["", data["id"]])
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=["weekly", "health"])
    args = parser.parse_args(argv)
    result = send_weekly() if args.command == "weekly" else health()
    print(json.dumps(result, ensure_ascii=False, sort_keys=True, default=str))
    return 1 if args.command == "weekly" and result["delivery"]["failed"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
