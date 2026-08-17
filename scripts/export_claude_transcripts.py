#!/usr/bin/env python3
"""Export Claude Code Telegram sessions into achiMem/tgdb/.

Scans ~/.claude/projects/ for recent conversation sessions, extracts
user messages and assistant responses, sanitizes secrets, and writes
structured notes into achiMem/tgdb/YYYY-MM/.

Usage:
    python scripts/export_claude_transcripts.py
"""

from __future__ import annotations

import datetime as dt
import json
import os
import re
import sys
from pathlib import Path
from zoneinfo import ZoneInfo

# Add scripts directory to sys.path
SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))
from tgdb_logger import format_tgdb_note, write_tgdb_session

LOCAL_TZ = ZoneInfo("Asia/Manila")
CLAUDE_PROJECTS_DIR = Path.home() / ".claude" / "projects"
DEFAULT_VAULT_PATH = Path.home() / "Documents" / "Obsidian" / "achiMem"


def parse_jsonl_session(file_path: Path) -> tuple[dict, list[dict]] | None:
    """Extract metadata and conversation messages from a Claude jsonl transcript."""
    try:
        lines = file_path.read_text(encoding="utf-8", errors="replace").splitlines()
        if not lines:
            return None

        messages: list[dict] = []
        first_prompt = ""
        session_id = file_path.stem
        start_ts = None

        for line in lines:
            if not line.strip():
                continue
            try:
                entry = json.loads(line)
            except Exception:
                continue

            # Extract user message
            if entry.get("type") == "user":
                msg_obj = entry.get("message", {})
                content = msg_obj.get("content", "")
                if isinstance(content, list):
                    # Extract text blocks
                    content = " ".join(b.get("text", "") for b in content if isinstance(b, dict))
                content = str(content).strip()
                if content:
                    if not first_prompt:
                        first_prompt = content
                        if "timestamp" in entry:
                            try:
                                start_ts = dt.datetime.fromisoformat(entry["timestamp"].replace("Z", "+00:00")).astimezone(LOCAL_TZ)
                            except Exception:
                                pass
                    messages.append({"role": "user", "content": content})

            # Extract assistant message
            elif entry.get("type") == "assistant":
                msg_obj = entry.get("message", {})
                content = msg_obj.get("content", "")
                if isinstance(content, list):
                    content = " ".join(b.get("text", "") for b in content if isinstance(b, dict))
                content = str(content).strip()
                if content:
                    messages.append({"role": "assistant", "content": content})

        if not messages:
            return None

        # Determine bot identity based on file location/cwd
        cwd = str(file_path)
        if "schoolmem" in cwd.lower():
            bot_name = "@schoMemBot"
            domain = "schoolmem"
        else:
            bot_name = "@achiOSClaudeBot"
            domain = "achios"

        # Create title from first prompt
        title = first_prompt.splitlines()[0][:60].strip() if first_prompt else "Claude Session"
        title = re.sub(r"[#*`_\[\]]", "", title).strip()

        meta = {
            "title": title or "Claude Code Session",
            "bot": bot_name,
            "engine": "Claude Sonnet",
            "summary": f"{bot_name} session covering {title}.",
            "tags": ["tgdb", "claude", domain],
            "timestamp": start_ts or dt.datetime.now(LOCAL_TZ),
        }

        return meta, messages

    except Exception as e:
        print(f"Error parsing {file_path.name}: {e}", file=sys.stderr)
        return None


def export_recent_sessions(days_lookback: int = 1) -> int:
    """Scan and export recent Claude Code sessions to achiMem/tgdb/."""
    if not CLAUDE_PROJECTS_DIR.exists():
        return 0

    exported_count = 0
    now = dt.datetime.now(LOCAL_TZ)
    cutoff = now - dt.timedelta(days=days_lookback)

    for project_dir in CLAUDE_PROJECTS_DIR.iterdir():
        if not project_dir.is_dir():
            continue

        for jsonl_file in project_dir.glob("*.jsonl"):
            # Check modification time
            mtime = dt.datetime.fromtimestamp(jsonl_file.stat().st_mtime, tz=LOCAL_TZ)
            if mtime < cutoff:
                continue

            parsed = parse_jsonl_session(jsonl_file)
            if not parsed:
                continue

            meta, messages = parsed
            note_content = format_tgdb_note(meta, messages)
            out_file = write_tgdb_session(DEFAULT_VAULT_PATH, meta["bot"], jsonl_file.stem, note_content, timestamp=meta["timestamp"])
            exported_count += 1

    return exported_count


def main() -> int:
    exported = export_recent_sessions(days_lookback=2)
    print(f"Exported {exported} Claude Code session(s) to achiMem/tgdb/.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
