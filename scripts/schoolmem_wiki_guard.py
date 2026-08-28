#!/usr/bin/env python3
"""PreToolUse guard: deny writes into schoolMem's wiki/ from the unattended Telegram bot.

The bot session runs with --permission-mode bypassPermissions, so nothing else stands
between the model and the vault. schoolMem's provenance guarantee depends on wiki/ only
ever being written with Aki present, so that gate has to be mechanical rather than a
line of instruction the model may reinterpret at 3am.

WHO THIS APPLIES TO
-------------------
telegram-bot.sh arms this hook by writing it into <repo>/.claude/settings.json, and that
file outlives the bot process. Every later interactive session in the same repo therefore
inherits the hook. Until 2026-08-28 the guard assumed it only ever ran inside the bot and
denied unconditionally, which blocked Aki's own attended sessions from the vault he owns.

So the guard now identifies the session before it judges the call:

  ACHIOS_UNATTENDED_BOT=1   set by telegram-bot.sh, the explicit marker
  TELEGRAM_STATE_DIR        also exported by telegram-bot.sh, and required by it

Either one means unattended. The second is a fallback so a launcher that predates the
marker stays guarded rather than silently failing open. An attended session matches
neither and is waved through untouched.

Hooks are spawned as children of the Claude Code process and inherit its environment, so
these are visible here exactly when the launcher exported them.

WHAT IT CATCHES
---------------
Write/Edit/MultiEdit/NotebookEdit carry a path argument, so they are closed exactly: the
path resolves against cwd and is denied if it lands in wiki/.

Bash has no path argument and a shell can write anywhere, so it is judged coarsely: any
command that mentions "wiki" AND contains a redirect or a write-capable verb is denied.
That is deliberately blunt. The previous version required the literal text "wiki/" to sit
next to the verb, which meant

    SRC=wiki/topics; cp "$SRC/a.md" "$DST/"

sailed straight through, because the only literal wiki/ was in the assignment. Matching
the two signals independently closes that. Shell state does not persist between Bash tool
calls, so a variable set in an earlier call cannot smuggle a path into a later one.

The cost is false positives. `cat wiki/index.md > inbox/note.md` reads the wiki and writes
the inbox, and is denied anyway. That is the right trade: precision lives in the
path-checked tools above, and the bot should use Read and Write for that shape of work.

It does not stop a determined bypass. `W=wik; cat > ${W}i/x` defeats it, as does anything
that assembles the path from pieces. This guards against a model doing the obvious thing
at 3am. It is not a sandbox.
"""

from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path

VAULT = Path.home() / "Documents" / "Obsidian" / "schoolMem"
PROTECTED = VAULT / "wiki"

PATH_TOOLS = {"Write", "Edit", "NotebookEdit", "MultiEdit"}

UNATTENDED_MARKER = "ACHIOS_UNATTENDED_BOT"
UNATTENDED_FALLBACK = "TELEGRAM_STATE_DIR"

# Any mention of the protected tree, however it is spelled or interpolated.
MENTIONS_WIKI = re.compile(r"wiki", re.IGNORECASE)

# A redirect, or any verb that can create, move, delete, or rewrite a file.
WRITES = re.compile(
    r"(>>?\s*[^|&\s])"
    r"|(\b(rm|rmdir|mv|cp|tee|truncate|dd|mkdir|touch|install|rsync|ln"
    r"|chmod|chown|chgrp|patch|shred|unlink|xargs)\b)"
    r"|(\b(sed|perl)\b[^|;&]*\s-i\b)"
    r"|(\bgit\b[^|;&]*\b(checkout|restore|reset|clean|apply|mv|rm|stash|switch)\b)"
    r"|(\b(python3?|perl|ruby|node|awk)\b)"
    r"|(\bfind\b[^|;&]*(-delete|-exec)\b)",
    re.IGNORECASE,
)

DENY_REASON = (
    "Denied by the schoolMem wiki guard. This session is the unattended Telegram bot, "
    "which may read wiki/ freely but never write to it. Wiki pages are only created "
    "with Aki present, in a real session, so the vault's provenance guarantee holds. "
    "Write the capture to inbox/ instead and it will be promoted by a proper INGEST later."
)

BASH_SUFFIX = (
    " (Blocked at the Bash layer, which is deliberately coarse: the command both mentions "
    "wiki and can write. If you are only reading the wiki and writing somewhere else, use "
    "the Read and Write tools, which are checked by exact path.)"
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


def session_is_unattended() -> bool:
    if os.environ.get(UNATTENDED_MARKER) == "1":
        return True
    return bool(os.environ.get(UNATTENDED_FALLBACK))


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
    # Attended sessions own the vault. Decide this before reading stdin, so a malformed
    # event can never deny Aki his own wiki.
    if not session_is_unattended():
        sys.exit(0)

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

    if tool == "Bash":
        command = str(tool_input.get("command", ""))
        if MENTIONS_WIKI.search(command) and WRITES.search(command):
            deny(DENY_REASON + BASH_SUFFIX)

    sys.exit(0)


if __name__ == "__main__":
    main()
