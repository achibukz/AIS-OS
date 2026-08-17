#!/usr/bin/env bash
# Push portable Claude Code config from this Mac to the headless server.
# Allowlist, not denylist: anything not named here never leaves the machine,
# so a new credential file added by some future tool cannot leak by default.
set -euo pipefail

HOST="${CLAUDE_SYNC_HOST:-achibuntu}"
DRY=""

for arg in "$@"; do
  case "$arg" in
    --dry-run) DRY="--dry-run -v" ;;
    *) HOST="$arg" ;;
  esac
done

SRC="$HOME/.claude"

FILES=(CLAUDE.md GEMINI_WORKFLOW.md settings.json)
DIRS=(skills agents commands hooks)

# Hermes reads its own ~/.hermes/skills, not ~/.claude/skills. Only the ones that work
# headless go there — Hermes already ships 40+ of its own, and the design and frontend
# skills are useless over Telegram.
HERMES_SKILLS=(message-writer linkedin-poster humanizer essay-writer)

echo "→ $HOST${DRY:+  (dry run)}"

ssh "$HOST" 'mkdir -p ~/.claude'
ssh "$HOST" 'test -f ~/.claude/settings.json && cp ~/.claude/settings.json ~/.claude/settings.json.bak' || true

for f in "${FILES[@]}"; do
  [[ -f "$SRC/$f" ]] || continue
  rsync -az $DRY "$SRC/$f" "$HOST:.claude/$f"
done

# --delete so a skill deleted on the Mac disappears on the server too.
for d in "${DIRS[@]}"; do
  [[ -d "$SRC/$d" ]] || continue
  rsync -az --delete --exclude='.DS_Store' $DRY "$SRC/$d/" "$HOST:.claude/$d/"
done

# ccstatusline keeps its layout outside ~/.claude, so settings.json alone renders a default bar.
if [[ -f "$HOME/.config/ccstatusline/settings.json" ]]; then
  ssh "$HOST" 'mkdir -p ~/.config/ccstatusline'
  rsync -az $DRY "$HOME/.config/ccstatusline/settings.json" "$HOST:.config/ccstatusline/settings.json"
fi

# projects/ stays off the allowlist above — it holds session transcripts. Only the
# memory/ subdirs go, and they need slug remapping and an index merge, so a helper
# does it rather than another rsync line.
"$(dirname "$0")/sync_claude_memory.py" ${DRY:+--dry-run} "$HOST"

if ssh "$HOST" 'test -d ~/.hermes'; then
  ssh "$HOST" 'mkdir -p ~/.hermes/skills'
  for s in "${HERMES_SKILLS[@]}"; do
    [[ -d "$SRC/skills/$s" ]] || continue
    rsync -az --delete --exclude='.git' --exclude='.DS_Store' $DRY \
      "$SRC/skills/$s/" "$HOST:.hermes/skills/$s/"
  done
  echo "hermes skills: ${HERMES_SKILLS[*]}"
fi

echo "done. plugins restore themselves from enabledPlugins in settings.json on next start."
