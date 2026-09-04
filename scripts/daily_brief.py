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
import json
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from zoneinfo import ZoneInfo

# Add scripts directory to sys.path to import telegram_notify
SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))
from telegram_notify import send
from google_auth_health import gws_env

GWS_BIN = Path.home() / ".npm-global" / "bin" / "gws"
GWS_PROFILES = ["personal", "dlsu", "main", "work"]

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
    """Fetch and deduplicate Google Calendar events through the gws CLI."""
    events: list[CalendarEvent] = []
    seen_summaries_and_times: set[tuple[str, str]] = set()
    errors: list[str] = []

    if not GWS_BIN.is_file():
        raise RuntimeError(f"gws binary missing: {GWS_BIN}")

    days_ahead = max(1, (end_dt.date() - start_dt.date()).days)
    for prof in GWS_PROFILES:
        cfg_dir = Path.home() / ".config" / f"gws-{prof}"
        if not cfg_dir.exists():
            continue
        try:
            res = subprocess.run(
                [str(GWS_BIN), "calendar", "+agenda", "--days", str(days_ahead), "--format", "json"],
                env=gws_env(prof),
                capture_output=True,
                text=True,
                timeout=10,
            )
            if res.returncode == 0 and res.stdout.strip():
                stdout_clean = res.stdout[res.stdout.find("{"):] if "{" in res.stdout else res.stdout
                data = json.loads(stdout_clean)
                for item in data.get("events", []):
                    raw_summary = item.get("summary", "")
                    if not raw_summary or "laguna" in raw_summary.lower():
                        continue
                    summary = clean_summary(raw_summary)
                    cal_title = item.get("calendar", "")
                    start_str = item.get("start", "")
                    if "T" in start_str:
                        evt_dt = dt.datetime.fromisoformat(start_str).astimezone(LOCAL_TZ)
                        is_all_day = False
                        time_key = evt_dt.strftime("%Y-%m-%d %H:%M")
                    else:
                        d = dt.date.fromisoformat(start_str)
                        evt_dt = dt.datetime.combine(d, dt.time.min, LOCAL_TZ)
                        is_all_day = True
                        time_key = evt_dt.strftime("%Y-%m-%d all-day")

                    key = (summary.lower(), time_key)
                    if key in seen_summaries_and_times:
                        continue
                    seen_summaries_and_times.add(key)

                    events.append(
                        CalendarEvent(
                            summary=summary,
                            start_dt=evt_dt,
                            is_all_day=is_all_day,
                            calendar_name=cal_title,
                        )
                    )
            elif res.returncode != 0:
                err_msg = res.stderr.strip().split("\n")[0] if res.stderr else f"exit code {res.returncode}"
                errors.append(f"{prof} ({err_msg})")
        except Exception as exc:
            errors.append(f"{prof} ({exc})")
            print(f"[WARN] gws calendar fetch failed for {prof}: {exc}", file=sys.stderr)

    events.sort(key=lambda e: (e.start_dt, not e.is_all_day, e.summary))
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
