#!/usr/bin/env python3
"""Add an all-day event to one of Aki's Google Calendars.

Used when a task in tasks.md carries a date, so the deadline exists in the calendar
too and not only in the register.

    gcal_add.py "Maybe buy Codex" 2026-08-29 --calendar Personal
    gcal_add.py --list

Re-running with the same title and date is a no-op, so it is safe to retry.

Credentials come from the gws CLI profiles in ~/.config/gws-<profile>. gws stores its
tokens encrypted, so they cannot be loaded by google-auth; every call shells out to the
binary instead.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import subprocess
import sys
from pathlib import Path

GWS_BIN = Path.home() / ".npm-global" / "bin" / "gws"
PROFILES = ["personal", "work", "main", "dlsu"]
WRITABLE = {"owner", "writer"}


class GwsError(RuntimeError):
    pass


def profile_dir(profile: str) -> Path:
    return Path.home() / ".config" / f"gws-{profile}"


def gws(profile: str, *args: str, timeout: int = 30) -> dict:
    """Run a gws subcommand for one profile and return its parsed JSON body."""
    if not GWS_BIN.exists():
        raise GwsError(f"gws binary not found at {GWS_BIN}")
    env = {
        **os.environ,
        "GOOGLE_WORKSPACE_CLI_CONFIG_DIR": str(profile_dir(profile)),
        "GOOGLE_WORKSPACE_CLI_KEYRING_BACKEND": "file",
    }
    res = subprocess.run(
        [str(GWS_BIN), *args, "--format", "json"],
        env=env,
        capture_output=True,
        text=True,
        timeout=timeout,
    )
    if res.returncode != 0:
        detail = (res.stderr or res.stdout).strip().splitlines()
        raise GwsError(f"gws {profile}: {detail[0] if detail else f'exit {res.returncode}'}")
    return parse_json(res.stdout)


def parse_json(stdout: str) -> dict:
    """gws prints a keyring banner before the body, so start at the first brace."""
    brace = stdout.find("{")
    if brace < 0:
        raise GwsError("gws returned no JSON")
    return json.loads(stdout[brace:])


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


def calendars(profile: str) -> list[dict]:
    return gws(profile, "calendar", "calendarList", "list").get("items", [])


def writable_calendars(profile: str) -> list[dict]:
    return [c for c in calendars(profile) if c.get("accessRole") in WRITABLE]


def find_calendar(name: str) -> tuple[str, str] | None:
    """Search every profile in order. Only a calendar Aki can write to is a match."""
    for profile in PROFILES:
        if not profile_dir(profile).exists():
            continue
        try:
            cal = pick_calendar(writable_calendars(profile), name)
        except (GwsError, subprocess.TimeoutExpired) as exc:
            print(f"[WARN] {exc}", file=sys.stderr)
            continue
        if cal:
            return profile, cal["id"]
    return None


def already_there(profile: str, calendar_id: str, title: str, date: dt.date) -> str | None:
    params = {
        "calendarId": calendar_id,
        "timeMin": dt.datetime.combine(date, dt.time.min).isoformat() + "Z",
        "timeMax": dt.datetime.combine(date + dt.timedelta(days=1), dt.time.min).isoformat() + "Z",
        "q": title,
        "singleEvents": True,
    }
    response = gws(profile, "calendar", "events", "list", "--params", json.dumps(params))
    for event in response.get("items", []):
        if event.get("summary") == title:
            return event.get("htmlLink")
    return None


def insert_event(profile: str, calendar_id: str, body: dict) -> str:
    event = gws(
        profile,
        "calendar",
        "events",
        "insert",
        "--params",
        json.dumps({"calendarId": calendar_id}),
        "--json",
        json.dumps(body),
    )
    return event.get("htmlLink", "")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("title", nargs="?", help="event title")
    parser.add_argument("date", nargs="?", help="YYYY-MM-DD")
    parser.add_argument("--calendar", default="Personal", help="calendar name. Default: Personal")
    parser.add_argument("--description", default="", help="event body")
    parser.add_argument("--list", action="store_true", help="list writable calendars and exit")
    args = parser.parse_args()

    if not GWS_BIN.exists():
        print(f"gws binary not found at {GWS_BIN}", file=sys.stderr)
        return 1

    if args.list:
        for profile in PROFILES:
            if not profile_dir(profile).exists():
                continue
            try:
                for cal in writable_calendars(profile):
                    print(f"{profile:9} {cal.get('summary')}")
            except (GwsError, subprocess.TimeoutExpired) as exc:
                print(f"[WARN] {exc}", file=sys.stderr)
        return 0

    if not args.title or not args.date:
        parser.error("title and date are required unless --list")

    date = dt.date.fromisoformat(args.date)
    found = find_calendar(args.calendar)
    if not found:
        print(f"no writable calendar named {args.calendar!r} — try --list", file=sys.stderr)
        return 1
    profile, calendar_id = found

    try:
        existing = already_there(profile, calendar_id, args.title, date)
        if existing:
            print(f"already on {args.calendar} for {date}: {existing}")
            return 0
        link = insert_event(profile, calendar_id, all_day_body(args.title, date, args.description))
    except (GwsError, subprocess.TimeoutExpired) as exc:
        print(f"{exc}", file=sys.stderr)
        return 1

    print(f"added to {args.calendar} on {date}: {link}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
