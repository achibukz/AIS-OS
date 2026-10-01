#!/usr/bin/env python3
"""Use an existing achiOS Google profile from any repository."""
from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path
from urllib.parse import urlparse

PROFILES = ("main", "personal", "work", "dlsu")
ROOT = Path(__file__).resolve().parent.parent


def operator_home() -> Path:
    if os.environ.get("ACHIOS_HOME"):
        return Path(os.environ["ACHIOS_HOME"]).expanduser()
    if ROOT.parent.name == "GitHub" and ROOT.parent.parent.name == "Code":
        return ROOT.parent.parent.parent
    return Path.home()


def executable() -> str:
    override = os.environ.get("ACHIOS_GWS_BIN")
    if override:
        return str(Path(override).expanduser())
    found = shutil.which("gws")
    if found:
        return found
    for candidate in (operator_home() / ".npm-global/bin/gws", Path("/opt/homebrew/bin/gws"), Path("/usr/local/bin/gws")):
        if candidate.is_file():
            return str(candidate)
    return str(operator_home() / ".npm-global/bin/gws")


def profile_env(profile: str) -> dict[str, str]:
    config = operator_home() / ".config" / f"gws-{profile}"
    if not config.is_dir():
        raise ValueError("profile_missing")
    env = dict(os.environ)
    for key in ("GOOGLE_WORKSPACE_CLI_TOKEN", "GOOGLE_WORKSPACE_CLI_CREDENTIALS_FILE"):
        env.pop(key, None)
    env["GOOGLE_WORKSPACE_CLI_CONFIG_DIR"] = str(config)
    env.setdefault("GOOGLE_WORKSPACE_CLI_KEYRING_BACKEND", "file")
    return env


def call(profile: str, args: list[str]) -> dict:
    binary = executable()
    env = profile_env(profile)
    env["PATH"] = str(Path(binary).parent) + os.pathsep + env.get("PATH", os.defpath)
    result = subprocess.run(
        [binary, *args], env=env, capture_output=True,
        text=True, timeout=45, stdin=subprocess.DEVNULL,
    )
    if result.returncode:
        # Diagnostics may contain credentials. Return only the structured error code.
        code = "gws_failed"
        try:
            error = json.loads(result.stdout[result.stdout.index("{"):]).get("error", {})
            status = error.get("code")
            code = {401: "auth_failed", 403: "permission_denied", 404: "not_found"}.get(status, code)
        except (ValueError, AttributeError):
            pass
        raise ValueError(code)
    try:
        data = json.loads(result.stdout[result.stdout.index("{"):])
    except ValueError:
        raise ValueError("invalid_gws_json") from None
    if not isinstance(data, dict):
        raise ValueError("invalid_gws_json")
    return data


def document_id(value: str) -> str:
    if re.fullmatch(r"[A-Za-z0-9_-]+", value):
        return value
    url = urlparse(value)
    if url.scheme == "https" and url.hostname == "docs.google.com":
        match = re.match(r"^/document/(?:u/\d+/)?d/([A-Za-z0-9_-]+)(?:/|$)", url.path)
        if match:
            return match.group(1)
    raise ValueError("invalid_docs_url_or_id")


def doctor(profile: str) -> dict:
    try:
        auth = call(profile, ["auth", "status"])
        ready = bool(auth.get("token_valid") and auth.get("has_refresh_token"))
        return {"profile": profile, "status": "authenticated" if ready else "auth_required",
                "scopes": auth.get("scopes", [])}
    except (OSError, subprocess.TimeoutExpired, ValueError) as exc:
        return {"profile": profile, "status": error_code(exc)}


def error_code(exc: Exception) -> str:
    if isinstance(exc, FileNotFoundError):
        return "gws_missing"
    if isinstance(exc, subprocess.TimeoutExpired):
        return "timeout"
    if isinstance(exc, OSError):
        return "local_access_failed"
    return str(exc)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--profile", choices=PROFILES)
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("doctor")
    doc = commands.add_parser("read-doc")
    doc.add_argument("url_or_id")
    mail = commands.add_parser("search-mail")
    mail.add_argument("query")
    mail.add_argument("--limit", type=int, default=10)
    read_mail = commands.add_parser("read-mail")
    read_mail.add_argument("id")
    drive = commands.add_parser("search-drive")
    drive.add_argument("query", help="Google Drive API query")
    drive.add_argument("--limit", type=int, default=10)
    raw = commands.add_parser("exec", help="Run a gws JSON command under an explicit profile")
    raw.add_argument("args", nargs=argparse.REMAINDER)
    args = parser.parse_args(argv)
    if args.command == "doctor":
        rows = [doctor(p) for p in ((args.profile,) if args.profile else PROFILES)]
        print(json.dumps({"profiles": rows}))
        return 0 if all(row["status"] == "authenticated" for row in rows) else 1
    if not args.profile:
        parser.error("--profile is required for Google operations")
    try:
        if args.command == "read-doc":
            command = ["docs", "documents", "get", "--params", json.dumps({
                "documentId": document_id(args.url_or_id), "includeTabsContent": True,
            })]
        elif args.command == "search-mail":
            command = ["gmail", "users", "messages", "list", "--params", json.dumps({
                "userId": "me", "q": args.query, "maxResults": args.limit,
            })]
        elif args.command == "read-mail":
            command = ["gmail", "users", "messages", "get", "--params", json.dumps({
                "userId": "me", "id": args.id, "format": "full",
            })]
        elif args.command == "search-drive":
            command = ["drive", "files", "list", "--params", json.dumps({
                "q": args.query, "pageSize": args.limit,
                "fields": "nextPageToken,files(id,name,mimeType,webViewLink)",
            })]
        else:
            command = args.args
            if command[:1] == ["--"]:
                command = command[1:]
            if not command or command[0] == "auth":
                raise ValueError("use_doctor_or_run_auth_interactively")
        data = call(args.profile, [*command, "--format", "json"])
        print(json.dumps({"status": "ok", "profile": args.profile, "data": data}, ensure_ascii=False))
        return 0
    except (OSError, subprocess.TimeoutExpired, ValueError) as exc:
        print(json.dumps({"status": "error", "profile": args.profile, "error": error_code(exc)}))
        return 1


if __name__ == "__main__":
    sys.exit(main())
