#!/usr/bin/env python3
"""SessionEnd hook. Captures an achiOS session into the achiMem vault."""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path

VAULT = Path.home() / "Documents" / "Obsidian" / "achiMem"
SESSIONS = VAULT / "raw" / "sessions"
WRITE_TOOLS = {"Edit", "Write", "NotebookEdit"}
TURN_THRESHOLD = 6
GIT_COMMIT_RE = re.compile(r"\bgit\s+(?:-C\s+\S+\s+)?commit\b")
ENRICH_MODEL = "claude-haiku-4-5-20251001"
DIGEST_LIMIT = 50_000
ENRICH_TIMEOUT = 180
GIT_TIMEOUT = 30

ENRICH_PROMPT = """Summarise a Claude Code session from the achiOS repo for a personal
knowledge vault. Output GitHub-flavored markdown only. No preamble, no closing remarks.

Use exactly these section headings, omitting any section that would be empty:

## What happened
Two to five bullets. Past tense. Concrete.

## Decisions
One bullet per decision, formatted "decision — why". Real decisions only, not routine
steps. Omit the section entirely if none were made.

## Open threads
One bullet per unfinished item. Omit the section entirely if nothing is open.

## Files touched
The list given below, verbatim, as bullets.

Rules. Report only what the transcript shows. Never speculate about the user's intent,
plans, or feelings. Never state a fact about the user that is not in the transcript. Be
terse. Do not use em dashes except as the separator in the Decisions section.

Files touched: {files}

Transcript digest follows.

{digest}
"""


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


def session_path(session_id: str, today: str) -> Path:
    return SESSIONS / f"{today}-achios-{session_id[:8]}.md"


def stub_text(summary: TranscriptSummary, session_id: str, transcript: str, today: str) -> str:
    files = ", ".join(Path(f).name for f in summary.files_touched) or "none"
    ask = summary.first_prompt[:300].replace('"', "'")
    return (
        "---\n"
        f'title: "achiOS session — {today}"\n'
        "type: session\n"
        "status: unenriched\n"
        f"session_id: {session_id}\n"
        f"transcript: {transcript}\n"
        f"branch: {summary.branch or 'unknown'}\n"
        f"created: {today}\n"
        "tags: [achios, session]\n"
        "---\n"
        "\n"
        "## Mechanical record\n"
        f"- Files touched: {files}\n"
        f"- Commits: {summary.commits}\n"
        f"- Turns: {summary.turns}\n"
        f'- Opening ask: "{ask}"\n'
    )


def append_log(path: Path, summary: TranscriptSummary, today: str) -> None:
    entry = (
        f"\n## [{today}] session | achiOS session {path.stem[-8:]}\n"
        f"- Captured at session end. Turns: {summary.turns}. "
        f"Files touched: {len(summary.files_touched)}. Commits: {summary.commits}.\n"
        f"- Source: `raw/sessions/{path.name}`\n"
    )
    with (VAULT / "log.md").open("a", encoding="utf-8") as handle:
        handle.write(entry)


def run_capture(payload: dict) -> Path | None:
    transcript = payload.get("transcript_path") or ""
    if not transcript:
        return None
    summary = parse_transcript(transcript)
    if not should_capture(summary):
        return None
    session_id = payload.get("session_id") or "unknown"
    today = date.today().isoformat()
    SESSIONS.mkdir(parents=True, exist_ok=True)
    path = session_path(session_id, today)
    path.write_text(stub_text(summary, session_id, transcript, today), encoding="utf-8")
    append_log(path, summary, today)
    return path


def build_digest(summary: TranscriptSummary, limit: int = DIGEST_LIMIT) -> str:
    text = "\n".join(summary.digest_lines)
    return text[-limit:] if len(text) > limit else text


def _frontmatter_value(text: str, key: str) -> str:
    match = re.search(rf"^{re.escape(key)}:\s*(.+?)\s*$", text, re.M)
    return match.group(1) if match else ""


def enrich(path: Path, runner=subprocess.run) -> bool:
    text = path.read_text(encoding="utf-8")
    summary = parse_transcript(_frontmatter_value(text, "transcript"))
    prompt = ENRICH_PROMPT.format(
        files=", ".join(summary.files_touched) or "none",
        digest=build_digest(summary),
    )
    env = {**os.environ, "ACHIMEM_CAPTURE": "1", "CLAUDE_MEM_INTERNAL": "1"}
    try:
        result = runner(
            ["claude", "-p", "--model", ENRICH_MODEL],
            input=prompt,
            capture_output=True,
            text=True,
            env=env,
            timeout=ENRICH_TIMEOUT,
        )
    except (OSError, subprocess.SubprocessError):
        return False
    body = (result.stdout or "").strip()
    if result.returncode != 0 or not body:
        return False
    head = text.split("\n## Mechanical record", 1)[0]
    path.write_text(
        head.replace("status: unenriched", "status: enriched") + "\n" + body + "\n",
        encoding="utf-8",
    )
    return True


def commit(paths, message: str, runner=subprocess.run) -> bool:
    rels = [str(Path(p).relative_to(VAULT)) for p in paths if Path(p).exists()]
    if not rels:
        return False
    try:
        runner(["git", "-C", str(VAULT), "add", *rels], capture_output=True, timeout=GIT_TIMEOUT)
        runner(
            ["git", "-C", str(VAULT), "commit", "-m", message],
            capture_output=True,
            timeout=GIT_TIMEOUT,
        )
    except (OSError, subprocess.SubprocessError):
        return False
    return True


def spawn_enrich(path: Path) -> None:
    env = {**os.environ, "ACHIMEM_CAPTURE": "1", "CLAUDE_MEM_INTERNAL": "1"}
    try:
        subprocess.Popen(
            [sys.executable, str(Path(__file__).resolve()), "--enrich", str(path)],
            env=env,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True,
        )
    except OSError:
        pass


def main(argv: list[str], stdin_text: str) -> None:
    if argv[1:2] == ["--enrich"]:
        path = Path(argv[2])
        if enrich(path):
            commit([path], f"achimem: enrich {path.stem}")
        return
    if os.environ.get("ACHIMEM_CAPTURE") == "1" or os.environ.get("CLAUDE_MEM_INTERNAL") == "1":
        return
    try:
        payload = json.loads(stdin_text or "{}")
    except json.JSONDecodeError:
        return
    if not isinstance(payload, dict):
        return
    path = run_capture(payload)
    if path is None:
        return
    commit([path, VAULT / "log.md"], f"achimem: auto-capture {path.stem}")
    spawn_enrich(path)


if __name__ == "__main__":
    try:
        main(sys.argv, sys.stdin.read())
    except Exception as exc:  # a logging hook must never break the session
        print(f"achimem_capture: {exc}", file=sys.stderr)
    sys.exit(0)
