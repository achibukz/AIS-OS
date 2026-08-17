#!/usr/bin/env python3
"""Focused Daily Tasks Checkpoint -> Telegram (achinouncements).

Filters and prioritizes active tasks strictly by:
1. Deadlines (Due Today, Overdue, Upcoming)
2. Priority (!high > !med > !low) as tie-breaker

Keeps the message clean, scannable, and un-overwhelming (capped at top focus items).
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

PRIORITY_MAP = {"high": 0, "med": 1, "low": 2}


@dataclass
class Task:
    text: str
    state: str
    priority: str = "med"
    due: dt.date | None = None
    area: str = ""

    @property
    def priority_score(self) -> int:
        return PRIORITY_MAP.get(self.priority, 1)


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
                priority=priority_match.group(1) if priority_match else "med",
                due=dt.date.fromisoformat(due_match.group(1)) if due_match else None,
                area=areas[0] if areas else "",
            )
        )
    return tasks


def build_focused_digest(tasks: list[Task]) -> str:
    now = dt.datetime.now(LOCAL_TZ)
    today = now.date()
    date_str = now.strftime("%b %d, %Y (%I:%M %p Manila)")

    if not tasks:
        return (
            "---------------------------------\n"
            "🎯 Daily Tasks Focus\n"
            f"🗓 {date_str}\n\n"
            "✨ All clear! No active tasks pending."
        )

    # Segregate tasks strictly by deadline and priority
    due_today_or_overdue: list[Task] = []
    upcoming_deadlines: list[Task] = []
    high_priority_no_due: list[Task] = []
    other_tasks: list[Task] = []

    for t in tasks:
        if t.due:
            if t.due <= today:
                due_today_or_overdue.append(t)
            elif (t.due - today).days <= 30:  # upcoming within month
                upcoming_deadlines.append(t)
            else:
                other_tasks.append(t)
        elif t.priority == "high":
            high_priority_no_due.append(t)
        else:
            other_tasks.append(t)

    # Sort each bucket: Deadline ascending, then priority
    due_today_or_overdue.sort(key=lambda t: (t.due or dt.date.max, t.priority_score, t.text))
    upcoming_deadlines.sort(key=lambda t: (t.due or dt.date.max, t.priority_score, t.text))
    high_priority_no_due.sort(key=lambda t: (t.priority_score, t.text))

    lines = [
        "---------------------------------",
        "🎯 Daily Tasks Focus",
        f"🗓 {date_str}",
        "",
    ]

    has_entries = False

    # 1. Due Today / Overdue
    if due_today_or_overdue:
        has_entries = True
        lines.append("🔥 DUE TODAY / OVERDUE:")
        for t in due_today_or_overdue:
            tag = "⏰ Due Today" if t.due == today else f"⚠️ Overdue ({t.due.strftime('%b %d')})"
            lines.append(f"• {t.text} ({tag})")
        lines.append("")

    # 2. Upcoming Deadlines (within near term)
    if upcoming_deadlines:
        has_entries = True
        lines.append("📅 UPCOMING DEADLINES:")
        for t in upcoming_deadlines[:4]:  # Top 4 nearest deadlines
            days_left = (t.due - today).days
            days_label = "tomorrow" if days_left == 1 else f"in {days_left}d"
            pri_tag = " [!high]" if t.priority == "high" else ""
            lines.append(f"• {t.text} (@{t.due.strftime('%b %d')} • {days_label}{pri_tag})")
        lines.append("")

    # 3. High Priority Focus
    if high_priority_no_due:
        has_entries = True
        lines.append("⚡ HIGH PRIORITY FOCUS:")
        for t in high_priority_no_due[:5]:  # Top 5 high priority tasks
            lines.append(f"• {t.text}")
        lines.append("")

    # Fallback if no deadlines or high priority exist
    if not has_entries:
        lines.append("📌 TOP ACTIVE TASKS:")
        for t in tasks[:5]:
            lines.append(f"• {t.text}")
        lines.append("")

    # Add quick counter footer
    lines.append(f"💡 Focus items: {len(due_today_or_overdue) + min(len(upcoming_deadlines), 4) + min(len(high_priority_no_due), 5)} of {len(tasks)} total active")

    return "\n".join(lines).strip()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print the focused tasks digest without sending to Telegram",
    )
    args = parser.parse_args()

    if not TASKS_FILE.exists():
        print(f"Error: {TASKS_FILE} does not exist.", file=sys.stderr)
        return 1

    content = TASKS_FILE.read_text(encoding="utf-8", errors="replace")
    tasks = parse_active_tasks(content)
    digest = build_focused_digest(tasks)

    if args.dry_run:
        print("=== DRY RUN (Not sending) ===")
        print(digest)
        return 0

    print(f"[{dt.datetime.now().isoformat()}] Sending focused tasks checkpoint to Telegram...")
    count = send(digest)
    print(f"Successfully sent {count} message(s) to Telegram.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
