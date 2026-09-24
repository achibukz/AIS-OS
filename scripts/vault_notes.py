#!/usr/bin/env python3
"""Typed, sourced writes into the achiMem and schoolMem vaults.

The caller names a destination type, never a path. Notes go to achiMem
raw/sessions or schoolMem inbox, the two places the vault contracts let an
unattended writer use. Five achiMem wiki targets exist, each off until the
operator enables it and its exact markers are on the page.

Every fact carries provenance. A [stated] fact needs a quote from a user source.
Anything else is [inferred] and says so. One source ID maps to one note, so a
retry returns the first receipt instead of a second note. Saved, linted,
committed and pushed stay separate in the receipt.
"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import re
import sqlite3
import subprocess
import sys
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

import owned_persist

MANILA = ZoneInfo("Asia/Manila")
HOME = Path.home()
VAULTS = {
    "achimem": HOME / "Documents" / "Obsidian" / "achiMem",
    "schoolmem": HOME / "Documents" / "Obsidian" / "schoolMem",
}
NOTE_DIRS = {"achimem": "raw/sessions", "schoolmem": "inbox"}
DEFAULT_DB = HOME / ".local" / "state" / "achios" / "vault_notes.sqlite3"
CONFIG_PATH = HOME / ".config" / "achios" / "vault_writes.json"
VIEWER = "http://100.106.210.38:8999"
USER_SOURCE_KINDS = {"telegram_user", "fixture_user"}
PROVENANCE = {"stated", "document", "inferred"}
SLUG_RE = re.compile(r"[^a-z0-9]+")
LINT_TIMEOUT = 60


@dataclass(frozen=True)
class WikiTarget:
    path: str
    mode: str  # "section" replaces between two markers; "insert" and "append" add one row
    start: str
    end: str | None = None


# The allowlist is fixed in code. Config can only switch targets on.
WIKI_TARGETS = {
    "achi-os-status": WikiTarget(
        "wiki/personal/systems/achi-os.md", "section",
        "<!-- achios:status:start -->", "<!-- achios:status:end -->"),
    "achi-core-status": WikiTarget(
        "wiki/personal/systems/achi-core.md", "section",
        "<!-- achios:status:start -->", "<!-- achios:status:end -->"),
    "achibuntu-status": WikiTarget(
        "wiki/personal/systems/achibuntu.md", "section",
        "<!-- achios:status:start -->", "<!-- achios:status:end -->"),
    "timeline-row": WikiTarget(
        "wiki/personal/timeline.md", "insert", "<!-- achios:timeline:insert -->"),
    "tooling-decision-row": WikiTarget(
        "wiki/personal/decisions.md", "append", "<!-- achios:tooling-decisions:append -->"),
}


class VaultError(ValueError):
    pass


def _now() -> dt.datetime:
    return dt.datetime.now(dt.UTC)


def _stable_id(*parts: str) -> str:
    return hashlib.sha256("\x1f".join(parts).encode("utf-8")).hexdigest()[:24]


def viewer_link(path: Path) -> str | None:
    try:
        relative = Path(path).resolve().relative_to(HOME.resolve())
    except ValueError:
        return None  # the viewer serves the home directory only
    return f"{VIEWER}/{relative.as_posix()}"


def enabled_targets(path: Path | None = None) -> set[str]:
    config = Path(path) if path else CONFIG_PATH
    if not config.is_file():
        return set()
    names = json.loads(config.read_text(encoding="utf-8")).get("wiki_targets", [])
    return {name for name in names if name in WIKI_TARGETS}


def _safe_path(vault: Path, relative: str) -> Path:
    """Resolve inside the vault, refusing traversal and any symlinked component."""
    candidate = vault / relative
    root = vault.resolve()
    if ".." in Path(relative).parts or Path(relative).is_absolute():
        raise VaultError("path_outside_vault")
    current = vault
    for part in Path(relative).parts:
        current = current / part
        if current.is_symlink():
            raise VaultError("symlink_in_path")
    if not candidate.resolve().is_relative_to(root):
        raise VaultError("path_outside_vault")
    return candidate


def _validate_source(source: dict) -> dict:
    required = {"id", "kind", "native_id", "revision", "timestamp"}
    if not isinstance(source, dict) or set(source) != required:
        raise VaultError("source envelope is incomplete or contains extra fields")
    for field in ("id", "kind", "native_id", "timestamp"):
        if not isinstance(source[field], str) or not source[field].strip():
            raise VaultError(f"source.{field} must be a non-empty string")
    parsed = dt.datetime.fromisoformat(source["timestamp"])
    if parsed.utcoffset() is None:
        raise VaultError("source.timestamp must include an offset")
    return source


def _render_facts(facts: list[dict], source: dict, evidence: str | None) -> list[str]:
    lines = []
    for fact in facts:
        text = str(fact.get("text") or "").strip()
        claimed = fact.get("provenance", "inferred")
        if not text or "\n" in text or claimed not in PROVENANCE:
            raise VaultError("each fact needs one line of text and a known provenance")
        provenance = claimed
        if claimed == "stated":
            quote = fact.get("quote")
            stated = (
                source["kind"] in USER_SOURCE_KINDS
                and isinstance(quote, str) and quote.strip()
                and evidence is not None and quote in evidence
            )
            # A model cannot promote its own inference to something Aki said.
            provenance = "stated" if stated else "inferred"
        elif claimed == "document" and not str(fact.get("cite") or "").strip():
            provenance = "inferred"
        suffix = f" (cite: {fact['cite']})" if provenance == "document" else ""
        lines.append(f"- {text} [{provenance}]{suffix}")
    return lines


def _committed_text(vault: Path, relative: str) -> str | None:
    shown = subprocess.run(
        ["git", "-C", str(vault), "show", f"HEAD:{relative}"],
        capture_output=True, text=True, check=False,
    )
    return shown.stdout if shown.returncode == 0 else None


class VaultNotes:
    def __init__(
        self,
        *,
        db_path: Path | None = None,
        vaults: dict[str, Path] | None = None,
        persister: owned_persist.Persister | None = None,
        config_path: Path | None = None,
        lint_runner=subprocess.run,
    ):
        self.db_path = Path(db_path) if db_path else DEFAULT_DB
        self.vaults = vaults or VAULTS
        self.persister = persister
        self.config_path = config_path
        self.lint_runner = lint_runner
        self.db_path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        with self._connect() as connection:
            connection.executescript(
                """
                CREATE TABLE IF NOT EXISTS vault_operations (
                    operation_id TEXT PRIMARY KEY,
                    source_id TEXT NOT NULL,
                    destination TEXT NOT NULL,
                    path TEXT,
                    item_id TEXT,
                    receipt_json TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );
                CREATE VIRTUAL TABLE IF NOT EXISTS vault_notes_fts USING fts5(
                    operation_id UNINDEXED, scope UNINDEXED, path UNINDEXED, title, body
                );
                """
            )

    @contextmanager
    def _connect(self):
        connection = sqlite3.connect(self.db_path)
        connection.row_factory = sqlite3.Row
        try:
            with connection:
                yield connection
        finally:
            connection.close()

    def _prior(self, operation_id: str) -> dict | None:
        with self._connect() as connection:
            row = connection.execute(
                "SELECT receipt_json FROM vault_operations WHERE operation_id=?", (operation_id,)
            ).fetchone()
        return json.loads(row[0]) if row else None

    def _store(self, operation_id, source_id, destination, path, item_id, receipt,
               title=None, body=None, scope=None) -> None:
        with self._connect() as connection:
            connection.execute(
                """INSERT INTO vault_operations VALUES(?,?,?,?,?,?,?)
                   ON CONFLICT(operation_id) DO UPDATE SET receipt_json=excluded.receipt_json""",
                (operation_id, source_id, destination, str(path) if path else None, item_id,
                 json.dumps(receipt, sort_keys=True), _now().isoformat()),
            )
            if title is not None:
                connection.execute(
                    "INSERT INTO vault_notes_fts VALUES(?,?,?,?,?)",
                    (operation_id, scope, str(path), title, body),
                )

    def _persist(self, operation_id: str, changes: list[tuple[Path, str | None, str]], message: str) -> dict:
        if self.persister is None:
            return {"state": "saved", "error": "persistence_not_configured"}
        match = owned_persist.policy_for(changes[0][0], self.persister.policies)
        if match is None or any(owned_persist.policy_for(p, [match[0]]) is None for p, _, _ in changes):
            return {"state": "saved", "error": "persistence_not_configured"}
        policy = match[0]
        owned = [
            owned_persist.OwnedChange(policy.owns(path), before, after) for path, before, after in changes
        ]
        return self.persister.persist(policy, owned, operation_id=operation_id, message=message)

    @staticmethod
    def _receipt(operation_id, state, path=None, *, linted=None, persistence=None, error=None):
        persistence = persistence or {}
        committed = bool(persistence.get("committed"))
        pushed = bool(persistence.get("pushed"))
        if state == "saved" and pushed:
            state = "pushed"
        elif state == "saved" and committed:
            state = "committed"
        return {
            "operation_id": operation_id,
            "state": state,
            "saved": state in {"saved", "committed", "pushed"},
            "linted": linted,
            "committed": committed,
            "pushed": pushed,
            "commit": persistence.get("commit"),
            "path": str(path) if path else None,
            "viewer_link": viewer_link(path) if path and state != "rejected" else None,
            "error": error or persistence.get("error"),
        }

    def save_note(self, request: dict, *, allowed: set[str], evidence: str | None = None) -> dict:
        """Save one sourced note. `allowed` is the caller topic's destination scope."""
        source = _validate_source(request.get("source"))
        note = request.get("note") or {}
        destination = note.get("destination")
        operation_id = "note:" + _stable_id(source["id"], str(destination), str(note.get("item_id")))
        prior = self._prior(operation_id)
        if prior is not None:
            return prior
        if destination == "achimem" and source["kind"] == "claude_session":
            captured = self._session_capture(source["native_id"])
            if captured is not None:
                # The SessionEnd hook already holds this session; one source, one note.
                return self._receipt(operation_id, "saved", captured, error="already_captured")
        if destination not in NOTE_DIRS:
            return self._receipt(operation_id, "rejected", error="unknown_destination")
        if destination not in allowed:
            return self._receipt(operation_id, "rejected", error="destination_not_permitted_for_topic")
        title = str(note.get("title") or "").strip().replace('"', "'")
        if not title or "\n" in title or "\r" in title or len(title) > 120:
            return self._receipt(operation_id, "rejected", error="title must be one line of at most 120 characters")
        try:
            facts = _render_facts(note.get("facts") or [], source, evidence)
        except VaultError as exc:
            return self._receipt(operation_id, "rejected", error=str(exc))
        vault = self.vaults[destination]
        day = dt.datetime.fromisoformat(source["timestamp"]).astimezone(MANILA).date().isoformat()
        slug = SLUG_RE.sub("-", title.lower()).strip("-")[:48] or "note"
        relative = f"{NOTE_DIRS[destination]}/{day}-{slug}-{operation_id[-6:]}.md"
        try:
            path = _safe_path(vault, relative)
            log_path = _safe_path(vault, "log.md") if destination == "achimem" else None
        except VaultError as exc:
            return self._receipt(operation_id, "rejected", error=str(exc))
        if path.exists():
            return self._receipt(operation_id, "conflict", path, error="note_path_exists")
        body = "\n".join([
            "---",
            f'title: "{title}"',
            "type: capture",
            f"source_id: {source['id']}",
            f"source_kind: {source['kind']}",
            f"source_native_id: {source['native_id']}",
            f"source_timestamp: {source['timestamp']}",
            *( [f"linked_item: {note['item_id']}"] if note.get("item_id") else [] ),
            f"created: {day}",
            "---",
            "",
            f"# {title}",
            "",
            "## What happened",
            *(facts or ["- (no facts recorded)"]),
            "",
        ])
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(body, encoding="utf-8")
        changes: list[tuple[Path, str | None, str]] = [(path, None, body)]
        if log_path is not None:
            entry = f"\n## [{day}] capture | {title}\n- Source: `{relative}`\n"
            before = log_path.read_text(encoding="utf-8") if log_path.exists() else ""
            log_path.write_text(before + entry, encoding="utf-8")
            # log.md is append-only and often has uncommitted lines at its tail. The
            # owned change is the entry alone, applied to the committed log.
            committed = _committed_text(vault, "log.md")
            base = before if committed is None else committed
            changes.append((log_path, base, base + entry))
        persistence = self._persist(operation_id, changes, f"{destination}: capture {title}\n")
        receipt = self._receipt(operation_id, "saved", path, persistence=persistence)
        self._store(operation_id, source["id"], destination, path, note.get("item_id"), receipt,
                    title, "\n".join(facts), destination)
        return receipt

    def _session_capture(self, session_id: str) -> Path | None:
        sessions = self.vaults["achimem"] / "raw" / "sessions"
        for path in sorted(sessions.glob(f"*-achios-{session_id[:8]}.md")):
            if f"session_id: {session_id}\n" in path.read_text(encoding="utf-8", errors="replace"):
                return path
        return None

    def record_completion(self, item_id: str, *, title: str, source: dict) -> dict | None:
        """A completed item adds one dated note beside its school record. None when unlinked."""
        with self._connect() as connection:
            linked = connection.execute(
                """SELECT destination, path FROM vault_operations
                   WHERE item_id=? AND destination IN ('achimem','schoolmem')
                   ORDER BY created_at LIMIT 1""",
                (item_id,),
            ).fetchone()
        if linked is None:
            return None
        original = Path(linked["path"]).name
        request = {
            "source": source,
            "note": {
                "destination": linked["destination"],
                "title": f"Completed: {title}"[:120],
                "item_id": f"{item_id}:completed",
                "facts": [{"text": f"Completed; see {original}", "provenance": "document",
                           "cite": source["native_id"]}],
            },
        }
        return self.save_note(request, allowed={linked["destination"]})

    def _lint_errors(self, vault: Path) -> set[str] | None:
        script = vault / "scripts" / "lint.py"
        if not script.is_file():
            return None
        completed = self.lint_runner(
            [sys.executable, str(script)], cwd=vault, capture_output=True, text=True,
            timeout=LINT_TIMEOUT, check=False,
        )
        return {line.strip() for line in completed.stdout.splitlines() if line.startswith("ERROR")}

    def write_wiki(self, request: dict) -> dict:
        source = _validate_source(request.get("source"))
        wiki = request.get("wiki") or {}
        name = wiki.get("target")
        operation_id = "wiki:" + _stable_id(source["id"], str(name))
        prior = self._prior(operation_id)
        if prior is not None:
            return prior
        target = WIKI_TARGETS.get(name)
        if target is None:
            return self._receipt(operation_id, "rejected", error="unknown_wiki_target")
        if name not in enabled_targets(self.config_path):
            return self._receipt(operation_id, "rejected", error="wiki_target_not_enabled")
        text = str(wiki.get("content") or "").rstrip("\n")
        provenance = wiki.get("provenance")
        if not text or provenance not in {"stated", "document"}:
            # Personal wiki pages hold confirmed facts only.
            return self._receipt(operation_id, "rejected", error="wiki writes need stated or document provenance")
        if provenance == "stated" and source["kind"] not in USER_SOURCE_KINDS:
            return self._receipt(operation_id, "rejected", error="stated wiki facts need a user source")
        if target.mode != "section" and "\n" in text:
            return self._receipt(operation_id, "rejected", error="a row must be one line")
        vault = self.vaults["achimem"]
        try:
            path = _safe_path(vault, target.path)
        except VaultError as exc:
            return self._receipt(operation_id, "rejected", error=str(exc))
        if not path.is_file():
            return self._receipt(operation_id, "rejected", error="wiki_page_missing")
        before = path.read_text(encoding="utf-8")
        expected = wiki.get("expected_sha256")
        if expected and hashlib.sha256(before.encode("utf-8")).hexdigest() != expected:
            return self._conflict(operation_id, source, name, text, "page_changed_since_read")
        if before.count(target.start) != 1 or (target.end and before.count(target.end) != 1):
            return self._receipt(operation_id, "rejected", path, error="section_markers_missing_or_repeated")
        tag = f"[{provenance}]"
        if target.mode == "section":
            start = before.index(target.start) + len(target.start)
            end = before.index(target.end)
            after = before[:start] + f"\n{text}\n\n_Source: {source['id']} {tag}_\n" + before[end:]
        elif target.mode == "insert":
            at = before.index(target.start) + len(target.start)
            after = before[:at] + f"\n{text} {tag}" + before[at:]
        else:
            at = before.index(target.start)
            after = before[:at] + f"{text} {tag}\n" + before[at:]
        lint_before = self._lint_errors(vault)
        if path.read_text(encoding="utf-8") != before:
            return self._conflict(operation_id, source, name, text, "page_changed_during_write")
        path.write_text(after, encoding="utf-8")
        lint_after = self._lint_errors(vault)
        new_errors = sorted((lint_after or set()) - (lint_before or set()))
        if new_errors:
            receipt = self._receipt(operation_id, "saved", path, linted=False,
                                    error="lint_failed: " + "; ".join(new_errors))
        else:
            persistence = self._persist(operation_id, [(path, before, after)], f"achimem: update {name}\n")
            receipt = self._receipt(operation_id, "saved", path,
                                    linted=None if lint_after is None else True,
                                    persistence=persistence)
        self._store(operation_id, source["id"], f"wiki:{name}", path, None, receipt)
        return receipt

    def _conflict(self, operation_id, source, name, text, reason) -> dict:
        """Keep the proposed version beside the current page instead of dropping it."""
        vault = self.vaults["achimem"]
        path = _safe_path(vault, f"raw/conflicts/{name}-{operation_id[-8:]}.md")
        path.parent.mkdir(parents=True, exist_ok=True)
        if not path.exists():
            path.write_text(
                f"---\ntype: conflict\ntarget: {name}\nsource_id: {source['id']}\nreason: {reason}\n---\n\n{text}\n",
                encoding="utf-8",
            )
        receipt = self._receipt(operation_id, "conflict", path, error=reason)
        self._store(operation_id, source["id"], f"wiki:{name}", path, None, receipt)
        return receipt

    def recall(self, scope: str, query: str, limit: int = 5) -> list[dict]:
        terms = [term for term in re.findall(r"\w+", query) if len(term) > 2]
        if not terms:
            return []
        match = " OR ".join(f'"{term}"' for term in terms)
        with self._connect() as connection:
            rows = connection.execute(
                """SELECT path, title FROM vault_notes_fts
                   WHERE vault_notes_fts MATCH ? AND scope=? ORDER BY rank LIMIT ?""",
                (match, scope, limit),
            ).fetchall()
        return [{"title": row["title"], "path": row["path"], "viewer_link": viewer_link(Path(row["path"]))}
                for row in rows if Path(row["path"]).exists()]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    note = sub.add_parser("note")
    note.add_argument("--allow", action="append", choices=sorted(NOTE_DIRS), required=True,
                      help="destinations the calling topic may write")
    note.add_argument("--input", default="-")
    wiki = sub.add_parser("wiki")
    wiki.add_argument("--input", default="-")
    recall = sub.add_parser("recall")
    recall.add_argument("--scope", choices=sorted(NOTE_DIRS), required=True)
    recall.add_argument("--query", required=True)
    args = parser.parse_args(argv)
    notes = VaultNotes(persister=owned_persist.Persister())
    if args.command == "recall":
        print(json.dumps(notes.recall(args.scope, args.query), ensure_ascii=False))
        return 0
    raw = sys.stdin.read() if args.input == "-" else Path(args.input).read_text(encoding="utf-8")
    request = json.loads(raw)
    try:
        if args.command == "note":
            receipt = notes.save_note(request, allowed=set(args.allow), evidence=request.get("evidence"))
        else:
            receipt = notes.write_wiki(request)
    except VaultError as exc:
        receipt = {"state": "rejected", "error": str(exc)}
    print(json.dumps(receipt, ensure_ascii=False, sort_keys=True))
    return 0 if receipt["state"] in {"saved", "committed", "pushed"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
