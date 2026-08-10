import json

import achimem_capture as cap
import pytest


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
