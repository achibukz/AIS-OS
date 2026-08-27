#!/usr/bin/env bash
# Installer for universal git hooks (enforcing session-log.md and link verification)
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
HOOK_SOURCE="$SCRIPT_DIR/hooks/pre-commit"

if [ ! -f "$HOOK_SOURCE" ]; then
    echo "❌ Error: Hook source not found at $HOOK_SOURCE"
    exit 1
fi

TARGET_PATH="${1:-$(pwd)}"

if [ -d "$TARGET_PATH/.git" ]; then
    REPO_ROOT="$TARGET_PATH"
else
    REPO_ROOT="$(cd "$TARGET_PATH" && git rev-parse --show-toplevel 2>/dev/null || true)"
fi

if [ -z "$REPO_ROOT" ] || [ ! -d "$REPO_ROOT/.git" ]; then
    echo "❌ Error: $TARGET_PATH is not inside a git repository."
    exit 1
fi

HOOKS_DIR="$REPO_ROOT/.git/hooks"
mkdir -p "$HOOKS_DIR"

DEST_HOOK="$HOOKS_DIR/pre-commit"
cp "$HOOK_SOURCE" "$DEST_HOOK"
chmod +x "$DEST_HOOK"

echo "✅ Installed universal pre-commit hook into $DEST_HOOK"
