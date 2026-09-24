import datetime as dt
import json
from pathlib import Path

import pytest

import cohesion
import evening_debrief
import sync_completed_tickets as sync
from sync_completed_tickets import _parse_item, completion_lines, move_line, run
from test_cohesion import FakeCalendar, write_calendars

REPO = "achibukz/achiCore"
NOW = dt.datetime(2026, 9, 24, 3, 0, tzinfo=dt.UTC)
DATE = dt.date(2026, 9, 24)


def issue(number, *, state="closed", reason="completed", closed="2026-09-24T01:00:00Z",
          updated=None, title=None):
    return {
        "number": number,
        "title": title or f"Issue {number}",
        "html_url": f"https://github.com/{REPO}/issues/{number}",
        "state": state,
        "state_reason": reason if state == "closed" else ("reopened" if reason == "reopened" else None),
        "closed_at": closed if state == "closed" else None,
        "updated_at": updated or closed or "2026-09-24T01:00:00Z",
    }


def pull(number, *, merged="2026-09-24T01:00:00Z", closed=None, updated=None):
    return {
        "number": number,
        "title": f"PR {number}",
        "html_url": f"https://github.com/{REPO}/pull/{number}",
        "state": "closed" if (merged or closed) else "open",
        "state_reason": None,
        "closed_at": merged or closed,
        "updated_at": updated or merged or closed or "2026-09-24T01:00:00Z",
        "pull_request": {"merged_at": merged},
    }


class FakeGitHub:
    def __init__(self, items=(), closes=None):
        self.items = {REPO: list(items)}
        self.closes = closes or {}
        self.since = []
        self.fetched = []

    def updated_since(self, repo, since):
        self.since.append((repo, since))
        threshold = since.astimezone(dt.UTC)
        return [
            _parse_item(repo, data)
            for data in self.items.get(repo, [])
            if dt.datetime.fromisoformat(data["updated_at"].replace("Z", "+00:00")) >= threshold
        ]

    def item(self, repo, kind, number):
        self.fetched.append((repo.lower(), kind, number))
        stored = next((items for name, items in self.items.items() if name.lower() == repo.lower()), [])
        for data in stored:
            if data["number"] == number and ("pull_request" in data) == (kind == "pull"):
                return _parse_item(repo, data)
        return _parse_item(repo, issue(number, state="open"))

    def closing_issues(self, repo, number):
        return tuple(sync.item_key(repo, "issue", n) for n in self.closes.get(number, ()))


def link(kind, number, repo=REPO):
    return f"[#{number}](https://github.com/{repo}/{'pull' if kind == 'pull' else 'issues'}/{number})"


@pytest.fixture
def tasks(tmp_path):
    path = tmp_path / "tasks.md"

    def write(*active, done=()):
        body = "# Tasks\n\n## Active\n" + "".join(f"{line}\n" for line in active)
        body += "\n## Blocked\n\n## Done\n" + "".join(f"{line}\n" for line in done)
        path.write_text(body, encoding="utf-8")
        return path

    return write


def sync_run(tmp_path, github, tasks_path, **changes):
    values = {
        "date": DATE,
        "repositories": [REPO],
        "github": github,
        "store_path": tmp_path / "completions.sqlite3",
        "tasks_path": tasks_path,
        "towork_path": tmp_path / "jobs.json",
        "now": NOW,
        **changes,
    }
    return run(**values)


def section(path, name):
    lines = path.read_text(encoding="utf-8").splitlines()
    start = lines.index(f"## {name}") + 1
    end = next((i for i in range(start, len(lines)) if lines[i].startswith("## ")), len(lines))
    return [line for line in lines[start:end] if line.strip()]


def test_completed_linked_issue_moves_its_task_to_done_once(tmp_path, tasks):
    path = tasks(f"- [ ] Fix the parser {link('issue', 5)} #achicore !high", "- [ ] Unrelated #x")
    github = FakeGitHub([issue(5)])

    first = sync_run(tmp_path, github, path)
    second = sync_run(tmp_path, github, path, now=NOW + dt.timedelta(hours=1))

    assert section(path, "Done") == [
        f"- [x] Fix the parser {link('issue', 5)} #achicore !high (done 2026-09-24)"
    ]
    assert section(path, "Active") == ["- [ ] Unrelated #x"]
    assert len(first["completed_tasks"]) == 1 and second["completed_tasks"] == []
    assert completion_lines(DATE, tmp_path / "completions.sqlite3") == []


def test_issue_and_its_merged_pr_are_one_piece_of_work(tmp_path, tasks):
    path = tasks("- [ ] Nothing linked")
    github = FakeGitHub([issue(7, title="Retry fetches"), pull(8)], closes={8: [7]})

    sync_run(tmp_path, github, path)

    assert completion_lines(DATE, tmp_path / "completions.sqlite3") == ["Retry fetches (achiCore #7)"]


def test_towork_job_links_a_pr_to_its_issue_without_completing_anything(tmp_path, tasks):
    path = tasks("- [ ] Nothing linked")
    (tmp_path / "jobs.json").write_text(json.dumps({
        "job": {"repository": REPO, "issue_number": 7, "pr_number": 8, "stage": "completed"},
        "shipped": {"repository": REPO, "issue_number": 9, "pr_number": 10, "stage": "hitl_passed"},
    }), encoding="utf-8")
    github = FakeGitHub([issue(7, title="Retry fetches"), pull(8), pull(10, merged=None)])

    sync_run(tmp_path, github, path)

    assert completion_lines(DATE, tmp_path / "completions.sqlite3") == ["Retry fetches (achiCore #7)"]


def test_renamed_issue_still_matches_by_link(tmp_path, tasks):
    path = tasks(f"- [ ] Old wording for the task {link('issue', 5)}")
    github = FakeGitHub([issue(5, title="A completely new title")])

    sync_run(tmp_path, github, path)

    assert section(path, "Active") == []


@pytest.mark.parametrize("item", [
    issue(5, reason="not_planned"),
    issue(5, reason="duplicate"),
])
def test_not_planned_closure_completes_nothing(tmp_path, tasks, item):
    path = tasks(f"- [ ] Fix the parser {link('issue', 5)}")

    report = sync_run(tmp_path, FakeGitHub([item]), path)

    assert report["completed_tasks"] == []
    assert len(section(path, "Active")) == 1
    assert completion_lines(DATE, tmp_path / "completions.sqlite3") == []


def test_unmerged_and_unrelated_prs_complete_nothing(tmp_path, tasks):
    path = tasks(
        f"- [ ] Land the PR {link('pull', 11)}",
        f"- [ ] Fix the issue {link('issue', 5)}",
    )
    github = FakeGitHub([pull(11, merged=None, closed="2026-09-24T01:00:00Z"), pull(12), issue(5, state="open")])

    report = sync_run(tmp_path, github, path)

    assert report["completed_tasks"] == []
    assert len(section(path, "Active")) == 2


def test_merged_pr_completes_a_task_linked_to_that_pr(tmp_path, tasks):
    path = tasks(f"- [ ] Review {link('pull', 21)}")

    sync_run(tmp_path, FakeGitHub([pull(21)]), path)

    assert section(path, "Done") == [f"- [x] Review {link('pull', 21)} (done 2026-09-24)"]


def test_issue_and_pr_numbers_do_not_collide(tmp_path, tasks):
    path = tasks(f"- [ ] Fix issue five {link('issue', 5)}")

    sync_run(tmp_path, FakeGitHub([pull(5)]), path)

    assert len(section(path, "Active")) == 1


def test_multi_link_task_waits_for_every_link(tmp_path, tasks):
    path = tasks(f"- [ ] Ship the batch {link('issue', 5)} and {link('issue', 6)}")
    github = FakeGitHub([issue(5)])

    waiting = sync_run(tmp_path, github, path)
    github.items[REPO].append(issue(6, closed="2026-09-24T02:00:00Z"))
    done = sync_run(tmp_path, github, path, now=NOW + dt.timedelta(hours=1))

    assert waiting["waiting"][0]["waiting_on"] == [sync.item_key(REPO, "issue", 6)]
    assert (REPO.lower(), "issue", 6) in github.fetched
    assert len(done["completed_tasks"]) == 1


def test_link_closed_before_the_poll_window_is_verified_directly(tmp_path, tasks):
    path = tasks(f"- [ ] Ship the batch {link('issue', 5)} and {link('issue', 6)}")
    github = FakeGitHub([issue(5), issue(6, closed="2026-08-01T00:00:00Z")])

    report = sync_run(tmp_path, github, path)

    assert len(report["completed_tasks"]) == 1
    assert (REPO.lower(), "issue", 6) in github.fetched


def test_item_linked_from_two_tasks_is_a_conflict(tmp_path, tasks):
    path = tasks(f"- [ ] First {link('issue', 5)}", f"- [ ] Second {link('issue', 5)}")

    report = sync_run(tmp_path, FakeGitHub([issue(5)]), path)

    assert report["completed_tasks"] == []
    assert {c["reason"] for c in report["conflicts"]} == {"ambiguous_task_match"}
    assert len(section(path, "Active")) == 2


def test_reopened_issue_moves_the_task_back(tmp_path, tasks):
    path = tasks(f"- [ ] Fix the parser {link('issue', 5)}")
    github = FakeGitHub([issue(5)])
    sync_run(tmp_path, github, path)

    github.items[REPO] = [issue(5, state="open", reason="reopened", updated="2026-09-24T05:00:00Z")]
    report = sync_run(tmp_path, github, path, now=NOW + dt.timedelta(hours=3))

    assert section(path, "Active") == [f"- [ ] Fix the parser {link('issue', 5)}"]
    assert section(path, "Done") == []
    assert len(report["reopened_tasks"]) == 1
    assert completion_lines(DATE, tmp_path / "completions.sqlite3") == []


def test_reopen_after_a_manual_edit_is_a_conflict(tmp_path, tasks):
    path = tasks(f"- [ ] Fix the parser {link('issue', 5)}")
    github = FakeGitHub([issue(5)])
    sync_run(tmp_path, github, path)
    path.write_text(path.read_text(encoding="utf-8").replace("(done 2026-09-24)", "(done, with notes)"),
                    encoding="utf-8")

    github.items[REPO] = [issue(5, state="open", reason="reopened", updated="2026-09-24T05:00:00Z")]
    report = sync_run(tmp_path, github, path, now=NOW + dt.timedelta(hours=3))

    assert report["conflicts"] == [{"key": sync.item_key(REPO, "issue", 5),
                                    "reason": "manual_edit_after_completion"}]
    assert "(done, with notes)" in section(path, "Done")[0]


def test_task_line_edited_before_the_write_is_a_conflict(tmp_path, tasks):
    path = tasks("- [ ] Original line")

    moved = move_line(path, "- [ ] Different line", "- [x] Different line", "## Done")

    assert moved is False
    assert section(path, "Active") == ["- [ ] Original line"]


def test_completion_after_midnight_counts_for_the_next_manila_day(tmp_path, tasks):
    path = tasks(f"- [ ] Late fix {link('issue', 5)}")
    github = FakeGitHub([issue(5, closed="2026-09-23T16:30:00Z")])

    sync_run(tmp_path, github, path, date=dt.date(2026, 9, 23))

    assert section(path, "Done")[0].endswith("(done 2026-09-24)")


def test_missed_polls_recover_work_finished_during_downtime(tmp_path, tasks):
    path = tasks("- [ ] Nothing linked")
    github = FakeGitHub([])
    sync_run(tmp_path, github, path)
    github.items[REPO] = [issue(9, title="Done while offline", closed="2026-09-24T02:30:00Z")]

    sync_run(tmp_path, github, path, now=NOW + dt.timedelta(days=2))

    assert github.since[1][1] == NOW - sync.OVERLAP
    assert completion_lines(DATE, tmp_path / "completions.sqlite3") == ["Done while offline (achiCore #9)"]


def test_first_run_starts_at_the_manila_day_minus_the_overlap(tmp_path, tasks):
    path = tasks("- [ ] Nothing linked")
    github = FakeGitHub([])

    sync_run(tmp_path, github, path)

    start = dt.datetime(2026, 9, 24, tzinfo=sync.MANILA) - sync.OVERLAP
    assert github.since[0][1] == start


def test_dry_run_changes_no_task_cursor_or_store(tmp_path, tasks):
    path = tasks(f"- [ ] Fix the parser {link('issue', 5)}")
    original = path.read_text(encoding="utf-8")

    report = sync_run(tmp_path, FakeGitHub([issue(5)]), path, dry_run=True)

    assert len(report["completed_tasks"]) == 1
    assert path.read_text(encoding="utf-8") == original
    assert not (tmp_path / "completions.sqlite3").exists()


def test_dry_run_leaves_an_existing_cursor_alone(tmp_path, tasks):
    path = tasks("- [ ] Nothing linked")
    github = FakeGitHub([])
    sync_run(tmp_path, github, path)

    sync_run(tmp_path, github, path, dry_run=True, now=NOW + dt.timedelta(days=1))
    sync_run(tmp_path, github, path, now=NOW + dt.timedelta(days=2))

    assert github.since[2][1] == NOW - sync.OVERLAP


def test_cohesion_tracked_task_completes_through_the_writer(tmp_path):
    tasks_path = tmp_path / "tasks.md"
    tasks_path.write_text("# Tasks\n\n## Active\n\n## Blocked\n\n## Done\n", encoding="utf-8")
    calendars = tmp_path / "calendars.json"
    write_calendars(calendars)
    service = cohesion.CohesionService(
        db_path=tmp_path / "cohesion.sqlite3", tasks_path=tasks_path,
        calendar=FakeCalendar(), calendars_path=calendars,
    )
    created = service.submit({
        "version": 1,
        "source": {"id": "telegram:1:r1", "kind": "telegram_message", "native_id": "-100:1",
                   "revision": 1, "timestamp": "2026-09-23T08:00:00+08:00"},
        "intent": {"action": "upsert", "category": "quick_task",
                   "title": f"Fix the parser {link('issue', 5)}", "area": "systems",
                   "placement": "tasks"},
    })
    assert created["applied"]

    report = sync_run(tmp_path, FakeGitHub([issue(5)]), tasks_path, cohesion_service=service)

    assert report["completed_tasks"][0]["method"] == "cohesion"
    done = section(tasks_path, "Done")
    assert len(done) == 1 and done[0].startswith("- [x] Fix the parser") and "task-id:" in done[0]


def test_evening_debrief_lists_unlinked_work_beside_done_tasks(tmp_path, tasks, monkeypatch):
    path = tasks("- [ ] Nothing linked")
    sync_run(tmp_path, FakeGitHub([issue(9, title="Shipped without a task")]), path)
    monkeypatch.setattr(sync, "DEFAULT_DB", tmp_path / "completions.sqlite3")
    monkeypatch.setattr(evening_debrief, "TASKS_FILE", path)
    monkeypatch.setattr(evening_debrief, "fetch_tomorrow_events", lambda tomorrow: ([], []))
    monkeypatch.setattr(evening_debrief, "check_failures_today", lambda: [])
    monkeypatch.setattr(evening_debrief, "get_corrections_today", lambda day: [])

    message, _ = evening_debrief.build_evening_debrief(DATE)

    assert "Other finished work:" in message
    assert "• Shipped without a task (achiCore #9)" in message
    assert "Quiet day" not in message


def test_direct_completion_is_handed_to_owned_persistence(tmp_path, tasks):
    path = tasks(f"- [ ] Fix the parser {link('issue', 5)}")
    calls = []

    class Recorder:
        def persist_file(self, file, before, after, *, operation_id, message):
            calls.append((file, before, after, message))
            return {"state": "pushed", "operation_id": operation_id}

    report = sync_run(tmp_path, FakeGitHub([issue(5)]), path, persister=Recorder())

    assert len(calls) == 1
    file, before, after, message = calls[0]
    assert file == path and "- [ ] Fix the parser" in before and "- [x] Fix the parser" in after
    assert message.startswith("tasks: complete for achibukz/achicore#issue/5")
    assert report["persistence"][0]["state"] == "pushed"


def test_default_jobs_file_is_the_hub_state_directory():
    import importlib

    fresh = importlib.reload(sync)
    try:
        assert fresh.TOWORK_JOBS.parts[-2:] == ("achicore-hub", "to_work_jobs.json")
    finally:
        importlib.reload(sync)
