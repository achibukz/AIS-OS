#!/usr/bin/env python3
"""SessionStart hook. Injects an achiMem recall digest for achiOS sessions."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

VAULT = Path.home() / "Documents" / "Obsidian" / "achiMem"
SESSIONS = VAULT / "raw" / "sessions"
RECENT_COUNT = 3
THREAD_SCAN_COUNT = 5
HEADLINE_LIMIT = 70

HAPPENED_RE = re.compile(r"^## What happened\s*\n\s*[-*]\s*(.+)$", re.M)
ASK_RE = re.compile(r'^- Opening ask:\s*"(.*)"\s*$', re.M)
THREADS_RE = re.compile(r"^## Open threads\s*$(.*?)(?=^## |\Z)", re.M | re.S)
BULLET_RE = re.compile(r"^\s*[-*]\s+\S", re.M)


def _read(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ""


def session_files() -> list[Path]:
    if not SESSIONS.is_dir():
        return []
    return sorted(SESSIONS.glob("*.md"), key=lambda p: p.name, reverse=True)


def headline(path: Path) -> str:
    body = _read(path)
    for pattern in (HAPPENED_RE, ASK_RE):
        match = pattern.search(body)
        if match:
            return match.group(1).strip()[:HEADLINE_LIMIT]
    return path.stem


def count_open_threads(paths) -> int:
    total = 0
    for path in paths:
        match = THREADS_RE.search(_read(path))
        if match:
            total += len(BULLET_RE.findall(match.group(1)))
    return total


def count_unenriched(paths) -> int:
    return sum(1 for path in paths if "status: unenriched" in _read(path))


def build_context() -> str:
    files = session_files()
    if not files:
        return "── achiMem recall ──\nNo achiOS sessions logged yet."
    recent = files[:RECENT_COUNT]
    lines = ["── achiMem recall ──", f"Last {len(recent)} sessions:"]
    for path in recent:
        lines.append(f"  {path.name[:10]}  {headline(path)}")
    lines.append(f"Open threads: {count_open_threads(files[:THREAD_SCAN_COUNT])}")
    lines.append(f"Unenriched logs: {count_unenriched(files)}")
    return "\n".join(lines)


def main() -> None:
    payload = {
        "hookSpecificOutput": {
            "hookEventName": "SessionStart",
            "additionalContext": build_context(),
        }
    }
    print(json.dumps(payload))


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:  # a recall hook must never break the session
        print(f"achimem_recall: {exc}", file=sys.stderr)
    sys.exit(0)
