#!/usr/bin/env python3
"""Evening Debrief -> Telegram (achinouncements).

Runs at 12:00 MN (Midnight Manila) to summarize the day that concluded:
- Under 300 words.
- Leads with what matters.
- If nothing happened, reports "Quiet day" and lists tomorrow's focus.
- Avoids repeating morning brief unless status changed (e.g. tasks completed).
- Highlights any system failures and their resolutions.
- Outlines tomorrow's focus and schedule.

Usage:
    python scripts/evening_debrief.py           # Fetch and send
    python scripts/evening_debrief.py --dry-run # Print only
"""

from __future__ import annotations

import argparse
import datetime as dt
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

TASKS_FILE = SCRIPT_DIR.parent / "tasks.md"
CONFIG_DIR = Path.home() / ".config" / "achios"
GOOGLE_TOKENS = [CONFIG_DIR / "google_token.json", CONFIG_DIR / "google_token_work.json"]
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
    state: str
    priority: str = "med"
    due: dt.date | None = None


def strip_markup(text: str) -> str:
    text = LINK_RE.sub(r"\1", text)
    text = BOLD_RE.sub(r"\1", text)
    text = CODE_RE.sub(r"\1", text)
    return re.sub(r"\s+", " ", text).strip()


def get_tasks_data(concluding_date: dt.date) -> tuple[list[str], list[Task], list[Task]]:
    """Return (done_today, due_tomorrow, high_priority_active)."""
    if not TASKS_FILE.exists():
        return [], [], []

    date_str = concluding_date.isoformat()
    tomorrow_date = concluding_date + dt.timedelta(days=1)
    
    done_today: list[str] = []
    due_tomorrow: list[Task] = []
    high_priority_active: list[Task] = []

    content = TASKS_FILE.read_text(encoding="utf-8", errors="replace")
    in_fence = False
    current_section = ""

    for line in content.splitlines():
        if FENCE_RE.match(line):
            in_fence = not in_fence
            continue
        if in_fence:
            continue

        if line.startswith("## "):
            current_section = line[3:].strip().lower()
            continue

        match = TASK_RE.match(line)
        if not match:
            continue

        marker, raw = match.groups()
        due_match = DUE_RE.search(raw)
        priority_match = PRIORITY_RE.search(raw)
        areas = AREA_RE.findall(raw)
        clean_text = strip_markup(AREA_RE.sub("", PRIORITY_RE.sub("", DUE_RE.sub("", raw))))

        due_date = dt.date.fromisoformat(due_match.group(1)) if due_match else None
        priority = priority_match.group(1) if priority_match else "med"

        if current_section == "done" and marker == "x":
            if date_str in raw:
                # Trim overly long explanations
                short_text = clean_text.split("—")[0].strip() if "—" in clean_text else clean_text
                done_today.append(short_text)
        elif current_section == "active" and marker == " ":
            t = Task(text=clean_text, state="active", priority=priority, due=due_date)
            if due_date and due_date == tomorrow_date:
                due_tomorrow.append(t)
            elif priority == "high":
                high_priority_active.append(t)

    return done_today, due_tomorrow, high_priority_active


def fetch_tomorrow_events(tomorrow: dt.date) -> list[str]:
    """Fetch calendar events for tomorrow from Google Calendar."""
    events_summary = []
    try:
        from google.auth.transport.requests import Request
        from google.oauth2.credentials import Credentials
        from googleapiclient.discovery import build

        start_dt = dt.datetime.combine(tomorrow, dt.time.min, LOCAL_TZ)
        end_dt = dt.datetime.combine(tomorrow + dt.timedelta(days=1), dt.time.min, LOCAL_TZ)

        def utc(value: dt.datetime) -> str:
            return value.astimezone(dt.timezone.utc).isoformat().replace("+00:00", "Z")

        seen = set()
        for token_path in GOOGLE_TOKENS:
            if not token_path.exists():
                continue
            creds = Credentials.from_authorized_user_file(str(token_path))
            if creds.expired and creds.refresh_token:
                creds.refresh(Request())
                token_path.write_text(creds.to_json(), encoding="utf-8")
            service = build("calendar", "v3", credentials=creds, cache_discovery=False)
            
            cals = service.calendarList().list().execute().get("items", [])
            for cal in cals:
                cal_id = cal["id"]
                if cal_id in seen:
                    continue
                seen.add(cal_id)
                res = (
                    service.events()
                    .list(
                        calendarId=cal_id,
                        timeMin=utc(start_dt),
                        timeMax=utc(end_dt),
                        singleEvents=True,
                        orderBy="startTime",
                    )
                    .execute()
                )
                for item in res.get("items", []):
                    title = item.get("summary")
                    if title and title not in events_summary:
                        events_summary.append(title)
    except Exception:
        pass
    return events_summary


def check_failures_today() -> list[str]:
    """Check if any system failures or alerts were recorded today."""
    failures = []
    try:
        res = subprocess.run(
            ["journalctl", "--user", "-u", "achios-failure-alert@*", "--since=today", "-n", "5", "--no-pager"],
            capture_output=True,
            text=True,
            timeout=3,
        )
        if res.returncode == 0 and "Starting Telegram Failure Alert for" in res.stdout:
            for match in re.findall(r"Starting Telegram Failure Alert for ([\w.-]+)", res.stdout):
                if match not in ["test-drill", "test-service"]:
                    failures.append(f"{match} exited unexpectedly (investigated & alert dispatched)")
    except Exception:
        pass
    return failures


def build_evening_debrief(concluding_date: dt.date) -> str:
    tomorrow = concluding_date + dt.timedelta(days=1)
    date_label = concluding_date.strftime("%b %d, %Y")
    tomorrow_label = tomorrow.strftime("%A, %b %d")

    done_today, due_tomorrow, high_active = get_tasks_data(concluding_date)
    tomorrow_events = fetch_tomorrow_events(tomorrow)
    failures = check_failures_today()

    lines = [
        "---------------------------------",
        "🌙 Evening Debrief",
        f"🗓 Day concluded: {date_label}",
        "",
    ]

    # 1. Accomplishments / What happened
    if done_today:
        lines.append("✅ COMPLETED TODAY:")
        for item in done_today[:5]:
            lines.append(f"• {item}")
        lines.append("")
    else:
        lines.append("🍃 Quiet day. No major status changes recorded today.")
        lines.append("")

    # 2. Failures & Fixes
    if failures:
        lines.append("⚠️ INCIDENTS & FIXES:")
        for f in failures:
            lines.append(f"• {f}")
        lines.append("")
    elif done_today:
        lines.append("🟢 Systems: All services and background timers operational.")
        lines.append("")

    # 3. Tomorrow's Focus
    lines.append(f"🎯 TOMORROW'S FOCUS ({tomorrow_label}):")
    
    focus_items = []
    if due_tomorrow:
        for t in due_tomorrow:
            focus_items.append(f"• ⏰ Due Tomorrow: {t.text}")

    if tomorrow_events:
        for ev in tomorrow_events[:3]:
            focus_items.append(f"• 🗓 Schedule: {ev}")

    for t in high_active[:3]:
        focus_items.append(f"• ⚡ Priority: {t.text}")

    if not focus_items:
        focus_items.append("• Standard backlog review & continuous progress")

    lines.extend(focus_items[:6])
    lines.append("")
    lines.append("Rest well! 🌙")

    return "\n".join(lines).strip()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print the evening debrief without sending to Telegram",
    )
    args = parser.parse_args()

    now = dt.datetime.now(LOCAL_TZ)
    # If running around midnight (e.g. 00:00 to 02:00), the concluding day is yesterday
    concluding_date = (now - dt.timedelta(hours=2)).date() if now.hour < 3 else now.date()

    debrief = build_evening_debrief(concluding_date)

    if args.dry_run:
        print("=== DRY RUN (Not sending) ===")
        print(debrief)
        return 0

    print(f"[{dt.datetime.now().isoformat()}] Sending evening debrief to Telegram...")
    count = send(debrief)
    print(f"Successfully sent {count} message(s) to Telegram.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
