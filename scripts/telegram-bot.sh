#!/usr/bin/env bash
# Bring a repo up to date, optionally arm a write guard, then hand the terminal to a
# Claude Code Telegram channel session. Runs inside tmux (see systemd/achios-*-bot.service)
# because `claude` falls back to --print when it has no TTY, and the channel needs the
# interactive session.
#
# Driven by env vars, set per bot in its unit:
#   BOT_NAME       label for logs                                   (required)
#   BOT_CWD        repo the session opens in, so its CLAUDE.md loads (required)
#   BOT_STATE_DIR  TELEGRAM_STATE_DIR — the token and allowlist      (required)
#   BOT_GUARD      PreToolUse hook to install; omit for an unguarded bot
#   BOT_MODEL      defaults to sonnet
set -uo pipefail

: "${BOT_NAME:?BOT_NAME is required}"
: "${BOT_CWD:?BOT_CWD is required}"
: "${BOT_STATE_DIR:?BOT_STATE_DIR is required}"
BOT_GUARD="${BOT_GUARD:-}"
BOT_MODEL="${BOT_MODEL:-sonnet}"

LOG="$HOME/.local/state/achios/${BOT_NAME}_bot.log"
mkdir -p "$(dirname "$LOG")"

log() { printf '%s  %s\n' "$(date '+%Y-%m-%d %H:%M:%S')" "$*" >> "$LOG"; }

log "--- starting $BOT_NAME bot ---"

[ -d "$BOT_CWD" ] || { log "FATAL: $BOT_CWD does not exist"; exit 1; }
[ -f "$BOT_STATE_DIR/.env" ] || { log "FATAL: no token at $BOT_STATE_DIR/.env"; exit 1; }

# A guarded bot runs with bypassPermissions, so the PreToolUse hook is the only thing
# holding its write ban. Install it before launching and refuse to start without it — an
# unguarded bot that believes it is guarded is worse than no bot.
if [ -n "$BOT_GUARD" ]; then
    mkdir -p "$BOT_CWD/.claude"
    if ! GUARD="$BOT_GUARD" SETTINGS="$BOT_CWD/.claude/settings.json" python3 - <<'PY' >> "$LOG" 2>&1
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
print(f"write guard armed in {path}")
PY
    then
        log "FATAL: could not arm the write guard — refusing to start an unguarded bot"
        exit 1
    fi
fi

# Fast-forward before the session opens so the bot works from a current tree. Stale is
# worse than slow; a failed fetch is not a reason to leave Aki without a bot, so this
# warns and continues rather than aborting.
if sync-repos "$BOT_CWD" >> "$LOG" 2>&1; then
    log "synced"
else
    log "WARNING: sync-repos exited non-zero — starting on a possibly stale tree"
fi

cd "$BOT_CWD" || exit 1

log "launching claude ($BOT_MODEL, bypassPermissions, guard=${BOT_GUARD:-none})"

export TELEGRAM_STATE_DIR="$BOT_STATE_DIR"

# Tells a PreToolUse guard that nobody is watching this session. The guard also
# falls back to TELEGRAM_STATE_DIR above, so it stays armed if this line is ever
# dropped, but set it explicitly rather than leaning on a side effect.
export ACHIOS_UNATTENDED_BOT=1

claude \
    --channels plugin:telegram@claude-plugins-official \
    --model "$BOT_MODEL" \
    --permission-mode bypassPermissions
EXIT_CODE=$?

log "Claude process exited with code $EXIT_CODE"
if [ "$EXIT_CODE" -ne 0 ]; then
    log "FATAL: Claude exited unexpectedly ($EXIT_CODE) — sending Telegram crash alert"
    /home/achibukz/.local/share/achios/venv/bin/python "$BOT_CWD/scripts/service_failure_alert.py" "achios-${BOT_NAME}-bot.service" --reason "Claude exited with code $EXIT_CODE" || true
fi
exit "$EXIT_CODE"
