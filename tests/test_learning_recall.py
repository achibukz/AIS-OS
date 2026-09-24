import datetime as dt
import json
import sqlite3

import pytest

import cohesion
import learning_recall
from test_cohesion import FakeCalendar
from vault_notes import VaultNotes

SOURCE = {"id": "telegram:1:r1", "kind": "telegram_user", "native_id": "-100:1",
          "revision": 1, "timestamp": "2026-09-24T09:00:00+08:00"}


@pytest.fixture
def service(tmp_path):
    vaults = {"achimem": tmp_path / "achiMem", "schoolmem": tmp_path / "schoolMem"}
    for root in vaults.values():
        (root / "raw" / "sessions").mkdir(parents=True)
        (root / "inbox").mkdir()
    (vaults["achimem"] / "log.md").write_text("# Log\n", encoding="utf-8")
    notes = VaultNotes(db_path=tmp_path / "notes.sqlite3", vaults=vaults)
    return cohesion.CohesionService(db_path=tmp_path / "c.sqlite3", tasks_path=tmp_path / "t.md",
                                    calendar=FakeCalendar(), notes=notes)


def learn(service, source_id="m1", **changes):
    preference = {"kind": "viewer_delivery", "scope": "global", "scope_value": "",
                  "value": "viewer_link", "evidence": "Show me the file",
                  "evidence_validated": True, "explicit": True, "exceptions": [], **changes}
    return service.semantic_preferences.record({**SOURCE, "id": source_id}, preference)


def note(service, destination, title, fact, source_id):
    return service.notes.save_note(
        {"source": {**SOURCE, "id": source_id},
         "note": {"destination": destination, "title": title,
                  "facts": [{"text": fact, "provenance": "inferred"}]}},
        allowed={destination})


def retrievals(service):
    with sqlite3.connect(service.db_path) as connection:
        return connection.execute(
            "SELECT record_kind, revision, selected, corrected_at FROM learning_retrievals ORDER BY rowid"
        ).fetchall()


def test_recall_returns_current_preferences_with_source_and_revision(service):
    learn(service)

    result = service.recall({"topic": "general", "query": "open the file", "source_id": "t:1"})

    assert 'viewer_delivery=viewer_link (global), from Aki: "Show me the file"' in result["text"]
    assert " r1:" in result["text"]
    assert retrievals(service) == [("preference", 1, 1, None)]


def test_revoked_and_superseded_revisions_never_appear(service):
    learn(service, "m1")
    learn(service, "m2", value="paste", evidence="just paste it")
    learn(service, "m3", kind="placement", value="tasks", action="revoke", evidence="stop that")

    text = service.recall({"topic": "general", "query": "x", "source_id": "t:1"})["text"]

    assert "viewer_delivery=paste" in text and "r2" in text
    assert "viewer_link" not in text


def test_a_new_revision_marks_earlier_retrievals_corrected(service):
    learn(service, "m1")
    service.recall({"topic": "general", "query": "x", "source_id": "t:1"})

    learn(service, "m2", value="paste", evidence="just paste it")

    assert retrievals(service)[0][3] is not None


def test_topics_read_only_their_own_domain(service):
    note(service, "achimem", "Seminar summary", "morning seminars", "n1")
    note(service, "schoolmem", "STDISCM seminar", "morning seminars", "n2")

    school = service.recall({"topic": "schoolmem", "query": "seminar", "source_id": "t:1"})
    personal = service.recall({"topic": "achimem", "query": "seminar", "source_id": "t:2"})
    coding = service.recall({"topic": "atlas", "query": "seminar", "source_id": "t:3"})

    assert "STDISCM seminar" in school["text"] and "Seminar summary" not in school["text"]
    assert "Seminar summary" in personal["text"] and "STDISCM" not in personal["text"]
    assert coding["text"] == "" and coding["scopes"] == []


def test_general_reaches_school_notes_only_for_a_school_request(service):
    note(service, "schoolmem", "Lab seminar notes", "seminar", "n2")

    plain = service.recall({"topic": "general", "query": "seminar plans", "source_id": "t:1"})
    school = service.recall({"topic": "general", "query": "seminar for my lab class", "source_id": "t:2"})

    assert "Lab seminar notes" not in plain["text"]
    assert "Lab seminar notes" in school["text"]


def test_recall_is_bounded_and_counts_what_it_drops(service, monkeypatch):
    for index in range(80):
        learn(service, f"m{index}", kind="placement", value="tasks", scope="category",
              scope_value=f"category_{index:02d}", evidence="put these in tasks " * 3)

    result = service.recall({"topic": "general", "query": "x", "source_id": "t:1"})

    assert len(result["text"]) <= learning_recall.MAX_TOKENS * learning_recall.CHARS_PER_TOKEN
    assert result["dropped"] > 0 and result["selected"] + result["dropped"] == 80
    selected = [row for row in retrievals(service) if row[2] == 1]
    assert len(selected) == result["selected"]


def test_stale_notes_are_left_out(service, monkeypatch):
    saved = note(service, "achimem", "Old seminar", "seminar", "n1")
    old = (dt.datetime.now() - dt.timedelta(days=400)).timestamp()
    import os
    os.utime(saved["path"], (old, old))

    assert "Old seminar" not in service.recall({"topic": "achimem", "query": "seminar",
                                                "source_id": "t:1"})["text"]


def test_recall_cli_requires_a_source(capsys, monkeypatch, tmp_path):
    monkeypatch.setattr("sys.stdin", __import__("io").StringIO(json.dumps({"query": "x"})))

    status = cohesion.main(["--db", str(tmp_path / "c.sqlite3"), "--tasks", str(tmp_path / "t.md"),
                            "recall"])

    assert status == 2
    assert "source_id" in json.loads(capsys.readouterr().out)["error"]
