import json
import tomllib
from pathlib import Path

import pytest

import install_portable_agents as installer


def registry():
    return json.loads((installer.ROOT / "config/portable-agents.json").read_text())


@pytest.mark.parametrize("name", list(registry()))
def test_native_definitions_preserve_prompt_and_open_skill_access(name):
    entry = registry()[name]
    codex = tomllib.loads(installer.render(name, entry, "codex"))
    claude_text = installer.render(name, entry, "claude")
    claude = {key: json.loads(value) for key, value in (
        line.split(":", 1) for line in claude_text.split("---", 2)[1].strip().splitlines()
    )}
    assert set(codex) == {"name", "description", "developer_instructions"}
    assert set(claude) == {"name", "description", "model", "effort"}
    assert claude["model"] == "claude-sonnet-5-5"
    assert claude["effort"] == "high"
    assert codex["name"] == claude["name"] == name
    source = (installer.ROOT / "agents" / f"{name}.md").read_text().strip()
    assert source in codex["developer_instructions"]
    assert source in claude_text
    assert all(skill in codex["developer_instructions"] and skill in claude_text
               for skill in entry["skills"])


@pytest.mark.parametrize("text", [
    "", 'model = "parent"\n',
    '[agents]\nmax_threads = 4\ndefault_subagent_model = "old"\n',
    '[agents] # personal\ndefault_subagent_reasoning_effort = "low"\n[agents.explorer]\nconfig_file = "x.toml"\n',
    '[agents]\nmax_threads = 4',
    '[agents]',
])
def test_defaults_preserve_existing_settings(text):
    before = tomllib.loads(text)
    after_text = installer.codex_defaults(text)
    after = tomllib.loads(after_text)
    assert after["agents"]["default_subagent_model"] == "gpt-6.1-sol"
    assert after["agents"]["default_subagent_reasoning_effort"] == "medium"
    for key, value in before.items():
        if key != "agents":
            assert after[key] == value
    for key, value in before.get("agents", {}).items():
        if not key.startswith("default_subagent_"):
            assert after["agents"][key] == value
    assert installer.codex_defaults(after_text) == after_text


def test_install_is_idempotent_and_backs_up_config(tmp_path):
    config = tmp_path / ".codex/config.toml"
    config.parent.mkdir()
    original = 'model = "my-main-model"\nmodel_reasoning_effort = "low"\n'
    config.write_text(original)
    first = installer.install(tmp_path, ["codex", "claude"])
    backup = next(item["backup"] for item in first if item["path"] == str(config))
    assert Path(backup).read_text() == original
    assert tomllib.loads(config.read_text())["model_reasoning_effort"] == "low"
    assert len(first) == 2 * len(registry()) + 1
    assert all(item["status"] == "present" for item in installer.install(tmp_path, ["codex", "claude"]))


@pytest.mark.parametrize("kind", ["file", "directory", "symlink"])
def test_conflict_preflight_leaves_all_targets_untouched(tmp_path, kind):
    conflict = tmp_path / ".claude/agents/asta.md"
    conflict.parent.mkdir(parents=True)
    if kind == "file":
        conflict.write_text("my existing agent")
    elif kind == "directory":
        conflict.mkdir()
    else:
        conflict.symlink_to(tmp_path / "missing")
    with pytest.raises(ValueError, match="Existing agent left intact"):
        installer.install(tmp_path, ["codex", "claude"])
    assert not (tmp_path / ".codex").exists()
    assert list(conflict.parent.iterdir()) == [conflict]


def test_dry_run_writes_nothing(tmp_path):
    result = installer.install(tmp_path, ["codex", "claude"], dry_run=True)
    assert all(item["status"] == "planned" for item in result)
    assert list(tmp_path.iterdir()) == []


def test_invalid_config_is_rejected_before_agent_writes(tmp_path):
    config = tmp_path / ".codex/config.toml"
    config.parent.mkdir()
    config.write_text("[invalid")
    with pytest.raises(tomllib.TOMLDecodeError):
        installer.install(tmp_path, ["codex", "claude"])
    assert not (tmp_path / ".codex/agents").exists()
    assert not (tmp_path / ".claude").exists()


def test_inline_agent_config_is_left_intact(tmp_path):
    config = tmp_path / ".codex/config.toml"
    config.parent.mkdir()
    original = "agents = {max_threads = 4}"
    config.write_text(original)
    with pytest.raises(ValueError, match="config left intact"):
        installer.install(tmp_path, ["codex", "claude"])
    assert config.read_text() == original
    assert not (tmp_path / ".codex/agents").exists()


def test_owned_agent_update_preserves_previous_content(tmp_path):
    installer.install(tmp_path, ["claude"])
    agent = tmp_path / ".claude/agents/aea.md"
    previous = agent.read_text() + "\nUser adjustment\n"
    agent.write_text(previous)
    result = installer.install(tmp_path, ["claude"])
    updated = next(item for item in result if item["path"] == str(agent))
    assert updated["status"] == "updated"
    assert Path(updated["backup"]).read_text() == previous
