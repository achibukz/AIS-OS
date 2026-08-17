import json
import subprocess
from pathlib import Path

import pytest

GUARD = Path(__file__).resolve().parent.parent / "scripts" / "schoolmem_wiki_guard.py"
VAULT = Path.home() / "Documents" / "Obsidian" / "schoolMem"
WIKI = VAULT / "wiki"


def run(event):
    return subprocess.run(
        ["python3", str(GUARD)],
        input=json.dumps(event),
        capture_output=True,
        text=True,
    )


def decision(result):
    if not result.stdout.strip():
        return None
    return json.loads(result.stdout)["hookSpecificOutput"]["permissionDecision"]


def write_event(path, tool="Write"):
    return {"tool_name": tool, "tool_input": {"file_path": str(path)}, "cwd": str(VAULT)}


def bash_event(command):
    return {"tool_name": "Bash", "tool_input": {"command": command}, "cwd": str(VAULT)}


@pytest.mark.parametrize("tool", ["Write", "Edit", "MultiEdit", "NotebookEdit"])
def test_denies_writes_anywhere_under_wiki(tool):
    target = WIKI / "AY2526-T3" / "CSOPESY" / "topics" / "threads.md"
    assert decision(run(write_event(target, tool))) == "deny"


def test_denies_the_wiki_root_itself():
    assert decision(run(write_event(WIKI))) == "deny"


def test_denies_relative_paths_resolved_from_cwd():
    event = {
        "tool_name": "Write",
        "tool_input": {"file_path": "wiki/log.md"},
        "cwd": str(VAULT),
    }
    assert decision(run(event)) == "deny"


def test_denies_traversal_that_lands_in_wiki():
    event = {
        "tool_name": "Write",
        "tool_input": {"file_path": "inbox/../wiki/index.md"},
        "cwd": str(VAULT),
    }
    assert decision(run(event)) == "deny"


def test_allows_the_inbox():
    assert decision(run(write_event(VAULT / "inbox" / "2026-08-17-capture.md"))) is None


def test_allows_output_and_notes():
    assert decision(run(write_event(VAULT / "output" / "study-guide.md"))) is None
    assert decision(run(write_event(VAULT / "notes" / "sheet.pdf"))) is None


def test_allows_paths_outside_the_vault():
    assert decision(run(write_event(Path("/tmp/scratch.md")))) is None


def test_does_not_match_a_lookalike_sibling_directory():
    # `wiki-archive` starts with the protected name but is not inside it.
    assert decision(run(write_event(VAULT / "wiki-archive" / "old.md"))) is None


def test_reads_are_untouched():
    event = {"tool_name": "Read", "tool_input": {"file_path": str(WIKI / "index.md")}}
    assert decision(run(event)) is None


@pytest.mark.parametrize(
    "command",
    [
        "echo hi > wiki/log.md",
        "echo hi >> /home/achibukz/Documents/Obsidian/schoolMem/wiki/log.md",
        "rm -rf wiki/AY2526-T3",
        "mv inbox/a.md wiki/a.md",
        "cp a.md wiki/",
        "sed -i s/a/b/ wiki/index.md",
        "git checkout -- wiki/index.md",
    ],
)
def test_denies_bash_that_would_mutate_wiki(command):
    assert decision(run(bash_event(command))) == "deny"


@pytest.mark.parametrize(
    "command",
    [
        "grep -rn threads wiki/",
        "cat wiki/index.md",
        "ls wiki/",
        "echo hi > inbox/note.md",
        "git status",
    ],
)
def test_allows_bash_that_only_reads_wiki(command):
    assert decision(run(bash_event(command))) is None


def test_unparseable_input_fails_closed():
    result = subprocess.run(
        ["python3", str(GUARD)], input="not json", capture_output=True, text=True
    )
    assert decision(result) == "deny"


def test_deny_reason_points_at_the_inbox():
    payload = json.loads(run(write_event(WIKI / "index.md")).stdout)
    assert "inbox/" in payload["hookSpecificOutput"]["permissionDecisionReason"]
