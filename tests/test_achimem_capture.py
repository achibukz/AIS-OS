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
