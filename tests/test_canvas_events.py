import json
import sqlite3

import pytest

from canvas_events import deliver, preview
from canvas_store import (configure_courses, open_reader, open_writer, project_record, query,
                          save_auth, save_failure, save_snapshot)
from test_canvas_store import AT, MAPPING, NOW, assignment


@pytest.fixture
def db(tmp_path):
    with open_writer(tmp_path / "cache.sqlite3") as db:
        configure_courses(db, MAPPING)
        yield db


def test_each_category_baseline_is_silent(db):
    save_snapshot(db, 42, "assignments", [assignment()], AT)
    save_failure(db, 42, "announcements", "permission_denied", AT)
    save_snapshot(db, 42, "announcements", [{"id": 1, "title": "Old announcement"}], AT)
    save_snapshot(db, 42, "grades", [{"id": 1, "current_grade": "A", "current_score": 95,
                                     "final_grade": None, "final_score": None}], AT)
    save_auth(db, "valid", AT)
    assert preview(db)["messages"] == []


def test_repeated_transitions_have_distinct_durable_identities(db):
    save_snapshot(db, 42, "assignments", [assignment()], AT)
    b = assignment(due="2026-09-09T00:00:00Z")
    for row in (b, b, assignment(), b):
        save_snapshot(db, 42, "assignments", [row], AT)
    messages = preview(db)["messages"]
    assert len(messages) == 3
    assert len({m["event_id"] for m in messages}) == 3
    assert messages[0]["text"] == messages[2]["text"]


def test_description_changes_remain_queryable_and_silent(db):
    save_snapshot(db, 42, "assignments", [assignment()], AT)
    save_snapshot(db, 42, "assignments", [assignment(description="Revised instructions")], AT)
    assert preview(db)["messages"] == []
    assert query(db, "detail", course="STDISCM", item=1, now=NOW)["data"][0]["description"] == "Revised instructions"


def test_crash_during_snapshot_rolls_back_event_and_data(db):
    save_snapshot(db, 42, "assignments", [assignment()], AT)
    db.execute("""CREATE TRIGGER crash BEFORE INSERT ON records
        BEGIN SELECT RAISE(ABORT,'injected'); END""")
    with pytest.raises(sqlite3.IntegrityError):
        save_snapshot(db, 42, "assignments", [assignment(due=None)], AT)
    assert preview(db)["messages"] == []
    assert query(db, "assignments", now=NOW)["data"][0]["due_at"] == assignment()["due_at"]


def test_crash_after_snapshot_commit_survives_reopen(tmp_path):
    path = tmp_path / "cache.sqlite3"
    with open_writer(path) as db:
        configure_courses(db, MAPPING)
        save_snapshot(db, 42, "assignments", [], AT)
        save_snapshot(db, 42, "assignments", [assignment()], AT)
    with open_writer(path) as db:
        save_snapshot(db, 42, "assignments", [assignment()], AT)
        assert len(preview(db)["messages"]) == 1


def test_outage_and_recovery_are_once_each(db):
    for state in ("expired", "expired", "valid", "valid", "expired", "valid"):
        save_auth(db, state, AT)
    kinds = [r[0] for r in db.execute("SELECT kind FROM events ORDER BY id")]
    assert kinds == ["authentication_expired", "authentication_restored"] * 2


def test_failed_delivery_stays_uncertain_and_retries(db):
    save_auth(db, "expired", AT)
    def fail(message):
        raise SystemExit("bot-token-secret")
    assert deliver(db, fail)["error"] == "delivery_unconfirmed"
    event = dict(db.execute("SELECT * FROM events").fetchone())
    assert event["state"] == "uncertain" and event["attempts"] == 1
    assert "secret" not in json.dumps(event)
    assert deliver(db, lambda message: 1)["sent"] == 1
    event = dict(db.execute("SELECT * FROM events").fetchone())
    assert event["state"] == "sent" and event["attempts"] == 2
    assert deliver(db, lambda message: pytest.fail("duplicate send"))["sent"] == 0


def test_crash_after_send_before_receipt_retries_with_possible_duplicate(db):
    save_auth(db, "expired", AT)
    sent = []
    def send(message):
        sent.append(message)
        return 1
    db.execute("""CREATE TRIGGER crash BEFORE UPDATE ON events WHEN NEW.state='sent'
        BEGIN SELECT RAISE(ABORT,'crash after send'); END""")
    with pytest.raises(sqlite3.IntegrityError):
        deliver(db, send)
    assert dict(db.execute("SELECT * FROM events").fetchone())["state"] == "uncertain"
    db.execute("DROP TRIGGER crash")
    assert deliver(db, send)["sent"] == 1
    assert len(sent) == 2 and sent[0] == sent[1]


def test_crash_before_send_keeps_event_retryable(db):
    save_auth(db, "expired", AT)
    def crash(message):
        raise KeyboardInterrupt
    with pytest.raises(KeyboardInterrupt):
        deliver(db, crash)
    assert preview(db)["messages"][0]["state"] == "uncertain"
    assert deliver(db, lambda message: 1)["sent"] == 1


def test_partial_fetch_cannot_emit_events(db):
    save_snapshot(db, 42, "assignments", [assignment()], AT)
    save_failure(db, 42, "assignments", "transient_failure", AT)
    assert preview(db)["messages"] == []


def test_preview_is_read_only_and_messages_are_bounded(tmp_path):
    path = tmp_path / "cache.sqlite3"
    with open_writer(path) as db:
        configure_courses(db, MAPPING)
        save_snapshot(db, 42, "assignments", [], AT)
        save_snapshot(db, 42, "assignments", [assignment(name="long" * 2000)], AT)
    before = path.read_bytes()
    with open_reader(path) as db:
        result = preview(db)
    assert path.read_bytes() == before
    assert len(result["messages"][0]["text"]) < 4096


def test_grades_and_new_announcements_emit_events(db):
    save_snapshot(db, 42, "assignments", [assignment()], AT)
    save_snapshot(db, 42, "announcements", [], AT)
    save_snapshot(db, 42, "assignments", [assignment(grade="10", score=10)], AT)
    save_snapshot(db, 42, "announcements", [{"id": 1, "title": "Hello", "source_url": "https://dlsu.instructure.com/courses/42/discussion_topics/1"}], AT)
    kinds = [r[0] for r in db.execute("SELECT kind FROM events ORDER BY id")]
    assert kinds == ["assignment_grade_changed", "new_announcement"]


def test_first_posted_grade_after_grade_less_baseline_emits_once(db):
    raw = {"id": 1, "name": "Lab", "due_at": "2026-09-08T00:00:00Z",
           "submission": {"user_id": 7, "workflow_state": "unsubmitted"}}
    save_snapshot(db, 42, "assignments", [project_record("assignments", raw, 42, 7)], AT)
    raw["submission"].update({"grade": "95", "score": 95})
    save_snapshot(db, 42, "assignments", [project_record("assignments", raw, 42, 7)], AT)
    kinds = [r[0] for r in db.execute("SELECT kind FROM events")]
    assert kinds == ["assignment_grade_changed"]


def test_grade_becoming_available_with_no_value_stays_silent(db):
    raw = {"id": 1, "name": "Lab", "due_at": "2026-09-08T00:00:00Z",
           "submission": {"user_id": 7, "workflow_state": "unsubmitted"}}
    save_snapshot(db, 42, "assignments", [project_record("assignments", raw, 42, 7)], AT)
    raw["submission"].update({"grade": None, "score": None})
    save_snapshot(db, 42, "assignments", [project_record("assignments", raw, 42, 7)], AT)
    assert db.execute("SELECT count(*) FROM events").fetchone()[0] == 0


def test_failed_head_does_not_block_later_events(db):
    save_auth(db, "expired", AT)
    save_auth(db, "valid", AT)
    def sender(message):
        if "expired" in message:
            raise SystemExit("rejected")
        return 1
    result = deliver(db, sender)
    assert result["sent"] == 1 and result["remaining"] == 1
    assert result["error"] == "delivery_unconfirmed"
    assert db.execute("SELECT state FROM events ORDER BY id").fetchall()[1][0] == "sent"


def test_retry_rotation_reaches_events_beyond_first_batch(db):
    for i in range(60):
        save_auth(db, "expired" if i % 2 == 0 else "valid", AT)
    deliver(db, lambda message: 0)
    result = deliver(db, lambda message: 1)
    assert result["sent"] == 50
    assert db.execute("SELECT count(*) FROM events WHERE id>50 AND state='sent'").fetchone()[0] == 10


def test_successful_multipart_receipt_is_accepted(db):
    save_auth(db, "expired", AT)
    assert deliver(db, lambda message: 2)["sent"] == 1
