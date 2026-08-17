#!/usr/bin/env python3
"""Universal Transcript Exporter for achiOS.

Exports conversation transcripts from BOTH:
1. Claude Code CLI/Telegram sessions (~/.claude/projects/)
2. Antigravity CLI/Telegram sessions (~/.gemini/antigravity-cli/brain/)

Sanitizes secrets and writes clean, structured Markdown notes into:
achiMem/tgdb/YYYY-MM/

Usage:
    python scripts/export_transcripts.py
"""

from __future__ import annotations

import datetime as dt
import json
import os
import re
import sys
from pathlib import Path
from zoneinfo import ZoneInfo

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))
from tgdb_logger import format_tgdb_note, write_tgdb_session

LOCAL_TZ = ZoneInfo("Asia/Manila")
CLAUDE_PROJECTS_DIR = Path.home() / ".claude" / "projects"
AGY_BRAIN_DIR = Path.home() / ".gemini" / "antigravity-cli" / "brain"
DEFAULT_VAULT_PATH = Path.home() / "Documents" / "Obsidian" / "achiMem"


def parse_claude_jsonl(file_path: Path) -> tuple[dict, list[dict]] | None:
    """Extract metadata and conversation messages from a Claude jsonl transcript."""
    try:
        lines = file_path.read_text(encoding="utf-8", errors="replace").splitlines()
        if not lines:
            return None

        messages: list[dict] = []
        first_prompt = ""
        start_ts = None

        for line in lines:
            if not line.strip():
                continue
            try:
                entry = json.loads(line)
            except Exception:
                continue

            if entry.get("type") == "user":
                msg_obj = entry.get("message", {})
                content = msg_obj.get("content", "")
                if isinstance(content, list):
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

        cwd = str(file_path)
        if "schoolmem" in cwd.lower():
            bot_name = "@schoMemBot"
            domain = "schoolmem"
        else:
            bot_name = "@achiOSClaudeBot"
            domain = "achios"

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
        print(f"Error parsing Claude session {file_path.name}: {e}", file=sys.stderr)
        return None


def parse_antigravity_transcript(transcript_path: Path) -> tuple[dict, list[dict]] | None:
    """Extract metadata and dialog messages from an Antigravity transcript.jsonl."""
    try:
        lines = transcript_path.read_text(encoding="utf-8", errors="replace").splitlines()
        if not lines:
            return None

        messages: list[dict] = []
        first_prompt = ""
        start_ts = None

        for line in lines:
            if not line.strip():
                continue
            try:
                entry = json.loads(line)
            except Exception:
                continue

            entry_type = entry.get("type")
            source = entry.get("source")
            content = entry.get("content", "")

            # User message
            if entry_type == "USER_INPUT" or source == "USER_EXPLICIT":
                # Extract clean user prompt out of XML tags if present
                user_match = re.search(r"<USER_REQUEST>(.*?)</USER_REQUEST>", content, re.DOTALL)
                clean_user = user_match.group(1).strip() if user_match else content.strip()
                if clean_user:
                    if not first_prompt:
                        first_prompt = clean_user
                        if "created_at" in entry:
                            try:
                                start_ts = dt.datetime.fromisoformat(entry["created_at"].replace("Z", "+00:00")).astimezone(LOCAL_TZ)
                            except Exception:
                                pass
                    messages.append({"role": "user", "content": clean_user})

            # Assistant response
            elif entry_type == "PLANNER_RESPONSE" or source == "MODEL":
                resp_text = content.strip() if isinstance(content, str) else ""
                if resp_text:
                    messages.append({"role": "assistant", "content": resp_text})

        if not messages:
            return None

        conv_id = transcript_path.parent.parent.name
        title = first_prompt.splitlines()[0][:60].strip() if first_prompt else "Antigravity Session"
        title = re.sub(r"[#*`_\[\]]", "", title).strip()

        meta = {
            "title": title or "Antigravity Pair Programming Session",
            "bot": "@achiAgyBot",
            "engine": "Gemini 2.5 Pro / Flash",
            "summary": f"Antigravity session covering {title}.",
            "tags": ["tgdb", "antigravity", "pair-programming", "achios"],
            "timestamp": start_ts or dt.datetime.now(LOCAL_TZ),
        }

        return meta, messages

    except Exception as e:
        print(f"Error parsing Antigravity session {transcript_path}: {e}", file=sys.stderr)
        return None


def export_recent_sessions(days_lookback: int = 2) -> int:
    """Scan and export recent Claude Code and Antigravity sessions to achiMem/tgdb/."""
    exported_count = 0
    now = dt.datetime.now(LOCAL_TZ)
    cutoff = now - dt.timedelta(days=days_lookback)

    # 1. Sweep Claude Code projects
    if CLAUDE_PROJECTS_DIR.exists():
        for project_dir in CLAUDE_PROJECTS_DIR.iterdir():
            if not project_dir.is_dir():
                continue
            for jsonl_file in project_dir.glob("*.jsonl"):
                mtime = dt.datetime.fromtimestamp(jsonl_file.stat().st_mtime, tz=LOCAL_TZ)
                if mtime < cutoff:
                    continue
                parsed = parse_claude_jsonl(jsonl_file)
                if not parsed:
                    continue
                meta, messages = parsed
                note_content = format_tgdb_note(meta, messages)
                write_tgdb_session(DEFAULT_VAULT_PATH, meta["bot"], jsonl_file.stem, note_content, timestamp=meta["timestamp"])
                exported_count += 1

    # 2. Sweep Antigravity CLI Brain sessions
    if AGY_BRAIN_DIR.exists():
        for conv_dir in AGY_BRAIN_DIR.iterdir():
            if not conv_dir.is_dir():
                continue
            transcript_file = conv_dir / ".system_generated" / "logs" / "transcript.jsonl"
            if not transcript_file.exists():
                continue
            mtime = dt.datetime.fromtimestamp(transcript_file.stat().st_mtime, tz=LOCAL_TZ)
            if mtime < cutoff:
                continue
            parsed = parse_antigravity_transcript(transcript_file)
            if not parsed:
                continue
            meta, messages = parsed
            note_content = format_tgdb_note(meta, messages)
            write_tgdb_session(DEFAULT_VAULT_PATH, meta["bot"], conv_dir.name, note_content, timestamp=meta["timestamp"])
            exported_count += 1

    return exported_count


def main() -> int:
    exported = export_recent_sessions(days_lookback=2)
    print(f"Exported {exported} total session(s) (Claude + Antigravity) to achiMem/tgdb/.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
