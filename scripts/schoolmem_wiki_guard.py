#!/usr/bin/env python3
"""PreToolUse guard: deny writes into schoolMem's wiki/ from the unattended Telegram bot.

The bot session runs with --permission-mode bypassPermissions, so nothing else stands
between the model and the vault. schoolMem's provenance guarantee depends on wiki/ only
ever being written with Aki present, so that gate has to be mechanical rather than a
line of instruction the model may reinterpret at 3am.

Write/Edit/NotebookEdit are closed deterministically by path. Bash is heuristic — see
GUARDED_BASH below for what it does and does not catch.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

VAULT = Path.home() / "Documents" / "Obsidian" / "schoolMem"
PROTECTED = VAULT / "wiki"

PATH_TOOLS = {"Write", "Edit", "NotebookEdit", "MultiEdit"}

# Bash is a hole under bypassPermissions: a shell can write anywhere and no path
# argument exists to inspect. These patterns catch the plausible accidents — a
# redirect, a copy, a delete, a rename aimed at wiki/ — not a determined bypass.
GUARDED_BASH = re.compile(
    r"(>>?\s*\S*wiki/)"
    r"|(\b(rm|mv|cp|tee|truncate|sed\s+-i|dd)\b[^|;&]*\bwiki/)"
    r"|(\bgit\b[^|;&]*\b(checkout|restore|reset)\b[^|;&]*\bwiki/)",
    re.IGNORECASE,
)

DENY_REASON = (
    "Denied by the schoolMem wiki guard. This session is the unattended Telegram bot, "
    "which may read wiki/ freely but never write to it — wiki pages are only created "
    "with Aki present, in a real session, so the vault's provenance guarantee holds. "
    "Write the capture to inbox/ instead and it will be promoted by a proper INGEST later."
)


def deny(reason: str) -> None:
    json.dump(
        {
            "hookSpecificOutput": {
                "hookEventName": "PreToolUse",
                "permissionDecision": "deny",
                "permissionDecisionReason": reason,
            }
        },
        sys.stdout,
    )
    sys.stdout.write("\n")
    sys.exit(0)


def targets_protected(raw_path: str, cwd: str) -> bool:
    if not raw_path:
        return False
    candidate = Path(raw_path).expanduser()
    if not candidate.is_absolute():
        candidate = Path(cwd) / candidate
    try:
        resolved = candidate.resolve()
    except OSError:
        resolved = Path(candidate)
    return resolved == PROTECTED or PROTECTED in resolved.parents


def main() -> None:
    try:
        event = json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError):
        # A hook that cannot parse its input must not silently wave the call through.
        deny("schoolMem wiki guard could not parse the tool call, so it refused it.")
        return

    tool = event.get("tool_name", "")
    tool_input = event.get("tool_input", {}) or {}
    cwd = event.get("cwd") or str(VAULT)

    if tool in PATH_TOOLS:
        for key in ("file_path", "notebook_path", "path"):
            if targets_protected(str(tool_input.get(key, "")), cwd):
                deny(DENY_REASON)

    if tool == "Bash" and GUARDED_BASH.search(str(tool_input.get("command", ""))):
        deny(
            DENY_REASON
            + " (Blocked at the Bash layer: the command looked like it would modify wiki/.)"
        )

    sys.exit(0)


if __name__ == "__main__":
    main()
