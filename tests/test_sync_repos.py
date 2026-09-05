import subprocess
from pathlib import Path

import pytest

SCRIPT = Path(__file__).resolve().parent.parent / "scripts" / "sync-repos.sh"


def git(cwd, *args):
    return subprocess.run(
        ["git", "-c", "core.hooksPath=", "-C", str(cwd), *args],
        check=True,
        capture_output=True,
        text=True,
    ).stdout


def run_sync(*args, home):
    return subprocess.run(
        ["bash", str(SCRIPT), *[str(a) for a in args]],
        capture_output=True,
        text=True,
        env={"HOME": str(home), "PATH": "/usr/bin:/bin", "GIT_TERMINAL_PROMPT": "0"},
    )


def run(root, home):
    return run_sync(root, home=home)


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


@pytest.fixture
def multi_workspace(tmp_path):
    """Two cloned repos under a scannable root."""
    upstream_a = tmp_path / "upstream_a.git"
    git(tmp_path, "init", "--bare", "-b", "main", str(upstream_a))
    seed_a = tmp_path / "seed_a"
    seed_a.mkdir()
    git(seed_a, "init", "-b", "main")
    commit(seed_a, "README")
    git(seed_a, "remote", "add", "origin", str(upstream_a))
    git(seed_a, "push", "-q", "origin", "main")

    upstream_b = tmp_path / "upstream_b.git"
    git(tmp_path, "init", "--bare", "-b", "main", str(upstream_b))
    seed_b = tmp_path / "seed_b"
    seed_b.mkdir()
    git(seed_b, "init", "-b", "main")
    commit(seed_b, "README")
    git(seed_b, "remote", "add", "origin", str(upstream_b))
    git(seed_b, "push", "-q", "origin", "main")

    root = tmp_path / "root"
    root.mkdir()
    clone_a = root / "repo_a"
    git(tmp_path, "clone", "-q", str(upstream_a), str(clone_a))
    clone_b = root / "repo_b"
    git(tmp_path, "clone", "-q", str(upstream_b), str(clone_b))

    return {
        "tmp": tmp_path,
        "root": root,
        "seed_a": seed_a,
        "seed_b": seed_b,
        "clone_a": clone_a,
        "clone_b": clone_b,
    }


@pytest.fixture
def direct_repo(tmp_path):
    """A standalone repo not located under any scanned root."""
    upstream = tmp_path / "direct_upstream.git"
    git(tmp_path, "init", "--bare", "-b", "main", str(upstream))

    seed = tmp_path / "direct_seed"
    seed.mkdir()
    git(seed, "init", "-b", "main")
    commit(seed, "README")
    git(seed, "remote", "add", "origin", str(upstream))
    git(seed, "push", "-q", "origin", "main")

    clone = tmp_path / "direct_clone"
    git(tmp_path, "clone", "-q", str(upstream), str(clone))

    return {"tmp": tmp_path, "seed": seed, "clone": clone}


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

    def test_baseline_multi_repo_sync_when_repo_flag_omitted(self, multi_workspace):
        commit(multi_workspace["seed_a"], "remote-a")
        git(multi_workspace["seed_a"], "push", "-q", "origin", "main")
        commit(multi_workspace["seed_b"], "remote-b")
        git(multi_workspace["seed_b"], "push", "-q", "origin", "main")

        result = run_sync(multi_workspace["root"], home=multi_workspace["tmp"])

        assert result.returncode == 0
        assert "2 repos" in result.stdout
        assert (multi_workspace["clone_a"] / "remote-a").exists()
        assert (multi_workspace["clone_b"] / "remote-b").exists()

    def test_targets_specific_repo_by_folder_name_with_repo_flag(self, multi_workspace):
        commit(multi_workspace["seed_a"], "remote-a")
        git(multi_workspace["seed_a"], "push", "-q", "origin", "main")
        commit(multi_workspace["seed_b"], "remote-b")
        git(multi_workspace["seed_b"], "push", "-q", "origin", "main")

        result = run_sync(
            "--repo", "repo_a", multi_workspace["root"], home=multi_workspace["tmp"]
        )

        assert result.returncode == 0
        assert "1 repos" in result.stdout
        assert "repo_a" in result.stdout
        assert "repo_b" not in result.stdout
        assert (multi_workspace["clone_a"] / "remote-a").exists()
        assert not (multi_workspace["clone_b"] / "remote-b").exists()

    def test_targets_specific_repo_with_short_flag(self, multi_workspace):
        commit(multi_workspace["seed_a"], "remote-a")
        git(multi_workspace["seed_a"], "push", "-q", "origin", "main")
        commit(multi_workspace["seed_b"], "remote-b")
        git(multi_workspace["seed_b"], "push", "-q", "origin", "main")

        result = run_sync(
            "-r", "repo_b", multi_workspace["root"], home=multi_workspace["tmp"]
        )

        assert result.returncode == 0
        assert "1 repos" in result.stdout
        assert "repo_b" in result.stdout
        assert "repo_a" not in result.stdout
        assert (multi_workspace["clone_b"] / "remote-b").exists()
        assert not (multi_workspace["clone_a"] / "remote-a").exists()

    def test_targets_direct_repo_path(self, multi_workspace, direct_repo):
        commit(direct_repo["seed"], "remote-direct")
        git(direct_repo["seed"], "push", "-q", "origin", "main")
        commit(multi_workspace["seed_a"], "remote-a")
        git(multi_workspace["seed_a"], "push", "-q", "origin", "main")

        result = run_sync(
            "--repo", str(direct_repo["clone"]), multi_workspace["root"], home=direct_repo["tmp"]
        )

        assert result.returncode == 0
        assert "1 repos" in result.stdout
        assert (direct_repo["clone"] / "remote-direct").exists()
        assert not (multi_workspace["clone_a"] / "remote-a").exists()

    def test_error_exit_when_no_repo_matches(self, multi_workspace):
        result = run_sync(
            "--repo", "nonexistent", multi_workspace["root"], home=multi_workspace["tmp"]
        )

        assert result.returncode == 1
        assert "no repository matching 'nonexistent' found" in result.stdout

    def test_error_exit_when_no_repo_matches_short_flag(self, multi_workspace):
        result = run_sync(
            "-r", "nonexistent", multi_workspace["root"], home=multi_workspace["tmp"]
        )

        assert result.returncode == 1
        assert "no repository matching 'nonexistent' found" in result.stdout

    def test_targets_specific_repo_with_equals_syntax(self, multi_workspace):
        commit(multi_workspace["seed_a"], "remote-a")
        git(multi_workspace["seed_a"], "push", "-q", "origin", "main")

        result = run_sync(
            "--repo=repo_a", multi_workspace["root"], home=multi_workspace["tmp"]
        )

        assert result.returncode == 0
        assert "1 repos" in result.stdout
        assert (multi_workspace["clone_a"] / "remote-a").exists()

    def test_targets_nested_repo_by_path_fragment(self, tmp_path):
        upstream = tmp_path / "upstream_nested.git"
        git(tmp_path, "init", "--bare", "-b", "main", str(upstream))
        seed = tmp_path / "seed_nested"
        seed.mkdir()
        git(seed, "init", "-b", "main")
        commit(seed, "README")
        git(seed, "remote", "add", "origin", str(upstream))
        git(seed, "push", "-q", "origin", "main")

        root = tmp_path / "root"
        nested = root / "category" / "subproject"
        nested.parent.mkdir(parents=True, exist_ok=True)
        git(tmp_path, "clone", "-q", str(upstream), str(nested))

        commit(seed, "remote-nested")
        git(seed, "push", "-q", "origin", "main")

        result = run_sync("--repo", "category/subproject", root, home=tmp_path)
        assert result.returncode == 0
        assert "1 repos" in result.stdout
        assert (nested / "remote-nested").exists()

    def test_targets_repo_under_default_roots(self, tmp_path):
        upstream = tmp_path / "upstream_default.git"
        git(tmp_path, "init", "--bare", "-b", "main", str(upstream))
        seed = tmp_path / "seed_default"
        seed.mkdir()
        git(seed, "init", "-b", "main")
        commit(seed, "README")
        git(seed, "remote", "add", "origin", str(upstream))
        git(seed, "push", "-q", "origin", "main")

        default_root = tmp_path / "Code" / "GitHub"
        default_root.mkdir(parents=True, exist_ok=True)
        clone = default_root / "auto_target"
        git(tmp_path, "clone", "-q", str(upstream), str(clone))

        commit(seed, "remote-default")
        git(seed, "push", "-q", "origin", "main")

        result = run_sync("--repo", "auto_target", home=tmp_path)
        assert result.returncode == 0
        assert "1 repos" in result.stdout
        assert (clone / "remote-default").exists()

    def test_missing_argument_for_repo_flag_fails(self, tmp_path):
        result = run_sync("--repo", home=tmp_path)
        assert result.returncode == 1
        assert "error: --repo requires an argument" in result.stdout

    def test_missing_argument_for_short_flag_fails(self, tmp_path):
        result = run_sync("-r", home=tmp_path)
        assert result.returncode == 1
        assert "error: -r requires an argument" in result.stdout


