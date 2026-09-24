#!/usr/bin/env python3
"""Reconcile verified GitHub completions into tasks.md and the evening debrief.

A closed-as-completed issue or a merged PR is a completion. Closed as not
planned, closed without merge, open, SHIP verdicts and HITL results are not.
A task completes when every GitHub item it links is complete, and only when no
other open task links the same item. A merged PR folds into the issues it
closes, so an issue and its PR count as one piece of work.

Polling starts from a persisted cursor minus an overlap, so a missed run or
downtime across midnight still sees the completion. Dates are Asia/Manila.
--dry-run reads everything and changes neither tasks.md nor the cursors.

Usage:
    python scripts/sync_completed_tickets.py [--date YYYY-MM-DD] [--dry-run]
        [--repo owner/name ...]
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import re
import sqlite3
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Iterable
from zoneinfo import ZoneInfo

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

MANILA = ZoneInfo("Asia/Manila")
DEFAULT_REPOSITORIES = ("achibukz/achiCore", "achibukz/AIS-OS", "achibukz/career-ops")
DEFAULT_DB = Path.home() / ".local" / "state" / "achios" / "completions.sqlite3"
TOWORK_JOBS = Path.home() / ".local" / "state" / "achi-core" / "to_work_jobs.json"
TASKS_FILE = SCRIPT_DIR.parent / "tasks.md"
OVERLAP = dt.timedelta(hours=6)
GH_TIMEOUT_SECONDS = 60

LINK_RE = re.compile(r"https://github\.com/([\w.-]+/[\w.-]+)/(issues|pull)/(\d+)")
TASK_RE = re.compile(r"^- \[([ x~])\] (.*\S)\s*$")
TASK_ID_RE = re.compile(r"<!--\s*task-id:\s*([A-Za-z0-9][A-Za-z0-9._:-]*)\s*-->")
FENCE_RE = re.compile(r"^\s*```")
DONE_OUTCOMES = {"completed", "merged"}


class SyncError(RuntimeError):
    pass


def item_key(repo: str, kind: str, number: int) -> str:
    """Issue and PR numbers share a counter but not a meaning, so kind is part of the key."""
    return f"{repo.lower()}#{kind}/{number}"


@dataclass(frozen=True)
class WorkItem:
    key: str
    repo: str
    kind: str
    number: int
    title: str
    url: str
    outcome: str
    at: str | None
    closes: tuple[str, ...] = ()


def _parse_item(repo: str, data: dict) -> WorkItem:
    pull = data.get("pull_request")
    kind = "pull" if pull else "issue"
    if pull:
        if pull.get("merged_at"):
            outcome, at = "merged", pull["merged_at"]
        elif data.get("state") == "closed":
            outcome, at = "unmerged", data.get("closed_at")
        else:
            outcome, at = "open", None
    elif data.get("state") == "closed":
        # GitHub leaves state_reason null on issues closed before it existed.
        reason = data.get("state_reason") or "completed"
        outcome = "completed" if reason == "completed" else reason
        at = data.get("closed_at")
    else:
        outcome, at = "open", None
    return WorkItem(
        key=item_key(repo, kind, int(data["number"])),
        repo=repo,
        kind=kind,
        number=int(data["number"]),
        title=str(data.get("title") or ""),
        url=str(data.get("html_url") or ""),
        outcome=outcome,
        at=at,
    )


class GitHub:
    def __init__(self, runner: Callable[..., subprocess.CompletedProcess] = subprocess.run):
        self.runner = runner

    def _gh(self, *args: str) -> Any:
        completed = self.runner(
            ["gh", *args], capture_output=True, text=True, timeout=GH_TIMEOUT_SECONDS, check=False
        )
        if completed.returncode != 0:
            raise SyncError(f"gh {' '.join(args[:2])} failed: {completed.stderr.strip()}")
        return json.loads(completed.stdout or "null")

    def updated_since(self, repo: str, since: dt.datetime) -> list[WorkItem]:
        stamp = since.astimezone(dt.UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
        pages = self._gh(
            "api", "--paginate", "--slurp",
            f"repos/{repo}/issues?state=all&per_page=100&since={stamp}",
        )
        return [_parse_item(repo, data) for page in pages for data in page]

    def item(self, repo: str, kind: str, number: int) -> WorkItem:
        return _parse_item(repo, self._gh("api", f"repos/{repo}/issues/{number}"))

    def closing_issues(self, repo: str, number: int) -> tuple[str, ...]:
        data = self._gh("pr", "view", str(number), "-R", repo, "--json", "closingIssuesReferences")
        return tuple(
            item_key(f"{ref['repository']['owner']['login']}/{ref['repository']['name']}", "issue", ref["number"])
            for ref in data.get("closingIssuesReferences") or []
        )


def towork_links(path: Path | None = None) -> dict[str, set[str]]:
    """PR key to issue keys from /ToWork jobs. A job stage never completes anything."""
    source = Path(path) if path else TOWORK_JOBS
    if not source.is_file():
        return {}
    data = json.loads(source.read_text(encoding="utf-8"))
    jobs = data.values() if isinstance(data, dict) else data
    links: dict[str, set[str]] = {}
    for job in jobs:
        if not isinstance(job, dict) or not job.get("pr_number") or not job.get("repository"):
            continue
        pull = item_key(job["repository"], "pull", int(job["pr_number"]))
        links.setdefault(pull, set()).add(item_key(job["repository"], "issue", int(job["issue_number"])))
    return links


def _manila_date(value: str) -> str:
    return dt.datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(MANILA).date().isoformat()


class Store:
    def __init__(self, path: Path, *, read_only: bool = False):
        self.path = Path(path)
        if read_only:
            self.connection = sqlite3.connect(":memory:")
            if self.path.is_file():
                with sqlite3.connect(f"file:{self.path}?mode=ro", uri=True) as source:
                    source.backup(self.connection)
        else:
            self.path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
            self.connection = sqlite3.connect(self.path)
        self.connection.row_factory = sqlite3.Row
        self.connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS cursors (repo TEXT PRIMARY KEY, polled_at TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS work_items (
                key TEXT PRIMARY KEY, repo TEXT NOT NULL, kind TEXT NOT NULL,
                number INTEGER NOT NULL, title TEXT NOT NULL, url TEXT NOT NULL,
                outcome TEXT NOT NULL, at TEXT, manila_date TEXT,
                closes_json TEXT NOT NULL, recorded_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS task_completions (
                task_line TEXT NOT NULL, done_line TEXT, task_id TEXT,
                method TEXT NOT NULL, links_json TEXT NOT NULL,
                manila_date TEXT NOT NULL, applied_at TEXT NOT NULL,
                reopened_at TEXT
            );
            CREATE TABLE IF NOT EXISTS conflicts (
                key TEXT NOT NULL, reason TEXT NOT NULL, detail TEXT, at TEXT NOT NULL,
                PRIMARY KEY (key, reason)
            );
            """
        )

    def close(self) -> None:
        self.connection.commit()
        self.connection.close()

    def cursor(self, repo: str) -> dt.datetime | None:
        row = self.connection.execute("SELECT polled_at FROM cursors WHERE repo=?", (repo,)).fetchone()
        return dt.datetime.fromisoformat(row[0]) if row else None

    def set_cursor(self, repo: str, at: dt.datetime) -> None:
        self.connection.execute(
            "INSERT INTO cursors VALUES(?,?) ON CONFLICT(repo) DO UPDATE SET polled_at=excluded.polled_at",
            (repo, at.isoformat()),
        )

    def record(self, item: WorkItem, now: dt.datetime) -> None:
        self.connection.execute(
            """INSERT INTO work_items VALUES(?,?,?,?,?,?,?,?,?,?,?)
               ON CONFLICT(key) DO UPDATE SET title=excluded.title, outcome=excluded.outcome,
               at=excluded.at, manila_date=excluded.manila_date,
               closes_json=CASE WHEN excluded.closes_json='[]' THEN work_items.closes_json
                                ELSE excluded.closes_json END""",
            (
                item.key, item.repo, item.kind, item.number, item.title, item.url, item.outcome,
                item.at, _manila_date(item.at) if item.at else None,
                json.dumps(sorted(item.closes)), now.isoformat(),
            ),
        )

    def outcome(self, key: str) -> str | None:
        row = self.connection.execute("SELECT outcome FROM work_items WHERE key=?", (key,)).fetchone()
        return row[0] if row else None

    def work_item(self, key: str) -> sqlite3.Row | None:
        return self.connection.execute("SELECT * FROM work_items WHERE key=?", (key,)).fetchone()

    def conflict(self, key: str, reason: str, detail: str, now: dt.datetime) -> None:
        self.connection.execute(
            "INSERT OR REPLACE INTO conflicts VALUES(?,?,?,?)", (key, reason, detail, now.isoformat())
        )

    def active_completion(self, link: str) -> sqlite3.Row | None:
        for row in self.connection.execute(
            "SELECT rowid, * FROM task_completions WHERE reopened_at IS NULL ORDER BY rowid DESC"
        ):
            if link in json.loads(row["links_json"]):
                return row
        return None


@dataclass(frozen=True)
class TaskLine:
    index: int
    line: str
    done: bool
    links: frozenset[str]
    task_id: str | None


def parse_task_lines(content: str) -> list[TaskLine]:
    tasks = []
    in_fence = False
    for index, line in enumerate(content.splitlines()):
        if FENCE_RE.match(line):
            in_fence = not in_fence
            continue
        match = None if in_fence else TASK_RE.match(line)
        if not match:
            continue
        links = frozenset(
            item_key(repo, "pull" if kind == "pull" else "issue", int(number))
            for repo, kind, number in LINK_RE.findall(line)
        )
        task_id = TASK_ID_RE.search(line)
        tasks.append(TaskLine(index, line, match.group(1) == "x", links, task_id.group(1) if task_id else None))
    return tasks


def done_line(line: str, date: str) -> str:
    body = line[len("- [ ] "):]
    marker = TASK_ID_RE.search(body)
    if marker:
        body = f"{body[:marker.start()].rstrip()} (done {date}) {marker.group(0)}"
    else:
        body = f"{body} (done {date})"
    return f"- [x] {body}"


def _write_atomic(path: Path, content: str) -> None:
    descriptor, temporary = tempfile.mkstemp(dir=path.parent, prefix=f".{path.name}.", text=True)
    try:
        os.fchmod(descriptor, path.stat().st_mode & 0o777)
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def move_line(path: Path, expected: str, replacement: str, section: str) -> bool:
    """Move one exact line under a section. False when the line changed or repeats."""
    content = path.read_text(encoding="utf-8")
    lines = content.splitlines()
    matches = [index for index, line in enumerate(lines) if line == expected]
    if len(matches) != 1 or section not in lines:
        return False
    lines.pop(matches[0])
    lines.insert(lines.index(section) + 1, replacement)
    _write_atomic(path, "\n".join(lines) + ("\n" if content.endswith("\n") else ""))
    return True


def _source_time(at: str) -> str:
    return dt.datetime.fromisoformat(at.replace("Z", "+00:00")).astimezone(MANILA).isoformat()


def run(
    *,
    date: dt.date,
    dry_run: bool = False,
    repositories: Iterable[str] = DEFAULT_REPOSITORIES,
    github: GitHub | None = None,
    store_path: Path | None = None,
    tasks_path: Path | None = None,
    towork_path: Path | None = None,
    cohesion_service: Any = None,
    now: dt.datetime | None = None,
) -> dict:
    github = github or GitHub()
    tasks_path = Path(tasks_path) if tasks_path else TASKS_FILE
    now = now or dt.datetime.now(dt.UTC)
    store = Store(Path(store_path) if store_path else DEFAULT_DB, read_only=dry_run)
    report: dict[str, Any] = {
        "date": date.isoformat(), "dry_run": dry_run, "polled": [], "completed_tasks": [],
        "reopened_tasks": [], "waiting": [], "conflicts": [], "errors": [],
    }
    day_start = dt.datetime.combine(date, dt.time(), MANILA)
    pr_links = towork_links(towork_path)
    seen: list[WorkItem] = []
    for repo in repositories:
        since = (store.cursor(repo) or day_start) - OVERLAP
        try:
            items = github.updated_since(repo, since)
        except SyncError as exc:
            report["errors"].append(str(exc))
            continue
        for item in items:
            if item.kind == "pull" and item.outcome == "merged":
                try:
                    closes = set(github.closing_issues(repo, item.number))
                except SyncError as exc:
                    report["errors"].append(str(exc))
                    closes = set()
                closes |= pr_links.get(item.key, set())
                item = WorkItem(**{**item.__dict__, "closes": tuple(sorted(closes))})
            seen.append(item)
        report["polled"].append({"repo": repo, "since": since.isoformat(), "items": len(items)})
        if not dry_run:
            store.set_cursor(repo, now)

    for item in seen:
        previous = store.outcome(item.key)
        if item.outcome in DONE_OUTCOMES or previous in DONE_OUTCOMES:
            store.record(item, now)
        if previous in DONE_OUTCOMES and item.outcome == "open":
            _reopen(store, item, tasks_path, dry_run, report, now)

    _complete_tasks(store, github, tasks_path, dry_run, cohesion_service, report, now)
    if not dry_run:
        store.close()
    return report


def _reopen(store, item, tasks_path, dry_run, report, now) -> None:
    record = store.active_completion(item.key)
    if record is None:
        return
    if record["method"] == "cohesion":
        store.conflict(item.key, "reopen_requires_clarification", record["task_line"], now)
        report["conflicts"].append({"key": item.key, "reason": "reopen_requires_clarification"})
        return
    if dry_run:
        report["reopened_tasks"].append({"key": item.key, "task": record["task_line"]})
        return
    if move_line(tasks_path, record["done_line"], record["task_line"], "## Active"):
        store.connection.execute(
            "UPDATE task_completions SET reopened_at=? WHERE rowid=?", (now.isoformat(), record["rowid"])
        )
        report["reopened_tasks"].append({"key": item.key, "task": record["task_line"]})
    else:
        store.conflict(item.key, "manual_edit_after_completion", record["done_line"], now)
        report["conflicts"].append({"key": item.key, "reason": "manual_edit_after_completion"})


def _link_done(store, github, key, report, now) -> bool:
    outcome = store.outcome(key)
    if outcome is not None:
        return outcome in DONE_OUTCOMES
    repo, rest = key.split("#", 1)
    kind, number = rest.split("/")
    try:
        item = github.item(repo, kind, int(number))
    except SyncError as exc:
        report["errors"].append(str(exc))
        return False
    if item.outcome in DONE_OUTCOMES:
        store.record(item, now)
        return True
    return False


def _complete_tasks(store, github, tasks_path, dry_run, cohesion_service, report, now) -> None:
    if not tasks_path.is_file():
        return
    tasks = parse_task_lines(tasks_path.read_text(encoding="utf-8"))
    open_tasks = [task for task in tasks if not task.done and task.links]
    owners: dict[str, list[TaskLine]] = {}
    for task in open_tasks:
        for link in task.links:
            owners.setdefault(link, []).append(task)
    for task in open_tasks:
        if not any(store.outcome(link) in DONE_OUTCOMES for link in task.links):
            continue
        shared = [link for link in task.links if len(owners[link]) > 1]
        if shared:
            for link in shared:
                store.conflict(link, "ambiguous_task_match", task.line, now)
                report["conflicts"].append({"key": link, "reason": "ambiguous_task_match"})
            continue
        pending = [link for link in sorted(task.links) if not _link_done(store, github, link, report, now)]
        if pending:
            report["waiting"].append({"task": task.line, "waiting_on": pending})
            continue
        finished = max(store.work_item(link)["at"] for link in task.links)
        date = _manila_date(finished)
        entry = {"task": task.line, "links": sorted(task.links), "date": date}
        if dry_run:
            report["completed_tasks"].append(entry)
            continue
        applied = _apply_completion(store, task, finished, date, tasks_path, cohesion_service, report, now)
        if applied:
            report["completed_tasks"].append({**entry, "method": applied})


def _apply_completion(store, task, finished, date, tasks_path, cohesion_service, report, now) -> str | None:
    key = sorted(task.links)[0]
    if task.task_id and cohesion_service is not None:
        item_id = cohesion_service.item_for_task(task.task_id)
        if item_id is not None:
            receipt = cohesion_service.submit({
                "version": 1,
                "source": {
                    "id": f"github-completion:{','.join(sorted(task.links))}",
                    "kind": "github_completion",
                    "native_id": key,
                    "revision": 1,
                    "timestamp": _source_time(finished),
                },
                "intent": {"action": "complete", "item_id": item_id},
            })
            if receipt.get("pending") or receipt.get("conflict"):
                detail = "; ".join(str(op.get("error")) for op in receipt.get("pending") or [])
                store.conflict(key, "cohesion_pending", detail or "conflict", now)
                report["conflicts"].append({"key": key, "reason": "cohesion_pending", "detail": detail})
                return None
            store.connection.execute(
                "INSERT INTO task_completions VALUES(?,?,?,?,?,?,?,NULL)",
                (task.line, None, task.task_id, "cohesion", json.dumps(sorted(task.links)), date, now.isoformat()),
            )
            return "cohesion"
    replacement = done_line(task.line, date)
    if not move_line(tasks_path, task.line, replacement, "## Done"):
        store.conflict(key, "task_line_changed", task.line, now)
        report["conflicts"].append({"key": key, "reason": "task_line_changed"})
        return None
    store.connection.execute(
        "INSERT INTO task_completions VALUES(?,?,?,?,?,?,?,NULL)",
        (task.line, replacement, task.task_id, "direct", json.dumps(sorted(task.links)), date, now.isoformat()),
    )
    return "direct"


def completion_lines(date: dt.date, store_path: Path | None = None) -> list[str]:
    """Work finished on this Manila date that no task already reports."""
    path = Path(store_path) if store_path else DEFAULT_DB
    if not path.is_file():
        return []
    store = Store(path, read_only=True)
    rows = store.connection.execute(
        "SELECT * FROM work_items WHERE manila_date=? AND outcome IN ('completed','merged') ORDER BY at",
        (date.isoformat(),),
    ).fetchall()
    tasked = set()
    for row in store.connection.execute("SELECT links_json FROM task_completions WHERE reopened_at IS NULL"):
        tasked |= set(json.loads(row[0]))
    recorded = {row["key"] for row in rows}
    lines = []
    for row in rows:
        closes = set(json.loads(row["closes_json"]))
        if row["key"] in tasked or closes & tasked:
            continue
        # A merged PR stands in for its issues only when none of them is listed.
        if closes and closes & recorded:
            continue
        label = f"{row['repo'].split('/')[-1]} {'PR ' if row['kind'] == 'pull' else ''}#{row['number']}"
        lines.append(f"{row['title']} ({label})")
    store.connection.close()
    return lines


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--date", type=dt.date.fromisoformat, default=None)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--repo", action="append", dest="repos")
    args = parser.parse_args(argv)
    date = args.date or dt.datetime.now(MANILA).date()
    import cohesion

    report = run(
        date=date,
        dry_run=args.dry_run,
        repositories=args.repos or DEFAULT_REPOSITORIES,
        cohesion_service=None if args.dry_run else cohesion.CohesionService(),
    )
    print(json.dumps(report, ensure_ascii=False, sort_keys=True))
    return 1 if report["errors"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
