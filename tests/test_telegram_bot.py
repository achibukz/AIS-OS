import json
import os
import subprocess
from pathlib import Path

import pytest

SCRIPT = Path(__file__).resolve().parent.parent / "scripts" / "telegram-bot.sh"
GUARD = Path(__file__).resolve().parent.parent / "scripts" / "schoolmem_wiki_guard.py"


@pytest.fixture
def bot(tmp_path):
    """A fake home, repo and state dir, plus stub claude/sync-repos on PATH."""
    home = tmp_path / "home"
    cwd = tmp_path / "repo"
    state = tmp_path / "state"
    stub = tmp_path / "bin"
    for d in (home, cwd, state, stub):
        d.mkdir(parents=True)
    (state / ".env").write_text("TELEGRAM_BOT_TOKEN=123:abc\n")

    (stub / "claude").write_text(
        "#!/usr/bin/env bash\n"
        'printf "%s\\n" "$@" > "$STUB_OUT"\n'
        'echo "cwd=$(pwd)" >> "$STUB_OUT"\n'
        'echo "state=$TELEGRAM_STATE_DIR" >> "$STUB_OUT"\n'
    )
    (stub / "sync-repos").write_text("#!/usr/bin/env bash\necho stub-sync\n")
    for f in ("claude", "sync-repos"):
        (stub / f).chmod(0o755)

    return {"home": home, "cwd": cwd, "state": state, "stub": stub, "out": tmp_path / "out.txt"}


def run(bot, **overrides):
    env = {
        "HOME": str(bot["home"]),
        "PATH": f"{bot['stub']}:/usr/bin:/bin",
        "STUB_OUT": str(bot["out"]),
        "BOT_NAME": "test",
        "BOT_CWD": str(bot["cwd"]),
        "BOT_STATE_DIR": str(bot["state"]),
    }
    for k, v in overrides.items():
        if v is None:
            env.pop(k, None)
        else:
            env[k] = v
    return subprocess.run(
        ["bash", str(SCRIPT)], capture_output=True, text=True, env=env
    )


def launched(bot):
    return bot["out"].read_text() if bot["out"].exists() else ""


@pytest.mark.parametrize("missing", ["BOT_NAME", "BOT_CWD", "BOT_STATE_DIR"])
def test_required_env_vars(bot, missing):
    result = run(bot, **{missing: None})
    assert result.returncode != 0
    assert missing in result.stderr
    assert launched(bot) == ""


def test_refuses_when_the_repo_is_missing(bot):
    assert run(bot, BOT_CWD=str(bot["cwd"] / "nope")).returncode == 1
    assert launched(bot) == ""


def test_refuses_when_the_token_is_missing(bot):
    (bot["state"] / ".env").unlink()
    assert run(bot).returncode == 1
    assert launched(bot) == ""


def test_launches_with_the_expected_flags(bot):
    assert run(bot).returncode == 0
    out = launched(bot)
    assert "--channels" in out
    assert "plugin:telegram@claude-plugins-official" in out
    assert "bypassPermissions" in out
    assert f"state={bot['state']}" in out
    assert f"cwd={bot['cwd']}" in out


def test_defaults_to_sonnet(bot):
    run(bot)
    assert "sonnet" in launched(bot)


def test_model_is_overridable(bot):
    run(bot, BOT_MODEL="haiku")
    out = launched(bot)
    assert "haiku" in out and "sonnet" not in out


def test_unguarded_bot_writes_no_settings(bot):
    assert run(bot).returncode == 0
    assert not (bot["cwd"] / ".claude" / "settings.json").exists()


def test_guard_is_armed_when_requested(bot):
    assert run(bot, BOT_GUARD=str(GUARD)).returncode == 0
    settings = json.loads((bot["cwd"] / ".claude" / "settings.json").read_text())
    hooks = settings["hooks"]["PreToolUse"]
    assert any(str(GUARD) in json.dumps(h) for h in hooks)
    assert launched(bot) != ""


def test_guard_install_is_idempotent(bot):
    for _ in range(3):
        run(bot, BOT_GUARD=str(GUARD))
    settings = json.loads((bot["cwd"] / ".claude" / "settings.json").read_text())
    assert len(settings["hooks"]["PreToolUse"]) == 1


def test_guard_preserves_a_hand_added_hook(bot):
    claude_dir = bot["cwd"] / ".claude"
    claude_dir.mkdir()
    (claude_dir / "settings.json").write_text(
        json.dumps(
            {"hooks": {"PreToolUse": [{"matcher": "Read", "hooks": [{"command": "/bin/true"}]}]}}
        )
    )
    run(bot, BOT_GUARD=str(GUARD))
    hooks = json.loads((claude_dir / "settings.json").read_text())["hooks"]["PreToolUse"]
    assert any("/bin/true" in json.dumps(h) for h in hooks)
    assert any(str(GUARD) in json.dumps(h) for h in hooks)


def test_fails_closed_when_the_guard_cannot_be_armed(bot):
    claude_dir = bot["cwd"] / ".claude"
    claude_dir.mkdir()
    (claude_dir / "settings.json").write_text("{ not json")
    assert run(bot, BOT_GUARD=str(GUARD)).returncode == 1
    # The whole point: a bot that cannot arm its guard must never reach claude.
    assert launched(bot) == ""


def test_a_failed_sync_still_launches(bot):
    (bot["stub"] / "sync-repos").write_text("#!/usr/bin/env bash\nexit 1\n")
    (bot["stub"] / "sync-repos").chmod(0o755)
    assert run(bot).returncode == 0
    assert launched(bot) != ""
    log = (bot["home"] / ".local/state/achios/test_bot.log").read_text()
    assert "WARNING" in log


# A token in the plugin's default state dir is claimed by every ordinary Claude Code
# session on the box, which polls but does not inject — the bot goes deaf in silence.
@pytest.mark.parametrize("unit", ["achios-bot.service", "achios-schoolmem-bot.service"])
def test_no_unit_uses_the_default_channel_state_dir(unit):
    text = (SCRIPT.parent.parent / "systemd" / unit).read_text()
    line = next(l for l in text.splitlines() if l.startswith("Environment=BOT_STATE_DIR="))
    assert not line.endswith("/channels/telegram")
