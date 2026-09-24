#!/usr/bin/env python3
"""Commit and push only the changes a writer owns, then prove the remote has them.

A writer reports the text it read and the text it wrote for each file. The
commit tree is built in a temporary index seeded from HEAD, and each file's blob
is a three-way merge of those texts with HEAD. The result is HEAD plus the
writer's hunks and nothing else, so unrelated dirty hunks, staged work and the
working tree stay as they were. Overlapping hunks are a conflict, not a commit.

The commit lands with a compare-and-swap on HEAD, so a concurrent commit is never
reverted. Push success is proven from the remote ref, not the push exit status.
Saved, committed and pushed stay distinct in every receipt.
"""

from __future__ import annotations

import argparse
import datetime as dt
import fcntl
import fnmatch
import json
import os
import sqlite3
import subprocess
import sys
import tempfile
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Iterable

CONFIG_PATH = Path.home() / ".config" / "achios" / "persistence.json"
DEFAULT_DB = Path.home() / ".local" / "state" / "achios" / "persistence.sqlite3"
PUSH_TIMEOUT_SECONDS = 20
GIT_TIMEOUT_SECONDS = 60


class PersistenceError(RuntimeError):
    pass


@dataclass(frozen=True)
class OwnedChange:
    path: str
    before: str | None
    after: str


@dataclass(frozen=True)
class RepositoryPolicy:
    root: Path
    remote: str
    remote_url: str
    branch: str
    author_name: str
    author_email: str
    paths: tuple[str, ...]

    def owns(self, path: Path) -> str | None:
        """Return the repository-relative path when this policy may persist it."""
        try:
            relative = Path(path).resolve().relative_to(self.root.resolve()).as_posix()
        except ValueError:
            return None
        if any(fnmatch.fnmatchcase(relative, pattern) for pattern in self.paths):
            return relative
        return None


def load_policies(path: Path | None = None) -> list[RepositoryPolicy]:
    config = Path(path) if path else CONFIG_PATH
    if not config.is_file():
        return []
    data = json.loads(config.read_text(encoding="utf-8"))
    return [
        RepositoryPolicy(
            root=Path(entry["root"]).expanduser(),
            remote=entry["remote"],
            remote_url=entry["remote_url"],
            branch=entry["branch"],
            author_name=entry["author_name"],
            author_email=entry["author_email"],
            paths=tuple(entry["paths"]),
        )
        for entry in data.get("repositories", [])
    ]


def policy_for(path: Path, policies: Iterable[RepositoryPolicy]) -> tuple[RepositoryPolicy, str] | None:
    for policy in policies:
        relative = policy.owns(path)
        if relative is not None:
            return policy, relative
    return None


def _now() -> str:
    return dt.datetime.now(dt.UTC).isoformat()


class ReceiptStore:
    def __init__(self, path: Path | None = None):
        self.path = Path(path) if path else DEFAULT_DB
        self.path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        with self._connect() as connection:
            connection.execute(
                """CREATE TABLE IF NOT EXISTS persistence_receipts (
                       operation_id TEXT PRIMARY KEY,
                       repository TEXT NOT NULL,
                       paths_json TEXT NOT NULL,
                       state TEXT NOT NULL,
                       commit_sha TEXT,
                       error TEXT,
                       updated_at TEXT NOT NULL
                   )"""
            )

    @contextmanager
    def _connect(self):
        connection = sqlite3.connect(self.path)
        connection.row_factory = sqlite3.Row
        try:
            with connection:
                yield connection
        finally:
            connection.close()

    def get(self, operation_id: str) -> dict[str, Any] | None:
        with self._connect() as connection:
            row = connection.execute(
                "SELECT * FROM persistence_receipts WHERE operation_id=?", (operation_id,)
            ).fetchone()
        return dict(row) if row else None

    def commits(self, repository: str) -> set[str]:
        with self._connect() as connection:
            return {
                row[0]
                for row in connection.execute(
                    """SELECT commit_sha FROM persistence_receipts
                       WHERE repository=? AND commit_sha IS NOT NULL""",
                    (repository,),
                )
            }

    def unpushed(self, repository: str) -> list[dict[str, Any]]:
        with self._connect() as connection:
            return [
                dict(row)
                for row in connection.execute(
                    """SELECT * FROM persistence_receipts
                       WHERE repository=? AND state='committed' AND commit_sha IS NOT NULL
                       ORDER BY updated_at""",
                    (repository,),
                )
            ]

    def save(self, operation_id: str, repository: str, paths: list[str], receipt: dict) -> None:
        with self._connect() as connection:
            connection.execute(
                """INSERT INTO persistence_receipts VALUES(?,?,?,?,?,?,?)
                   ON CONFLICT(operation_id) DO UPDATE SET
                   state=excluded.state,commit_sha=excluded.commit_sha,
                   error=excluded.error,updated_at=excluded.updated_at""",
                (
                    operation_id,
                    repository,
                    json.dumps(paths),
                    receipt["state"],
                    receipt["commit"],
                    receipt["error"],
                    _now(),
                ),
            )


def _receipt(operation_id: str, state: str, commit: str | None = None, error: str | None = None) -> dict:
    return {
        "operation_id": operation_id,
        "state": state,
        "saved": True,
        "committed": commit is not None,
        "pushed": state == "pushed",
        "commit": commit,
        "error": error,
    }


class Git:
    def __init__(self, root: Path, runner: Callable[..., subprocess.CompletedProcess] = subprocess.run):
        self.root = Path(root)
        self.runner = runner

    def run(
        self,
        *args: str,
        env: dict[str, str] | None = None,
        input_text: str | None = None,
        check: bool = True,
        timeout: float = GIT_TIMEOUT_SECONDS,
    ) -> subprocess.CompletedProcess:
        merged_env = {**os.environ, **(env or {})}
        try:
            completed = self.runner(
                ["git", *args],
                cwd=self.root,
                env=merged_env,
                input=input_text,
                capture_output=True,
                text=True,
                timeout=timeout,
                check=False,
            )
        except subprocess.TimeoutExpired as exc:
            raise PersistenceError(f"git {args[0]} timed out") from exc
        if check and completed.returncode != 0:
            detail = (completed.stderr or completed.stdout).strip()
            raise PersistenceError(f"git {args[0]} failed: {detail}")
        return completed

    def out(self, *args: str, **kwargs) -> str:
        return self.run(*args, **kwargs).stdout.strip()

    def blob(self, revision: str, path: str) -> str | None:
        completed = self.run("cat-file", "blob", f"{revision}:{path}", check=False)
        return completed.stdout if completed.returncode == 0 else None

    def mode(self, revision: str, path: str) -> str:
        listing = self.out("ls-tree", revision, "--", path)
        return listing.split()[0] if listing else "100644"

    def is_ancestor(self, older: str, newer: str) -> bool:
        return self.run("merge-base", "--is-ancestor", older, newer, check=False).returncode == 0

    def has_object(self, sha: str) -> bool:
        return self.run("cat-file", "-e", f"{sha}^{{commit}}", check=False).returncode == 0


def _merge(git: Git, change: OwnedChange, head_text: str | None) -> str | None:
    """HEAD plus the writer's own hunks, or None when the hunks overlap other edits."""
    if change.before == head_text:
        return change.after
    with tempfile.TemporaryDirectory() as scratch:
        current = Path(scratch, "after")
        base = Path(scratch, "before")
        other = Path(scratch, "head")
        current.write_text(change.after, encoding="utf-8")
        base.write_text(change.before or "", encoding="utf-8")
        other.write_text(head_text or "", encoding="utf-8")
        completed = git.run(
            "merge-file", "-p", "--quiet", str(current), str(base), str(other), check=False
        )
    if completed.returncode != 0:
        return None
    return completed.stdout


@contextmanager
def _repository_lock(git: Git):
    common = Path(git.out("rev-parse", "--git-common-dir"))
    if not common.is_absolute():
        common = git.root / common
    with open(common / "achios-persist.lock", "a+", encoding="utf-8") as handle:
        fcntl.flock(handle, fcntl.LOCK_EX)
        yield


class Persister:
    def __init__(
        self,
        policies: Iterable[RepositoryPolicy] | None = None,
        *,
        store: ReceiptStore | None = None,
        runner: Callable[..., subprocess.CompletedProcess] = subprocess.run,
    ):
        self.policies = list(load_policies() if policies is None else policies)
        self._store = store
        self.runner = runner

    @property
    def store(self) -> ReceiptStore:
        if self._store is None:
            self._store = ReceiptStore()
        return self._store

    def persist_file(
        self, path: Path, before: str | None, after: str, *, operation_id: str, message: str
    ) -> dict | None:
        """Persist one written file. None means no policy covers the path."""
        match = policy_for(path, self.policies)
        if match is None:
            return None
        policy, relative = match
        return self.persist(
            policy, [OwnedChange(relative, before, after)], operation_id=operation_id, message=message
        )

    def persist(
        self,
        policy: RepositoryPolicy,
        changes: list[OwnedChange],
        *,
        operation_id: str,
        message: str,
    ) -> dict:
        git = Git(policy.root, self.runner)
        paths = [change.path for change in changes]
        repository = str(policy.root.resolve())
        try:
            with _repository_lock(git):
                receipt = self._persist_locked(git, policy, changes, operation_id, message, repository)
        except PersistenceError as exc:
            receipt = _receipt(operation_id, "saved", error=str(exc))
        self.store.save(operation_id, repository, paths, receipt)
        if receipt["state"] == "pushed":
            self._mark_carried(git, repository, receipt["commit"])
        return receipt

    def _mark_carried(self, git: Git, repository: str, pushed: str) -> None:
        """Earlier commits under a pushed one reached the remote with it."""
        for prior in self.store.unpushed(repository):
            if git.has_object(prior["commit_sha"]) and git.is_ancestor(prior["commit_sha"], pushed):
                self.store.save(
                    prior["operation_id"], repository, json.loads(prior["paths_json"]),
                    _receipt(prior["operation_id"], "pushed", prior["commit_sha"]),
                )

    def retry_unpushed(self) -> list[dict]:
        """Push every recorded commit that has not reached its remote yet."""
        receipts = []
        for policy in self.policies:
            repository = str(policy.root.resolve())
            pending = self.store.unpushed(repository)
            if not pending:
                continue
            newest = pending[-1]
            receipts.append(
                self.resume(policy.root / json.loads(newest["paths_json"])[0],
                            operation_id=newest["operation_id"])
            )
        return receipts

    def _persist_locked(self, git, policy, changes, operation_id, message, repository) -> dict:
        disallowed = [
            change.path for change in changes
            if not any(fnmatch.fnmatchcase(change.path, pattern) for pattern in policy.paths)
        ]
        if disallowed:
            return _receipt(operation_id, "saved", error=f"path_not_authorized: {', '.join(disallowed)}")
        branch = git.run("symbolic-ref", "--short", "HEAD", check=False).stdout.strip()
        if branch != policy.branch:
            return _receipt(operation_id, "saved", error=f"wrong_branch: {branch or 'detached'}")
        url = git.run("remote", "get-url", policy.remote, check=False).stdout.strip()
        if url != policy.remote_url:
            return _receipt(operation_id, "saved", error=f"wrong_remote: {url or 'missing'}")

        prior = self.store.get(operation_id)
        if prior and prior["state"] == "pushed":
            return _receipt(operation_id, "pushed", prior["commit_sha"])
        commit = prior["commit_sha"] if prior else None
        if commit and not (git.has_object(commit) and git.is_ancestor(commit, "HEAD")):
            commit = None
        created = commit is not None
        if commit is None:
            outcome = self._commit(git, policy, changes, message)
            if outcome["state"] != "committed":
                return _receipt(operation_id, outcome["state"], error=outcome["error"])
            commit, created = outcome["commit"], outcome["created"]
        return self._push(git, policy, commit, created, operation_id, repository)

    def resume(self, path: Path, *, operation_id: str) -> dict | None:
        """Retry the push of a recorded commit. None when nothing was recorded."""
        match = policy_for(path, self.policies)
        prior = self.store.get(operation_id)
        if match is None or prior is None:
            return None
        if prior["state"] == "pushed" or not prior["commit_sha"]:
            return _receipt(operation_id, prior["state"], prior["commit_sha"], prior["error"])
        policy = match[0]
        git = Git(policy.root, self.runner)
        repository = str(policy.root.resolve())
        try:
            with _repository_lock(git):
                receipt = self._push(git, policy, prior["commit_sha"], True, operation_id, repository)
        except PersistenceError as exc:
            receipt = _receipt(operation_id, "committed", prior["commit_sha"], str(exc))
        self.store.save(operation_id, repository, json.loads(prior["paths_json"]), receipt)
        if receipt["state"] == "pushed":
            self._mark_carried(git, repository, receipt["commit"])
        return receipt

    def _commit(self, git: Git, policy: RepositoryPolicy, changes: list[OwnedChange], message: str) -> dict:
        head = git.out("rev-parse", "HEAD")
        blobs = []
        for change in changes:
            head_text = git.blob(head, change.path)
            merged = _merge(git, change, head_text)
            if merged is None:
                return {"state": "conflict", "error": f"concurrent_changes_overlap: {change.path}"}
            if merged != head_text:
                blobs.append((change.path, merged))
        if not blobs:
            # The owned change is already in HEAD, from an earlier attempt or by hand.
            return {"state": "committed", "commit": head, "created": False, "error": None}

        with tempfile.TemporaryDirectory() as scratch:
            env = {"GIT_INDEX_FILE": str(Path(scratch, "index"))}
            git.run("read-tree", head, env=env)
            written = []
            for path, text in blobs:
                sha = git.out("hash-object", "-w", "--stdin", input_text=text)
                mode = git.mode(head, path)
                git.run("update-index", "--add", "--cacheinfo", f"{mode},{sha},{path}", env=env)
                written.append((path, mode, sha))
            hook = git.run("hook", "run", "--ignore-missing", "pre-commit", env=env, check=False)
            if hook.returncode != 0:
                detail = (hook.stderr or hook.stdout).strip().splitlines()[-3:]
                return {"state": "saved", "error": "hook_failed: " + " ".join(detail)}
            tree = git.out("write-tree", env=env)
        identity = {
            "GIT_AUTHOR_NAME": policy.author_name,
            "GIT_AUTHOR_EMAIL": policy.author_email,
            "GIT_COMMITTER_NAME": policy.author_name,
            "GIT_COMMITTER_EMAIL": policy.author_email,
        }
        commit = git.out("commit-tree", tree, "-p", head, env=identity, input_text=message)
        moved = git.run("update-ref", "-m", "achios persist", "HEAD", commit, head, check=False)
        if moved.returncode != 0:
            return {"state": "saved", "error": "head_moved_during_commit"}
        self._sync_index(git, head, written)
        return {"state": "committed", "commit": commit, "created": True, "error": None}

    @staticmethod
    def _sync_index(git: Git, old_head: str, written: list[tuple[str, str, str]]) -> None:
        """Point the real index at the new blobs only where it still held the old HEAD."""
        for path, mode, sha in written:
            staged = git.out("ls-files", "--stage", "--", path)
            staged_sha = staged.split()[1] if staged else None
            head_sha = git.run("rev-parse", f"{old_head}:{path}", check=False).stdout.strip() or None
            if staged_sha == head_sha:
                git.run("update-index", "--add", "--cacheinfo", f"{mode},{sha},{path}")

    def _push(
        self, git: Git, policy: RepositoryPolicy, commit: str, created: bool,
        operation_id: str, repository: str,
    ) -> dict:
        # A commit this operation did not create is someone else's to publish.
        ours = self.store.commits(repository) | ({commit} if created else set())
        remote_ref = f"refs/remotes/{policy.remote}/{policy.branch}"
        tracked = git.run("rev-parse", "--verify", "--quiet", remote_ref, check=False).stdout.strip()
        if tracked and git.has_object(tracked):
            unpushed = git.out("rev-list", f"{tracked}..{commit}").split()
            foreign = [sha for sha in unpushed if sha not in ours]
            if foreign:
                return _receipt(
                    operation_id, "committed", commit,
                    f"unrelated_local_commits: {len(foreign)} would be published",
                )
        pushed = git.run(
            "push", "--porcelain", policy.remote, f"{commit}:refs/heads/{policy.branch}",
            check=False, timeout=PUSH_TIMEOUT_SECONDS,
        )
        verified, remote_sha = self._verify_remote(git, policy, commit)
        if verified:
            git.run("update-ref", remote_ref, remote_sha, check=False)
            return _receipt(operation_id, "pushed", commit)
        porcelain = pushed.stdout or ""
        if "[rejected]" in porcelain or "non-fast-forward" in porcelain or "fetch first" in porcelain:
            return _receipt(operation_id, "committed", commit, "divergent_remote")
        errors = [line for line in (pushed.stderr or "").splitlines() if line.strip()]
        return _receipt(
            operation_id, "committed", commit,
            "push_failed: " + (errors[-1].strip() if errors else "remote does not show the commit"),
        )

    @staticmethod
    def _verify_remote(git: Git, policy: RepositoryPolicy, commit: str) -> tuple[bool, str | None]:
        listed = git.run(
            "ls-remote", policy.remote, f"refs/heads/{policy.branch}",
            check=False, timeout=PUSH_TIMEOUT_SECONDS,
        )
        if listed.returncode != 0 or not listed.stdout.strip():
            return False, None
        remote_sha = listed.stdout.split()[0]
        if remote_sha == commit:
            return True, remote_sha
        return (git.has_object(remote_sha) and git.is_ancestor(commit, remote_sha)), remote_sha


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", default="-", help="JSON request file or - for stdin")
    parser.add_argument("--retry", action="store_true", help="push recorded unpushed commits")
    args = parser.parse_args(argv)
    if args.retry:
        receipts = Persister().retry_unpushed()
        print(json.dumps({"retried": receipts}, ensure_ascii=False, sort_keys=True))
        return 0 if all(item and item["state"] == "pushed" for item in receipts) else 1
    raw = sys.stdin.read() if args.input == "-" else Path(args.input).read_text(encoding="utf-8")
    request = json.loads(raw)
    persister = Persister()
    matches = [policy_for(Path(change["path"]), persister.policies) for change in request["changes"]]
    policies = {match[0] for match in matches if match}
    if None in matches or len(policies) != 1:
        receipt = {"state": "saved", "error": "persistence_not_configured_for_every_path"}
    else:
        changes = [
            OwnedChange(match[1], change.get("before"), change["after"])
            for match, change in zip(matches, request["changes"])
        ]
        receipt = persister.persist(
            policies.pop(), changes, operation_id=request["operation_id"], message=request["message"]
        )
    print(json.dumps(receipt, ensure_ascii=False, sort_keys=True))
    return 0 if receipt["state"] == "pushed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
