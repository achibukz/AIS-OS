#!/usr/bin/env python3
"""Daily 8:00 AM Morning Briefing -> Telegram (achinouncements).

Chronological timeline format (Option 2):
1. ⏰ TODAY'S TIMELINE: Chronological events & classes
2. ⚡ KEY ACTIONS TODAY: Top 3-4 prioritized action items
3. 📅 COMING UP NEXT: Next week highlights & deadlines

Usage:
    python scripts/daily_brief.py           # Fetch and send
    python scripts/daily_brief.py --dry-run # Print only
"""

from __future__ import annotations

import argparse
import datetime as dt
import html
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from zoneinfo import ZoneInfo

# Add scripts directory to sys.path to import telegram_notify
SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))
import gcal
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


@dataclass
class CalendarEvent:
    summary: str
    start_dt: dt.datetime
    is_all_day: bool = False
    calendar_name: str = ""


@dataclass
class Task:
    text: str
    state: str
    priority: str = "med"
    due: dt.date | None = None


def clean_summary(text: str) -> str:
    """Clean redundant Canvas brackets and suffixes from event titles."""
    text = html.unescape(text).strip()
    # Strip raw course code brackets like [MERGED_1253_THS-ST1_S0x] or [THS-ST1_S08]
    text = re.sub(r"\[(MERGED_)?\d+_[\w-]+\]", "", text)
    text = re.sub(r"\[[A-Z0-9_-]+_S\d+\]", "", text)
    # Strip extra whitespace
    text = re.sub(r"\s+", " ", text).strip()
    return text


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
        if marker != " ":
            continue

        due_match = DUE_RE.search(raw)
        priority_match = PRIORITY_RE.search(raw)
        clean_text = strip_markup(AREA_RE.sub("", PRIORITY_RE.sub("", DUE_RE.sub("", raw))))

        tasks.append(
            Task(
                text=clean_text,
                state="active",
                priority=priority_match.group(1) if priority_match else "med",
                due=dt.date.fromisoformat(due_match.group(1)) if due_match else None,
            )
        )
    return tasks


def fetch_calendar_events(start_dt: dt.datetime, end_dt: dt.datetime) -> tuple[list[CalendarEvent], list[str]]:
    """Read the configured schedule calendars through the shared client.

    A missing config or gws binary raises; a failing profile only adds a warning.
    """
    result = gcal.agenda(gcal.load_config(), start_dt.date(), end_dt.date())
    events: list[CalendarEvent] = []
    for item in result["events"]:
        if not item["title"] or "laguna" in item["title"].lower():
            continue
        if item["all_day"]:
            start = dt.datetime.combine(dt.date.fromisoformat(item["start"]), dt.time.min, LOCAL_TZ)
        else:
            start = dt.datetime.fromisoformat(item["start"]).astimezone(LOCAL_TZ)
        events.append(
            CalendarEvent(
                summary=clean_summary(item["title"]),
                start_dt=start,
                is_all_day=item["all_day"],
                calendar_name=item["calendar"],
            )
        )
    events.sort(key=lambda e: (e.start_dt, not e.is_all_day, e.summary))
    errors = gcal.failure_labels(result["errors"])
    for error in errors:
        print(f"[WARN] calendar fetch failed for {error}", file=sys.stderr)
    return events, errors


def build_daily_brief(events: list[CalendarEvent], tasks: list[Task], today: dt.date, errors: list[str] | None = None) -> str:
    date_str = today.strftime("%a, %b %d, %Y")
    errors = errors or []

    today_events = [e for e in events if e.start_dt.date() == today]
    upcoming_events = [e for e in events if e.start_dt.date() > today]

    # Separate timed vs all day for today's timeline
    timed_events = [e for e in today_events if not e.is_all_day]
    all_day_events = [e for e in today_events if e.is_all_day]

    lines = [
        "---------------------------------",
        f"🌅 Daily Briefing • {date_str}",
        "",
    ]

    # 1. ⏰ TODAY'S TIMELINE
    lines.append("⏰ TODAY'S TIMELINE:")
    if not today_events:
        if errors and not events:
            lines.append(f"⚠️ Calendar sync failed: {', '.join(errors)}")
        else:
            lines.append("• No scheduled meetings or classes today.")
    else:
        for e in timed_events:
            time_label = e.start_dt.strftime("%I:%M %p")
            lines.append(f"{time_label}  {e.summary}")
        for e in all_day_events:
            lines.append(f"All Day   {e.summary}")
        if errors:
            lines.append(f"⚠️ Partial sync warning: {', '.join(errors)}")
    lines.append("")

    # 2. ⚡ KEY ACTIONS TODAY
    # Filter top tasks: due today/overdue first, then high priority
    due_today = [t for t in tasks if t.due and t.due <= today]
    high_pri = [t for t in tasks if t.priority == "high" and (not t.due or t.due > today)]

    action_items = due_today + high_pri
    if not action_items:
        action_items = tasks[:3]

    lines.append("⚡ KEY ACTIONS TODAY:")
    for idx, t in enumerate(action_items[:5], start=1):
        # Shorten overly verbose sentences for the clean brief
        short_text = t.text.split("—")[0].strip() if "—" in t.text else t.text
        pri_tag = " [!high]" if t.priority == "high" and not t.due else ""
        due_tag = " (Due Today)" if t.due and t.due == today else ""
        lines.append(f"{idx}. {short_text}{due_tag}{pri_tag}")
    lines.append("")

    # 3. 📅 COMING UP NEXT
    lines.append("📅 COMING UP NEXT:")
    if upcoming_events:
        for e in upcoming_events[:4]:
            days_left = (e.start_dt.date() - today).days
            if days_left == 1:
                day_label = "Tomorrow (Wed)"
            else:
                day_label = e.start_dt.strftime("%a %b %d")
            lines.append(f"• {day_label}: {e.summary}")
    else:
        if errors and not events:
            lines.append("⚠️ Upcoming schedule unavailable due to calendar sync error.")
        else:
            lines.append("• No upcoming deadlines in the next 7 days.")

    return "\n".join(lines).strip()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print the daily briefing without sending to Telegram",
    )
    args = parser.parse_args()

    now = dt.datetime.now(LOCAL_TZ)
    today = now.date()
    start_dt = dt.datetime.combine(today, dt.time.min, LOCAL_TZ)
    end_dt = start_dt + dt.timedelta(days=7)

    events, errors = fetch_calendar_events(start_dt, end_dt)
    tasks = parse_active_tasks(TASKS_FILE.read_text(encoding="utf-8", errors="replace")) if TASKS_FILE.exists() else []

    brief = build_daily_brief(events, tasks, today, errors=errors)

    if args.dry_run:
        print("=== DRY RUN (Option 2 Timeline) ===")
        print(brief)
        return 0

    print(f"[{dt.datetime.now().isoformat()}] Sending Daily Briefing to Telegram...")
    count = send(brief)
    print(f"Successfully sent {count} message(s) to Telegram.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
