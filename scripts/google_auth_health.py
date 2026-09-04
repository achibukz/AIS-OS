#!/usr/bin/env python3
"""Check every achiOS Google Workspace OAuth profile."""

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from zoneinfo import ZoneInfo

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))
from telegram_notify import send

LOCAL_TZ = ZoneInfo("Asia/Manila")
GWS_BIN = Path.home() / ".npm-global" / "bin" / "gws"
GWS_CONFIG_ROOT = Path.home() / ".config"
GWS_PROFILES = ("main", "personal", "work", "dlsu")
COMMAND_TIMEOUT_SECONDS = 30

CALENDAR_SCOPE = "https://www.googleapis.com/auth/calendar"
GMAIL_SCOPES = frozenset(
    {
        "https://mail.google.com/",
        "https://www.googleapis.com/auth/gmail.modify",
        "https://www.googleapis.com/auth/gmail.readonly",
    }
)
DRIVE_SCOPES = frozenset(
    {
        "https://www.googleapis.com/auth/drive",
        "https://www.googleapis.com/auth/drive.readonly",
    }
)


@dataclass(frozen=True)
class ProfileStatus:
    profile: str
    failures: tuple[str, ...] = ()

    @property
    def healthy(self) -> bool:
        return not self.failures


def profile_config_dir(profile: str) -> Path:
    return GWS_CONFIG_ROOT / f"gws-{profile}"


def gws_env(profile: str) -> dict[str, str]:
    return {
        **os.environ,
        "GOOGLE_WORKSPACE_CLI_CONFIG_DIR": str(profile_config_dir(profile)),
        "GOOGLE_WORKSPACE_CLI_KEYRING_BACKEND": "file",
    }


def parse_json(output: str) -> dict:
    start = output.find("{")
    if start < 0:
        raise ValueError("gws returned no JSON response")
    value = json.loads(output[start:])
    if not isinstance(value, dict):
        raise ValueError("gws returned an unexpected JSON response")
    return value


def run_gws(profile: str, *args: str) -> dict:
    if not GWS_BIN.is_file():
        raise RuntimeError(f"gws binary missing: {GWS_BIN}")

    config_dir = profile_config_dir(profile)
    if not config_dir.is_dir():
        raise RuntimeError(f"gws profile missing: {config_dir}")

    result = subprocess.run(
        [str(GWS_BIN), *args],
        env=gws_env(profile),
        capture_output=True,
        text=True,
        timeout=COMMAND_TIMEOUT_SECONDS,
    )
    if result.returncode != 0:
        detail = next(
            (line.strip() for line in reversed(result.stderr.splitlines()) if line.strip()),
            f"exit code {result.returncode}",
        )
        raise RuntimeError(detail)
    return parse_json(result.stdout)


def _record_failure(failures: list[str], check: str, operation) -> dict | None:
    try:
        return operation()
    except Exception as exc:
        failures.append(f"{check}: {exc}")
        return None


def check_profile(profile: str) -> ProfileStatus:
    failures: list[str] = []

    auth = _record_failure(failures, "auth status", lambda: run_gws(profile, "auth", "status"))
    if auth is not None:
        if not auth.get("token_valid") or not auth.get("has_refresh_token"):
            failures.append("auth status: token is not valid")
        scopes = set(auth.get("scopes", []))
        if CALENDAR_SCOPE not in scopes:
            failures.append("calendar scope: full Calendar scope is missing")
        if not scopes.intersection(GMAIL_SCOPES):
            failures.append("gmail scope: Gmail read scope is missing")
        if not scopes.intersection(DRIVE_SCOPES):
            failures.append("drive scope: Drive scope is missing")

    calendars = _record_failure(
        failures,
        "calendar read",
        lambda: run_gws(
            profile,
            "calendar",
            "calendarList",
            "list",
            "--params",
            json.dumps({"maxResults": 250, "minAccessRole": "writer"}),
        ),
    )
    if calendars is not None and not any(
        item.get("accessRole") in {"owner", "writer"} for item in calendars.get("items", [])
    ):
        failures.append("calendar write: no owner or writer calendar found")

    _record_failure(
        failures,
        "gmail read",
        lambda: run_gws(
            profile,
            "gmail",
            "users",
            "messages",
            "list",
            "--params",
            json.dumps({"userId": "me", "maxResults": 1}),
        ),
    )
    _record_failure(
        failures,
        "drive read",
        lambda: run_gws(
            profile,
            "drive",
            "files",
            "list",
            "--params",
            json.dumps({"pageSize": 1, "fields": "files(id)"}),
        ),
    )

    return ProfileStatus(
        profile=profile,
        failures=tuple(failures),
    )


def check_all_profiles() -> list[ProfileStatus]:
    return [check_profile(profile) for profile in GWS_PROFILES]


def failed_profile_names(statuses: list[ProfileStatus] | None = None) -> list[str]:
    checked = statuses if statuses is not None else check_all_profiles()
    return [status.profile for status in checked if not status.healthy]


def auth_warning_banner(failed_profiles: list[str]) -> str:
    if not failed_profiles:
        return ""
    return f"⚠️ Google auth failed: {', '.join(failed_profiles)}"


def build_report(statuses: list[ProfileStatus], weekly: bool = False) -> str:
    failed = any(not status.healthy for status in statuses)
    if weekly:
        title = "Google OAuth weekly heartbeat"
    elif failed:
        title = "Google OAuth needs attention"
    else:
        title = "Google OAuth health check"
    lines = [title, ""]
    for status in statuses:
        if status.failures:
            lines.append(f"{status.profile}: FAILED")
            lines.extend(f"  - {failure}" for failure in status.failures)
        else:
            lines.append(f"{status.profile}: healthy")
    return "\n".join(lines)


def is_weekly_run(now: dt.datetime) -> bool:
    return now.astimezone(LOCAL_TZ).weekday() == 6 and now.astimezone(LOCAL_TZ).hour >= 9


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dry-run", action="store_true", help="Print the report without sending it")
    parser.add_argument("--weekly", action="store_true", help="Always produce the Sunday heartbeat")
    parser.add_argument(
        "--scheduled",
        action="store_true",
        help="Infer the Sunday heartbeat from the current Manila time",
    )
    args = parser.parse_args()

    now = dt.datetime.now(LOCAL_TZ)
    weekly = args.weekly or (args.scheduled and is_weekly_run(now))
    statuses = check_all_profiles()
    needs_attention = any(not status.healthy for status in statuses)

    if not weekly and not needs_attention and not args.dry_run:
        return 0

    report = build_report(statuses, weekly=weekly)
    if args.dry_run:
        print(report)
        return 0

    send(report)
    print(report)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
