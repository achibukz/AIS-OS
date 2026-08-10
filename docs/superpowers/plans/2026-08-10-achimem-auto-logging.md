# achiOS → achiMem Auto-Logging Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Automatically capture every substantive achiOS session into the achiMem Obsidian vault, without letting unattended automation write unverified facts into the vault's `wiki/` branch.

**Architecture:** A SessionEnd hook parses the session transcript, gates on whether real work happened, writes a mechanical stub into `achiMem/raw/sessions/`, appends to `log.md`, commits, then detaches a background re-invocation of itself that calls Haiku to enrich the stub into a real summary. A SessionStart hook reads those files back as a recall digest, replacing claude-mem inside this repo. Anything reaching `wiki/` prose stays behind achiMem's two-phase human INGEST gate.

**Tech Stack:** Python 3 stdlib only (no runtime dependencies), `uv` for the test runner, pytest, git, Claude Code hooks.

**Spec:** `docs/superpowers/specs/2026-08-10-achimem-auto-logging-design.md`

## Global Constraints

- **Vault path:** `~/Documents/Obsidian/achiMem` — resolve via `Path.home()`, never hardcode `/Users/achibukz`.
- **Python:** stdlib only in both scripts. No third-party imports at runtime.
- **Package management:** `uv` only. Never `pip install`. Tests run as `uv run --with pytest pytest`.
- **Hooks never break a session.** Both scripts wrap `main()` and always `sys.exit(0)`.
- **Recursion guard:** both `ACHIMEM_CAPTURE=1` and `CLAUDE_MEM_INTERNAL=1` are checked before any work, and both are set on every subprocess spawned.
- **Haiku gets no tools.** Enrichment is `claude -p` with output captured from stdout; the Python wrapper performs every file write.
- **Enrich model:** `claude-haiku-4-5-20251001` exactly.
- **Turn threshold:** 6.
- **Git staging is path-scoped.** Never `git add -A` in the vault — it would sweep up Aki's unsaved Obsidian edits.
- **No comments in code** unless the *why* is non-obvious (per `~/.claude/CLAUDE.md`).
- **No `Co-Authored-By` trailers** on any commit.
- **Prose written into the vault** follows achiMem voice: terse, no em dashes except the `decision — why` separator.

---

## File Structure

| File | Responsibility |
|---|---|
| `scripts/achimem_capture.py` | SessionEnd hook. Transcript parsing, gate, stub write, log append, commit, detached enrich spawn, and the `--enrich` mode itself. |
| `scripts/achimem_recall.py` | SessionStart hook. Reads `raw/sessions/`, emits `additionalContext`. Pure read, no LLM, no network. |
| `tests/conftest.py` | Puts `scripts/` on `sys.path`. |
| `tests/test_achimem_capture.py` | Parser, gate, stub, enrich, log tests. |
| `tests/test_achimem_recall.py` | Recall digest tests. |
| `.claude/settings.json` | Hook registration. |

Both scripts are single-file by design: they are hooks, invoked as executables, and splitting a ~200-line hook across modules would add import fragility for no benefit. Every function in them is a pure, importable unit so the tests reach them directly.

---

### Task 1: achiMem version control and capture folder

No tests — this is filesystem scaffolding that later tasks depend on. Verified by inspection.

**Files:**
- Create: `~/Documents/Obsidian/achiMem/.gitignore`
- Create: `~/Documents/Obsidian/achiMem/raw/sessions/.gitkeep`

- [ ] **Step 1: Confirm the vault is not already a repo**

```bash
git -C ~/Documents/Obsidian/achiMem rev-parse --is-inside-work-tree
```

Expected: `fatal: not a git repository`. If it prints `true`, stop and report — the vault is already tracked and this task must be skipped.

- [ ] **Step 2: Write the .gitignore**

Create `~/Documents/Obsidian/achiMem/.gitignore`:

```gitignore
.DS_Store
.obsidian/workspace.json
.obsidian/workspace-mobile.json
.obsidian/cache
.trash/
```

- [ ] **Step 3: Create the sessions folder**

```bash
mkdir -p ~/Documents/Obsidian/achiMem/raw/sessions
touch ~/Documents/Obsidian/achiMem/raw/sessions/.gitkeep
```

- [ ] **Step 4: Initialise and make the baseline commit**

```bash
git -C ~/Documents/Obsidian/achiMem init
git -C ~/Documents/Obsidian/achiMem add -A
git -C ~/Documents/Obsidian/achiMem commit -m "achimem: baseline snapshot before auto-capture"
```

This is the one and only `git add -A` in the whole plan — a baseline of pre-existing state. Every later commit is path-scoped.

- [ ] **Step 5: Verify**

```bash
git -C ~/Documents/Obsidian/achiMem log --oneline
git -C ~/Documents/Obsidian/achiMem status --short
```

Expected: one commit, and a clean working tree (no output from `status`).

---

### Task 2: Transcript parsing and the capture gate

**Files:**
- Create: `scripts/achimem_capture.py`
- Create: `tests/conftest.py`
- Test: `tests/test_achimem_capture.py`

**Interfaces:**
- Consumes: nothing.
- Produces:
  - `TranscriptSummary` dataclass with fields `turns: int`, `files_touched: list[str]`, `commits: int`, `first_prompt: str`, `branch: str`, `digest_lines: list[str]`
  - `parse_transcript(path: str | Path) -> TranscriptSummary`
  - `should_capture(summary: TranscriptSummary) -> bool`
  - Module constants `WRITE_TOOLS`, `TURN_THRESHOLD`, `VAULT`, `SESSIONS`

Transcript format facts this task must honour, verified against a real transcript at
`~/.claude/projects/-Users-achibukz-Code-GitHub-AIS-OS/*.jsonl`:

- A real typed prompt is `{"type": "user", "promptSource": "typed", "message": {"content": "<str>"}}`.
- A tool result is *also* `type: "user"` but has `promptSource: null` and a **list** content. Counting those as prompts would be wrong.
- Subagent messages carry `isSidechain: true` and must be skipped entirely.
- Assistant messages carry `gitBranch` and a `message.content` list of blocks; tool calls are `{"type": "tool_use", "name": ..., "input": {...}}`.

- [ ] **Step 1: Write conftest.py**

Create `tests/conftest.py`:

```python
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
```

- [ ] **Step 2: Write the failing tests**

Create `tests/test_achimem_capture.py`:

```python
import json

import achimem_capture as cap


def write_transcript(tmp_path, *entries):
    path = tmp_path / "transcript.jsonl"
    path.write_text("\n".join(json.dumps(e) for e in entries), encoding="utf-8")
    return path


def assistant(*blocks, branch="main", sidechain=False):
    return {
        "type": "assistant",
        "isSidechain": sidechain,
        "gitBranch": branch,
        "message": {"content": list(blocks)},
    }


def typed(text):
    return {
        "type": "user",
        "isSidechain": False,
        "promptSource": "typed",
        "message": {"content": text},
    }


def tool_result(text):
    return {
        "type": "user",
        "isSidechain": False,
        "promptSource": None,
        "message": {"content": [{"type": "tool_result", "content": text}]},
    }


def tool_use(name, **inp):
    return {"type": "tool_use", "name": name, "input": inp}


def test_counts_assistant_turns(tmp_path):
    path = write_transcript(
        tmp_path,
        typed("hello"),
        assistant({"type": "text", "text": "hi"}),
        assistant({"type": "text", "text": "again"}),
    )
    assert cap.parse_transcript(path).turns == 2


def test_ignores_sidechain_messages(tmp_path):
    path = write_transcript(
        tmp_path,
        assistant({"type": "text", "text": "main"}),
        assistant({"type": "text", "text": "subagent"}, sidechain=True),
    )
    assert cap.parse_transcript(path).turns == 1


def test_tool_results_are_not_prompts(tmp_path):
    path = write_transcript(
        tmp_path,
        typed("the real ask"),
        tool_result("some command output"),
    )
    assert cap.parse_transcript(path).first_prompt == "the real ask"


def test_collects_written_files_without_duplicates(tmp_path):
    path = write_transcript(
        tmp_path,
        assistant(
            tool_use("Write", file_path="/a/one.py"),
            tool_use("Edit", file_path="/a/one.py"),
            tool_use("Edit", file_path="/a/two.py"),
            tool_use("Read", file_path="/a/three.py"),
        ),
    )
    assert cap.parse_transcript(path).files_touched == ["/a/one.py", "/a/two.py"]


def test_collects_notebook_edits(tmp_path):
    path = write_transcript(
        tmp_path,
        assistant(tool_use("NotebookEdit", notebook_path="/a/nb.ipynb")),
    )
    assert cap.parse_transcript(path).files_touched == ["/a/nb.ipynb"]


def test_detects_git_commits_in_bash(tmp_path):
    path = write_transcript(
        tmp_path,
        assistant(tool_use("Bash", command="git add -A && git commit -m x")),
        assistant(tool_use("Bash", command="git status")),
    )
    assert cap.parse_transcript(path).commits == 1


def test_captures_branch(tmp_path):
    path = write_transcript(tmp_path, assistant({"type": "text", "text": "x"}, branch="feat/y"))
    assert cap.parse_transcript(path).branch == "feat/y"


def test_malformed_line_does_not_crash(tmp_path):
    path = tmp_path / "t.jsonl"
    path.write_text('{"broken\n' + json.dumps(assistant({"type": "text", "text": "ok"})), encoding="utf-8")
    assert cap.parse_transcript(path).turns == 1


def test_missing_file_returns_empty_summary(tmp_path):
    summary = cap.parse_transcript(tmp_path / "nope.jsonl")
    assert summary.turns == 0
    assert summary.files_touched == []


def test_gate_rejects_short_readonly_session():
    summary = cap.TranscriptSummary(turns=3)
    assert cap.should_capture(summary) is False


def test_gate_accepts_single_file_write():
    summary = cap.TranscriptSummary(turns=1, files_touched=["/a/one.py"])
    assert cap.should_capture(summary) is True


def test_gate_accepts_commit_with_no_writes():
    summary = cap.TranscriptSummary(turns=2, commits=1)
    assert cap.should_capture(summary) is True


def test_gate_accepts_long_conversation():
    summary = cap.TranscriptSummary(turns=6)
    assert cap.should_capture(summary) is True
```

- [ ] **Step 3: Run the tests to verify they fail**

Run: `uv run --with pytest pytest tests/test_achimem_capture.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'achimem_capture'`

- [ ] **Step 4: Write the minimal implementation**

Create `scripts/achimem_capture.py`:

```python
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
```

- [ ] **Step 5: Run the tests to verify they pass**

Run: `uv run --with pytest pytest tests/test_achimem_capture.py -v`
Expected: PASS, 13 passed

- [ ] **Step 6: Commit**

```bash
git add scripts/achimem_capture.py tests/conftest.py tests/test_achimem_capture.py
git commit -m "feat(achimem): transcript parser and capture gate"
```

---

### Task 3: Stub writing, log append, and the hook entry point

**Files:**
- Modify: `scripts/achimem_capture.py`
- Test: `tests/test_achimem_capture.py`

**Interfaces:**
- Consumes: `TranscriptSummary`, `parse_transcript`, `should_capture`, `VAULT`, `SESSIONS` from Task 2.
- Produces:
  - `stub_text(summary, session_id, transcript, today) -> str`
  - `session_path(session_id, today) -> Path`
  - `append_log(path, summary, today) -> None`
  - `run_capture(payload) -> Path | None`
  - `main(argv, stdin_text) -> None`

`run_capture` returns the written path, or `None` when the gate rejected the session. It does not enrich or commit — Task 4 adds those calls.

- [ ] **Step 1: Write the failing tests**

Append to `tests/test_achimem_capture.py`:

```python
import pytest


@pytest.fixture
def vault(tmp_path, monkeypatch):
    root = tmp_path / "achiMem"
    (root / "raw" / "sessions").mkdir(parents=True)
    (root / "log.md").write_text("# Log\n", encoding="utf-8")
    monkeypatch.setattr(cap, "VAULT", root)
    monkeypatch.setattr(cap, "SESSIONS", root / "raw" / "sessions")
    return root


def test_stub_has_valid_frontmatter_and_status(vault):
    summary = cap.TranscriptSummary(turns=4, files_touched=["/a/one.py"], branch="main", first_prompt="do the thing")
    text = cap.stub_text(summary, "abcd1234efgh", "/t/abcd.jsonl", "2026-08-10")
    assert text.startswith("---\n")
    assert "status: unenriched\n" in text
    assert "type: session\n" in text
    assert "branch: main\n" in text
    assert "## Mechanical record" in text
    assert "do the thing" in text


def test_stub_truncates_long_opening_ask(vault):
    summary = cap.TranscriptSummary(turns=1, first_prompt="x" * 500)
    text = cap.stub_text(summary, "abcd1234", "/t/a.jsonl", "2026-08-10")
    assert "x" * 300 in text
    assert "x" * 301 not in text


def test_stub_handles_missing_branch(vault):
    summary = cap.TranscriptSummary(turns=1)
    assert "branch: unknown\n" in cap.stub_text(summary, "abcd1234", "/t/a.jsonl", "2026-08-10")


def test_session_path_uses_date_and_short_id(vault):
    path = cap.session_path("abcd1234efgh5678", "2026-08-10")
    assert path.name == "2026-08-10-achios-abcd1234.md"


def test_append_log_is_additive(vault):
    path = vault / "raw" / "sessions" / "2026-08-10-achios-abcd1234.md"
    path.write_text("stub", encoding="utf-8")
    cap.append_log(path, cap.TranscriptSummary(turns=7), "2026-08-10")
    cap.append_log(path, cap.TranscriptSummary(turns=7), "2026-08-10")
    body = (vault / "log.md").read_text(encoding="utf-8")
    assert body.startswith("# Log\n")
    assert body.count("[2026-08-10] session |") == 2


def test_run_capture_writes_file_when_gate_passes(vault, tmp_path):
    transcript = write_transcript(
        tmp_path,
        typed("build it"),
        assistant(tool_use("Write", file_path="/a/one.py")),
    )
    path = cap.run_capture({"session_id": "abcd1234", "transcript_path": str(transcript)})
    assert path is not None
    assert path.exists()
    assert "status: unenriched" in path.read_text(encoding="utf-8")


def test_run_capture_skips_when_gate_fails(vault, tmp_path):
    transcript = write_transcript(tmp_path, typed("what is the path to x"))
    assert cap.run_capture({"session_id": "abcd1234", "transcript_path": str(transcript)}) is None
    assert list((vault / "raw" / "sessions").glob("*.md")) == []


def test_run_capture_skips_without_transcript_path(vault):
    assert cap.run_capture({"session_id": "abcd1234"}) is None


def test_main_respects_achimem_capture_guard(vault, tmp_path, monkeypatch):
    monkeypatch.setenv("ACHIMEM_CAPTURE", "1")
    transcript = write_transcript(tmp_path, assistant(tool_use("Write", file_path="/a/one.py")))
    cap.main(["achimem_capture.py"], json.dumps({"session_id": "a", "transcript_path": str(transcript)}))
    assert list((vault / "raw" / "sessions").glob("*.md")) == []


def test_main_respects_claude_mem_internal_guard(vault, tmp_path, monkeypatch):
    monkeypatch.setenv("CLAUDE_MEM_INTERNAL", "1")
    transcript = write_transcript(tmp_path, assistant(tool_use("Write", file_path="/a/one.py")))
    cap.main(["achimem_capture.py"], json.dumps({"session_id": "a", "transcript_path": str(transcript)}))
    assert list((vault / "raw" / "sessions").glob("*.md")) == []


def test_main_survives_garbage_stdin(vault):
    cap.main(["achimem_capture.py"], "not json at all")
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `uv run --with pytest pytest tests/test_achimem_capture.py -v -k "stub or session_path or append_log or run_capture or main"`
Expected: FAIL with `AttributeError: module 'achimem_capture' has no attribute 'stub_text'`

- [ ] **Step 3: Write the implementation**

Add these imports to the top of `scripts/achimem_capture.py`, alongside the existing ones:

```python
import os
import subprocess
import sys
from datetime import date
```

Append to `scripts/achimem_capture.py`:

```python
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


def main(argv: list[str], stdin_text: str) -> None:
    if os.environ.get("ACHIMEM_CAPTURE") == "1" or os.environ.get("CLAUDE_MEM_INTERNAL") == "1":
        return
    try:
        payload = json.loads(stdin_text or "{}")
    except json.JSONDecodeError:
        return
    if not isinstance(payload, dict):
        return
    run_capture(payload)


if __name__ == "__main__":
    try:
        main(sys.argv, sys.stdin.read())
    except Exception as exc:  # a logging hook must never break the session
        print(f"achimem_capture: {exc}", file=sys.stderr)
    sys.exit(0)
```

- [ ] **Step 4: Run the full test file to verify it passes**

Run: `uv run --with pytest pytest tests/test_achimem_capture.py -v`
Expected: PASS, 24 passed

- [ ] **Step 5: Commit**

```bash
git add scripts/achimem_capture.py tests/test_achimem_capture.py
git commit -m "feat(achimem): stub writing, log append, hook entry point"
```

---

### Task 4: Haiku enrichment and path-scoped commits

**Files:**
- Modify: `scripts/achimem_capture.py`
- Test: `tests/test_achimem_capture.py`

**Interfaces:**
- Consumes: everything from Tasks 2 and 3.
- Produces:
  - `build_digest(summary, limit=DIGEST_LIMIT) -> str`
  - `enrich(path, runner=subprocess.run) -> bool`
  - `commit(paths, message, runner=subprocess.run) -> bool`
  - `spawn_enrich(path) -> None`
  - Module constants `ENRICH_MODEL`, `DIGEST_LIMIT`, `ENRICH_PROMPT`

`enrich` re-reads the transcript path out of the stub's own frontmatter, so it is
re-runnable standalone. That is what makes `--enrich` usable both as the detached
background call and as the skill's "process pending" mode.

`runner` is injected so tests never shell out.

- [ ] **Step 1: Write the failing tests**

Append to `tests/test_achimem_capture.py`:

```python
import subprocess
import types


class FakeRunner:
    def __init__(self, stdout="", returncode=0, exc=None):
        self.stdout = stdout
        self.returncode = returncode
        self.exc = exc
        self.calls = []

    def __call__(self, cmd, **kwargs):
        self.calls.append((cmd, kwargs))
        if self.exc:
            raise self.exc
        return types.SimpleNamespace(stdout=self.stdout, stderr="", returncode=self.returncode)


def make_stub(vault, tmp_path, transcript=None):
    if transcript is None:
        transcript = write_transcript(
            tmp_path,
            typed("build it"),
            assistant(tool_use("Write", file_path="/a/one.py")),
        )
    return cap.run_capture({"session_id": "abcd1234", "transcript_path": str(transcript)})


def test_build_digest_keeps_the_tail_when_over_limit():
    summary = cap.TranscriptSummary(digest_lines=["A: " + "x" * 100 for _ in range(50)])
    digest = cap.build_digest(summary, limit=200)
    assert len(digest) == 200
    assert digest.endswith("x")


def test_enrich_replaces_body_and_flips_status(vault, tmp_path):
    path = make_stub(vault, tmp_path)
    runner = FakeRunner(stdout="## What happened\n- Wrote the parser\n")
    assert cap.enrich(path, runner=runner) is True
    body = path.read_text(encoding="utf-8")
    assert "status: enriched" in body
    assert "status: unenriched" not in body
    assert "## Mechanical record" not in body
    assert "- Wrote the parser" in body
    assert body.startswith("---\n")


def test_enrich_sets_both_recursion_guards(vault, tmp_path):
    path = make_stub(vault, tmp_path)
    runner = FakeRunner(stdout="## What happened\n- x\n")
    cap.enrich(path, runner=runner)
    env = runner.calls[0][1]["env"]
    assert env["ACHIMEM_CAPTURE"] == "1"
    assert env["CLAUDE_MEM_INTERNAL"] == "1"


def test_enrich_uses_the_pinned_haiku_model(vault, tmp_path):
    path = make_stub(vault, tmp_path)
    runner = FakeRunner(stdout="## What happened\n- x\n")
    cap.enrich(path, runner=runner)
    assert cap.ENRICH_MODEL in runner.calls[0][0]


def test_enrich_leaves_stub_intact_on_nonzero_exit(vault, tmp_path):
    path = make_stub(vault, tmp_path)
    before = path.read_text(encoding="utf-8")
    assert cap.enrich(path, runner=FakeRunner(stdout="junk", returncode=1)) is False
    assert path.read_text(encoding="utf-8") == before


def test_enrich_leaves_stub_intact_on_empty_output(vault, tmp_path):
    path = make_stub(vault, tmp_path)
    before = path.read_text(encoding="utf-8")
    assert cap.enrich(path, runner=FakeRunner(stdout="   ")) is False
    assert path.read_text(encoding="utf-8") == before


def test_enrich_leaves_stub_intact_on_timeout(vault, tmp_path):
    path = make_stub(vault, tmp_path)
    before = path.read_text(encoding="utf-8")
    runner = FakeRunner(exc=subprocess.TimeoutExpired(cmd="claude", timeout=1))
    assert cap.enrich(path, runner=runner) is False
    assert path.read_text(encoding="utf-8") == before


def test_enrich_returns_false_when_claude_is_missing(vault, tmp_path):
    path = make_stub(vault, tmp_path)
    assert cap.enrich(path, runner=FakeRunner(exc=FileNotFoundError())) is False


def test_commit_is_path_scoped(vault, tmp_path):
    path = make_stub(vault, tmp_path)
    runner = FakeRunner()
    cap.commit([path, vault / "log.md"], "achimem: auto-capture test", runner=runner)
    add_cmd = runner.calls[0][0]
    assert "-A" not in add_cmd
    assert "raw/sessions/" + path.name in add_cmd
    assert "log.md" in add_cmd


def test_commit_survives_git_failure(vault, tmp_path):
    path = make_stub(vault, tmp_path)
    assert cap.commit([path], "msg", runner=FakeRunner(exc=OSError())) is False


def test_enrich_mode_dispatches_from_main(vault, tmp_path, monkeypatch):
    path = make_stub(vault, tmp_path)
    seen = []
    monkeypatch.setattr(cap, "enrich", lambda p, **kw: seen.append(p) or True)
    monkeypatch.setattr(cap, "commit", lambda *a, **kw: True)
    cap.main(["achimem_capture.py", "--enrich", str(path)], "")
    assert seen == [path]
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `uv run --with pytest pytest tests/test_achimem_capture.py -v -k "digest or enrich or commit"`
Expected: FAIL with `AttributeError: module 'achimem_capture' has no attribute 'build_digest'`

- [ ] **Step 3: Write the implementation**

Add these constants near the existing ones at the top of `scripts/achimem_capture.py`:

```python
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
```

Now replace the existing `main` with this version, which wires enrichment and commits in:

```python
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
```

The `--enrich` branch sits above the guard deliberately: the detached child runs with
`ACHIMEM_CAPTURE=1` set, and must still do its job.

- [ ] **Step 4: Run the full test file to verify it passes**

Run: `uv run --with pytest pytest tests/test_achimem_capture.py -v`
Expected: PASS, 35 passed

- [ ] **Step 5: Commit**

```bash
git add scripts/achimem_capture.py tests/test_achimem_capture.py
git commit -m "feat(achimem): haiku enrichment and path-scoped commits"
```

---

### Task 5: The recall hook

**Files:**
- Create: `scripts/achimem_recall.py`
- Test: `tests/test_achimem_recall.py`

**Interfaces:**
- Consumes: the on-disk format written by Task 3 and Task 4. No Python imports from `achimem_capture`.
- Produces:
  - `headline(path) -> str`
  - `count_open_threads(paths) -> int`
  - `count_unenriched(paths) -> int`
  - `build_context() -> str`
  - `main() -> None` emitting `hookSpecificOutput.additionalContext` JSON on stdout

- [ ] **Step 1: Write the failing tests**

Create `tests/test_achimem_recall.py`:

```python
import json

import achimem_recall as recall
import pytest


@pytest.fixture
def sessions(tmp_path, monkeypatch):
    folder = tmp_path / "achiMem" / "raw" / "sessions"
    folder.mkdir(parents=True)
    monkeypatch.setattr(recall, "SESSIONS", folder)
    return folder


def enriched(folder, name, happened, threads=()):
    body = f'---\ntitle: "achiOS session"\nstatus: enriched\n---\n\n## What happened\n- {happened}\n'
    if threads:
        body += "\n## Open threads\n" + "".join(f"- {t}\n" for t in threads)
    (folder / name).write_text(body, encoding="utf-8")


def unenriched(folder, name, ask):
    (folder / name).write_text(
        f'---\ntitle: "achiOS session"\nstatus: unenriched\n---\n\n'
        f'## Mechanical record\n- Opening ask: "{ask}"\n',
        encoding="utf-8",
    )


def test_empty_vault_returns_placeholder(sessions):
    assert "No achiOS sessions logged yet" in recall.build_context()


def test_missing_folder_does_not_crash(tmp_path, monkeypatch):
    monkeypatch.setattr(recall, "SESSIONS", tmp_path / "nope")
    assert "No achiOS sessions logged yet" in recall.build_context()


def test_headline_prefers_first_what_happened_bullet(sessions):
    enriched(sessions, "2026-08-09-achios-aaaa1111.md", "wired the capture hook")
    assert recall.headline(sessions / "2026-08-09-achios-aaaa1111.md") == "wired the capture hook"


def test_headline_falls_back_to_opening_ask(sessions):
    unenriched(sessions, "2026-08-09-achios-bbbb2222.md", "make the logging work")
    assert recall.headline(sessions / "2026-08-09-achios-bbbb2222.md") == "make the logging work"


def test_headline_is_truncated(sessions):
    enriched(sessions, "2026-08-09-achios-cccc3333.md", "y" * 200)
    assert len(recall.headline(sessions / "2026-08-09-achios-cccc3333.md")) == 70


def test_lists_three_most_recent_newest_first(sessions):
    for day in ("06", "07", "08", "09"):
        enriched(sessions, f"2026-08-{day}-achios-aaaa{day}11.md", f"work on {day}")
    context = recall.build_context()
    assert "work on 09" in context
    assert "work on 07" in context
    assert "work on 06" not in context
    assert context.index("work on 09") < context.index("work on 08")


def test_counts_open_threads_across_files(sessions):
    enriched(sessions, "2026-08-08-achios-aaaa1111.md", "a", threads=["one", "two"])
    enriched(sessions, "2026-08-09-achios-bbbb2222.md", "b", threads=["three"])
    assert "Open threads: 3" in recall.build_context()


def test_counts_unenriched(sessions):
    enriched(sessions, "2026-08-08-achios-aaaa1111.md", "a")
    unenriched(sessions, "2026-08-09-achios-bbbb2222.md", "b")
    assert "Unenriched logs: 1" in recall.build_context()


def test_main_emits_valid_hook_json(sessions, capsys):
    enriched(sessions, "2026-08-09-achios-aaaa1111.md", "did a thing")
    recall.main()
    payload = json.loads(capsys.readouterr().out)
    assert payload["hookSpecificOutput"]["hookEventName"] == "SessionStart"
    assert "did a thing" in payload["hookSpecificOutput"]["additionalContext"]
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `uv run --with pytest pytest tests/test_achimem_recall.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'achimem_recall'`

- [ ] **Step 3: Write the implementation**

Create `scripts/achimem_recall.py`:

```python
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
```

- [ ] **Step 4: Run all tests to verify they pass**

Run: `uv run --with pytest pytest tests/ -v`
Expected: PASS, 44 passed

- [ ] **Step 5: Commit**

```bash
git add scripts/achimem_recall.py tests/test_achimem_recall.py
git commit -m "feat(achimem): session recall hook"
```

---

### Task 6: Register the hooks and smoke-test end to end

**Files:**
- Create: `.claude/settings.json`

**Interfaces:**
- Consumes: `scripts/achimem_capture.py`, `scripts/achimem_recall.py`.
- Produces: live hooks for this repo only.

- [ ] **Step 1: Write the settings file**

Create `.claude/settings.json`:

```json
{
  "hooks": {
    "SessionEnd": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "python3 \"$CLAUDE_PROJECT_DIR/scripts/achimem_capture.py\"",
            "timeout": 60
          }
        ]
      }
    ],
    "SessionStart": [
      {
        "matcher": "startup|resume|clear",
        "hooks": [
          {
            "type": "command",
            "command": "python3 \"$CLAUDE_PROJECT_DIR/scripts/achimem_recall.py\"",
            "timeout": 15
          }
        ]
      }
    ]
  }
}
```

`$CLAUDE_PROJECT_DIR` is expanded by Claude Code to this repo's root, so the hooks stay
portable and fire only here.

- [ ] **Step 2: Smoke-test the recall hook directly**

```bash
python3 scripts/achimem_recall.py | python3 -m json.tool
```

Expected: valid JSON with `hookEventName: "SessionStart"`. On a fresh vault the context
reads `No achiOS sessions logged yet.`

- [ ] **Step 3: Smoke-test the capture hook against a real transcript, gate rejecting**

```bash
python3 -c "
import json, pathlib, tempfile
p = pathlib.Path(tempfile.mkdtemp()) / 't.jsonl'
p.write_text(json.dumps({'type':'user','promptSource':'typed','message':{'content':'hi'}}))
print(json.dumps({'session_id':'smoke0001','transcript_path':str(p)}))
" | python3 scripts/achimem_capture.py
ls ~/Documents/Obsidian/achiMem/raw/sessions/
```

Expected: no new file. A one-prompt session with no writes is below the gate.

- [ ] **Step 4: Smoke-test the capture hook with the gate passing**

This is the first step that spends anything: it triggers one real Haiku call and two real
commits in the vault. Step 8 cleans up the artifacts afterwards.

```bash
python3 -c "
import json, pathlib, tempfile
p = pathlib.Path(tempfile.mkdtemp()) / 't.jsonl'
rows = [
  {'type':'user','promptSource':'typed','message':{'content':'smoke test the capture hook'}},
  {'type':'assistant','isSidechain':False,'gitBranch':'main','message':{'content':[
    {'type':'text','text':'writing a file'},
    {'type':'tool_use','name':'Write','input':{'file_path':'/tmp/smoke.py'}}
  ]}},
]
p.write_text('\n'.join(json.dumps(r) for r in rows))
print(json.dumps({'session_id':'smoke0002','transcript_path':str(p)}))
" | python3 scripts/achimem_capture.py

ls ~/Documents/Obsidian/achiMem/raw/sessions/
```

Expected: one file named `<today>-achios-smoke000.md`.

- [ ] **Step 5: Verify the stub, the log entry, and the commit**

```bash
cat ~/Documents/Obsidian/achiMem/raw/sessions/*smoke000*.md
tail -5 ~/Documents/Obsidian/achiMem/log.md
git -C ~/Documents/Obsidian/achiMem log --oneline -3
```

Expected: frontmatter with `status:` set, a `## [<today>] session |` block at the end of
`log.md`, and a commit titled `achimem: auto-capture <today>-achios-smoke000`.

- [ ] **Step 6: Wait for enrichment and confirm the status flip**

```bash
sleep 45
grep -c "status: enriched" ~/Documents/Obsidian/achiMem/raw/sessions/*smoke000*.md
git -C ~/Documents/Obsidian/achiMem log --oneline -2
```

Expected: `1`, and a second commit titled `achimem: enrich …`. If it still reads
`unenriched`, that is the designed fallback, not a failure — record it and move on;
Task 10's "process pending" mode covers it.

- [ ] **Step 7: Confirm recall now reads the session back**

```bash
python3 scripts/achimem_recall.py
```

Expected: the digest lists the smoke session with a headline.

- [ ] **Step 8: Clean up the smoke artifacts**

```bash
rm ~/Documents/Obsidian/achiMem/raw/sessions/*smoke000*.md
git -C ~/Documents/Obsidian/achiMem add -u raw/sessions
git -C ~/Documents/Obsidian/achiMem commit -m "achimem: remove smoke test artifacts"
```

Leave the `log.md` entries — `log.md` is append-only by the vault's own rules.

- [ ] **Step 9: Commit**

```bash
git add .claude/settings.json
git commit -m "feat(achimem): register capture and recall hooks"
```

---

### Task 7: Disable claude-mem for this repo

**Files:**
- Modify: `~/.claude-mem/settings.json`

Anchoring matters here. `fL` in `worker-service.cjs` compiles each pattern through `ebt`
into `^…$`, then tests it against both the full cwd and its basename. The bare pattern
`AIS-OS` would therefore match the repo root only and miss every subdirectory, so both
entries are required.

- [ ] **Step 1: Back up the current settings**

```bash
cp ~/.claude-mem/settings.json ~/.claude-mem/settings.json.bak
```

- [ ] **Step 2: Set the exclusion**

```bash
python3 -c "
import json, pathlib
p = pathlib.Path.home() / '.claude-mem' / 'settings.json'
d = json.loads(p.read_text())
d['CLAUDE_MEM_EXCLUDED_PROJECTS'] = '~/Code/GitHub/AIS-OS,~/Code/GitHub/AIS-OS/**'
p.write_text(json.dumps(d, indent=2) + '\n')
print(d['CLAUDE_MEM_EXCLUDED_PROJECTS'])
"
```

Expected output: `~/Code/GitHub/AIS-OS,~/Code/GitHub/AIS-OS/**`

- [ ] **Step 3: Verify the pattern matches what it should, and nothing else**

This reimplements `ebt` and `fL` exactly, so it proves the real matcher's behaviour:

```bash
python3 -c "
import os, re
from pathlib import PurePosixPath

def ebt(pat):
    p = os.path.expanduser(pat).replace('\\\\', '/')
    p = re.sub(r'[.+^\${}()|\[\]\\\\]', lambda m: '\\\\' + m.group(0), p)
    p = p.replace('**', '<<G>>').replace('*', '[^/]*').replace('?', '[^/]').replace('<<G>>', '.*')
    return re.compile('^' + p + '\$')

pats = [ebt(x) for x in '~/Code/GitHub/AIS-OS,~/Code/GitHub/AIS-OS/**'.split(',')]
def excluded(cwd):
    base = PurePosixPath(cwd).name
    return any(p.match(cwd) or p.match(base) for p in pats)

home = os.path.expanduser('~')
for cwd, want in [
    (home + '/Code/GitHub/AIS-OS', True),
    (home + '/Code/GitHub/AIS-OS/scripts', True),
    (home + '/Code/GitHub/AIS-OS/docs/superpowers', True),
    (home + '/Code/GitHub/sfv-thesis', False),
    (home + '/Code/GitHub/career-ops', False),
    (home + '/Documents/Obsidian/achiMem', False),
]:
    got = excluded(cwd)
    print(('OK  ' if got == want else 'FAIL'), cwd, got)
"
```

Expected: six lines, all `OK`.

- [ ] **Step 4: Restart the claude-mem worker so it reloads settings**

```bash
node "$(ls -dt ~/.claude/plugins/cache/thedotmack/claude-mem/[0-9]*/ | head -1)scripts/bun-runner.js" \
     "$(ls -dt ~/.claude/plugins/cache/thedotmack/claude-mem/[0-9]*/ | head -1)scripts/worker-service.cjs" restart
```

If `restart` is not a supported verb, run `stop` then `start`. The worker also restarts on
the next SessionStart in any non-excluded project, so this step is a convenience.

- [ ] **Step 5: Record the change**

There is nothing to commit — this file lives outside the repo. Note in the task report
that `~/.claude-mem/settings.json.bak` holds the previous state.

---

### Task 8: Amend achiMem's constitution

**Files:**
- Modify: `~/Documents/Obsidian/achiMem/CLAUDE.md`
- Modify: `~/Documents/Obsidian/achiMem/wiki/personal/decisions.md`
- Modify: `~/Documents/Obsidian/achiMem/wiki/personal/achi-os.md`
- Modify: `~/Documents/Obsidian/achiMem/log.md`

Read `~/Documents/Obsidian/achiMem/CLAUDE.md` in full before editing. Match its existing
register: dense, tables where tables fit, no padding.

- [ ] **Step 1: Document the sessions folder**

In the Folder Layout code block, under the `raw/` line, add the nested entry so it reads:

```
├── raw/               ← dump zone: all raw sources go here, unsorted
│   └── sessions/      ← machine-owned: achiOS session captures
```

- [ ] **Step 2: Amend Behavior Rule 1**

Replace:

```
1. Never modify files in `raw/`.
```

with:

```
1. Never modify hand-dropped sources in `raw/`. The one exception is `raw/sessions/`, which
   is machine-owned: the achiOS capture pipeline may rewrite a file it created while that
   file is `status: unenriched`. Once `enriched`, it is immutable like any other source.
```

- [ ] **Step 3: Add the Automated writes section**

Insert a new section immediately after the Anti-Hallucination Rules section:

```markdown
---

## Automated writes

The achiOS capture pipeline (`AIS-OS/scripts/achimem_capture.py`, SessionEnd hook) writes
here without a human present. The allowlist is split by *who* is writing, because the
anti-hallucination rules bind an unattended model more tightly than they bind a session
with Aki in it.

| Target | Unattended (hook + Haiku) | In session (skill or agent) |
|---|---|---|
| `raw/sessions/*.md` | yes | yes |
| `log.md` | yes | yes |
| `wiki/personal/timeline.md` | no | yes, append row |
| `wiki/personal/decisions.md` | no | yes, append row |
| `wiki/personal/achi-os.md` | no | yes, snapshot block |
| `wiki/**` everything else | no | INGEST only |
| `index.md` | no | yes, when a page is created |

Why the split: `raw/` and `log.md` sit outside `wiki/`, so a bad entry there is noise. A
bad row in `wiki/personal/` is a fabricated fact about a real person, in the one branch
that promises there are none.

The enriching model is given **no tools**. Its markdown is captured from stdout and the
Python wrapper performs every write, so a model failure can produce bad text but never a
bad file operation.

Nothing is lost by deferring the `wiki/` rows. The SessionStart recall hook reports how
many sessions are still `unenriched`, and those rows get written on the next session with
Aki present.
```

- [ ] **Step 4: Extend the frontmatter spec**

In the Frontmatter block, change the `type` and `status` lines to:

```yaml
type: topic | profile | decision | index | log | session
status: active | planned | abandoned        # personal/ pages only
                                            # session pages: unenriched | enriched
```

- [ ] **Step 5: Add the session log action**

In the Log Format section, change the actions line to:

```
Actions: `ingest`, `query`, `update`, `decide`, `lint`, `restructure`, `note`, `correction`, `session`
```

Add below it:

```
`session` entries are written automatically by the achiOS capture hook. They point at a
file in `raw/sessions/` and are never the canonical record of anything — the session file
is.
```

- [ ] **Step 6: Add the Systems category to decisions.md**

Append a new category section to `~/Documents/Obsidian/achiMem/wiki/personal/decisions.md`,
matching the existing table shape (`Decision | Status | Date | Why | Detail`):

```markdown
## Systems

Build and tooling decisions live in `AIS-OS/decisions/log.md`, in prose, with alternatives
considered. A decision is promoted here only when it changes how Aki works, spends, or
decides **outside** that repo. One line, linking out. The reasoning is never duplicated.

| Decision | Status | Date | Why | Detail |
| --- | --- | --- | --- | --- |
| achiOS auto-logs sessions to achiMem | active | 2026-08-10 | Session work left no trace in the memory layer. Unattended capture goes to `raw/` and `log.md` only; anything reaching `wiki/` stays behind the INGEST gate. | [[achi-os]] |
| claude-mem disabled inside achiOS | active | 2026-08-10 | Two capture systems, one vault. achiMem's own recall hook replaces the claude-mem digest in that repo. Still on everywhere else. | [[achi-os]] |
```

Bump `updated:` in that file's frontmatter to `2026-08-10`.

- [ ] **Step 7: Resolve the open question in achi-os.md**

In `~/Documents/Obsidian/achiMem/wiki/personal/achi-os.md`, find the paragraph beginning
"**Relationship to this wiki:**" and replace its final sentence — the one saying the two
schemas "will need reconciling" and that ownership "should be clear" — with:

```markdown
**Decisions ownership, settled 2026-08-10:** `AIS-OS/decisions/log.md` is canonical for
build and tooling decisions, in prose, with alternatives considered.
`wiki/personal/decisions.md` is canonical for life and strategy decisions, as a
categorized table. A build decision is promoted here only when it changes how Aki works,
spends, or decides outside the repo, and the promotion is a one-line row linking back. See
the `## Systems` category in [[decisions]].
```

Then add a row to the agent-layer table in the same file:

```markdown
| `achimem_capture` / `achimem_recall` | achiMem + AIS-OS | SessionEnd capture and SessionStart recall for achiOS work |
```

Bump `updated:` to `2026-08-10`.

- [ ] **Step 8: Tick the open question**

In `~/Documents/Obsidian/achiMem/wiki/personal/open-questions.md`, find the item recording
that achiOS and achiMem both claim a `decisions/` concept and mark it resolved with the
date `2026-08-10`, following whatever convention that file already uses for resolved items.
Read the file first and match it.

- [ ] **Step 9: Run the broken-link scanner**

```bash
cd ~/Documents/Obsidian/achiMem && python3 -c "
import re
from pathlib import Path
wiki = Path('wiki')
targets = {p.stem for p in wiki.rglob('*.md')} | {'index', 'log'}
link_re = re.compile(r'!?\[\[([^\]]+)\]\]')
broken = []
for md in wiki.rglob('*.md'):
    for m in link_re.finditer(md.read_text(encoding='utf-8', errors='replace')):
        t = re.split(r'\\\\?\|', m.group(1), maxsplit=1)[0].split('#', 1)[0].strip()
        t = Path(t).stem
        if t and t not in targets:
            broken.append((str(md.relative_to(wiki)), m.group(1)))
print(f'Broken: {len(broken)}')
for f, raw in broken: print(f'  {f}: [[{raw}]]')
"
```

Expected: `Broken: 0`

- [ ] **Step 10: Append the vault log entry and commit**

Append to `~/Documents/Obsidian/achiMem/log.md`:

```markdown
## [2026-08-10] update | achiOS capture pipeline wired into the vault
- Schema: added the **Automated writes** section, the `raw/sessions/` folder, `type: session`, `status: unenriched | enriched`, and the `session` log action.
- Behavior rule 1 narrowed: hand-dropped `raw/` sources stay immutable; `raw/sessions/` is machine-owned and rewritable while unenriched.
- **Decisions ownership settled.** AIS-OS owns build decisions in prose; this wiki owns life decisions in a table. Promotion rule and `## Systems` category added. Closes the open question filed 2026-08-10.
- claude-mem excluded from the AIS-OS repo. achiMem's own recall hook replaces its digest there.
- Broken-link scan: `Broken: 0`.
- Pages updated: CLAUDE.md, personal/decisions, personal/achi-os, personal/open-questions
```

```bash
git -C ~/Documents/Obsidian/achiMem add CLAUDE.md log.md wiki/personal/decisions.md wiki/personal/achi-os.md wiki/personal/open-questions.md
git -C ~/Documents/Obsidian/achiMem commit -m "achimem: schema for automated writes, decisions ownership settled"
```

---

### Task 9: Document the contract in achiOS

**Files:**
- Modify: `CLAUDE.md`
- Modify: `decisions/log.md`

- [ ] **Step 1: Add the logging contract to CLAUDE.md**

Insert a new section immediately after the existing `## Connections` section in
`/Users/achibukz/Code/GitHub/AIS-OS/CLAUDE.md`:

```markdown
## Logging contract

Every substantive session here is captured into achiMem automatically. claude-mem is
**disabled in this repo** — achiMem is the only memory layer for achiOS work.

**Automatic.** A SessionEnd hook (`scripts/achimem_capture.py`) captures the session when
files were written, a commit was made, or the conversation ran 6+ turns. It writes a stub
to `achiMem/raw/sessions/`, appends to `achiMem/log.md`, commits, then enriches the stub
in the background with Haiku. A SessionStart hook (`scripts/achimem_recall.py`) reads
those files back as the recall digest at the top of each session.

**Manual.** `/log-achimem` (or "log this to achimem") captures mid-session and then offers
achiMem's INGEST Phase 1 so a session can become real wiki pages while context is live.

**What automation may never do.** Unattended writes go to `raw/sessions/` and `log.md`
only. Anything reaching `achiMem/wiki/` needs a human in the session — that is what keeps
the vault's anti-hallucination guarantee true. The full allowlist lives in achiMem's
`CLAUDE.md` under **Automated writes**.

**Decisions.** `decisions/log.md` here is canonical for build and tooling decisions, in
prose, with alternatives considered. `achiMem/wiki/personal/decisions.md` is canonical for
life and strategy decisions. When Aki makes a decision, write it here, then apply the
promotion test out loud: does this change how he works, spends, or decides *outside* this
repo? If yes, add a one-line row to achiMem's `## Systems` category linking back. Never
duplicate the reasoning.

**Pointers, not copies.** achiOS never duplicates achiMem content, and achiMem never
duplicates code or build rationale. One canonical home per fact.
```

- [ ] **Step 2: Append the build decision**

Append to `/Users/achibukz/Code/GitHub/AIS-OS/decisions/log.md`, matching the existing
prose format:

```markdown
## 2026-08-10 — achiOS session capture into achiMem

**Decision:** SessionEnd hook writes a mechanical stub into `achiMem/raw/sessions/`, appends to `achiMem/log.md`, commits path-scoped, then detaches a background Haiku call to enrich the stub. A SessionStart hook reads those files back as the recall digest. Unattended automation never writes to `achiMem/wiki/`. claude-mem is excluded from this repo via `CLAUDE_MEM_EXCLUDED_PROJECTS`.

**Why:** Session work was evaporating — decisions and discoveries lived only in transcripts. achiMem's constitution makes INGEST a two-phase human gate and forbids inventing facts about Aki, so unattended writes are routed to targets where those rules do not bind (`raw/`, `log.md`) and everything touching `wiki/` waits for a human. The stub is written before the model is called and `status` only flips on success, so a dead or garbage Haiku call leaves a valid unenriched file rather than a truncated one. Haiku is given no tools at all; its stdout is captured and Python does the writing, so a model failure can produce bad text but never a bad file operation. Would revisit the exclusion if achiMem's recall proves thinner in practice than claude-mem's observation database.

**Alternatives considered:** Raw drop only (safest, but the wiki stays stale until Aki sits down with it). Full auto-write into `wiki/` (fastest to a current wiki, but defeats the one mechanism that makes the vault trustworthy). Stop hook instead of SessionEnd (fires every turn, mostly noise). Synchronous enrichment (blocks session exit for 20-30s). Keeping claude-mem on alongside (pure redundancy, duplicate Haiku cost per session).

**Owner:** Aki.
```

- [ ] **Step 3: Verify the hook paths named in the docs actually exist**

```bash
ls scripts/achimem_capture.py scripts/achimem_recall.py .claude/settings.json
```

Expected: all three listed, no errors.

- [ ] **Step 4: Commit**

```bash
git add CLAUDE.md decisions/log.md
git commit -m "docs(achimem): logging contract and capture decision"
```

---

### Task 10: Rewrite the sync-achimem skill

**Files:**
- Modify: `~/.claude/skills/sync-achimem/SKILL.md`

Per Aki's standing rule ("Always use skill-creator for new skills"), drive this task through
the `skill-creator` workflow rather than hand-editing. Invoke it, and give it the
requirements below.

The current skill is **broken, not merely stale**: it writes to `wiki/work/`, which does not
exist in the vault. Its full-sync subagent prompt names
`wiki/work/internship-pipeline.md` and `wiki/work/aios-context.md`. Both must be re-homed.

- [ ] **Step 1: Read the current skill and the vault schema**

```bash
cat ~/.claude/skills/sync-achimem/SKILL.md
ls ~/Documents/Obsidian/achiMem/wiki/personal/
```

Note which pages already cover the internship pipeline — `wiki/personal/job-search.md` and
`wiki/personal/career-ops-hub.md` both exist and overlap what `wiki/work/internship-pipeline.md`
was going to hold. Prefer updating those over creating new pages; the vault's Behavior Rule
8 says so explicitly.

- [ ] **Step 2: Invoke skill-creator**

Use the `skill-creator` skill in edit mode against `~/.claude/skills/sync-achimem/`, with
these requirements.

**Path corrections.** Every `wiki/work/` reference becomes the correct existing page:
pipeline content goes to `wiki/personal/job-search.md`; achiOS state goes to
`wiki/personal/achi-os.md`. Do not create `wiki/work/`.

**Three modes**, dispatched from what Aki says:

| Mode | Triggers | Behaviour |
|---|---|---|
| capture | `/log-achimem`, "log this to achimem", "save this session" | Write the `raw/sessions/` file and the in-session allowlist rows now, then run INGEST Phase 1 |
| process pending | "process pending", or offered when recall reports unenriched logs | Enrich `status: unenriched` files |
| sync | "sync achimem", "update my notes" | Existing internship-pipeline sync, corrected paths |

**Capture mode** must: write the session file in the same frontmatter format
`achimem_capture.py` produces (`type: session`, `status: enriched`, matching field order);
append the `session` entry to `log.md`; append rows to `wiki/personal/timeline.md` and, if a
real decision was made, `wiki/personal/decisions.md` with a provenance tag; then **stop** and
run achiMem INGEST Phase 1 — surface 3-8 candidate pages across `studies/` and `personal/`,
state which branch each belongs in, suggest tags, and ask the four INGEST questions. Write
`wiki/` pages only after Aki picks. On writing a page: add it to `index.md`, add backlinks on
related pages, and re-run the broken-link scanner.

**Process pending mode** must run `python3 ~/Code/GitHub/AIS-OS/scripts/achimem_capture.py
--enrich <path>` per unenriched file, or write the summary directly when the transcript is
the current conversation.

**Constraints for the skill body:** never write to `wiki/` without an explicit pick from
Aki; always provenance-tag personal facts; use bare-basename wikilinks, never paths; commit
vault changes path-scoped with an `achimem:` message prefix.

- [ ] **Step 3: Verify no stale paths survive**

```bash
grep -n "wiki/work" ~/.claude/skills/sync-achimem/SKILL.md
```

Expected: no output.

- [ ] **Step 4: Verify the frontmatter description still triggers correctly**

```bash
head -20 ~/.claude/skills/sync-achimem/SKILL.md
```

Expected: the `description:` field still carries the original trigger phrases ("sync
achimem", "log this to achimem", "update my notes", "save this to my notes") plus the new
`/log-achimem` and "process pending". Losing the originals would silently break the
existing triggers.

- [ ] **Step 5: Report**

Nothing to commit — the skill lives outside the repo. Report which modes were written and
paste the final `description:` field so the trigger surface is reviewable.

---

## Verification

After every task, the full suite must be green:

```bash
uv run --with pytest pytest tests/ -v
```

Expected: 44 passed.

Final end-to-end check, in a fresh Claude Code session opened in this repo:

1. The session opens with an `── achiMem recall ──` block instead of the claude-mem digest.
2. Do real work (write a file), then exit.
3. `ls ~/Documents/Obsidian/achiMem/raw/sessions/` shows a new dated file.
4. After ~45 seconds it reads `status: enriched` with a real summary.
5. `git -C ~/Documents/Obsidian/achiMem log --oneline` shows both the capture and enrich commits.
6. Open a session in `~/Code/GitHub/sfv-thesis` and confirm the claude-mem digest still appears there.

Step 6 is the one that proves the exclusion is scoped and did not disable claude-mem globally.
