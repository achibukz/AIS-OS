#!/usr/bin/env python3
"""Durable Telegram outbox with stable message IDs.

A report is enqueued once under a stable ID, so a rerun or restart catch-up
cannot queue the same report twice. Delivery retries transient failures with a
bounded backoff and stops for good on a permanent one. A send that dies without
an answer is retried, which can duplicate a message; the footer carries the ID
so a duplicate is recognizable. A sent message is never sent again.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import sqlite3
import sys
from contextlib import contextmanager
from pathlib import Path
from typing import Callable

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

DEFAULT_DB = Path.home() / ".local" / "state" / "achios" / "outbox.sqlite3"
MAX_ATTEMPTS = 8
BACKOFF = dt.timedelta(minutes=5)
MAX_BACKOFF = dt.timedelta(hours=6)


def _now() -> dt.datetime:
    return dt.datetime.now(dt.UTC)


def classify(error: str) -> str:
    """telegram_notify raises SystemExit text; a 4xx rejection or missing config is permanent."""
    if error.startswith("Telegram rejected") or error.startswith("Missing TELEGRAM"):
        return "permanent"
    return "retryable"


class Outbox:
    def __init__(self, path: Path | None = None, sender: Callable[..., int] | None = None):
        self.path = Path(path) if path else DEFAULT_DB
        self.path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        self._sender = sender
        with self._connect() as connection:
            connection.execute(
                """CREATE TABLE IF NOT EXISTS messages (
                       message_id TEXT PRIMARY KEY,
                       body TEXT NOT NULL,
                       html INTEGER NOT NULL,
                       thread_id INTEGER,
                       state TEXT NOT NULL,
                       attempts INTEGER NOT NULL DEFAULT 0,
                       created_at TEXT NOT NULL,
                       next_attempt_at TEXT NOT NULL,
                       sent_at TEXT,
                       last_error TEXT
                   )"""
            )

    @contextmanager
    def _connect(self):
        connection = sqlite3.connect(self.path, timeout=10)
        connection.row_factory = sqlite3.Row
        try:
            with connection:
                yield connection
        finally:
            connection.close()

    @property
    def sender(self) -> Callable[..., int]:
        if self._sender is None:
            from telegram_notify import send

            self._sender = send
        return self._sender

    def enqueue(
        self, message_id: str, body: str, *, html: bool = False, thread_id: int | None = None,
        now: dt.datetime | None = None,
    ) -> bool:
        """Queue a message. False when this ID was already queued or sent."""
        stamp = (now or _now()).isoformat()
        with self._connect() as connection:
            cursor = connection.execute(
                """INSERT OR IGNORE INTO messages
                   (message_id, body, html, thread_id, state, created_at, next_attempt_at)
                   VALUES (?,?,?,?, 'pending', ?, ?)""",
                (message_id, body, int(html), thread_id, stamp, stamp),
            )
        return cursor.rowcount == 1

    def deliver(self, now: dt.datetime | None = None) -> dict:
        now = now or _now()
        with self._connect() as connection:
            # A row left in 'sending' died mid-send. Its outcome is unknown, so retry it.
            connection.execute("UPDATE messages SET state='pending' WHERE state='sending'")
            due = connection.execute(
                """SELECT * FROM messages WHERE state='pending' AND next_attempt_at<=?
                   ORDER BY created_at""",
                (now.isoformat(),),
            ).fetchall()
        report = {"sent": [], "retrying": [], "failed": []}
        for row in due:
            with self._connect() as connection:
                connection.execute(
                    "UPDATE messages SET state='sending', attempts=attempts+1 WHERE message_id=?",
                    (row["message_id"],),
                )
            try:
                self.sender(row["body"], html=bool(row["html"]), thread_id=row["thread_id"])
            except (SystemExit, Exception) as exc:  # telegram_notify signals failure with SystemExit
                error = str(exc)
                attempts = row["attempts"] + 1
                permanent = classify(error) == "permanent" or attempts >= MAX_ATTEMPTS
                delay = min(BACKOFF * (2 ** (attempts - 1)), MAX_BACKOFF)
                with self._connect() as connection:
                    connection.execute(
                        """UPDATE messages SET state=?, last_error=?, next_attempt_at=?
                           WHERE message_id=?""",
                        ("failed" if permanent else "pending", error,
                         (now + delay).isoformat(), row["message_id"]),
                    )
                report["failed" if permanent else "retrying"].append(row["message_id"])
                continue
            with self._connect() as connection:
                connection.execute(
                    "UPDATE messages SET state='sent', sent_at=?, last_error=NULL WHERE message_id=?",
                    (now.isoformat(), row["message_id"]),
                )
            report["sent"].append(row["message_id"])
        return report

    def health(self, now: dt.datetime | None = None) -> dict:
        now = now or _now()
        with self._connect() as connection:
            counts = dict(
                connection.execute("SELECT state, count(*) FROM messages GROUP BY state").fetchall()
            )
            oldest = connection.execute(
                "SELECT min(created_at) FROM messages WHERE state IN ('pending','sending')"
            ).fetchone()[0]
            failures = [
                {"message_id": row["message_id"], "error": row["last_error"]}
                for row in connection.execute(
                    "SELECT message_id, last_error FROM messages WHERE state='failed' ORDER BY created_at DESC LIMIT 5"
                )
            ]
        age = (now - dt.datetime.fromisoformat(oldest)).total_seconds() if oldest else 0
        return {"counts": counts, "oldest_pending_seconds": int(age), "recent_failures": failures}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=["deliver", "health"])
    args = parser.parse_args(argv)
    outbox = Outbox()
    result = outbox.deliver() if args.command == "deliver" else outbox.health()
    print(json.dumps(result, sort_keys=True))
    return 1 if args.command == "deliver" and result["failed"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
