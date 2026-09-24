import json
import subprocess
from pathlib import Path

import pytest

import cohesion
from owned_persist import OwnedChange, Persister, ReceiptStore, RepositoryPolicy
from test_cohesion import FakeCalendar, write_calendars

BASE = "# Tasks\n\n## Active\n\n- [ ] Existing task\n\n## Blocked\n\n## Done\n"


def git(root: Path, *args: str) -> str:
    return subprocess.run(
        ["git", *args], cwd=root, check=True, capture_output=True, text=True
    ).stdout.strip()


@pytest.fixture
def repo(tmp_path):
    remote = tmp_path / "remote.git"
    work = tmp_path / "work"
    hooks = tmp_path / "hooks"
    hooks.mkdir()
    subprocess.run(["git", "init", "-q", "--bare", "-b", "main", str(remote)], check=True)
    subprocess.run(["git", "init", "-q", "-b", "main", str(work)], check=True)
    for key, value in (
        ("user.name", "Fixture"),
        ("user.email", "fixture@example.com"),
        ("core.hooksPath", str(hooks)),
    ):
        git(work, "config", key, value)
    (work / "tasks.md").write_text(BASE, encoding="utf-8")
    (work / "notes.md").write_text("notes\n", encoding="utf-8")
    git(work, "add", ".")
    git(work, "commit", "-q", "-m", "init")
    git(work, "remote", "add", "origin", str(remote))
    git(work, "push", "-q", "-u", "origin", "main")
    return work, remote, hooks


def policy(work: Path, remote: Path, **changes) -> RepositoryPolicy:
    values = {
        "root": work,
        "remote": "origin",
        "remote_url": str(remote),
        "branch": "main",
        "author_name": "Aki Bukuhan",
        "author_email": "akibukzwork@gmail.com",
        "paths": ("tasks.md", "session-log.md"),
        **changes,
    }
    return RepositoryPolicy(**values)


def persister(tmp_path, work, remote, runner=subprocess.run, **changes):
    return Persister(
        [policy(work, remote, **changes)],
        store=ReceiptStore(tmp_path / "receipts.sqlite3"),
        runner=runner,
    )


def write_task(work: Path, line: str) -> tuple[str, str]:
    before = (work / "tasks.md").read_text(encoding="utf-8")
    after = before.replace("## Active\n\n", f"## Active\n\n{line}\n", 1)
    (work / "tasks.md").write_text(after, encoding="utf-8")
    return before, after


def remote_head(remote: Path) -> str:
    return git(remote, "rev-parse", "refs/heads/main")


def test_owned_hunk_reaches_the_remote_under_the_configured_identity(repo, tmp_path):
    work, remote, _ = repo
    before, after = write_task(work, "- [ ] New task")

    receipt = persister(tmp_path, work, remote).persist_file(
        work / "tasks.md", before, after, operation_id="op-1", message="tasks: add\n"
    )

    assert receipt["state"] == "pushed"
    assert (receipt["saved"], receipt["committed"], receipt["pushed"]) == (True, True, True)
    assert remote_head(remote) == receipt["commit"]
    assert git(work, "log", "-1", "--format=%an <%ae>") == "Aki Bukuhan <akibukzwork@gmail.com>"
    assert git(work, "status", "--porcelain") == ""


def test_unrelated_hunks_files_and_staged_work_stay_out_of_the_commit(repo, tmp_path):
    work, remote, _ = repo
    (work / "tasks.md").write_text(BASE + "\nsomeone else's footer\n", encoding="utf-8")
    (work / "notes.md").write_text("notes\nunrelated edit\n", encoding="utf-8")
    (work / "staged.md").write_text("staged by hand\n", encoding="utf-8")
    git(work, "add", "staged.md")
    before, after = write_task(work, "- [ ] Owned task")

    receipt = persister(tmp_path, work, remote).persist_file(
        work / "tasks.md", before, after, operation_id="op-1", message="tasks: add\n"
    )

    assert receipt["state"] == "pushed"
    committed = git(work, "show", f"{receipt['commit']}:tasks.md")
    assert "- [ ] Owned task" in committed
    assert "someone else's footer" not in committed
    assert git(work, "show", "--name-only", "--format=", receipt["commit"]) == "tasks.md"
    assert (work / "tasks.md").read_text(encoding="utf-8") == after
    status = subprocess.run(
        ["git", "status", "--porcelain"], cwd=work, check=True, capture_output=True, text=True
    ).stdout.splitlines()
    assert " M notes.md" in status and "A  staged.md" in status and " M tasks.md" in status


def test_overlapping_concurrent_edit_is_a_conflict_not_a_commit(repo, tmp_path):
    work, remote, _ = repo
    edited = BASE.replace("- [ ] Existing task", "- [ ] Existing task, renamed by hand")
    (work / "tasks.md").write_text(edited, encoding="utf-8")
    git(work, "commit", "-q", "-am", "hand edit")
    head = git(work, "rev-parse", "HEAD")
    before = BASE
    after = BASE.replace("- [ ] Existing task", "- [x] Existing task")

    receipt = persister(tmp_path, work, remote).persist_file(
        work / "tasks.md", before, after, operation_id="op-1", message="tasks: complete\n"
    )

    assert receipt["state"] == "conflict" and receipt["committed"] is False
    assert "concurrent_changes_overlap" in receipt["error"]
    assert git(work, "rev-parse", "HEAD") == head


def test_a_commit_that_lands_mid_operation_is_never_reverted(repo, tmp_path):
    work, remote, _ = repo
    before, after = write_task(work, "- [ ] Owned task")

    def racing_runner(argv, **kwargs):
        if argv[:2] == ["git", "commit-tree"]:
            (work / "notes.md").write_text("notes\nconcurrent commit\n", encoding="utf-8")
            git(work, "commit", "-q", "-m", "concurrent", "--", "notes.md")
        return subprocess.run(argv, **kwargs)

    receipt = persister(tmp_path, work, remote, runner=racing_runner).persist_file(
        work / "tasks.md", before, after, operation_id="op-1", message="tasks: add\n"
    )

    assert receipt["state"] == "saved" and receipt["error"] == "head_moved_during_commit"
    assert git(work, "log", "-1", "--format=%s") == "concurrent"
    assert "concurrent commit" in git(work, "show", "HEAD:notes.md")


def test_hook_failure_keeps_the_file_saved_and_uncommitted(repo, tmp_path):
    work, remote, hooks = repo
    hook = hooks / "pre-commit"
    hook.write_text("#!/bin/sh\necho 'blocked by policy' >&2\nexit 1\n", encoding="utf-8")
    hook.chmod(0o755)
    head = git(work, "rev-parse", "HEAD")
    before, after = write_task(work, "- [ ] Owned task")

    receipt = persister(tmp_path, work, remote).persist_file(
        work / "tasks.md", before, after, operation_id="op-1", message="tasks: add\n"
    )

    assert receipt["state"] == "saved" and receipt["committed"] is False
    assert "hook_failed" in receipt["error"] and "blocked by policy" in receipt["error"]
    assert git(work, "rev-parse", "HEAD") == head
    assert (work / "tasks.md").read_text(encoding="utf-8") == after


def test_the_hook_sees_only_the_owned_staging(repo, tmp_path):
    work, remote, hooks = repo
    seen = tmp_path / "seen.txt"
    hook = hooks / "pre-commit"
    hook.write_text(f"#!/bin/sh\ngit diff --cached --name-only > {seen}\n", encoding="utf-8")
    hook.chmod(0o755)
    (work / "staged.md").write_text("staged by hand\n", encoding="utf-8")
    git(work, "add", "staged.md")
    before, after = write_task(work, "- [ ] Owned task")

    persister(tmp_path, work, remote).persist_file(
        work / "tasks.md", before, after, operation_id="op-1", message="tasks: add\n"
    )

    assert seen.read_text(encoding="utf-8").split() == ["tasks.md"]


def test_auth_failure_keeps_the_commit_and_retry_pushes_it_once(repo, tmp_path):
    work, remote, _ = repo
    before, after = write_task(work, "- [ ] Owned task")
    offline = {"value": True}

    def runner(argv, **kwargs):
        if offline["value"] and argv[1] in {"push", "ls-remote"}:
            return subprocess.CompletedProcess(argv, 128, "", "fatal: Authentication failed")
        return subprocess.run(argv, **kwargs)

    tool = persister(tmp_path, work, remote, runner=runner)
    first = tool.persist_file(
        work / "tasks.md", before, after, operation_id="op-1", message="tasks: add\n"
    )
    offline["value"] = False
    second = tool.persist_file(
        work / "tasks.md", before, after, operation_id="op-1", message="tasks: add\n"
    )

    assert first["state"] == "committed" and first["pushed"] is False
    assert first["error"].startswith("push_failed") and "Authentication failed" in first["error"]
    assert second["state"] == "pushed" and second["commit"] == first["commit"]
    assert git(work, "rev-list", "--count", "HEAD") == "2"
    assert remote_head(remote) == first["commit"]


def test_lost_push_acknowledgement_is_verified_from_the_remote(repo, tmp_path):
    work, remote, _ = repo
    before, after = write_task(work, "- [ ] Owned task")

    def runner(argv, **kwargs):
        completed = subprocess.run(argv, **kwargs)
        if argv[1] == "push":
            return subprocess.CompletedProcess(argv, 1, "", "error: connection reset")
        return completed

    receipt = persister(tmp_path, work, remote, runner=runner).persist_file(
        work / "tasks.md", before, after, operation_id="op-1", message="tasks: add\n"
    )

    assert receipt["state"] == "pushed"
    assert remote_head(remote) == receipt["commit"]


def test_divergent_remote_preserves_the_local_commit(repo, tmp_path):
    work, remote, _ = repo
    other = tmp_path / "other"
    subprocess.run(["git", "clone", "-q", str(remote), str(other)], check=True)
    (other / "notes.md").write_text("notes\nfrom elsewhere\n", encoding="utf-8")
    git(other, "-c", "user.name=Other", "-c", "user.email=o@example.com",
        "commit", "-q", "-am", "elsewhere")
    git(other, "push", "-q", "origin", "main")
    elsewhere = remote_head(remote)
    before, after = write_task(work, "- [ ] Owned task")

    receipt = persister(tmp_path, work, remote).persist_file(
        work / "tasks.md", before, after, operation_id="op-1", message="tasks: add\n"
    )

    assert receipt["state"] == "committed" and receipt["error"] == "divergent_remote"
    assert remote_head(remote) == elsewhere
    assert git(work, "log", "-1", "--format=%s") == "tasks: add"


def test_wrong_remote_commits_nothing(repo, tmp_path):
    work, remote, _ = repo
    head = git(work, "rev-parse", "HEAD")
    before, after = write_task(work, "- [ ] Owned task")

    receipt = persister(
        tmp_path, work, remote, remote_url="https://github.com/achibukz/AIS-OS.git"
    ).persist_file(work / "tasks.md", before, after, operation_id="op-1", message="tasks: add\n")

    assert receipt["state"] == "saved" and receipt["error"].startswith("wrong_remote")
    assert git(work, "rev-parse", "HEAD") == head


def test_wrong_branch_and_unlisted_paths_commit_nothing(repo, tmp_path):
    work, remote, _ = repo
    git(work, "switch", "-q", "-c", "ticket/1-x")
    before, after = write_task(work, "- [ ] Owned task")
    tool = persister(tmp_path, work, remote)

    on_branch = tool.persist_file(
        work / "tasks.md", before, after, operation_id="op-1", message="tasks: add\n"
    )
    unlisted = tool.persist_file(
        work / "notes.md", "notes\n", "notes\nmore\n", operation_id="op-2", message="notes\n"
    )

    assert on_branch["state"] == "saved" and on_branch["error"] == "wrong_branch: ticket/1-x"
    assert unlisted is None


def test_unrelated_local_commits_are_never_published(repo, tmp_path):
    work, remote, _ = repo
    (work / "notes.md").write_text("notes\nlocal only\n", encoding="utf-8")
    git(work, "commit", "-q", "-am", "local only")
    pushed_before = remote_head(remote)
    before, after = write_task(work, "- [ ] Owned task")

    receipt = persister(tmp_path, work, remote).persist_file(
        work / "tasks.md", before, after, operation_id="op-1", message="tasks: add\n"
    )

    assert receipt["state"] == "committed"
    assert receipt["error"] == "unrelated_local_commits: 1 would be published"
    assert remote_head(remote) == pushed_before


def test_multi_file_change_lands_in_one_commit(repo, tmp_path):
    work, remote, _ = repo
    before, after = write_task(work, "- [ ] Owned task")
    (work / "session-log.md").write_text("# Session Log\n\n## entry\n", encoding="utf-8")
    tool = persister(tmp_path, work, remote)

    receipt = tool.persist(
        tool.policies[0],
        [OwnedChange("tasks.md", before, after),
         OwnedChange("session-log.md", None, "# Session Log\n\n## entry\n")],
        operation_id="op-1",
        message="tasks and log\n",
    )

    assert receipt["state"] == "pushed"
    assert sorted(git(work, "show", "--name-only", "--format=", receipt["commit"]).split()) == [
        "session-log.md", "tasks.md",
    ]


def test_cohesion_task_update_is_pushed_without_another_request(repo, tmp_path):
    work, remote, _ = repo
    calendars = tmp_path / "calendars.json"
    write_calendars(calendars)
    service = cohesion.CohesionService(
        db_path=tmp_path / "cohesion.sqlite3",
        tasks_path=work / "tasks.md",
        calendar=FakeCalendar(),
        calendars_path=calendars,
        persister=persister(tmp_path, work, remote),
    )

    receipt = service.submit({
        "version": 1,
        "source": {
            "id": "telegram:1:r1",
            "kind": "telegram_message",
            "native_id": "-100:1",
            "revision": 1,
            "timestamp": "2026-09-24T08:00:00+08:00",
        },
        "intent": {"action": "upsert", "category": "quick_task", "title": "Buy milk",
                   "area": "personal", "placement": "tasks"},
    })

    task = next(item for item in receipt["applied"] if item["destination"] == "tasks")
    persistence = task["result"]["persistence"]
    assert persistence["state"] == "pushed"
    assert "Buy milk" in git(remote, "show", "refs/heads/main:tasks.md")
    assert json.loads(json.dumps(persistence))["commit"] == remote_head(remote)


def test_replay_after_a_crash_before_the_receipt_resumes_the_push(repo, tmp_path):
    """The process died after writing tasks.md, so the operation is still pending."""
    work, remote, _ = repo
    calendars = tmp_path / "calendars.json"
    write_calendars(calendars)
    offline = {"value": True}

    def runner(argv, **kwargs):
        if offline["value"] and argv[1] in {"push", "ls-remote"}:
            return subprocess.CompletedProcess(argv, 128, "", "fatal: Could not resolve host")
        return subprocess.run(argv, **kwargs)

    service = cohesion.CohesionService(
        db_path=tmp_path / "cohesion.sqlite3",
        tasks_path=work / "tasks.md",
        calendar=FakeCalendar(),
        calendars_path=calendars,
        persister=persister(tmp_path, work, remote, runner=runner),
    )
    request = {
        "version": 1,
        "source": {
            "id": "telegram:2:r1",
            "kind": "telegram_message",
            "native_id": "-100:2",
            "revision": 1,
            "timestamp": "2026-09-24T08:00:00+08:00",
        },
        "intent": {"action": "upsert", "category": "quick_task", "title": "Call bank",
                   "area": "personal", "placement": "tasks"},
    }

    first = service.submit(request)
    task_op = first["applied"][0]
    service._finish_operation(task_op["operation_id"], "pending", None, None, "push pending")
    offline["value"] = False
    second = service.submit(request)

    assert task_op["result"]["persistence"]["state"] == "committed"
    persistence = second["applied"][0]["result"]["persistence"]
    assert persistence["state"] == "pushed"
    assert persistence["commit"] == task_op["result"]["persistence"]["commit"]
    assert git(work, "rev-list", "--count", "HEAD") == "2"


def test_next_push_carries_an_earlier_unpushed_commit(repo, tmp_path):
    work, remote, _ = repo
    offline = {"value": True}

    def runner(argv, **kwargs):
        if offline["value"] and argv[1] in {"push", "ls-remote"}:
            return subprocess.CompletedProcess(argv, 128, "", "fatal: Could not resolve host")
        return subprocess.run(argv, **kwargs)

    tool = persister(tmp_path, work, remote, runner=runner)
    before, after = write_task(work, "- [ ] First")
    first = tool.persist_file(work / "tasks.md", before, after, operation_id="op-1", message="one\n")
    offline["value"] = False
    before, after = write_task(work, "- [ ] Second")
    second = tool.persist_file(work / "tasks.md", before, after, operation_id="op-2", message="two\n")

    assert first["state"] == "committed" and second["state"] == "pushed"
    assert tool.store.get("op-1")["state"] == "pushed"
    assert remote_head(remote) == second["commit"]


def test_retry_pushes_recorded_commits_for_a_timer(repo, tmp_path):
    work, remote, _ = repo
    offline = {"value": True}

    def runner(argv, **kwargs):
        if offline["value"] and argv[1] in {"push", "ls-remote"}:
            return subprocess.CompletedProcess(argv, 128, "", "fatal: Could not resolve host")
        return subprocess.run(argv, **kwargs)

    tool = persister(tmp_path, work, remote, runner=runner)
    before, after = write_task(work, "- [ ] First")
    committed = tool.persist_file(work / "tasks.md", before, after, operation_id="op-1", message="one\n")
    offline["value"] = False

    retried = tool.retry_unpushed()

    assert committed["state"] == "committed"
    assert [item["state"] for item in retried] == ["pushed"]
    assert remote_head(remote) == committed["commit"]
    assert tool.retry_unpushed() == []
