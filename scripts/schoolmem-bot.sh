#!/usr/bin/env bash
# Bring the schoolMem vault up to date, arm the wiki guard, then hand the terminal to the
# Telegram bot session. Runs inside tmux (see systemd/achios-schoolmem-bot.service) because
# `claude` drops to --print mode when it has no TTY, and the channel needs the interactive
# session.
set -uo pipefail

VAULT="$HOME/Documents/Obsidian/schoolMem"
STATE_DIR="$HOME/.claude/channels/telegram-schoolmem"
GUARD="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/schoolmem_wiki_guard.py"
SETTINGS="$VAULT/.claude/settings.json"
LOG="$HOME/.local/state/achios/schoolmem_bot.log"

mkdir -p "$(dirname "$LOG")"

log() { printf '%s  %s\n' "$(date '+%Y-%m-%d %H:%M:%S')" "$*" >> "$LOG"; }

log "--- starting schoolMem bot ---"

[ -d "$VAULT" ] || { log "FATAL: vault missing at $VAULT"; exit 1; }

# The session runs with bypassPermissions, so the PreToolUse guard is the only thing
# keeping it out of wiki/. Install it before launching and refuse to start without it —
# an unguarded bot is worse than no bot.
mkdir -p "$VAULT/.claude"
if ! GUARD="$GUARD" SETTINGS="$SETTINGS" python3 - <<'PY' >> "$LOG" 2>&1
import json, os, sys
from pathlib import Path

guard, path = os.environ["GUARD"], Path(os.environ["SETTINGS"])
settings = {}
if path.exists():
    try:
        settings = json.loads(path.read_text())
    except json.JSONDecodeError:
        sys.exit(f"{path} is not valid JSON; refusing to overwrite it by hand")

entry = {
    "matcher": "Write|Edit|MultiEdit|NotebookEdit|Bash",
    "hooks": [{"type": "command", "command": guard}],
}
hooks = settings.setdefault("hooks", {})
pre = hooks.setdefault("PreToolUse", [])
# Replace our own entry rather than appending a duplicate on every restart, and leave any
# hook Aki added himself untouched.
pre[:] = [h for h in pre if guard not in json.dumps(h)] + [entry]

path.write_text(json.dumps(settings, indent=2) + "\n")
print(f"wiki guard armed in {path}")
PY
then
    log "FATAL: could not arm the wiki guard — refusing to start an unguarded bot"
    exit 1
fi

# Fast-forward before the session opens so the bot answers from a current vault. A stale
# vault gives wrong answers; a failed fetch is not a reason to leave Aki without a bot, so
# this warns and continues rather than aborting.
if sync-repos "$VAULT" >> "$LOG" 2>&1; then
    log "vault synced"
else
    log "WARNING: sync-repos exited non-zero — starting on a possibly stale vault"
fi

cd "$VAULT" || exit 1

log "launching claude (sonnet, bypassPermissions, wiki/ write-blocked)"

export TELEGRAM_STATE_DIR="$STATE_DIR"

exec claude \
    --channels plugin:telegram@claude-plugins-official \
    --model sonnet \
    --permission-mode bypassPermissions
