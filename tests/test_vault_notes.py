import hashlib
import json
import subprocess
from pathlib import Path

import pytest

import cohesion
import vault_notes
from owned_persist import Persister, ReceiptStore, RepositoryPolicy
from test_cohesion import FakeCalendar, write_calendars
from vault_notes import VaultNotes, WIKI_TARGETS

SOURCE = {
    "id": "telegram:-100:7:r1",
    "kind": "telegram_user",
    "native_id": "-100:7",
    "revision": 1,
    "timestamp": "2026-09-24T09:00:00+08:00",
}
MARKED = {
    "achi-os-status": "# achiOS\n\n## Status\n<!-- achios:status:start -->\nold\n<!-- achios:status:end -->\n\n## Rest\n",
    "achi-core-status": "# achiCore\n<!-- achios:status:start -->\n<!-- achios:status:end -->\n",
    "achibuntu-status": "# achibuntu\n<!-- achios:status:start -->\n<!-- achios:status:end -->\n",
    "timeline-row": "# Timeline\n\n| Date | Event | Provenance |\n|---|---|---|\n<!-- achios:timeline:insert -->\n| 2026-09-07 | Older | [document] |\n",
    "tooling-decision-row": "# Decisions\n\n## Tooling / workflow\n\n| Decision | Status |\n|---|---|\n| Old | active |\n<!-- achios:tooling-decisions:append -->\n\n## Other\n",
}


@pytest.fixture
def vaults(tmp_path):
    roots = {"achimem": tmp_path / "achiMem", "schoolmem": tmp_path / "schoolMem"}
    for root in roots.values():
        (root / "raw" / "sessions").mkdir(parents=True)
        (root / "inbox").mkdir()
    (roots["achimem"] / "log.md").write_text("# Log\n", encoding="utf-8")
    return roots


def notes(tmp_path, vaults, **changes):
    values = {"db_path": tmp_path / "notes.sqlite3", "vaults": vaults, **changes}
    return VaultNotes(**values)


def request(destination="achimem", **note):
    return {"source": dict(SOURCE), "note": {
        "destination": destination, "title": "Seminar summary",
        "facts": [{"text": "Aki prefers morning seminars", "provenance": "stated",
                   "quote": "I like morning seminars"}],
        **note,
    }}


def test_personal_note_lands_in_achimem_raw_sessions_with_a_log_entry(tmp_path, vaults):
    receipt = notes(tmp_path, vaults).save_note(
        request(), allowed={"achimem"}, evidence="honestly I like morning seminars")

    path = Path(receipt["path"])
    assert receipt["state"] == "saved" and receipt["saved"] is True
    assert receipt["committed"] is False and receipt["error"] == "persistence_not_configured"
    assert path.parent == vaults["achimem"] / "raw" / "sessions"
    text = path.read_text(encoding="utf-8")
    assert "source_id: telegram:-100:7:r1" in text
    assert "- Aki prefers morning seminars [stated]" in text
    assert f"`raw/sessions/{path.name}`" in (vaults["achimem"] / "log.md").read_text(encoding="utf-8")


def test_school_note_lands_in_the_schoolmem_inbox(tmp_path, vaults):
    receipt = notes(tmp_path, vaults).save_note(request("schoolmem"), allowed={"schoolmem"})

    assert Path(receipt["path"]).parent == vaults["schoolmem"] / "inbox"
    assert not (vaults["schoolmem"] / "log.md").exists()


def test_topic_scope_limits_the_destination(tmp_path, vaults):
    receipt = notes(tmp_path, vaults).save_note(request("achimem"), allowed={"schoolmem"})

    assert receipt["state"] == "rejected"
    assert receipt["error"] == "destination_not_permitted_for_topic"
    assert list((vaults["achimem"] / "raw" / "sessions").iterdir()) == []


@pytest.mark.parametrize("destination", ["../etc", "wiki", "achimem/../../x", None])
def test_unknown_or_model_chosen_destinations_fail_before_writing(tmp_path, vaults, destination):
    receipt = notes(tmp_path, vaults).save_note(request(destination), allowed={"achimem", "schoolmem"})

    assert receipt["state"] == "rejected" and receipt["error"] == "unknown_destination"


def test_symlinked_note_directory_is_refused(tmp_path, vaults):
    outside = tmp_path / "outside"
    outside.mkdir()
    (vaults["schoolmem"] / "inbox").rmdir()
    (vaults["schoolmem"] / "inbox").symlink_to(outside)

    receipt = notes(tmp_path, vaults).save_note(request("schoolmem"), allowed={"schoolmem"})

    assert receipt["state"] == "rejected" and receipt["error"] == "symlink_in_path"
    assert list(outside.iterdir()) == []


def test_title_cannot_smuggle_a_path_or_frontmatter(tmp_path, vaults):
    receipt = notes(tmp_path, vaults).save_note(
        request(title="../../wiki/personal/_profile"), allowed={"achimem"})

    assert receipt["state"] == "saved"
    assert Path(receipt["path"]).parent == vaults["achimem"] / "raw" / "sessions"
    smuggled = request(title="a\n---\nprovenance: stated")
    smuggled["source"]["id"] = "telegram:-100:9:r1"
    assert notes(tmp_path, vaults).save_note(smuggled, allowed={"achimem"})["state"] == "rejected"


@pytest.mark.parametrize("fact, tag", [
    ({"text": "Prefers mornings", "provenance": "stated", "quote": "not in the message"}, "[inferred]"),
    ({"text": "Prefers mornings", "provenance": "stated"}, "[inferred]"),
    ({"text": "Enrolled in STDISCM", "provenance": "document", "cite": "raw/enrollment.pdf"},
     "[document] (cite: raw/enrollment.pdf)"),
    ({"text": "Enrolled in STDISCM", "provenance": "document"}, "[inferred]"),
    ({"text": "Probably likes coffee", "provenance": "inferred"}, "[inferred]"),
])
def test_only_quoted_user_evidence_is_stated(tmp_path, vaults, fact, tag):
    receipt = notes(tmp_path, vaults).save_note(
        request(facts=[fact]), allowed={"achimem"}, evidence="I like morning seminars")

    assert f"{fact['text']} {tag}" in Path(receipt["path"]).read_text(encoding="utf-8")


def test_assistant_source_cannot_state_a_personal_fact(tmp_path, vaults):
    body = request()
    body["source"]["kind"] = "telegram_assistant"

    receipt = notes(tmp_path, vaults).save_note(body, allowed={"achimem"}, evidence="I like morning seminars")

    assert "[inferred]" in Path(receipt["path"]).read_text(encoding="utf-8")


def test_repeated_source_returns_the_first_receipt(tmp_path, vaults):
    tool = notes(tmp_path, vaults)
    first = tool.save_note(request(), allowed={"achimem"})
    second = tool.save_note(request(title="Different wording"), allowed={"achimem"})

    assert second == first
    assert len(list((vaults["achimem"] / "raw" / "sessions").iterdir())) == 1


def test_claude_session_note_reuses_the_hook_capture(tmp_path, vaults):
    session = "abcdef1234567890"
    captured = vaults["achimem"] / "raw" / "sessions" / f"2026-09-24-achios-{session[:8]}.md"
    captured.write_text(f"---\nsession_id: {session}\n---\n", encoding="utf-8")
    body = request()
    body["source"].update(kind="claude_session", native_id=session)

    receipt = notes(tmp_path, vaults).save_note(body, allowed={"achimem"})

    assert receipt["path"] == str(captured) and receipt["error"] == "already_captured"
    assert len(list(captured.parent.iterdir())) == 1


def test_uncertain_legacy_session_match_is_not_reused(tmp_path, vaults):
    session = "abcdef1234567890"
    lookalike = vaults["achimem"] / "raw" / "sessions" / f"2026-09-24-achios-{session[:8]}.md"
    lookalike.write_text("---\nsession_id: abcdef12ffffffff\n---\n", encoding="utf-8")
    body = request()
    body["source"].update(kind="claude_session", native_id=session)

    receipt = notes(tmp_path, vaults).save_note(body, allowed={"achimem"})

    assert receipt["path"] != str(lookalike)


def test_notes_are_recallable_by_scope(tmp_path, vaults):
    tool = notes(tmp_path, vaults)
    tool.save_note(request(), allowed={"achimem"})

    assert [hit["title"] for hit in tool.recall("achimem", "morning seminars")] == ["Seminar summary"]
    assert tool.recall("schoolmem", "morning seminars") == []


def wiki_request(target, content, **changes):
    return {"source": dict(SOURCE), "wiki": {"target": target, "content": content,
                                               "provenance": "stated", **changes}}


def enable(tmp_path, *targets):
    config = tmp_path / "vault_writes.json"
    config.write_text(json.dumps({"wiki_targets": list(targets)}), encoding="utf-8")
    return config


def seed_wiki(vaults, *names):
    for name in names:
        path = vaults["achimem"] / WIKI_TARGETS[name].path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(MARKED[name], encoding="utf-8")


def test_the_allowlist_is_exactly_five_pages():
    assert {target.path for target in WIKI_TARGETS.values()} == {
        "wiki/personal/systems/achi-os.md",
        "wiki/personal/systems/achi-core.md",
        "wiki/personal/systems/achibuntu.md",
        "wiki/personal/timeline.md",
        "wiki/personal/decisions.md",
    }


@pytest.mark.parametrize("name, content, expected", [
    ("achi-os-status", "Hub runs master at 93a47e6",
     "<!-- achios:status:start -->\nHub runs master at 93a47e6\n\n_Source: telegram:-100:7:r1 [stated]_\n<!-- achios:status:end -->"),
    ("timeline-row", "| 2026-09-24 | Shipped #148 | ",
     "<!-- achios:timeline:insert -->\n| 2026-09-24 | Shipped #148 |  [stated]\n| 2026-09-07 | Older"),
    ("tooling-decision-row", "| Squash-merge PRs | active |",
     "| Old | active |\n| Squash-merge PRs | active | [stated]\n<!-- achios:tooling-decisions:append -->"),
])
def test_enabled_wiki_targets_write_only_inside_their_markers(tmp_path, vaults, name, content, expected):
    seed_wiki(vaults, name)
    tool = notes(tmp_path, vaults, config_path=enable(tmp_path, name))

    receipt = tool.write_wiki(wiki_request(name, content))

    text = (vaults["achimem"] / WIKI_TARGETS[name].path).read_text(encoding="utf-8")
    assert receipt["state"] == "saved" and expected in text
    assert text.endswith(MARKED[name].rsplit(WIKI_TARGETS[name].end or WIKI_TARGETS[name].start, 1)[1])


def test_wiki_targets_are_off_until_enabled(tmp_path, vaults):
    seed_wiki(vaults, "achi-os-status")

    receipt = notes(tmp_path, vaults).write_wiki(wiki_request("achi-os-status", "x"))

    assert receipt["error"] == "wiki_target_not_enabled"
    assert "old" in (vaults["achimem"] / WIKI_TARGETS["achi-os-status"].path).read_text(encoding="utf-8")


@pytest.mark.parametrize("target", ["../AGENTS.md", "wiki/personal/_profile.md", "open-questions"])
def test_unknown_wiki_targets_fail(tmp_path, vaults, target):
    assert notes(tmp_path, vaults).write_wiki(wiki_request(target, "x"))["error"] == "unknown_wiki_target"


def test_missing_markers_fail_before_mutation(tmp_path, vaults):
    path = vaults["achimem"] / WIKI_TARGETS["achi-core-status"].path
    path.parent.mkdir(parents=True)
    path.write_text("# achiCore\nno markers here\n", encoding="utf-8")
    tool = notes(tmp_path, vaults, config_path=enable(tmp_path, "achi-core-status"))

    receipt = tool.write_wiki(wiki_request("achi-core-status", "x"))

    assert receipt["error"] == "section_markers_missing_or_repeated"
    assert path.read_text(encoding="utf-8") == "# achiCore\nno markers here\n"


def test_inferred_content_never_reaches_the_personal_wiki(tmp_path, vaults):
    seed_wiki(vaults, "timeline-row")
    tool = notes(tmp_path, vaults, config_path=enable(tmp_path, "timeline-row"))

    receipt = tool.write_wiki(wiki_request("timeline-row", "| x |", provenance="inferred"))

    assert receipt["state"] == "rejected"


def test_changed_page_keeps_both_versions(tmp_path, vaults):
    seed_wiki(vaults, "achi-os-status")
    path = vaults["achimem"] / WIKI_TARGETS["achi-os-status"].path
    stale = hashlib.sha256(b"what the proposer read").hexdigest()
    tool = notes(tmp_path, vaults, config_path=enable(tmp_path, "achi-os-status"))

    receipt = tool.write_wiki(wiki_request("achi-os-status", "Proposed status", expected_sha256=stale))

    assert receipt["state"] == "conflict"
    assert path.read_text(encoding="utf-8") == MARKED["achi-os-status"]
    assert "Proposed status" in Path(receipt["path"]).read_text(encoding="utf-8")
    assert Path(receipt["path"]).parent == vaults["achimem"] / "raw" / "conflicts"


def test_new_lint_errors_stop_persistence(tmp_path, vaults):
    seed_wiki(vaults, "achi-os-status")
    lint = vaults["achimem"] / "scripts" / "lint.py"
    lint.parent.mkdir()
    lint.write_text("", encoding="utf-8")
    calls = []

    def runner(argv, **kwargs):
        calls.append(argv)
        errors = "ERROR  STALE  wiki/index.md\n" + ("ERROR  broken link\n" if len(calls) > 1 else "")
        return subprocess.CompletedProcess(argv, 1, errors, "")

    tool = notes(tmp_path, vaults, config_path=enable(tmp_path, "achi-os-status"), lint_runner=runner)
    receipt = tool.write_wiki(wiki_request("achi-os-status", "x"))

    assert receipt["state"] == "saved" and receipt["linted"] is False
    assert receipt["error"] == "lint_failed: ERROR  broken link"


def test_existing_lint_errors_do_not_block_a_clean_write(tmp_path, vaults):
    seed_wiki(vaults, "achi-os-status")
    lint = vaults["achimem"] / "scripts" / "lint.py"
    lint.parent.mkdir()
    lint.write_text("", encoding="utf-8")

    def runner(argv, **kwargs):
        return subprocess.CompletedProcess(argv, 1, "ERROR  STALE  wiki/index.md\n", "")

    tool = notes(tmp_path, vaults, config_path=enable(tmp_path, "achi-os-status"), lint_runner=runner)

    assert tool.write_wiki(wiki_request("achi-os-status", "x"))["linted"] is True


@pytest.fixture
def vault_repo(tmp_path, vaults):
    remote = tmp_path / "achiMem.git"
    root = vaults["achimem"]
    subprocess.run(["git", "init", "-q", "--bare", "-b", "main", str(remote)], check=True)
    subprocess.run(["git", "init", "-q", "-b", "main", str(root)], check=True)
    hooks = tmp_path / "hooks"
    hooks.mkdir()
    for key, value in (("user.name", "t"), ("user.email", "t@t"), ("core.hooksPath", str(hooks))):
        subprocess.run(["git", "-C", str(root), "config", key, value], check=True)
    (root / "raw" / "sessions" / ".keep").write_text("", encoding="utf-8")
    subprocess.run(["git", "-C", str(root), "add", "."], check=True)
    subprocess.run(["git", "-C", str(root), "commit", "-q", "-m", "init"], check=True)
    subprocess.run(["git", "-C", str(root), "remote", "add", "origin", str(remote)], check=True)
    subprocess.run(["git", "-C", str(root), "push", "-q", "-u", "origin", "main"], check=True)
    policy = RepositoryPolicy(root=root, remote="origin", remote_url=str(remote), branch="main",
                              author_name="Aki Bukuhan", author_email="akibukzwork@gmail.com",
                              paths=("raw/sessions/*.md", "log.md", "wiki/personal/*.md",
                                     "wiki/personal/systems/*.md"))
    return remote, Persister([policy], store=ReceiptStore(tmp_path / "receipts.sqlite3"))


def test_note_and_log_are_committed_and_pushed_together(tmp_path, vaults, vault_repo):
    remote, persister = vault_repo
    (vaults["achimem"] / "log.md").write_text("# Log\nunrelated dirty line\n", encoding="utf-8")

    receipt = notes(tmp_path, vaults, persister=persister).save_note(request(), allowed={"achimem"})

    assert receipt["state"] == "pushed", receipt["error"]
    assert receipt["committed"] and receipt["pushed"]
    files = subprocess.run(["git", "-C", str(remote), "show", "--name-only", "--format=", "main"],
                           capture_output=True, text=True, check=True).stdout.split()
    assert sorted(files) == ["log.md", f"raw/sessions/{Path(receipt['path']).name}"]
    pushed_log = subprocess.run(["git", "-C", str(remote), "show", "main:log.md"],
                                capture_output=True, text=True, check=True).stdout
    assert "unrelated dirty line" not in pushed_log and "capture | Seminar summary" in pushed_log
    local_log = (vaults["achimem"] / "log.md").read_text(encoding="utf-8")
    assert "unrelated dirty line" in local_log and "capture | Seminar summary" in local_log


def test_failed_push_keeps_the_note_committed_locally(tmp_path, vaults, vault_repo):
    remote, persister = vault_repo

    def offline(argv, **kwargs):
        if argv[1] in {"push", "ls-remote"}:
            return subprocess.CompletedProcess(argv, 128, "", "fatal: Could not resolve host")
        return subprocess.run(argv, **kwargs)

    persister.runner = offline
    receipt = notes(tmp_path, vaults, persister=persister).save_note(request(), allowed={"achimem"})

    assert receipt["state"] == "committed" and receipt["pushed"] is False
    assert receipt["error"].startswith("push_failed")


def test_completed_school_task_adds_one_note_to_its_linked_record(tmp_path, vaults):
    tasks = tmp_path / "tasks.md"
    tasks.write_text("# Tasks\n\n## Active\n\n## Blocked\n\n## Done\n", encoding="utf-8")
    calendars = tmp_path / "calendars.json"
    write_calendars(calendars)
    tool = notes(tmp_path, vaults)
    service = cohesion.CohesionService(db_path=tmp_path / "c.sqlite3", tasks_path=tasks,
                                       calendar=FakeCalendar(), calendars_path=calendars, notes=tool)
    created = service.submit({"version": 1, "source": {**SOURCE, "kind": "telegram_message"},
                              "intent": {"action": "upsert", "category": "quick_task",
                                         "title": "Submit STDISCM lab", "area": "school",
                                         "placement": "tasks"}})
    item_id = created["item_id"]
    tool.save_note(request("schoolmem", title="STDISCM lab notes", item_id=item_id),
                   allowed={"schoolmem"})

    done = {"version": 1, "source": {**SOURCE, "id": "telegram:-100:8:r1", "native_id": "-100:8",
                                     "kind": "telegram_message"},
            "intent": {"action": "complete", "item_id": item_id}}
    first = service.submit(done)
    service.submit(done)

    assert first["note"]["state"] == "saved"
    inbox = sorted(path.name for path in (vaults["schoolmem"] / "inbox").iterdir())
    assert len(inbox) == 2 and any("completed-submit-stdiscm-lab" in name for name in inbox)
    assert tasks.read_text(encoding="utf-8").count("Submit STDISCM lab") == 1


def test_cohesion_advertises_note_destinations(tmp_path):
    service = cohesion.CohesionService(db_path=tmp_path / "c.sqlite3", tasks_path=tmp_path / "t.md",
                                       calendar=FakeCalendar())

    assert service.capabilities()["note_destinations"] == ["achimem", "schoolmem"]


def test_cli_rejects_a_note_outside_the_topic_scope(capsys, monkeypatch, tmp_path):
    monkeypatch.setattr("sys.stdin", __import__("io").StringIO(json.dumps(request("achimem"))))

    status = vault_notes.main(["note", "--allow", "schoolmem"])

    assert status == 1
    assert json.loads(capsys.readouterr().out)["error"] == "destination_not_permitted_for_topic"
