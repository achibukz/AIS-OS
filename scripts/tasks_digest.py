#!/usr/bin/env python3
"""Active Tasks Checkpoint -> Telegram (achinouncements).

Parses tasks.md and sends an active tasks briefing grouped by area and priority.
Scheduled at 11am, 3pm, 6pm, 9pm, 11pm Manila time.

Usage:
    python scripts/tasks_digest.py           # Fetch and send
    python scripts/tasks_digest.py --dry-run # Print only
"""

from __future__ import annotations

import argparse
import datetime as dt
import re
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from zoneinfo import ZoneInfo

# Add scripts directory to sys.path to import telegram_notify
SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))
from telegram_notify import send

TASKS_FILE = SCRIPT_DIR.parent / "tasks.md"
LOCAL_TZ = ZoneInfo("Asia/Manila")

TASK_RE = re.compile(r"^\s*-\s*\[([ x~])\]\s+(.*\S)\s*$")
DUE_RE = re.compile(r"@(\d{4}-\d{2}-\d{2})")
PRIORITY_RE = re.compile(r"!(high|med|low)\b")
AREA_RE = re.compile(r"#([A-Za-z0-9][\w-]*)")
FENCE_RE = re.compile(r"^\s*```")
LINK_RE = re.compile(r"\[\[([^\]|]+)(?:\|[^\]]*)?\]\]")
BOLD_RE = re.compile(r"\*\*(.+?)\*\*")
CODE_RE = re.compile(r"`([^`]+)`")

AREA_TITLES = {
    "career": "💼 Career",
    "work": "💼 Work",
    "school": "🎓 School",
    "thesis": "📄 Thesis",
    "finances": "💰 Finances",
    "money": "💰 Finances",
    "achios": "🖥 achiOS & Infra",
    "infra": "🖥 achiOS & Infra",
    "achimem": "🧠 Knowledge & Vaults",
    "general": "📌 General",
}


@dataclass
class Task:
    text: str
    state: str
    areas: list[str] = field(default_factory=list)
    priority: str = "med"
    due: dt.date | None = None


def strip_markup(text: str) -> str:
    text = LINK_RE.sub(r"\1", text)
    text = BOLD_RE.sub(r"\1", text)
    text = CODE_RE.sub(r"\1", text)
    return re.sub(r"\s+", " ", text).strip()


def parse_active_tasks(body: str) -> list[Task]:
    tasks: list[Task] = []
    in_fence = False
    current_section = ""

    for line in body.splitlines():
        if FENCE_RE.match(line):
            in_fence = not in_fence
            continue
        if in_fence:
            continue

        if line.startswith("## "):
            current_section = line[3:].strip().lower()
            continue

        if current_section != "active":
            continue

        match = TASK_RE.match(line)
        if not match:
            continue

        marker, raw = match.groups()
        if marker != " ":  # only active tasks
            continue

        due_match = DUE_RE.search(raw)
        priority_match = PRIORITY_RE.search(raw)
        areas = AREA_RE.findall(raw)
        text = AREA_RE.sub("", PRIORITY_RE.sub("", DUE_RE.sub("", raw)))

        tasks.append(
            Task(
                text=strip_markup(text),
                state="active",
                areas=areas,
                priority=priority_match.group(1) if priority_match else "med",
                due=dt.date.fromisoformat(due_match.group(1)) if due_match else None,
            )
        )
    return tasks


def format_task_line(task: Task) -> str:
    tags = []
    if task.priority == "high":
        tags.append("🔴 !high")
    elif task.priority == "low":
        tags.append("!low")

    if task.due:
        today = dt.datetime.now(LOCAL_TZ).date()
        if task.due == today:
            tags.append("⏰ Due Today")
        elif task.due < today:
            tags.append(f"⚠️ Overdue ({task.due.isoformat()})")
        else:
            tags.append(f"📅 @{task.due.isoformat()}")

    tag_str = f" ({', '.join(tags)})" if tags else ""
    return f"• {task.text}{tag_str}"


def build_tasks_digest(tasks: list[Task]) -> str:
    now = dt.datetime.now(LOCAL_TZ)
    date_str = now.strftime("%b %d, %Y (%I:%M %p Manila)")

    if not tasks:
        return (
            "---------------------------------\n"
            "📋 Active Tasks Checkpoint\n"
            f"🗓 {date_str}\n\n"
            "✨ All clear! No active tasks in the register."
        )

    # Group tasks by primary area
    grouped: dict[str, list[Task]] = defaultdict(list)
    for task in tasks:
        area_key = task.areas[0].lower() if task.areas else "general"
        # Normalize area key
        area_title = AREA_TITLES.get(area_key, f"📌 #{area_key.title()}")
        grouped[area_title].append(task)

    lines = [
        "---------------------------------",
        "📋 Active Tasks Checkpoint",
        f"🗓 {date_str}",
        f"⚡ Total Active: {len(tasks)}",
        "",
    ]

    for title, group in sorted(grouped.items()):
        # Sort by priority (high first), then due date
        sorted_group = sorted(
            group,
            key=lambda t: (
                0 if t.priority == "high" else (2 if t.priority == "low" else 1),
                t.due or dt.date.max,
            ),
        )
        lines.append(f"{title}:")
        for task in sorted_group:
            lines.append(format_task_line(task))
        lines.append("")

    return "\n".join(lines).strip()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print the active tasks digest without sending to Telegram",
    )
    args = parser.parse_args()

    if not TASKS_FILE.exists():
        print(f"Error: {TASKS_FILE} does not exist.", file=sys.stderr)
        return 1

    content = TASKS_FILE.read_text(encoding="utf-8", errors="replace")
    tasks = parse_active_tasks(content)
    digest = build_tasks_digest(tasks)

    if args.dry_run:
        print("=== DRY RUN (Not sending) ===")
        print(digest)
        return 0

    print(f"[{dt.datetime.now().isoformat()}] Sending active tasks checkpoint to Telegram...")
    count = send(digest)
    print(f"Successfully sent {count} message(s) to Telegram.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
