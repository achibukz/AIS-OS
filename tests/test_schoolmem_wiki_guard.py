import json
import os
import subprocess
from pathlib import Path

import pytest

GUARD = Path(__file__).resolve().parent.parent / "scripts" / "schoolmem_wiki_guard.py"
VAULT = Path.home() / "Documents" / "Obsidian" / "schoolMem"
WIKI = VAULT / "wiki"

MARKER = "ACHIOS_UNATTENDED_BOT"
FALLBACK = "TELEGRAM_STATE_DIR"


def bot_env(**overrides):
    """The environment telegram-bot.sh hands the guard."""
    env = os.environ.copy()
    env[MARKER] = "1"
    env[FALLBACK] = "/home/achibukz/.local/state/achios/schoolmem-bot"
    env.update(overrides)
    return env


def attended_env():
    """A session Aki is sitting in front of: neither marker present."""
    env = os.environ.copy()
    env.pop(MARKER, None)
    env.pop(FALLBACK, None)
    return env


def run(event, env=None):
    return subprocess.run(
        ["python3", str(GUARD)],
        input=json.dumps(event),
        capture_output=True,
        text=True,
        env=env if env is not None else bot_env(),
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
        ["python3", str(GUARD)],
        input="not json",
        capture_output=True,
        text=True,
        env=bot_env(),
    )
    assert decision(result) == "deny"


def test_deny_reason_points_at_the_inbox():
    payload = json.loads(run(write_event(WIKI / "index.md")).stdout)
    assert "inbox/" in payload["hookSpecificOutput"]["permissionDecisionReason"]


# --- session detection -------------------------------------------------------
# The hook is armed in <repo>/.claude/settings.json by telegram-bot.sh and outlives the
# bot, so every later interactive session inherits it. It must judge who is running.


@pytest.mark.parametrize("tool", ["Write", "Edit", "MultiEdit", "NotebookEdit"])
def test_attended_session_may_write_the_wiki(tool):
    target = WIKI / "AY2627-T1" / "_term-index.md"
    assert decision(run(write_event(target, tool), env=attended_env())) is None


def test_attended_session_may_run_bash_against_the_wiki():
    assert decision(run(bash_event("echo hi > wiki/log.md"), env=attended_env())) is None


def test_attended_session_is_not_denied_by_a_malformed_event():
    # main() checks the environment before touching stdin, so an unparseable event can
    # never lock Aki out of the vault he owns.
    result = subprocess.run(
        ["python3", str(GUARD)],
        input="not json",
        capture_output=True,
        text=True,
        env=attended_env(),
    )
    assert decision(result) is None


def test_explicit_marker_alone_is_enough():
    env = attended_env()
    env[MARKER] = "1"
    assert decision(run(write_event(WIKI / "index.md"), env=env)) == "deny"


def test_telegram_state_dir_alone_is_enough():
    # Fallback: a launcher predating the marker stays guarded rather than failing open.
    env = attended_env()
    env[FALLBACK] = "/home/achibukz/.local/state/achios/schoolmem-bot"
    assert decision(run(write_event(WIKI / "index.md"), env=env)) == "deny"


def test_marker_set_to_something_other_than_one_does_not_arm_it():
    env = attended_env()
    env[MARKER] = "0"
    assert decision(run(write_event(WIKI / "index.md"), env=env)) is None


# --- the variable-indirection hole -------------------------------------------
# The old pattern required the literal "wiki/" to sit next to the write verb, so a path
# held in a shell variable walked straight past it. This is how the AY2627-T1 scaffold
# copied four files into the vault on 2026-08-28 without tripping the guard.


@pytest.mark.parametrize(
    "command",
    [
        'SRC=wiki/AY2526-T3/x; DST=/tmp/y; cp "$SRC/CLAUDE.md" "$DST/"',
        'D=wiki/AY2627-T1; mkdir -p "$D/topics"',
        'F=wiki/index.md; sed -i "s/a/b/" "$F"',
        'B=wiki/log.md\ncat >> "$B" <<EOF\nhi\nEOF',
        "mkdir wiki/AY2627-T1",
        "touch wiki/AY2627-T1/.gitkeep",
        'python3 -c "open(\'wiki/index.md\', \'w\').write(\'x\')"',
        "find wiki/ -name '*.md' -delete",
        "rsync -a /tmp/x wiki/",
        "ln -s /tmp/x wiki/x",
    ],
)
def test_denies_indirect_and_previously_missed_writes(command):
    assert decision(run(bash_event(command))) == "deny"


def test_bash_denial_explains_the_coarseness():
    payload = json.loads(run(bash_event("cp a.md wiki/")).stdout)
    reason = payload["hookSpecificOutput"]["permissionDecisionReason"]
    assert "coarse" in reason


def test_still_allows_reads_that_mention_no_write_verb():
    for command in ["wc -l wiki/index.md", "head -20 wiki/log.md", "diff wiki/a wiki/b"]:
        assert decision(run(bash_event(command))) is None, command
