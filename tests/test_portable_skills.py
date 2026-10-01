import json
import os
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

import achios_access as access
import achios_workspace as workspace
import install_portable_skills as installer


@pytest.fixture
def profile(tmp_path, monkeypatch):
    monkeypatch.setenv("ACHIOS_HOME", str(tmp_path))
    (tmp_path / ".config/gws-dlsu").mkdir(parents=True)
    return tmp_path


def test_profile_reuses_credentials_and_clears_account_overrides(profile, monkeypatch):
    monkeypatch.setenv("GOOGLE_WORKSPACE_CLI_TOKEN", "secret")
    monkeypatch.setenv("GOOGLE_WORKSPACE_CLI_CREDENTIALS_FILE", "/other-account.json")
    monkeypatch.setenv("GOOGLE_WORKSPACE_CLI_KEYRING_BACKEND", "file")
    env = workspace.profile_env("dlsu")
    assert env["GOOGLE_WORKSPACE_CLI_CONFIG_DIR"] == str(profile / ".config/gws-dlsu")
    assert env["GOOGLE_WORKSPACE_CLI_KEYRING_BACKEND"] == "file"
    assert "GOOGLE_WORKSPACE_CLI_TOKEN" not in env
    assert "GOOGLE_WORKSPACE_CLI_CREDENTIALS_FILE" not in env
    assert os.environ["GOOGLE_WORKSPACE_CLI_TOKEN"] == "secret"
    assert list((profile / ".config/gws-dlsu").iterdir()) == []


def test_missing_profile_never_invokes_google(profile, monkeypatch):
    monkeypatch.setattr(workspace.subprocess, "run", lambda *a, **kw: pytest.fail("Google was called"))
    with pytest.raises(ValueError, match="profile_missing"):
        workspace.call("work", ["auth", "status"])


@pytest.mark.parametrize("url", ["https://docs.google.com/document/d/abc_123/edit?usp=sharing",
                                 "https://docs.google.com/document/u/1/d/abc_123/edit", "abc_123"])
def test_document_ids(url):
    assert workspace.document_id(url) == "abc_123"


@pytest.mark.parametrize("url", ["https://evil.example/document/d/abc/edit",
                                 "https://docs.google.com.evil.example/document/d/abc/edit",
                                 "https://docs.google.com/spreadsheets/d/abc/edit"])
def test_rejects_unrelated_urls(url):
    with pytest.raises(ValueError, match="invalid_docs"):
        workspace.document_id(url)


def test_read_doc_selects_account_and_all_tabs(profile, monkeypatch, capsys):
    seen = []
    monkeypatch.setattr(workspace, "call", lambda p, a: seen.append((p, a)) or {"documentId": "abc"})
    assert workspace.main(["--profile", "dlsu", "read-doc", "https://docs.google.com/document/d/abc/edit"]) == 0
    account, command = seen[0]
    assert account == "dlsu"
    assert command[:3] == ["docs", "documents", "get"]
    assert json.loads(command[4]) == {"documentId": "abc", "includeTabsContent": True}
    assert json.loads(capsys.readouterr().out)["profile"] == "dlsu"


def test_operation_requires_explicit_profile(monkeypatch):
    monkeypatch.setattr(workspace, "call", lambda *a: pytest.fail("Google was called"))
    with pytest.raises(SystemExit) as exc:
        workspace.main(["read-doc", "abc"])
    assert exc.value.code == 2


def test_call_handles_banner_and_closed_stdin(profile, monkeypatch):
    def run(command, **kwargs):
        assert kwargs["stdin"] == subprocess.DEVNULL
        assert kwargs["timeout"] == 45
        assert kwargs["env"]["GOOGLE_WORKSPACE_CLI_CONFIG_DIR"].endswith("gws-dlsu")
        return SimpleNamespace(returncode=0, stdout='Using keyring backend: file\n{"title":"test"}', stderr="")
    monkeypatch.setattr(workspace.subprocess, "run", run)
    assert workspace.call("dlsu", ["docs", "documents", "get"]) == {"title": "test"}


@pytest.mark.parametrize("status,code", [(401, "auth_failed"), (403, "permission_denied"), (404, "not_found")])
def test_google_failure_is_sanitized(profile, monkeypatch, status, code):
    monkeypatch.setattr(workspace.subprocess, "run", lambda *a, **kw: SimpleNamespace(
        returncode=1, stdout=json.dumps({"error": {"code": status, "message": "secret-token"}}),
        stderr="secret-token"))
    with pytest.raises(ValueError, match=f"^{code}$"):
        workspace.call("dlsu", ["docs", "documents", "get"])


def test_doctor_does_not_print_credentials(monkeypatch):
    monkeypatch.setattr(workspace, "call", lambda *a: {"token_valid": True, "has_refresh_token": True,
                                                     "scopes": ["docs"], "token": "secret"})
    assert workspace.doctor("dlsu") == {"profile": "dlsu", "status": "authenticated", "scopes": ["docs"]}


def test_gws_uses_mac_path_or_explicit_override(monkeypatch):
    monkeypatch.setattr(workspace.shutil, "which", lambda name: "/opt/homebrew/bin/gws")
    assert workspace.executable() == "/opt/homebrew/bin/gws"
    monkeypatch.setenv("ACHIOS_GWS_BIN", "/custom/bin/gws")
    assert workspace.executable() == "/custom/bin/gws"


def test_installer_global_discovery_and_idempotency(tmp_path):
    first = installer.install(tmp_path, ["codex", "claude"])
    second = installer.install(tmp_path, ["codex", "claude"])
    assert len(first) == 8
    assert all(row["status"] == "present" for row in second)
    for target in [".agents/skills", ".claude/skills"]:
        for name in installer.SKILLS:
            folder = tmp_path / target / name
            assert folder.is_symlink()
            assert (folder / "SKILL.md").is_file()
            assert next((folder / "scripts").iterdir()).is_file()


def test_installer_preflights_conflicts_without_partial_install(tmp_path):
    collision = tmp_path / ".claude/skills/achios-recall"
    collision.mkdir(parents=True)
    (collision / "keep.txt").write_text("keep")
    with pytest.raises(ValueError, match="Existing skill left intact"):
        installer.install(tmp_path, ["codex", "claude"])
    assert not (tmp_path / ".agents").exists()
    assert (collision / "keep.txt").read_text() == "keep"


def test_installer_preserves_broken_links(tmp_path):
    collision = tmp_path / ".agents/skills/achios-google"
    collision.parent.mkdir(parents=True)
    collision.symlink_to(tmp_path / "absent")
    with pytest.raises(ValueError, match="Existing skill left intact"):
        installer.install(tmp_path, ["codex"])
    assert collision.is_symlink()


def test_installer_dry_run_writes_nothing(tmp_path):
    rows = installer.install(tmp_path, ["codex", "claude"], dry_run=True)
    assert all(row["status"] == "planned" for row in rows)
    assert list(tmp_path.iterdir()) == []


def test_installed_google_skill_runs_from_another_repo(tmp_path):
    installer.install(tmp_path, ["codex"])
    cwd = tmp_path / "schoolMem"
    cwd.mkdir()
    result = subprocess.run([sys.executable, str(tmp_path / ".agents/skills/achios-google/scripts/workspace.py"),
                             "--help"], cwd=cwd, capture_output=True, text=True)
    assert result.returncode == 0
    assert "read-doc" in result.stdout


def test_tasks_reads_achios_register_from_another_repo(tmp_path, monkeypatch, capsys):
    (tmp_path / "tasks.md").write_text("## Active\n- [ ] thesis deadline #school !high\n")
    elsewhere = tmp_path / "schoolMem"
    elsewhere.mkdir()
    monkeypatch.chdir(elsewhere)
    monkeypatch.setattr(access, "ROOT", tmp_path)
    assert access.main(["tasks", "school"]) == 0
    assert "thesis deadline" in capsys.readouterr().out


def test_canvas_missing_cache_is_a_failure(profile, capsys):
    assert access.main(["canvas", "due"]) == 1
    assert json.loads(capsys.readouterr().out)["error"] == "canvas_cache_missing"


@pytest.mark.parametrize("args", [["canvas", "sync"], ["calendar", "insert"], ["canvas", "deliver", "--send"]])
def test_access_reader_refuses_writes(args):
    with pytest.raises(SystemExit) as exc:
        access.main(args)
    assert exc.value.code == 2


def test_canvas_passes_explicit_operator_cache(profile, monkeypatch):
    db = profile / "cache.sqlite3"
    db.touch()
    monkeypatch.setenv("ACHICORE_CANVAS_DB", str(db))
    seen = []
    monkeypatch.setattr(access.subprocess, "run", lambda a, **kw: seen.append((a, kw)) or SimpleNamespace(returncode=0))
    assert access.main(["canvas", "status"]) == 0
    assert seen[0][0][-3:] == ["--db", str(db), "status"]
    assert seen[0][1]["env"]["ACHIOS_HOME"] == str(profile)
