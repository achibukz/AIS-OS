import json
from datetime import datetime, timezone

import pytest

import cohesion
from canvas_client import CanvasError
from canvas_store import configure_courses, open_writer, save_failure, save_snapshot
from canvas_events import deliver
from canvas_tasks import (
    activate,
    activation_preview,
    announcement_intent,
    assignment_state,
    reconcile,
)
from test_canvas_store import AT, MAPPING, assignment
from test_cohesion import FakeCalendar, FailOnceCalendar, write_calendars


NOW = datetime.fromisoformat(AT)


def active_assignment(item_id=1, due="2026-09-12T00:00:00Z", **changes):
    return assignment(
        item_id,
        due,
        submission_status="unsubmitted",
        submitted_at=None,
        **changes,
    )


def announcement(item_id=9, title="Homework 2", message="Submit Homework 2 by September 15"):
    return {
        "id": item_id,
        "title": title,
        "message": message,
        "posted_at": "2026-09-08T00:00:00+00:00",
        "source_url": f"https://dlsu.instructure.com/courses/42/discussion_topics/{item_id}",
    }


@pytest.fixture
def db(tmp_path):
    with open_writer(tmp_path / "canvas.sqlite3") as connection:
        configure_courses(connection, MAPPING)
        yield connection


def service(tmp_path, calendar=None):
    tasks = tmp_path / "tasks.md"
    tasks.write_text("# Tasks\n\n## Active\n\n## Blocked\n\n## Done\n", encoding="utf-8")
    calendars = tmp_path / "calendars.json"
    write_calendars(calendars, extra=[{
        "name": "DLSU",
        "id": "dlsu-main",
        "profile": "dlsu",
        "write_owner": ["cohesion"],
        "schedule": True,
    }])
    return cohesion.CohesionService(
        db_path=tmp_path / "cohesion.sqlite3",
        tasks_path=tasks,
        calendar=calendar or FakeCalendar(),
        calendars_path=calendars,
    )


def test_activation_preview_is_bounded_and_activation_is_explicit(db):
    rows = [active_assignment(1), active_assignment(2, None)]
    save_snapshot(db, 42, "assignments", rows, AT)
    save_snapshot(db, 42, "announcements", [announcement()], AT)

    preview = activation_preview(db, "STDISCM", now=NOW, limit=1)

    assert preview["active"] is False
    assert preview["eligible_assignments"] == 1
    assert preview["blocked_assignments"] == 1
    assert preview["announcement_tasks"] == 1
    assert len(preview["preview"]) == 1 and preview["remaining"] == 1
    assert db.execute("SELECT count(*) FROM canvas_task_ops").fetchone()[0] == 0

    result = activate(db, "STDISCM", at=AT, now=NOW)
    assert result["activated"] is True and result["queued"] == 2
    assert db.execute("SELECT count(*) FROM canvas_task_ops").fetchone()[0] == 2


def test_historical_baseline_does_not_queue_until_activation(db):
    save_snapshot(db, 42, "assignments", [active_assignment()], AT)
    save_snapshot(db, 42, "assignments", [active_assignment(name="Renamed")], AT)

    assert db.execute("SELECT count(*) FROM canvas_task_ops").fetchone()[0] == 0


def test_assignment_replay_rename_and_due_a_b_a_keep_one_task(db, tmp_path):
    first = active_assignment(name="Lab A")
    save_snapshot(db, 42, "assignments", [first], AT)
    activate(db, "STDISCM", at=AT, now=NOW)
    app = service(tmp_path)

    assert reconcile(db, service=app)["applied"] == 1
    changed = active_assignment(name="Lab B", due="2026-09-13T00:00:00Z")
    save_snapshot(db, 42, "assignments", [changed], "2026-09-08T11:00:00+00:00")
    assert reconcile(db, service=app)["applied"] == 1
    save_snapshot(db, 42, "assignments", [first], "2026-09-08T12:00:00+00:00")
    assert reconcile(db, service=app)["applied"] == 1
    save_snapshot(db, 42, "assignments", [first], "2026-09-08T13:00:00+00:00")

    content = app.tasks_path.read_text(encoding="utf-8")
    assert content.count("<!-- task-id:") == 1
    assert "STDISCM Lab A" in content and "@2026-09-12" in content
    assert db.execute("SELECT count(*) FROM canvas_task_ops").fetchone()[0] == 3


@pytest.mark.parametrize(
    "record,state",
    [
        (active_assignment(), "active"),
        (assignment(), "submitted"),
        (assignment(submission_status="graded", grade="A"), "graded"),
        (assignment(submission_status="completed"), "completed"),
        (assignment(excused=True), "excused"),
        (assignment(submission_status="mystery", submitted_at=None), "unknown"),
    ],
)
def test_submission_states_stay_distinct(record, state):
    assert assignment_state(record) == state


def test_submission_completes_the_existing_link(db, tmp_path):
    save_snapshot(db, 42, "assignments", [active_assignment()], AT)
    activate(db, "STDISCM", at=AT, now=NOW)
    app = service(tmp_path)
    reconcile(db, service=app)

    save_snapshot(db, 42, "assignments", [assignment()], "2026-09-08T11:00:00+00:00")
    result = reconcile(db, service=app)

    assert result["applied"] == 1
    content = app.tasks_path.read_text(encoding="utf-8")
    assert "- [x] STDISCM Lab" in content
    assert db.execute(
        "SELECT source_state FROM canvas_task_ops ORDER BY id DESC LIMIT 1"
    ).fetchone()[0] == "submitted"


def test_unknown_state_and_missing_due_never_invent_changes(db):
    save_snapshot(db, 42, "assignments", [active_assignment()], AT)
    activate(db, "STDISCM", at=AT, now=NOW)
    db.execute("DELETE FROM canvas_task_ops")

    unknown = assignment(submission_status="mystery", submitted_at=None)
    save_snapshot(db, 42, "assignments", [unknown], "2026-09-08T11:00:00+00:00")
    missing = active_assignment(due=None)
    save_snapshot(db, 42, "assignments", [missing], "2026-09-08T12:00:00+00:00")

    rows = db.execute(
        "SELECT source_state,state,intent FROM canvas_task_ops ORDER BY id"
    ).fetchall()
    assert [(row[0], row[1]) for row in rows] == [
        ("unknown", "conflict"),
        ("active", "conflict"),
    ]
    assert all(row[2] is None for row in rows)


def test_stale_or_failed_assignment_data_cannot_activate(db):
    save_snapshot(db, 42, "assignments", [active_assignment()], AT)
    with pytest.raises(CanvasError, match="stale_assignment_data"):
        activation_preview(db, "STDISCM", now=datetime(2026, 9, 9, tzinfo=timezone.utc))
    save_failure(db, 42, "assignments", "transient_failure", "2026-09-08T11:00:00+00:00")
    with pytest.raises(CanvasError, match="assignment_data_failed"):
        activation_preview(db, "STDISCM", now=NOW)


def test_stale_announcement_data_is_named_and_not_extracted(db):
    save_snapshot(db, 42, "assignments", [active_assignment()], AT)
    save_snapshot(db, 42, "announcements", [announcement()], AT)
    save_failure(db, 42, "announcements", "transient_failure", "2026-09-08T11:00:00+00:00")

    preview = activation_preview(db, "STDISCM", now=NOW)
    result = activate(db, "STDISCM", at=AT, now=NOW)

    assert preview["announcements_ready"] is False
    assert preview["announcement_tasks"] == 0
    assert result["queued"] == 1


def test_partial_destination_failure_stays_pending_independently(db, tmp_path):
    save_snapshot(db, 42, "assignments", [active_assignment()], AT)
    activate(db, "STDISCM", at=AT, now=NOW)
    app = service(tmp_path, FailOnceCalendar())

    first = reconcile(db, service=app)
    second = reconcile(db, service=app)

    assert first["pending"] == 1
    assert first["task_applied"] == 1 and first["calendar_applied"] == 0
    first_receipt = first["receipts"][0]["receipt"]
    assert [item["destination"] for item in first_receipt["applied"]] == ["tasks"]
    assert [item["destination"] for item in first_receipt["pending"]] == ["calendar"]
    assert second["applied"] == 1 and second["remaining"] == 0
    assert second["task_applied"] == 0 and second["calendar_applied"] == 1


def test_manual_conflict_remains_pending(db):
    save_snapshot(db, 42, "assignments", [active_assignment()], AT)
    activate(db, "STDISCM", at=AT, now=NOW)

    class ConflictService:
        def submit(self, request):
            return {
                "item_id": request["intent"]["item_id"],
                "applied": [],
                "pending": [{"destination": "tasks", "error": "manual edit conflict"}],
            }

    result = reconcile(db, service=ConflictService())

    assert result["pending"] == 1
    row = db.execute("SELECT state,error FROM canvas_task_ops").fetchone()
    assert tuple(row) == ("pending", "manual edit conflict")


def test_notification_delivery_is_not_task_creation(db):
    save_snapshot(db, 42, "assignments", [], AT)
    activate(db, "STDISCM", at=AT, now=NOW)
    save_snapshot(
        db,
        42,
        "assignments",
        [active_assignment()],
        "2026-09-08T11:00:00+00:00",
    )

    assert deliver(db, sender=lambda _message: 1)["sent"] == 1
    assert db.execute("SELECT state FROM canvas_task_ops").fetchone()[0] == "pending"
    assert db.execute("SELECT count(*) FROM canvas_task_links").fetchone()[0] == 0


def test_announcement_extraction_requires_action_deadline_and_explicit_date(db):
    course = db.execute("SELECT * FROM courses WHERE id=42").fetchone()

    intent = announcement_intent(course, announcement())
    assert intent["due"] == "2026-09-15"
    assert intent["title"] == "STDISCM Homework 2"
    assert announcement_intent(course, announcement(message="Class meets on September 15")) is None
    assert announcement_intent(course, announcement(message="Submit the work soon")) is None


def test_announcement_replay_queues_one_task_after_activation(db):
    save_snapshot(db, 42, "assignments", [active_assignment()], AT)
    save_snapshot(db, 42, "announcements", [], AT)
    activate(db, "STDISCM", at=AT, now=NOW)
    db.execute("DELETE FROM canvas_task_ops")

    item = announcement()
    save_snapshot(db, 42, "announcements", [item], "2026-09-08T11:00:00+00:00")
    save_snapshot(db, 42, "announcements", [item], "2026-09-08T12:00:00+00:00")

    rows = db.execute(
        "SELECT source_kind,source_id,source_revision FROM canvas_task_ops"
    ).fetchall()
    assert [tuple(row) for row in rows] == [("announcement", 9, 1)]


def test_announcement_edit_updates_the_same_task_and_ambiguous_edit_conflicts(db, tmp_path):
    save_snapshot(db, 42, "assignments", [active_assignment()], AT)
    save_snapshot(db, 42, "announcements", [], AT)
    activate(db, "STDISCM", at=AT, now=NOW)
    db.execute("DELETE FROM canvas_task_ops")
    app = service(tmp_path)

    first = announcement()
    save_snapshot(db, 42, "announcements", [first], "2026-09-08T11:00:00+00:00")
    assert reconcile(db, service=app)["applied"] == 1
    changed = announcement(message="Submit Homework 2 by September 16")
    save_snapshot(db, 42, "announcements", [changed], "2026-09-08T12:00:00+00:00")
    assert reconcile(db, service=app)["applied"] == 1

    content = app.tasks_path.read_text(encoding="utf-8")
    assert content.count("<!-- task-id:") == 1
    assert "@2026-09-16" in content

    ambiguous = announcement(message="Homework 2 details were revised")
    save_snapshot(db, 42, "announcements", [ambiguous], "2026-09-08T13:00:00+00:00")
    report = reconcile(db, service=app)
    assert report["conflicts"] == 1
    assert "@2026-09-16" in app.tasks_path.read_text(encoding="utf-8")
