import os
import subprocess
from datetime import datetime
from pathlib import Path
import zoneinfo
import pytest

HOOK_SOURCE = Path(__file__).resolve().parent.parent / "scripts" / "hooks" / "pre-commit"
INSTALLER_SOURCE = Path(__file__).resolve().parent.parent / "scripts" / "install_git_hooks.sh"


def run_git(repo_dir: Path, *args, env=None) -> subprocess.CompletedProcess:
    full_env = os.environ.copy()
    if env:
        full_env.update(env)
    return subprocess.run(
        ["git", *args],
        cwd=repo_dir,
        capture_output=True,
        text=True,
        env=full_env,
    )


@pytest.fixture
def temp_git_repo(tmp_path: Path):
    repo = tmp_path / "repo"
    repo.mkdir()
    run_git(repo, "init", "-b", "ticket/test-branch")
    run_git(repo, "config", "user.name", "Test User")
    run_git(repo, "config", "user.email", "test@example.com")
    run_git(repo, "config", "core.hooksPath", ".git/hooks")
    
    # Create initial commit so HEAD exists
    readme = repo / "README.md"
    readme.write_text("# Test Repo\n")
    run_git(repo, "add", "README.md")
    res = run_git(repo, "commit", "--no-verify", "-m", "Initial commit")
    assert res.returncode == 0, f"Initial commit failed: {res.stderr}"
    
    # Install the hook into .git/hooks/pre-commit
    hooks_dir = repo / ".git" / "hooks"
    hooks_dir.mkdir(parents=True, exist_ok=True)
    hook_dest = hooks_dir / "pre-commit"
    hook_dest.write_bytes(HOOK_SOURCE.read_bytes())
    hook_dest.chmod(0o755)
    
    return repo


def get_manila_today() -> str:
    manila_tz = zoneinfo.ZoneInfo("Asia/Manila")
    return datetime.now(manila_tz).strftime("%Y-%m-%d")


def test_hook_and_installer_files_exist_and_executable():
    assert HOOK_SOURCE.exists(), f"{HOOK_SOURCE} must exist"
    assert os.access(HOOK_SOURCE, os.X_OK), f"{HOOK_SOURCE} must be executable"
    assert INSTALLER_SOURCE.exists(), f"{INSTALLER_SOURCE} must exist"
    assert os.access(INSTALLER_SOURCE, os.X_OK), f"{INSTALLER_SOURCE} must be executable"


def test_installer_script_installs_hook_idempotently(tmp_path: Path):
    repo = tmp_path / "target_repo"
    repo.mkdir()
    run_git(repo, "init", "-b", "main")
    
    # Run installer specifying target repo
    res = subprocess.run(
        [str(INSTALLER_SOURCE), str(repo)],
        capture_output=True,
        text=True,
    )
    assert res.returncode == 0, f"Installer failed: {res.stderr}"
    
    installed_hook = repo / ".git" / "hooks" / "pre-commit"
    assert installed_hook.exists()
    assert os.access(installed_hook, os.X_OK)
    assert installed_hook.read_bytes() == HOOK_SOURCE.read_bytes()
    
    # Run installer again (idempotent)
    res2 = subprocess.run(
        [str(INSTALLER_SOURCE), str(repo)],
        capture_output=True,
        text=True,
    )
    assert res2.returncode == 0
    assert installed_hook.exists()
    assert os.access(installed_hook, os.X_OK)


def test_doc_only_changes_pass_without_session_log(temp_git_repo: Path):
    doc_file = temp_git_repo / "tasks.md"
    doc_file.write_text("# Tasks\n- task 1\n")
    run_git(temp_git_repo, "add", "tasks.md")
    
    res = run_git(temp_git_repo, "commit", "-m", "update tasks")
    assert res.returncode == 0, f"Doc commit should pass: {res.stderr}\n{res.stdout}"


def test_significant_file_without_session_log_fails(temp_git_repo: Path):
    py_file = temp_git_repo / "main.py"
    py_file.write_text("print('hello')\n")
    run_git(temp_git_repo, "add", "main.py")
    
    res = run_git(temp_git_repo, "commit", "-m", "add main.py")
    assert res.returncode == 1, "Significant file without session-log.md must abort"
    output = res.stderr + res.stdout
    assert "session-log.md" in output
    assert "main.py" in output


def test_significant_file_with_stale_session_log_fails(temp_git_repo: Path):
    py_file = temp_git_repo / "main.py"
    py_file.write_text("print('hello')\n")
    log_file = temp_git_repo / "session-log.md"
    log_file.write_text("# Session Log\n\n## 2020-01-01 10:00 [saved]\nGoal: Old\n")
    
    run_git(temp_git_repo, "add", "main.py", "session-log.md")
    res = run_git(temp_git_repo, "commit", "-m", "add main and stale log")
    assert res.returncode == 1, "Stale session-log.md must abort commit"
    output = res.stderr + res.stdout
    assert "session-log.md" in output


def test_significant_file_with_valid_today_session_log_succeeds(temp_git_repo: Path):
    py_file = temp_git_repo / "main.py"
    py_file.write_text("print('hello')\n")
    log_file = temp_git_repo / "session-log.md"
    today_str = get_manila_today()
    log_file.write_text(f"# Session Log\n\n## {today_str} 12:00 [saved]\nGoal: Implement feature\n")
    
    run_git(temp_git_repo, "add", "main.py", "session-log.md")
    res = run_git(temp_git_repo, "commit", "-m", "add main and valid log")
    assert res.returncode == 0, f"Commit with valid session log should succeed: {res.stderr}\n{res.stdout}"


def test_skip_session_check_env_var_bypasses(temp_git_repo: Path):
    py_file = temp_git_repo / "main.py"
    py_file.write_text("print('hello')\n")
    run_git(temp_git_repo, "add", "main.py")
    
    res = run_git(temp_git_repo, "commit", "-m", "bypass with env", env={"SKIP_SESSION_CHECK": "1"})
    assert res.returncode == 0, f"SKIP_SESSION_CHECK=1 must bypass hook: {res.stderr}\n{res.stdout}"


def test_no_verify_flag_bypasses(temp_git_repo: Path):
    py_file = temp_git_repo / "main.py"
    py_file.write_text("print('hello')\n")
    run_git(temp_git_repo, "add", "main.py")
    
    res = run_git(temp_git_repo, "commit", "--no-verify", "-m", "bypass with --no-verify")
    assert res.returncode == 0, f"--no-verify must bypass hook: {res.stderr}\n{res.stdout}"


@pytest.mark.parametrize("filename", [
    "app.ts",
    "index.js",
    "config.json",
    "deploy.sh",
    "SKILL.md",
    "skills/custom/SKILL.md",
    "AGENTS.md",
    "agents/worker.md",
    "systemd/bot.service",
])
def test_all_significant_file_patterns_require_session_log(temp_git_repo: Path, filename: str):
    target = temp_git_repo / filename
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text("content\n")
    run_git(temp_git_repo, "add", filename)
    
    res = run_git(temp_git_repo, "commit", "-m", f"add {filename}")
    assert res.returncode == 1, f"Adding {filename} without session-log.md must fail"
    output = res.stderr + res.stdout
    assert "session-log.md" in output
