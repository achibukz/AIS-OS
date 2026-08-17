import subprocess
from pathlib import Path

import pytest

SCRIPT = Path(__file__).resolve().parent.parent / "scripts" / "sync-repos.sh"


def git(cwd, *args):
    return subprocess.run(
        ["git", "-C", str(cwd), *args],
        check=True,
        capture_output=True,
        text=True,
    ).stdout


def run(root, home):
    return subprocess.run(
        ["bash", str(SCRIPT), str(root)],
        capture_output=True,
        text=True,
        env={"HOME": str(home), "PATH": "/usr/bin:/bin", "GIT_TERMINAL_PROMPT": "0"},
    )


def commit(repo, name, body="x"):
    (repo / name).write_text(body)
    git(repo, "add", name)
    git(repo, "-c", "user.email=t@t", "-c", "user.name=t", "commit", "-m", name)


@pytest.fixture
def workspace(tmp_path):
    """An upstream bare repo plus a clone of it, under a scannable root."""
    upstream = tmp_path / "upstream.git"
    git(tmp_path, "init", "--bare", "-b", "main", str(upstream))

    seed = tmp_path / "seed"
    seed.mkdir()
    git(seed, "init", "-b", "main")
    commit(seed, "README")
    git(seed, "remote", "add", "origin", str(upstream))
    git(seed, "push", "-q", "origin", "main")

    root = tmp_path / "root"
    root.mkdir()
    clone = root / "project"
    git(tmp_path, "clone", "-q", str(upstream), str(clone))

    return {"tmp": tmp_path, "upstream": upstream, "seed": seed, "root": root, "clone": clone}


def push_new_commit(workspace):
    commit(workspace["seed"], "remote-change")
    git(workspace["seed"], "push", "-q", "origin", "main")


class TestSync:
    def test_reports_up_to_date_when_nothing_changed(self, workspace):
        result = run(workspace["root"], workspace["tmp"])
        assert result.returncode == 0
        assert "up to date" in result.stdout
        assert "0 failed" in result.stdout

    def test_fast_forwards_a_behind_repo(self, workspace):
        push_new_commit(workspace)

        result = run(workspace["root"], workspace["tmp"])

        assert result.returncode == 0
        assert "pulled 1" in result.stdout
        assert (workspace["clone"] / "remote-change").exists()

    def test_holds_back_a_repo_with_tracked_changes(self, workspace):
        push_new_commit(workspace)
        (workspace["clone"] / "README").write_text("work in progress")

        result = run(workspace["root"], workspace["tmp"])

        assert result.returncode == 0
        assert "held back" in result.stdout
        assert not (workspace["clone"] / "remote-change").exists()
        assert (workspace["clone"] / "README").read_text() == "work in progress"

    def test_untracked_files_do_not_block_a_pull(self, workspace):
        push_new_commit(workspace)
        (workspace["clone"] / "scratch.txt").write_text("scratch")

        result = run(workspace["root"], workspace["tmp"])

        assert result.returncode == 0
        assert "pulled 1" in result.stdout
        assert "1 untracked" in result.stdout
        assert (workspace["clone"] / "remote-change").exists()
        assert (workspace["clone"] / "scratch.txt").read_text() == "scratch"

    def test_untracked_file_in_the_way_fails_without_clobbering(self, workspace):
        push_new_commit(workspace)
        (workspace["clone"] / "remote-change").write_text("mine")

        result = run(workspace["root"], workspace["tmp"])

        assert result.returncode == 1
        assert "PULL FAILED" in result.stdout
        assert (workspace["clone"] / "remote-change").read_text() == "mine"

    def test_never_merges_a_diverged_repo(self, workspace):
        push_new_commit(workspace)
        commit(workspace["clone"], "local-change")

        result = run(workspace["root"], workspace["tmp"])

        assert result.returncode == 1
        assert "DIVERGED" in result.stdout
        assert "1 behind, 1 ahead" in result.stdout
        assert not (workspace["clone"] / "remote-change").exists()

    def test_flags_unpushed_commits_without_failing(self, workspace):
        commit(workspace["clone"], "local-change")

        result = run(workspace["root"], workspace["tmp"])

        assert result.returncode == 0
        assert "1 unpushed" in result.stdout
        assert "1 need a look" in result.stdout

    def test_marks_a_shallow_clone_so_the_count_is_not_believed(self, workspace, tmp_path):
        shallow_root = tmp_path / "shallow-root"
        shallow_root.mkdir()
        git(
            tmp_path,
            "clone",
            "-q",
            "--depth",
            "1",
            "file://" + str(workspace["upstream"]),
            str(shallow_root / "shallow"),
        )
        push_new_commit(workspace)

        result = run(shallow_root, workspace["tmp"])

        assert result.returncode == 0
        assert "shallow" in result.stdout
        assert "pulled" in result.stdout

    def test_skips_a_repo_with_no_remote(self, workspace):
        loner = workspace["root"] / "loner"
        loner.mkdir()
        git(loner, "init", "-b", "main")
        commit(loner, "README")

        result = run(workspace["root"], workspace["tmp"])

        assert result.returncode == 0
        assert "no remote" in result.stdout
        assert "2 repos" in result.stdout

    def test_reports_a_branch_with_no_upstream(self, workspace):
        git(workspace["clone"], "checkout", "-q", "-b", "side")

        result = run(workspace["root"], workspace["tmp"])

        assert result.returncode == 0
        assert "side has no upstream" in result.stdout

    def test_fetch_failure_is_reported_not_fatal(self, workspace):
        git(workspace["clone"], "remote", "set-url", "origin", str(workspace["tmp"] / "gone.git"))

        result = run(workspace["root"], workspace["tmp"])

        assert result.returncode == 1
        assert "FETCH FAILED" in result.stdout
        assert "1 failed" in result.stdout

    def test_missing_root_is_not_an_error(self, tmp_path):
        result = run(tmp_path / "nope", tmp_path)

        assert result.returncode == 0
        assert "no repos found" in result.stdout
