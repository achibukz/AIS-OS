#!/usr/bin/env python3
"""Render the full task register and optionally send it to Telegram.

Usage:
    python scripts/tasks_digest.py
    python scripts/tasks_digest.py --dry-run
    python scripts/tasks_digest.py --dry-run --area school
"""

from __future__ import annotations

import argparse
import datetime as dt
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

from task_engine import FILTER_AREAS, parse_tasks, render_tasks
from telegram_notify import send

TASKS_FILE = SCRIPT_DIR.parent / "tasks.md"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print the task view without sending it to Telegram",
    )
    parser.add_argument(
        "--area",
        choices=FILTER_AREAS,
        help="Show one primary area or the uncategorized migration view",
    )
    args = parser.parse_args(argv)

    if not TASKS_FILE.exists():
        print(f"Error: {TASKS_FILE} does not exist.", file=sys.stderr)
        return 1

    tasks = parse_tasks(TASKS_FILE.read_text(encoding="utf-8", errors="replace"))
    digest = render_tasks(tasks, area=args.area)

    if args.dry_run:
        print("=== DRY RUN (Not sending) ===")
        print(digest)
        return 0

    print(f"[{dt.datetime.now(dt.UTC).isoformat()}] Sending task register to Telegram...")
    count = send(digest)
    print(f"Successfully sent {count} message(s) to Telegram.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
