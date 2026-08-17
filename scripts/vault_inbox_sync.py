#!/usr/bin/env python3
"""Vault Inbox Sync Daemon for achiOS.

Automatically commits and pushes new mobile captures from schoolMem/inbox/
(and achiMem/inbox/) so that captures made via @schoMemBot
seamlessly sync to Obsidian on the Mac.

Usage:
    python scripts/vault_inbox_sync.py           # Run sync
    python scripts/vault_inbox_sync.py --dry-run # Preview pending changes
"""

from __future__ import annotations

import argparse
import datetime as dt
import subprocess
import sys
from pathlib import Path
from zoneinfo import ZoneInfo

LOCAL_TZ = ZoneInfo("Asia/Manila")

VAULTS = [
    {
        "name": "schoolMem",
        "path": Path.home() / "Documents" / "Obsidian" / "schoolMem",
        "branch": "main",
        "watch_dirs": ["inbox"],
    },
    {
        "name": "achiMem",
        "path": Path.home() / "Documents" / "Obsidian" / "achiMem",
        "branch": "main",
        "watch_dirs": ["inbox"],
    },
]


def run_git(vault_dir: Path, args: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git"] + args,
        cwd=vault_dir,
        capture_output=True,
        text=True,
        check=False,
    )


def check_and_sync_vault(vault: dict, dry_run: bool = False) -> tuple[bool, str]:
    vault_path: Path = vault["path"]
    name: str = vault["name"]
    branch: str = vault.get("branch", "main")
    watch_dirs: list[str] = vault.get("watch_dirs", ["inbox"])

    if not vault_path.exists() or not (vault_path / ".git").exists():
        return False, f"[{name}] Vault directory or .git not found at {vault_path}"

    # 1. Check git status
    status = run_git(vault_path, ["status", "--porcelain"])
    if status.returncode != 0:
        return False, f"[{name}] git status failed: {status.stderr.strip()}"

    lines = [line.strip() for line in status.stdout.splitlines() if line.strip()]
    if not lines:
        return True, f"[{name}] Clean. No pending changes to sync."

    # Filter for changes inside watched directories (e.g. inbox/)
    inbox_changes = []
    for line in lines:
        parts = line.split(maxsplit=1)
        if len(parts) == 2:
            filepath = parts[1]
            if any(filepath.startswith(f"{wd}/") or filepath == wd for wd in watch_dirs):
                inbox_changes.append(filepath)

    if not inbox_changes:
        return True, f"[{name}] Clean. No pending inbox captures found."

    if dry_run:
        return True, f"[{name}] [DRY RUN] {len(inbox_changes)} pending inbox capture(s) found:\n  " + "\n  ".join(inbox_changes)

    # 2. Rebase pull to get latest remote commits before pushing
    pull = run_git(vault_path, ["pull", "--rebase", "--autostash", "origin", branch])
    if pull.returncode != 0:
        run_git(vault_path, ["rebase", "--abort"])
        return False, f"[{name}] git pull --rebase failed: {pull.stderr.strip()}. Aborted rebase to prevent corruption."

    # 3. Stage ONLY watched directories
    for wd in watch_dirs:
        target = vault_path / wd
        if target.exists():
            stage = run_git(vault_path, ["add", wd])
            if stage.returncode != 0:
                return False, f"[{name}] git add {wd} failed: {stage.stderr.strip()}"

    # Check if there are staged changes
    staged_status = run_git(vault_path, ["diff", "--cached", "--quiet"])
    if staged_status.returncode == 0:
        return True, f"[{name}] No staged changes to commit."

    # 4. Commit
    now_str = dt.datetime.now(LOCAL_TZ).strftime("%Y-%m-%d %H:%M")
    commit_msg = f"sync(inbox): auto-sync mobile captures [{now_str}]"
    commit = run_git(vault_path, ["commit", "-m", commit_msg])
    if commit.returncode != 0:
        return False, f"[{name}] git commit failed: {commit.stderr.strip()}"

    # 5. Push
    push = run_git(vault_path, ["push", "origin", branch])
    if push.returncode != 0:
        return False, f"[{name}] git push origin {branch} failed: {push.stderr.strip()}"

    return True, f"[{name}] Successfully synced {len(inbox_changes)} capture(s) to origin/{branch}."


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview pending vault inbox changes without committing or pushing",
    )
    args = parser.parse_args()

    overall_success = True
    for vault in VAULTS:
        if not vault["path"].exists():
            continue
        success, msg = check_and_sync_vault(vault, dry_run=args.dry_run)
        print(f"[{dt.datetime.now(LOCAL_TZ).isoformat()}] {msg}")
        if not success:
            overall_success = False

    return 0 if overall_success else 1


if __name__ == "__main__":
    raise SystemExit(main())
