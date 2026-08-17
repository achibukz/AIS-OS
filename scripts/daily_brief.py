#!/usr/bin/env python3
"""Daily Morning Briefing -> Telegram (achinouncements).

Clean, deterministic, high-signal briefing scheduled at 08:00 AM Manila:
- Today's Google Calendar events across DLSU, Personal, and Work
- Key deadlines and upcoming schedule for the week
- Top priority focus items from tasks.md

Usage:
    python scripts/daily_brief.py           # Fetch and send
    python scripts/daily_brief.py --dry-run # Print only
"""

from __future__ import annotations

import argparse
import datetime as dt
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from zoneinfo import ZoneInfo

# Add scripts directory to sys.path to import telegram_notify
SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))
from telegram_notify import send

CONFIG_DIR = Path.home() / ".config" / "achios"
GOOGLE_TOKENS = [
    CONFIG_DIR / "google_token_dlsu.json",
    CONFIG_DIR / "google_token.json",
    CONFIG_DIR / "google_token_work.json",
]
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
class Task:
    text: str
    priority: str = "med"
    due: dt.date | None = None


def strip_markup(text: str) -> str:
    text = LINK_RE.sub(r"\1", text)
    text = BOLD_RE.sub(r"\1", text)
    text = CODE_RE.sub(r"\1", text)
    return re.sub(r"\s+", " ", text).strip()


def parse_tasks(body: str) -> list[Task]:
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
        text = AREA_RE.sub("", PRIORITY_RE.sub("", DUE_RE.sub("", raw)))

        tasks.append(
            Task(
                text=strip_markup(text),
                priority=priority_match.group(1) if priority_match else "med",
                due=dt.date.fromisoformat(due_match.group(1)) if due_match else None,
            )
        )
    return tasks


def event_start(raw: dict) -> tuple[dt.datetime, bool]:
    if "dateTime" in raw:
        value = dt.datetime.fromisoformat(raw["dateTime"].replace("Z", "+00:00"))
        return value.astimezone(LOCAL_TZ), False
    day = dt.date.fromisoformat(raw["date"])
    return dt.datetime.combine(day, dt.time.min, LOCAL_TZ), True


def fetch_events(start: dt.datetime, end: dt.datetime) -> list[dict]:
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials
    from googleapiclient.discovery import build

    def utc(value: dt.datetime) -> str:
        return value.astimezone(dt.timezone.utc).isoformat().replace("+00:00", "Z")

    events: list[dict] = []
    seen_calendars: set[str] = set()
    seen_events: set[tuple[str, str]] = set()

    for token_path in GOOGLE_TOKENS:
        if not token_path.exists():
            continue
        try:
            creds = Credentials.from_authorized_user_file(str(token_path))
            if creds.expired and creds.refresh_token:
                creds.refresh(Request())
                token_path.write_text(creds.to_json(), encoding="utf-8")
            service = build("calendar", "v3", credentials=creds, cache_discovery=False)

            calendars = service.calendarList().list().execute().get("items", [])
            for calendar in calendars:
                calendar_id = calendar["id"]
                if calendar_id in seen_calendars:
                    continue
                seen_calendars.add(calendar_id)
                response = (
                    service.events()
                    .list(
                        calendarId=calendar_id,
                        timeMin=utc(start),
                        timeMax=utc(end),
                        singleEvents=True,
                        orderBy="startTime",
                        maxResults=50,
                    )
                    .execute()
                )
                for event in response.get("items", []):
                    key = (calendar_id, event.get("id", ""))
                    if key in seen_events:
                        continue
                    seen_events.add(key)
                    summary = event.get("summary", "(no title)")
                    
                    # Skip Laguna campus events
                    if "laguna" in summary.lower():
                        continue

                    when, all_day = event_start(event["start"])
                    events.append(
                        {
                            "when": when,
                            "all_day": all_day,
                            "calendar": calendar.get("summary", calendar_id),
                            "summary": summary,
                        }
                    )
        except Exception:
            continue

    events.sort(key=lambda item: item["when"])
    return events


def build_daily_brief(today: dt.date, events: list[dict], tasks: list[Task]) -> str:
    date_str = today.strftime("%A, %b %d, %Y")
    
    today_events = [e for e in events if e["when"].date() == today]
    upcoming_events = [e for e in events if e["when"].date() > today]

    lines = [
        "---------------------------------",
        "🌅 Daily Morning Briefing",
        f"🗓 {date_str}",
        "",
    ]

    # 1. Today's Schedule
    lines.append("☀️ TODAY'S SCHEDULE:")
    if today_events:
        for ev in today_events[:5]:
            time_str = "all day" if ev["all_day"] else ev["when"].strftime("%I:%M %p")
            lines.append(f"• {time_str} — {ev['summary']}")
    else:
        lines.append("• Nothing on the schedule today. 🎉")
    lines.append("")

    # 2. Week Ahead (Next 7 days)
    if upcoming_events:
        lines.append("🗓 THE WEEK AHEAD:")
        for ev in upcoming_events[:4]:
            day_str = ev["when"].strftime("%a %b %d")
            time_str = "" if ev["all_day"] else f" ({ev['when'].strftime('%I:%M %p')})"
            lines.append(f"• {day_str}{time_str} — {ev['summary']}")
        lines.append("")

    # 3. Top Active Focus Tasks
    high_priority = [t for t in tasks if t.priority == "high"]
    due_soon = [t for t in tasks if t.due and (t.due - today).days <= 7]

    focus_list = []
    seen_text = set()

    for t in due_soon:
        if t.text not in seen_text:
            tag = "⏰ Due Today" if t.due == today else f"@{t.due.strftime('%b %d')}"
            focus_list.append(f"• {t.text} ({tag})")
            seen_text.add(t.text)

    for t in high_priority:
        if t.text not in seen_text:
            focus_list.append(f"• {t.text} [!high]")
            seen_text.add(t.text)

    if focus_list:
        lines.append("⚡ TODAY'S FOCUS TASKS:")
        lines.extend(focus_list[:5])
        lines.append("")

    lines.append("Make it a great day! 🚀")
    return "\n".join(lines).strip()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dry-run", action="store_true", help="print instead of sending")
    parser.add_argument("--days", type=int, default=7, help="lookahead days for calendar")
    args = parser.parse_args()

    now = dt.datetime.now(LOCAL_TZ)
    today = now.date()
    start = dt.datetime.combine(today, dt.time.min, LOCAL_TZ)
    end = start + dt.timedelta(days=args.days + 1)

    tasks = parse_tasks(TASKS_FILE.read_text(encoding="utf-8", errors="replace")) if TASKS_FILE.exists() else []
    events = fetch_events(start, end)

    brief = build_daily_brief(today, events, tasks)

    if args.dry_run:
        print("=== DRY RUN (Not sending) ===")
        print(brief)
        return 0

    print(f"[{dt.datetime.now().isoformat()}] Sending Daily Morning Briefing to Telegram...")
    count = send(brief)
    print(f"Successfully sent {count} message(s) to Telegram.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
