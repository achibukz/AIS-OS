#!/usr/bin/env python3
"""Read and write Aki's Google Calendars. The only code in AIS-OS that talks to Calendar.

    gcal.py calendars list [--profile P]
    gcal.py calendars check
    gcal.py agenda --from 2026-09-17 --to 2026-09-23
    gcal.py events list --calendar DLSU --from 2026-09-17 --to 2026-09-17
    gcal.py insert --calendar workouts --owner asta --title "Upper A" --start 2026-09-18T07:00 --end 2026-09-18T08:00
    gcal.py insert --calendar Personal --owner asa --title "Pay rent" --date 2026-09-30
    gcal.py update --calendar Personal --event ID --owner asa --date 2026-10-01
    gcal.py delete --calendar Personal --event ID --owner asa

Every command prints one JSON object with a `status` field. Calendars are named through
the private ~/.config/achios/calendars.json; config/calendars.example.json shows its shape.
Credentials come from the gws profiles in ~/.config/gws-<profile>. gws encrypts its tokens,
so every call shells out to the binary.
"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
import re
import subprocess
import sys
from pathlib import Path
from zoneinfo import ZoneInfo

SCRIPT_DIR = Path(__file__).resolve().parent


def user_home() -> Path:
    """The operator's home, even when a bound agent turn runs with a scoped HOME.

    Codex turns point HOME at a private state directory. This checkout lives at
    <home>/Code/GitHub/AIS-OS, so walking out of it recovers the real home.
    """
    github = SCRIPT_DIR.parent.parent
    if github.name == "GitHub" and github.parent.name == "Code":
        return github.parent.parent
    return Path.home()


USER_HOME = user_home()
GWS_BIN = USER_HOME / ".npm-global" / "bin" / "gws"
CONFIG_PATH = USER_HOME / ".config" / "achios" / "calendars.json"
WIKI_PATH = USER_HOME / "Documents" / "Obsidian" / "schoolMem" / "wiki"
PROFILES = ("personal", "work", "main", "dlsu")
OWNER_COHESION = "cohesion"
OWNERS = ("asta", "asa", OWNER_COHESION)
WRITABLE_ROLES = {"owner", "writer"}
MANILA = ZoneInfo("Asia/Manila")
KEYRING_BANNER = "Using keyring backend"
COURSE_PURPOSE = "course"


class GcalError(RuntimeError):
    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code


class GwsError(GcalError):
    def __init__(
        self,
        message: str,
        *,
        profile: str | None = None,
        status: int | None = None,
        reason: str | None = None,
    ):
        auth = status == 401 or reason == "authError" or "error[auth]" in message or "invalid_grant" in message
        super().__init__("auth_failed" if auth else "gws_failed", message)
        self.profile = profile
        self.status = status


def profile_dir(profile: str) -> Path:
    return USER_HOME / ".config" / f"gws-{profile}"


def gws_env(profile: str) -> dict[str, str]:
    return {
        **os.environ,
        "GOOGLE_WORKSPACE_CLI_CONFIG_DIR": str(profile_dir(profile)),
        "GOOGLE_WORKSPACE_CLI_KEYRING_BACKEND": "file",
    }


def parse_json(stdout: str) -> dict:
    """gws prints a keyring banner before the body, so start at the first brace."""
    brace = stdout.find("{")
    if brace < 0:
        raise GwsError("gws returned no JSON")
    value = json.loads(stdout[brace:])
    if not isinstance(value, dict):
        raise GwsError("gws returned an unexpected JSON response")
    return value


def gws(profile: str, *args: str, timeout: int = 30, json_format: bool = True) -> dict:
    """Run one gws subcommand for a profile and return its JSON body.

    `gws auth status` prints JSON already and rejects `--format`, so its caller passes
    json_format=False. A timeout is raised as subprocess.TimeoutExpired, because an insert
    that timed out may still have been accepted and the caller has to look before retrying.
    """
    if not GWS_BIN.is_file():
        raise GcalError("gws_missing", f"gws binary not found at {GWS_BIN}")
    result = subprocess.run(
        [str(GWS_BIN), *args, *(("--format", "json") if json_format else ())],
        env=gws_env(profile),
        capture_output=True,
        text=True,
        timeout=timeout,
    )
    if result.returncode != 0:
        detail = [
            line.strip()
            for line in result.stderr.splitlines()
            if line.strip() and not line.startswith(KEYRING_BANNER)
        ]
        try:
            error = parse_json(result.stdout).get("error", {})
        except (GwsError, ValueError):
            error = {}
        if not isinstance(error, dict):
            error = {}
        raise GwsError(
            " ".join(detail) if detail else f"exit {result.returncode}",
            profile=profile,
            status=error.get("code"),
            reason=error.get("reason"),
        )
    if not result.stdout.strip():
        return {}
    return parse_json(result.stdout)


def load_config(path: Path | None = None) -> list[dict]:
    path = Path(path or CONFIG_PATH)
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        raise GcalError("config_missing", f"calendar config not found at {path}") from None
    except (OSError, ValueError) as exc:
        raise GcalError("config_invalid", f"calendar config at {path} is unreadable: {exc}") from None
    calendars = raw.get("calendars") if isinstance(raw, dict) else None
    if not isinstance(calendars, list):
        raise GcalError("config_invalid", f"{path} needs a calendars list")
    names = set()
    for entry in calendars:
        if not isinstance(entry, dict):
            raise GcalError("config_invalid", "every calendar entry must be an object")
        for field in ("name", "id", "profile"):
            if not isinstance(entry.get(field), str) or not entry[field]:
                raise GcalError("config_invalid", f"calendar entry is missing {field}")
        owners = entry.setdefault("write_owner", [])
        if not isinstance(owners, list) or any(owner not in OWNERS for owner in owners):
            raise GcalError(
                "config_invalid",
                f"{entry['name']}: write_owner must be a list drawn from {', '.join(OWNERS)}",
            )
        if not isinstance(entry.setdefault("schedule", False), bool):
            raise GcalError("config_invalid", f"{entry['name']}: schedule must be true or false")
        entry.setdefault("purpose", "")
        if entry["name"] in names:
            raise GcalError("config_invalid", f"calendar name {entry['name']} is configured twice")
        names.add(entry["name"])
    return calendars


def find_calendar(config: list[dict], name: str) -> dict:
    for entry in config:
        if entry["name"] == name:
            return entry
    raise GcalError("unknown_calendar", f"no configured calendar named {name!r}")


def calendar_by_id(config: list[dict], calendar_id: str) -> dict | None:
    return next((entry for entry in config if entry["id"] == calendar_id), None)


def event_id_for(item_id: str) -> str:
    """Google event IDs allow 0-9 and a-v, so a hex digest is always valid."""
    return "a" + hashlib.sha256(item_id.encode()).hexdigest()[:31]


def default_item_id(owner: str, calendar_id: str, title: str, when: str) -> str:
    digest = hashlib.sha256(f"{owner}\n{calendar_id}\n{title}\n{when}".encode()).hexdigest()
    return f"{owner}_{digest[:24]}"


def to_manila(value: str) -> str:
    """Treat a naive ISO time as Manila and return an offset ISO string."""
    parsed = dt.datetime.fromisoformat(value)
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=MANILA)
    return parsed.astimezone(MANILA).isoformat()


def window(start: dt.date, end: dt.date) -> tuple[str, str]:
    """Inclusive Manila days as the half-open range Google expects."""
    if end < start:
        raise GcalError("invalid_arguments", "--to is before --from")
    time_min = dt.datetime.combine(start, dt.time.min, MANILA)
    time_max = dt.datetime.combine(end + dt.timedelta(days=1), dt.time.min, MANILA)
    return time_min.isoformat(), time_max.isoformat()


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


def timed_body(title: str, start: str, end: str) -> dict:
    start_at, end_at = to_manila(start), to_manila(end)
    if dt.datetime.fromisoformat(end_at) <= dt.datetime.fromisoformat(start_at):
        raise GcalError("invalid_arguments", "--end must be after --start")
    return {
        "summary": title,
        "start": {"dateTime": start_at, "timeZone": "Asia/Manila"},
        "end": {"dateTime": end_at, "timeZone": "Asia/Manila"},
    }


def private_properties(event: dict) -> dict:
    return (event.get("extendedProperties") or {}).get("private") or {}


def normalize_event(entry: dict, raw: dict) -> dict:
    start, end = raw.get("start") or {}, raw.get("end") or {}
    all_day = bool(start.get("date")) and not start.get("dateTime")
    private = private_properties(raw)
    return {
        "calendar": entry["name"],
        "calendar_id": entry["id"],
        "profile": entry["profile"],
        "event_id": raw.get("id"),
        "title": raw.get("summary", ""),
        "start": start.get("date") if all_day else to_manila(start["dateTime"]),
        "end": end.get("date") if all_day else to_manila(end["dateTime"]),
        "all_day": all_day,
        "recurring_event_id": raw.get("recurringEventId"),
        "owner": private.get("achios_owner"),
        "item_id": private.get("achios_item_id"),
    }


def dedupe_events(events: list[dict]) -> list[dict]:
    """One calendar shared into two accounts yields each event twice. Drop by ID, then by title plus start."""
    seen_ids: set[str] = set()
    seen_slots: set[tuple[str, str]] = set()
    unique = []
    for event in events:
        slot = (event["title"].strip().casefold(), event["start"])
        if event["event_id"] in seen_ids or slot in seen_slots:
            continue
        seen_ids.add(event["event_id"])
        seen_slots.add(slot)
        unique.append(event)
    return unique


def calendar_list(profile: str) -> list[dict]:
    items: list[dict] = []
    page_token = None
    while True:
        params: dict = {"maxResults": 250}
        if page_token:
            params["pageToken"] = page_token
        page = gws(profile, "calendar", "calendarList", "list", "--params", json.dumps(params))
        items.extend(page.get("items", []))
        page_token = page.get("nextPageToken")
        if not page_token:
            return items


def fetch_events(profile: str, calendar_id: str, start: dt.date, end: dt.date) -> list[dict]:
    time_min, time_max = window(start, end)
    items: list[dict] = []
    page_token = None
    while True:
        params = {
            "calendarId": calendar_id,
            "timeMin": time_min,
            "timeMax": time_max,
            "singleEvents": True,
            "orderBy": "startTime",
            "timeZone": "Asia/Manila",
            "maxResults": 250,
        }
        if page_token:
            params["pageToken"] = page_token
        page = gws(profile, "calendar", "events", "list", "--params", json.dumps(params))
        items.extend(item for item in page.get("items", []) if item.get("status") != "cancelled")
        page_token = page.get("nextPageToken")
        if not page_token:
            return items


def _failure(profile: str, calendar: str | None, exc: Exception) -> dict:
    if isinstance(exc, subprocess.TimeoutExpired):
        return {"profile": profile, "calendar": calendar, "error": "timeout", "message": "gws timed out"}
    code = getattr(exc, "code", "gws_failed")
    return {"profile": profile, "calendar": calendar, "error": code, "message": str(exc)}


def _status(read: int, errors: list) -> str:
    """`error` only when nothing could be read. An empty day on a readable calendar is not a failure."""
    if not errors:
        return "ok"
    return "partial" if read else "error"


def read_events(entries: list[dict], start: dt.date, end: dt.date) -> dict:
    """Read each calendar ID once, falling back through every profile configured for it.

    A profile that fails auth or times out is skipped for the rest of the run, so it is
    reported once and cannot hide calendars read through the other profiles.
    """
    events: list[dict] = []
    errors: list[dict] = []
    read = 0
    dead_profiles: set[str] = set()
    by_id: dict[str, list[dict]] = {}
    for entry in entries:
        by_id.setdefault(entry["id"], []).append(entry)
    for candidates in by_id.values():
        for entry in candidates:
            if entry["profile"] in dead_profiles:
                continue
            try:
                raw = fetch_events(entry["profile"], entry["id"], start, end)
            except (GwsError, subprocess.TimeoutExpired) as exc:
                failure = _failure(entry["profile"], entry["name"], exc)
                errors.append(failure)
                if failure["error"] in {"auth_failed", "timeout"}:
                    dead_profiles.add(entry["profile"])
                continue
            events.extend(normalize_event(entry, item) for item in raw)
            read += 1
            break
    events = dedupe_events(events)
    events.sort(key=lambda event: (event["start"], event["all_day"], event["title"]))
    return {"status": _status(read, errors), "events": events, "errors": errors}


def agenda(config: list[dict], start: dt.date, end: dt.date) -> dict:
    return read_events([entry for entry in config if entry["schedule"]], start, end)


def list_calendars(profiles: tuple[str, ...] | list[str] = PROFILES) -> dict:
    calendars: list[dict] = []
    errors: list[dict] = []
    read = 0
    for profile in profiles:
        if not profile_dir(profile).is_dir():
            errors.append({"profile": profile, "calendar": None, "error": "profile_missing",
                           "message": f"gws profile missing: {profile_dir(profile)}"})
            continue
        try:
            items = calendar_list(profile)
        except (GwsError, subprocess.TimeoutExpired) as exc:
            errors.append(_failure(profile, None, exc))
            continue
        read += 1
        calendars.extend(
            {
                "id": item.get("id"),
                "name": item.get("summaryOverride") or item.get("summary"),
                "access_role": item.get("accessRole"),
                "profile": profile,
            }
            for item in items
        )
    return {"status": _status(read, errors), "calendars": calendars, "errors": errors}


def _course_key(code: str) -> str:
    return re.sub(r"[^A-Z0-9]", "", code.upper())


def read_current_courses(wiki: Path = WIKI_PATH) -> list[str]:
    sys.path.insert(0, str(SCRIPT_DIR))
    import canvas_subjects

    return [subject["code"] for subject in canvas_subjects.read_subjects(wiki)["subjects"]]


def check_calendars(config: list[dict], live: dict, courses: list[str] | None) -> dict:
    """Compare config with live calendar lists and current courses. Never writes."""
    failed_profiles = {error["profile"] for error in live["errors"]}
    seen = {(item["profile"], item["id"]) for item in live["calendars"]}
    configured_ids = {entry["id"] for entry in config}
    missing = [
        {"name": entry["name"], "profile": entry["profile"]}
        for entry in config
        if entry["profile"] not in failed_profiles and (entry["profile"], entry["id"]) not in seen
    ]
    unconfigured: dict[str, dict] = {}
    for item in live["calendars"]:
        if item["access_role"] in WRITABLE_ROLES and item["id"] not in configured_ids:
            unconfigured.setdefault(item["id"], {"name": item["name"], "profiles": []})["profiles"].append(
                item["profile"]
            )
    report = {
        "missing_calendars": missing,
        "unconfigured_writable": list(unconfigured.values()),
        "courses_without_calendar": None,
        "course_calendars_not_current": None,
        "errors": list(live["errors"]),
    }
    if courses is None:
        report["errors"].append({"profile": None, "calendar": None, "error": "courses_unavailable",
                                 "message": "current Canvas courses could not be read"})
    else:
        current = {_course_key(code): code for code in courses}
        course_entries = {_course_key(entry["name"]): entry["name"]
                          for entry in config if entry["purpose"] == COURSE_PURPOSE}
        report["courses_without_calendar"] = [code for key, code in current.items() if key not in course_entries]
        report["course_calendars_not_current"] = [
            name for key, name in course_entries.items() if key not in current
        ]
    drift = any(
        report[key]
        for key in ("missing_calendars", "unconfigured_writable", "courses_without_calendar",
                    "course_calendars_not_current")
    )
    if report["errors"]:
        report["status"] = "error" if not live["calendars"] else "partial"
    else:
        report["status"] = "drift" if drift else "ok"
    report["drift"] = drift
    return report


def drift_lines(report: dict) -> list[str]:
    lines = [f"configured calendar not found: {item['name']} ({item['profile']})"
             for item in report["missing_calendars"]]
    lines += [f"writable calendar not in config: {item['name']} ({', '.join(item['profiles'])})"
              for item in report["unconfigured_writable"]]
    lines += [f"current course has no calendar: {code}" for code in report["courses_without_calendar"] or []]
    lines += [f"course calendar is not a current course: {name}"
              for name in report["course_calendars_not_current"] or []]
    lines += [f"check failed: {error['message']}" for error in report["errors"]]
    return lines


def failure_labels(errors: list[dict]) -> list[str]:
    """One `profile (message)` label per distinct failure, for the brief warnings."""
    labels: list[str] = []
    for error in errors:
        label = f"{error['profile']} ({error['message']})"
        if label not in labels:
            labels.append(label)
    return labels


def get_event(profile: str, calendar_id: str, event_id: str) -> dict | None:
    try:
        return gws(
            profile, "calendar", "events", "get",
            "--params", json.dumps({"calendarId": calendar_id, "eventId": event_id}),
        )
    except GwsError as exc:
        if exc.status in (404, 410):
            return None
        raise


def insert_event(profile: str, calendar_id: str, body: dict) -> dict:
    return gws(
        profile, "calendar", "events", "insert",
        "--params", json.dumps({"calendarId": calendar_id}),
        "--json", json.dumps(body),
    )


def patch_event(profile: str, calendar_id: str, event_id: str, body: dict) -> dict:
    return gws(
        profile, "calendar", "events", "patch",
        "--params", json.dumps({"calendarId": calendar_id, "eventId": event_id}),
        "--json", json.dumps(body),
    )


def replace_event(profile: str, calendar_id: str, event_id: str, event: dict) -> dict:
    return gws(
        profile, "calendar", "events", "update",
        "--params", json.dumps({"calendarId": calendar_id, "eventId": event_id}),
        "--json", json.dumps(event),
    )


def delete_event(profile: str, calendar_id: str, event_id: str) -> None:
    gws(
        profile, "calendar", "events", "delete",
        "--params", json.dumps({"calendarId": calendar_id, "eventId": event_id}),
    )


def _refused(reason: str, message: str) -> dict:
    return {"status": "refused", "reason": reason, "message": message}


def write_guard(entry: dict, owner: str) -> dict | None:
    """Refuse a write to a calendar the owner does not hold or cannot write live."""
    if not entry["write_owner"]:
        return _refused("read_only", f"{entry['name']} is read-only for agents")
    if owner not in entry["write_owner"]:
        return _refused("calendar_owner", f"{entry['name']} is not written by {owner}")
    role = gws(
        entry["profile"], "calendar", "calendarList", "get",
        "--params", json.dumps({"calendarId": entry["id"]}),
    ).get("accessRole")
    if role not in WRITABLE_ROLES:
        return _refused("read_only", f"{entry['name']} is {role or 'unknown'} for {entry['profile']}")
    return None


def event_guard(event: dict | None, owner: str) -> dict | None:
    if event is None or event.get("status") == "cancelled":
        return {"status": "error", "error": "not_found", "message": "event does not exist"}
    tagged = private_properties(event).get("achios_owner")
    if tagged is None:
        return _refused("untagged", "event was not created by an achiOS agent")
    if tagged != owner:
        return _refused("event_owner", f"event belongs to {tagged}")
    return None


def insert(
    config: list[dict],
    *,
    calendar: str,
    owner: str,
    title: str,
    start: str | None = None,
    end: str | None = None,
    date: str | None = None,
    item_id: str | None = None,
) -> dict:
    entry = find_calendar(config, calendar)
    refusal = write_guard(entry, owner)
    if refusal:
        return refusal
    if date:
        body = all_day_body(title, dt.date.fromisoformat(date))
        when = date
    else:
        body = timed_body(title, start, end)
        when = body["start"]["dateTime"]
    item_id = item_id or default_item_id(owner, entry["id"], title, when)
    event_id = event_id_for(item_id)
    body["id"] = event_id
    body["extendedProperties"] = {"private": {"achios_owner": owner, "achios_item_id": item_id}}

    existing = get_event(entry["profile"], entry["id"], event_id)
    if existing is not None:
        private = private_properties(existing)
        if private.get("achios_item_id") != item_id or private.get("achios_owner") != owner:
            return _refused("event_owner", f"event {event_id} belongs to another item")
        if existing.get("status") != "cancelled":
            return {"status": "exists", "event": normalize_event(entry, existing)}
        # Google keeps a deleted event's ID forever, so asking for the same item again restores it.
        restore = {key: value for key, value in body.items() if key != "id"}
        event = patch_event(entry["profile"], entry["id"], event_id, {**restore, "status": "confirmed"})
        return {"status": "ok", "restored": True, "event": normalize_event(entry, event)}
    try:
        event = insert_event(entry["profile"], entry["id"], body)
    except subprocess.TimeoutExpired:
        event = get_event(entry["profile"], entry["id"], event_id)
        if event is None:
            raise
    except GwsError as exc:
        if exc.status != 409:
            raise
        event = get_event(entry["profile"], entry["id"], event_id)
        if event is None:
            raise
        return {"status": "exists", "event": normalize_event(entry, event)}
    return {"status": "ok", "event": normalize_event(entry, event)}


def update(
    config: list[dict],
    *,
    calendar: str,
    event_id: str,
    owner: str,
    title: str | None = None,
    start: str | None = None,
    end: str | None = None,
    date: str | None = None,
) -> dict:
    entry = find_calendar(config, calendar)
    if not (title or start or end or date):
        raise GcalError("invalid_arguments", "nothing to update")
    if (start or end) and not (start and end):
        raise GcalError("invalid_arguments", "--start and --end go together")
    refusal = write_guard(entry, owner)
    if refusal:
        return refusal
    event = get_event(entry["profile"], entry["id"], event_id)
    refusal = event_guard(event, owner)
    if refusal:
        return refusal
    # gws rejects null fields, so a patch cannot switch between timed and all day.
    # Replacing the whole event can, and it keeps every field this call does not change.
    if date:
        times = all_day_body("", dt.date.fromisoformat(date))
        event["start"], event["end"] = times["start"], times["end"]
    elif start:
        times = timed_body("", start, end)
        event["start"], event["end"] = times["start"], times["end"]
    if title:
        event["summary"] = title
    event = replace_event(entry["profile"], entry["id"], event_id, event)
    return {"status": "ok", "event": normalize_event(entry, event)}


def delete(config: list[dict], *, calendar: str, event_id: str, owner: str) -> dict:
    entry = find_calendar(config, calendar)
    refusal = write_guard(entry, owner) or event_guard(get_event(entry["profile"], entry["id"], event_id), owner)
    if refusal:
        return refusal
    delete_event(entry["profile"], entry["id"], event_id)
    return {"status": "ok", "deleted": event_id, "calendar": calendar}


def _date(value: str) -> dt.date:
    try:
        return dt.date.fromisoformat(value)
    except ValueError:
        raise argparse.ArgumentTypeError(f"{value!r} is not YYYY-MM-DD") from None


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--config", type=Path, default=None, help="calendar config path")
    commands = parser.add_subparsers(dest="command", required=True)

    calendars = commands.add_parser("calendars").add_subparsers(dest="calendars_command", required=True)
    listing = calendars.add_parser("list")
    listing.add_argument("--profile", choices=PROFILES)
    check = calendars.add_parser("check")
    check.add_argument("--wiki", type=Path, default=WIKI_PATH)

    agenda_parser = commands.add_parser("agenda")
    agenda_parser.add_argument("--from", dest="start", type=_date, required=True)
    agenda_parser.add_argument("--to", dest="end", type=_date, required=True)

    events = commands.add_parser("events").add_subparsers(dest="events_command", required=True)
    events_list = events.add_parser("list")
    events_list.add_argument("--calendar", required=True)
    events_list.add_argument("--from", dest="start", type=_date, required=True)
    events_list.add_argument("--to", dest="end", type=_date, required=True)

    insert_parser = commands.add_parser("insert")
    insert_parser.add_argument("--calendar", required=True)
    insert_parser.add_argument("--owner", choices=OWNERS, required=True)
    insert_parser.add_argument("--title", required=True)
    insert_parser.add_argument("--start")
    insert_parser.add_argument("--end")
    insert_parser.add_argument("--date", type=_date)
    insert_parser.add_argument("--item-id")

    for name in ("update", "delete"):
        write = commands.add_parser(name)
        write.add_argument("--calendar", required=True)
        write.add_argument("--event", required=True)
        write.add_argument("--owner", choices=OWNERS, required=True)
        if name == "update":
            write.add_argument("--title")
            write.add_argument("--start")
            write.add_argument("--end")
            write.add_argument("--date", type=_date)
    return parser


def run(args: argparse.Namespace) -> dict:
    if args.command == "calendars" and args.calendars_command == "list":
        return list_calendars([args.profile] if args.profile else PROFILES)
    config = load_config(args.config)
    if args.command == "calendars":
        live = list_calendars(sorted({*PROFILES, *(entry["profile"] for entry in config)}))
        try:
            courses = read_current_courses(args.wiki)
        except (OSError, UnicodeError, ValueError):
            courses = None
        return check_calendars(config, live, courses)
    if args.command == "agenda":
        return agenda(config, args.start, args.end)
    if args.command == "events":
        return read_events([find_calendar(config, args.calendar)], args.start, args.end)
    if args.command == "insert":
        timed = args.start is not None or args.end is not None
        if bool(args.date) == timed or (timed and not (args.start and args.end)):
            raise GcalError("invalid_arguments", "give --date, or both --start and --end")
        return insert(
            config, calendar=args.calendar, owner=args.owner, title=args.title, start=args.start,
            end=args.end, date=args.date.isoformat() if args.date else None, item_id=args.item_id,
        )
    if args.command == "update":
        return update(
            config, calendar=args.calendar, event_id=args.event, owner=args.owner, title=args.title,
            start=args.start, end=args.end, date=args.date.isoformat() if args.date else None,
        )
    return delete(config, calendar=args.calendar, event_id=args.event, owner=args.owner)


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        result = run(args)
    except GcalError as exc:
        result = {"status": "error", "error": exc.code, "message": str(exc)}
        if isinstance(exc, GwsError) and exc.profile:
            result["profile"] = exc.profile
    except subprocess.TimeoutExpired:
        result = {"status": "error", "error": "timeout", "message": "gws timed out"}
    except ValueError as exc:
        result = {"status": "error", "error": "invalid_arguments", "message": str(exc)}
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0 if result["status"] in {"ok", "exists", "partial", "drift"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
