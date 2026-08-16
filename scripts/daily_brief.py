#!/usr/bin/env python3
"""Daily 8am brief: schedule, active tasks, open questions.

Python gathers and structures the data. Sonnet rewrites it to read like a person
wrote it. If that step fails the structured version sends unchanged.

    daily_brief.py --dry-run     print the message instead of sending
    daily_brief.py --raw         skip the Sonnet pass
    daily_brief.py --days 7      calendar lookahead after today
"""

from __future__ import annotations

import argparse
import colorsys
import datetime as dt
import os
import re
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path
from zoneinfo import ZoneInfo

sys.path.insert(0, str(Path(__file__).resolve().parent))
from telegram_notify import find_chat_ids, send  # noqa: E402

CONFIG_DIR = Path.home() / ".config" / "achios"
GOOGLE_TOKENS = [CONFIG_DIR / "google_token.json", CONFIG_DIR / "google_token_work.json"]

TASKS_FILE = Path(__file__).resolve().parent.parent / "tasks.md"

LOCAL_TZ = ZoneInfo("Asia/Manila")
PRIORITY_ORDER = {"high": 0, "med": 1, "low": 2}
BIRTHDAY_CALENDARS = {"bdayy", "birthdays"}

# Upper hue bound (degrees) → circle emoji. Matching on hue rather than RGB distance,
# because Google's calendar colours are dark and saturated: plain RGB distance sends
# basil green (#0b8043) to black.
HUE_DOTS = [(15, "🔴"), (40, "🟠"), (70, "🟡"), (165, "🟢"), (260, "🔵"), (345, "🟣"), (360, "🔴")]
DEFAULT_DOT = "⚪"

AREA_EMOJI = {
    "school": "🎓",
    "thesis": "📄",
    "career": "💼",
    "work": "💼",
    "achios": "🖥",
    "achimem": "🧠",
    "money": "💰",
    "health": "🏋",
}
DEFAULT_AREA_EMOJI = "📌"

CLAUDE_MODEL = "claude-sonnet-5"
CLAUDE_CWD = Path.home() / ".local" / "share" / "achios" / "llm"
CLAUDE_TIMEOUT = 300

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
    areas: list[str] = field(default_factory=list)
    priority: str = "med"
    due: dt.date | None = None

    @property
    def sort_key(self) -> tuple:
        return (
            self.due or dt.date.max,
            PRIORITY_ORDER.get(self.priority, 1),
            self.text.lower(),
        )


def strip_markup(text: str) -> str:
    text = LINK_RE.sub(r"\1", text)
    text = BOLD_RE.sub(r"\1", text)
    text = CODE_RE.sub(r"\1", text)
    return re.sub(r"\s+", " ", text).strip()


def parse_tasks(body: str) -> list[Task]:
    tasks: list[Task] = []
    in_fence = False
    for line in body.splitlines():
        if FENCE_RE.match(line):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        match = TASK_RE.match(line)
        if not match:
            continue
        marker, raw = match.groups()
        due_match = DUE_RE.search(raw)
        priority_match = PRIORITY_RE.search(raw)
        areas = AREA_RE.findall(raw)
        text = AREA_RE.sub("", PRIORITY_RE.sub("", DUE_RE.sub("", raw)))
        tasks.append(
            Task(
                text=strip_markup(text),
                state={" ": "active", "x": "done", "~": "blocked"}[marker],
                areas=areas,
                priority=priority_match.group(1) if priority_match else "med",
                due=dt.date.fromisoformat(due_match.group(1)) if due_match else None,
            )
        )
    return tasks


def read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ""


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
        creds = Credentials.from_authorized_user_file(str(token_path))
        if creds.expired and creds.refresh_token:
            creds.refresh(Request())
            token_path.write_text(creds.to_json(), encoding="utf-8")
        service = build("calendar", "v3", credentials=creds, cache_discovery=False)

        calendars, page = [], None
        while True:
            response = service.calendarList().list(pageToken=page).execute()
            calendars.extend(response.get("items", []))
            page = response.get("nextPageToken")
            if not page:
                break

        for calendar in calendars:
            calendar_id = calendar["id"]
            if calendar_id in seen_calendars:
                continue
            seen_calendars.add(calendar_id)
            try:
                response = (
                    service.events()
                    .list(
                        calendarId=calendar_id,
                        timeMin=utc(start),
                        timeMax=utc(end),
                        singleEvents=True,
                        orderBy="startTime",
                        maxResults=100,
                    )
                    .execute()
                )
            except Exception:
                continue
            for event in response.get("items", []):
                key = (calendar_id, event.get("id", ""))
                if key in seen_events:
                    continue
                seen_events.add(key)
                when, all_day = event_start(event["start"])
                events.append(
                    {
                        "when": when,
                        "all_day": all_day,
                        "calendar": calendar.get("summary", calendar_id),
                        "color": calendar.get("backgroundColor", ""),
                        "summary": event.get("summary", "(no title)"),
                        "location": event.get("location", ""),
                    }
                )

    events.sort(key=lambda item: item["when"])
    return events


def color_dot(hex_color: str) -> str:
    """Closest circle emoji to a calendar's Google colour."""
    raw = (hex_color or "").lstrip("#")
    if len(raw) != 6:
        return DEFAULT_DOT
    try:
        red, green, blue = (int(raw[i : i + 2], 16) / 255 for i in (0, 2, 4))
    except ValueError:
        return DEFAULT_DOT

    hue, saturation, value = colorsys.rgb_to_hsv(red, green, blue)
    if value < 0.2:
        return "⚫"
    if saturation < 0.15:
        return DEFAULT_DOT if value >= 0.5 else "⚫"

    degrees = hue * 360
    dot = next(emoji for bound, emoji in HUE_DOTS if degrees < bound)
    return "🟤" if dot == "🟠" and value < 0.6 else dot


def is_birthday(event: dict) -> bool:
    return event["calendar"].strip().lower() in BIRTHDAY_CALENDARS


def due_note(task: Task, today: dt.date) -> str:
    if task.due and task.due < today:
        return f"⚠️ overdue since {task.due:%b %d}"
    if task.due == today:
        return "🔥 due today"
    if task.due:
        return f"🗓 due {task.due:%b %d}"
    return ""


def schedule_message(events: list[dict], today: dt.date) -> str:
    blocks = [f"📅  SCHEDULE\n{today:%A, %d %B}"]

    today_events = [e for e in events if e["when"].date() == today and not is_birthday(e)]
    lines = ["☀️  TODAY", ""]
    if today_events:
        for event in today_events:
            when = "all day" if event["all_day"] else f"{event['when']:%H:%M}"
            lines.append(f"{color_dot(event['color'])}  {when}   {event['summary']}")
            lines.append(f"      {event['calendar']}")
            if event["location"]:
                lines.append(f"      📍 {event['location']}")
            lines.append("")
    else:
        lines += ["Nothing scheduled. 🎉", ""]
    blocks.append("\n".join(lines).rstrip())

    later = [e for e in events if e["when"].date() > today and not is_birthday(e)]
    if later:
        by_calendar: dict[str, list[dict]] = {}
        for event in later:
            by_calendar.setdefault(event["calendar"], []).append(event)
        week = ["🗓  THE WEEK AHEAD"]
        for calendar, items in by_calendar.items():
            week += ["", f"{color_dot(items[0]['color'])}  {calendar}"]
            for event in items:
                when = f"{event['when']:%a %d}"
                if not event["all_day"]:
                    when += f", {event['when']:%H:%M}"
                week.append(f"      {when}   {event['summary']}")
        blocks.append("\n".join(week))
    else:
        blocks.append("🗓  THE WEEK AHEAD\n\nNothing scheduled. 🎉")

    birthdays = [e for e in events if is_birthday(e)]
    if birthdays:
        cake = ["🎂  BIRTHDAYS", ""]
        cake += [f"      {e['when']:%a %d}   {e['summary']}" for e in birthdays]
        blocks.append("\n".join(cake))

    return "\n\n\n".join(blocks)


def tasks_message(tasks: list[Task], today: dt.date) -> str:
    active = sorted((t for t in tasks if t.state == "active"), key=lambda t: t.sort_key)
    blocked = [t for t in tasks if t.state == "blocked"]
    header = f"✅  TASKS\n{len(active)} active"

    if not active and not blocked:
        return f"{header}\n\n\nNothing on the register. 🎉"

    blocks = [header]
    by_area: dict[str, list[Task]] = {}
    for task in active:
        by_area.setdefault(task.areas[0].lower() if task.areas else "other", []).append(task)

    for area, items in by_area.items():
        emoji = AREA_EMOJI.get(area, DEFAULT_AREA_EMOJI)
        lines = [f"{emoji}  {area.upper()}", ""]
        for number, task in enumerate(items, start=1):
            lines.append(f"{number}.  {task.text}")
            note = due_note(task, today)
            if note:
                lines.append(f"      {note}")
            lines.append("")
        blocks.append("\n".join(lines).rstrip())

    if blocked:
        lines = ["🚧  BLOCKED", ""]
        lines += [f"{n}.  {t.text}" for n, t in enumerate(blocked, start=1)]
        blocks.append("\n".join(lines))

    return "\n\n\n".join(blocks)


POLISH_PROMPT = """Rewrite this Telegram message so it reads like Aki wrote it for himself.

Rules:
- Every item stays. Do not add, invent, drop, merge, or reorder anything.
- Keep the layout exactly: the same section headers, the same emoji, the same blank
  lines, the same indentation, the same numbering. The spacing is the design.
- You may only reword the event and task text itself, to shorten it or make it read
  naturally. Names, times, dates and file paths must survive unchanged.
- Plain text. No markdown, no bold, no bullet characters. Keep the emoji already there
  and do not add new ones mid-line.
- Short sentences. No em dashes. Never use these words: leverage, passionate, synergy,
  driven, dynamic, utilize, impactful, holistic.
- Add one short line under the top header saying what actually matters. One sentence.
- Output the rewritten message and nothing else. No preamble, no commentary.

---
"""


def polish_with_claude(brief: str) -> str | None:
    """Hand the brief to Sonnet for a human pass. None if the step fails."""
    CLAUDE_CWD.mkdir(parents=True, exist_ok=True)
    try:
        result = subprocess.run(
            [
                "claude",
                "-p",
                POLISH_PROMPT + brief,
                "--model",
                CLAUDE_MODEL,
                "--allowed-tools",
                "",
                "--strict-mcp-config",
                "--mcp-config",
                '{"mcpServers":{}}',
            ],
            capture_output=True,
            text=True,
            timeout=CLAUDE_TIMEOUT,
            cwd=CLAUDE_CWD,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        print(f"polish skipped: {exc}", file=sys.stderr)
        return None
    if result.returncode != 0:
        print(f"polish skipped: claude exited {result.returncode}: {result.stderr[:400]}", file=sys.stderr)
        return None
    text = result.stdout.strip()
    return text or None


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dry-run", action="store_true", help="print instead of sending")
    parser.add_argument("--days", type=int, default=7, help="lookahead after today. Default: 7")
    parser.add_argument("--no-calendar", action="store_true", help="skip Google Calendar")
    parser.add_argument("--raw", action="store_true", help="skip the Sonnet pass")
    parser.add_argument("--find-chat-id", action="store_true", help="list chat ids that messaged the bot")
    args = parser.parse_args()

    if args.find_chat_id:
        return find_chat_ids()

    now = dt.datetime.now(LOCAL_TZ)
    today = now.date()
    start = dt.datetime.combine(today, dt.time.min, LOCAL_TZ)
    end = start + dt.timedelta(days=args.days + 1)

    tasks = parse_tasks(read_text(TASKS_FILE))
    events = [] if args.no_calendar else fetch_events(start, end)

    messages = [schedule_message(events, today), tasks_message(tasks, today)]
    if not args.raw:
        messages = polish_all(messages)

    if args.dry_run:
        print("\n\n════════════════════════\n\n".join(messages))
        return 0

    parts = send(*messages)
    total = sum(len(m) for m in messages)
    print(f"{now:%Y-%m-%d %H:%M} sent ({total} chars, {parts} message(s))")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except SystemExit:
        raise
    except Exception as exc:
        print(f"daily_brief: {exc}", file=sys.stderr)
        raise SystemExit(1)
