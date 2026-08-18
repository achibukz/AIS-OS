#!/usr/bin/env python3
"""Universal Transcript Exporter for achiOS.

Exports conversation transcripts from BOTH:
1. Claude Code CLI/Telegram sessions (~/.claude/projects/)
2. Antigravity CLI/Telegram sessions (~/.gemini/antigravity-cli/brain/)

Sanitizes secrets, strips noisy intermediate tool execution dumps,
and writes clean, structured Markdown notes with key takeaways into:
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


def clean_title(prompt: str, fallback: str = "Session") -> str:
    """Generate a clean, readable note title from the first prompt."""
    if not prompt:
        return fallback
    # Strip XML tags
    clean = re.sub(r"<[^>]+>", "", prompt)
    # Strip leading markdown symbols, headers, bullet points, emojis
    clean = re.sub(
        r"^[\s#*`_>\-\U00010000-\U0010ffff\u2600-\u27ff\u2b50-\u2b55]+", "", clean
    ).strip()
    # Take the first line
    clean = clean.splitlines()[0].strip()
    # Strip quotes or punctuation around
    clean = clean.strip("\"'[]()`*# ")
    if not clean:
        return fallback
    # Truncate at word boundary near 65 chars
    if len(clean) > 65:
        clean = clean[:65].rsplit(" ", 1)[0].strip()
    return clean or fallback


def clean_claude_text(text: str) -> str:
    """Strip XML tags, skill definitions, and internal tool logs from Claude text."""
    if not text:
        return ""

    # Extract user text from <channel ...> wrapper if present
    channel_match = re.search(r"<channel[^>]*>(.*?)</channel>", text, re.DOTALL)
    if channel_match:
        text = channel_match.group(1).strip()

    # Remove internal command & system tags
    text = re.sub(r"<command-message>.*?</command-message>", "", text, flags=re.DOTALL)
    text = re.sub(r"<command-name>.*?</command-name>", "", text, flags=re.DOTALL)
    text = re.sub(r"<command-args>.*?</command-args>", "", text, flags=re.DOTALL)
    text = re.sub(r"<local-command-[^>]+>.*?</local-command-[^>]+>", "", text, flags=re.DOTALL)
    text = re.sub(r"<system>.*?</system>", "", text, flags=re.DOTALL)
    text = re.sub(r"<persisted-output>.*?</persisted-output>", "", text, flags=re.DOTALL)
    text = re.sub(r"<EXTREMELY_IMPORTANT>.*?</EXTREMELY_IMPORTANT>", "", text, flags=re.DOTALL)
    text = re.sub(r"<SUBAGENT-STOP>.*?</SUBAGENT-STOP>", "", text, flags=re.DOTALL)

    # Discard pure system skill instruction dumps
    stripped = text.strip()
    if stripped.startswith("Base directory for this skill:") or stripped.startswith("# /"):
        return ""

    # Clean residual multiple blank lines
    cleaned = re.sub(r"\n{3,}", "\n\n", text).strip()
    return cleaned


def clean_antigravity_text(text: str) -> str:
    """Strip system envelopes, settings changes, and thought tags from Antigravity text."""
    if not text:
        return ""

    # Extract user prompt from <USER_REQUEST> wrapper if present
    user_match = re.search(r"<USER_REQUEST>(.*?)</USER_REQUEST>", text, re.DOTALL)
    if user_match:
        text = user_match.group(1).strip()

    # Strip system noise
    text = re.sub(r"<SYSTEM_MESSAGE>.*?</SYSTEM_MESSAGE>", "", text, flags=re.DOTALL)
    text = re.sub(r"<USER_SETTINGS_CHANGE>.*?</USER_SETTINGS_CHANGE>", "", text, flags=re.DOTALL)
    text = re.sub(r"<ADDITIONAL_METADATA>.*?</ADDITIONAL_METADATA>", "", text, flags=re.DOTALL)
    text = re.sub(r"<thought>.*?</thought>", "", text, flags=re.DOTALL)

    cleaned = re.sub(r"\n{3,}", "\n\n", text).strip()
    return cleaned


def extract_takeaways_and_tasks(messages: list[dict]) -> tuple[list[str], list[str]]:
    """Extract action items (- [ ]) and decision takeaways from messages."""
    takeaways: list[str] = []
    tasks: list[str] = []

    for msg in messages:
        c = msg.get("content", "")
        # Extract action items
        for t in re.findall(r"^\s*-\s*\[\s*\]\s+(.+)$", c, re.MULTILINE):
            t_clean = t.strip()
            if t_clean and t_clean not in tasks:
                tasks.append(t_clean)

        # Extract highlighted decisions / takeaways
        for d in re.findall(r"^\s*(?:\*|-)\s+\*\*([^*]+)\*\*:\s*(.+)$", c, re.MULTILINE):
            dec_clean = f"{d[0]}: {d[1]}".strip()
            if dec_clean and dec_clean not in takeaways:
                takeaways.append(dec_clean)

    return takeaways[:6], tasks[:6]


def parse_claude_jsonl(file_path: Path) -> tuple[dict, list[dict], list[str], list[str]] | None:
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

            entry_type = entry.get("type")
            msg_obj = entry.get("message", {})
            content = msg_obj.get("content", "")

            if isinstance(content, list):
                content = " ".join(b.get("text", "") for b in content if isinstance(b, dict))
            raw_text = str(content).strip()
            if not raw_text:
                continue

            cleaned = clean_claude_text(raw_text)
            if not cleaned:
                continue

            if entry_type == "user":
                if not first_prompt:
                    first_prompt = cleaned
                    if "timestamp" in entry:
                        try:
                            start_ts = dt.datetime.fromisoformat(
                                entry["timestamp"].replace("Z", "+00:00")
                            ).astimezone(LOCAL_TZ)
                        except Exception:
                            pass
                messages.append({"role": "user", "content": cleaned})

            elif entry_type == "assistant":
                messages.append({"role": "assistant", "content": cleaned})

        if not messages:
            return None

        cwd = str(file_path)
        if "schoolmem" in cwd.lower():
            bot_name = "@schoMemBot"
            domain = "schoolmem"
        else:
            bot_name = "@achiOSClaudeBot"
            domain = "achios"

        title = clean_title(first_prompt, fallback="Claude Code Session")
        takeaways, tasks = extract_takeaways_and_tasks(messages)

        summary = f"{bot_name} session covering {title}."
        if takeaways:
            summary = f"{title}. Key outcome: {takeaways[0]}"

        meta = {
            "title": title,
            "bot": bot_name,
            "engine": "Claude Sonnet",
            "summary": summary,
            "tags": ["tgdb", "claude", domain],
            "timestamp": start_ts or dt.datetime.now(LOCAL_TZ),
        }

        return meta, messages, takeaways, tasks

    except Exception as e:
        print(f"Error parsing Claude session {file_path.name}: {e}", file=sys.stderr)
        return None


def parse_antigravity_transcript(
    transcript_path: Path,
) -> tuple[dict, list[dict], list[str], list[str]] | None:
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
                clean_user = clean_antigravity_text(content)
                if clean_user:
                    if not first_prompt:
                        first_prompt = clean_user
                        if "created_at" in entry:
                            try:
                                start_ts = dt.datetime.fromisoformat(
                                    entry["created_at"].replace("Z", "+00:00")
                                ).astimezone(LOCAL_TZ)
                            except Exception:
                                pass
                    messages.append({"role": "user", "content": clean_user})

            # Assistant response (skip intermediate tool execution outputs)
            elif entry_type == "PLANNER_RESPONSE":
                # If it is only a tool call without assistant message text, skip
                tool_calls = entry.get("tool_calls")
                if isinstance(content, str) and content.strip():
                    clean_resp = clean_antigravity_text(content)
                    if clean_resp:
                        messages.append({"role": "assistant", "content": clean_resp})
                elif not tool_calls and isinstance(content, str) and content.strip():
                    clean_resp = clean_antigravity_text(content)
                    if clean_resp:
                        messages.append({"role": "assistant", "content": clean_resp})

        if not messages:
            return None

        conv_id = transcript_path.parent.parent.name
        title = clean_title(first_prompt, fallback="Antigravity Session")
        takeaways, tasks = extract_takeaways_and_tasks(messages)

        summary = f"Antigravity session covering {title}."
        if takeaways:
            summary = f"{title}. Key outcome: {takeaways[0]}"

        meta = {
            "title": title,
            "bot": "@achiAgyBot",
            "engine": "Gemini 2.5 Pro / Flash",
            "summary": summary,
            "tags": ["tgdb", "antigravity", "pair-programming", "achios"],
            "timestamp": start_ts or dt.datetime.now(LOCAL_TZ),
        }

        return meta, messages, takeaways, tasks

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
                meta, messages, takeaways, tasks = parsed
                note_content = format_tgdb_note(meta, messages, takeaways=takeaways, tasks=tasks)
                write_tgdb_session(
                    DEFAULT_VAULT_PATH,
                    meta["bot"],
                    jsonl_file.stem,
                    note_content,
                    timestamp=meta["timestamp"],
                )
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
            meta, messages, takeaways, tasks = parsed
            note_content = format_tgdb_note(meta, messages, takeaways=takeaways, tasks=tasks)
            write_tgdb_session(
                DEFAULT_VAULT_PATH,
                meta["bot"],
                conv_dir.name,
                note_content,
                timestamp=meta["timestamp"],
            )
            exported_count += 1

    return exported_count


def main() -> int:
    exported = export_recent_sessions(days_lookback=2)
    print(f"Exported {exported} total session(s) (Claude + Antigravity) to achiMem/tgdb/.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
