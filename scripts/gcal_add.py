#!/usr/bin/env python3
"""Add an all-day event to one of Aki's Google Calendars.

Used when a task in tasks.md carries a date, so the deadline exists in the calendar
too and not only in the register.

    gcal_add.py "Maybe buy Codex" 2026-08-29 --calendar Personal
    gcal_add.py --list

Re-running with the same title and date is a no-op, so it is safe to retry.
"""

from __future__ import annotations

import argparse
import datetime as dt
import sys
from pathlib import Path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

CONFIG_DIR = Path.home() / ".config" / "achios"
TOKENS = {"personal": CONFIG_DIR / "google_token.json", "work": CONFIG_DIR / "google_token_work.json"}


def all_day_body(title: str, date: dt.date, description: str = "") -> dict:
    """Google wants an exclusive end date, so a one-day event ends the next morning."""
    body = {
        "summary": title,
        "start": {"date": date.isoformat()},
        "end": {"date": (date + dt.timedelta(days=1)).isoformat()},
        "reminders": {"useDefault": False, "overrides": []},
    }
    if description:
        body["description"] = description
    return body


def pick_calendar(calendars: list[dict], name: str) -> dict | None:
    """Exact summary match first, then a unique case-insensitive prefix."""
    for cal in calendars:
        if cal.get("summary") == name:
            return cal
    lowered = name.lower()
    hits = [c for c in calendars if str(c.get("summary", "")).lower().startswith(lowered)]
    return hits[0] if len(hits) == 1 else None


def _service(account: str):
    creds = Credentials.from_authorized_user_file(str(TOKENS[account]))
    if not creds.valid and creds.refresh_token:
        creds.refresh(Request())
        TOKENS[account].write_text(creds.to_json())
    return build("calendar", "v3", credentials=creds, cache_discovery=False)


def _calendars(svc) -> list[dict]:
    items, page = [], None
    while True:
        response = svc.calendarList().list(pageToken=page).execute()
        items.extend(response.get("items", []))
        page = response.get("nextPageToken")
        if not page:
            return items


def find_calendar(name: str) -> tuple[object, str] | None:
    """Search both accounts. Only a calendar Aki can write to is a match."""
    for account in TOKENS:
        svc = _service(account)
        cal = pick_calendar(_calendars(svc), name)
        if cal and cal.get("accessRole") in {"owner", "writer"}:
            return svc, cal["id"]
    return None


def already_there(svc, calendar_id: str, title: str, date: dt.date) -> str | None:
    response = (
        svc.events()
        .list(
            calendarId=calendar_id,
            timeMin=dt.datetime.combine(date, dt.time.min).isoformat() + "Z",
            timeMax=dt.datetime.combine(date + dt.timedelta(days=1), dt.time.min).isoformat() + "Z",
            q=title,
            singleEvents=True,
        )
        .execute()
    )
    for event in response.get("items", []):
        if event.get("summary") == title:
            return event.get("htmlLink")
    return None


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("title", nargs="?", help="event title")
    parser.add_argument("date", nargs="?", help="YYYY-MM-DD")
    parser.add_argument("--calendar", default="Personal", help="calendar name. Default: Personal")
    parser.add_argument("--description", default="", help="event body")
    parser.add_argument("--list", action="store_true", help="list writable calendars and exit")
    args = parser.parse_args()

    if args.list:
        for account in TOKENS:
            for cal in _calendars(_service(account)):
                if cal.get("accessRole") in {"owner", "writer"}:
                    print(f"{account:9} {cal.get('summary')}")
        return 0

    if not args.title or not args.date:
        parser.error("title and date are required unless --list")

    date = dt.date.fromisoformat(args.date)
    found = find_calendar(args.calendar)
    if not found:
        print(f"no writable calendar named {args.calendar!r} — try --list", file=sys.stderr)
        return 1
    svc, calendar_id = found

    existing = already_there(svc, calendar_id, args.title, date)
    if existing:
        print(f"already on {args.calendar} for {date}: {existing}")
        return 0

    event = svc.events().insert(calendarId=calendar_id, body=all_day_body(args.title, date, args.description)).execute()
    print(f"added to {args.calendar} on {date}: {event.get('htmlLink')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
