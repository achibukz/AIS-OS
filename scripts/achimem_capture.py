#!/usr/bin/env python3
"""SessionEnd hook. Captures an achiOS session into the achiMem vault."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path

VAULT = Path.home() / "Documents" / "Obsidian" / "achiMem"
SESSIONS = VAULT / "raw" / "sessions"
WRITE_TOOLS = {"Edit", "Write", "NotebookEdit"}
TURN_THRESHOLD = 6
GIT_COMMIT_RE = re.compile(r"\bgit\s+(?:-C\s+\S+\s+)?commit\b")


@dataclass
class TranscriptSummary:
    turns: int = 0
    files_touched: list[str] = field(default_factory=list)
    commits: int = 0
    first_prompt: str = ""
    branch: str = ""
    digest_lines: list[str] = field(default_factory=list)


def _handle_assistant(entry, summary, seen):
    summary.turns += 1
    summary.branch = entry.get("gitBranch") or summary.branch
    for block in entry.get("message", {}).get("content") or []:
        if not isinstance(block, dict):
            continue
        if block.get("type") == "text":
            text = (block.get("text") or "").strip()
            if text:
                summary.digest_lines.append(f"A: {text}")
        elif block.get("type") == "tool_use":
            name = block.get("name") or ""
            inp = block.get("input") or {}
            if name in WRITE_TOOLS:
                target = inp.get("file_path") or inp.get("notebook_path") or ""
                if target and target not in seen:
                    seen.add(target)
                    summary.files_touched.append(target)
            if name == "Bash" and GIT_COMMIT_RE.search(str(inp.get("command", ""))):
                summary.commits += 1
            summary.digest_lines.append(f"T: {name} {json.dumps(inp, default=str)[:200]}")


def _handle_user(entry, summary):
    if entry.get("promptSource") != "typed":
        return
    content = entry.get("message", {}).get("content")
    if not isinstance(content, str) or not content.strip():
        return
    text = content.strip()
    if not summary.first_prompt:
        summary.first_prompt = text
    summary.digest_lines.append(f"U: {text}")


def parse_transcript(path) -> TranscriptSummary:
    summary = TranscriptSummary()
    seen: set[str] = set()
    try:
        raw = Path(path).read_text(encoding="utf-8", errors="replace")
    except OSError:
        return summary
    for line in raw.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            entry = json.loads(line)
        except json.JSONDecodeError:
            continue
        if not isinstance(entry, dict) or entry.get("isSidechain"):
            continue
        if entry.get("type") == "assistant":
            _handle_assistant(entry, summary, seen)
        elif entry.get("type") == "user":
            _handle_user(entry, summary)
    return summary


def should_capture(summary: TranscriptSummary) -> bool:
    return bool(summary.files_touched) or summary.commits > 0 or summary.turns >= TURN_THRESHOLD
