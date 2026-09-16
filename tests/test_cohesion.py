import json
import subprocess

import cohesion
import pytest

SOURCE_TIME = "2026-09-11T15:30:00+08:00"


class FakeCalendar:
    def __init__(self):
        self.events = {}
        self.insert_calls = 0
        self.update_calls = 0

    def insert(self, *, profile, calendar_id, event_id, body):
        self.insert_calls += 1
        event = {**body, "id": event_id, "etag": f"v{self.insert_calls}"}
        self.events[event_id] = event
        return event

    def get(self, *, profile, calendar_id, event_id):
        return self.events.get(event_id)

    def update(self, *, profile, calendar_id, event_id, body, expected_version):
        current = self.events[event_id]
        if current["etag"] != expected_version:
            raise cohesion.ConcurrentEdit("calendar event changed")
        self.update_calls += 1
        event = {**body, "id": event_id, "etag": f"updated-{self.update_calls}"}
        self.events[event_id] = event
        return event


class FailOnceCalendar(FakeCalendar):
    def insert(self, **kwargs):
        self.insert_calls += 1
        if self.insert_calls == 1:
            raise cohesion.CohesionError("calendar unavailable")
        event = {**kwargs["body"], "id": kwargs["event_id"], "etag": "v2"}
        self.events[kwargs["event_id"]] = event
        return event


class AcceptedTimeoutCalendar(FakeCalendar):
    def insert(self, **kwargs):
        super().insert(**kwargs)
        raise subprocess.TimeoutExpired("calendar insert", 30)


def request(source_id, category, title, **intent):
    return {
        "version": 1,
        "source": {
            "id": source_id,
            "kind": "fixture",
            "native_id": source_id,
            "revision": 1,
            "timestamp": SOURCE_TIME,
        },
        "intent": {"action": "upsert", "category": category, "title": title, **intent},
    }


def service(tmp_path, calendar=None):
    tasks_path = tmp_path / "tasks.md"
    tasks_path.write_text("# Tasks\n\n## Active\n\n## Blocked\n\n## Done\n", encoding="utf-8")
    return cohesion.CohesionService(
        db_path=tmp_path / "cohesion.sqlite3",
        tasks_path=tasks_path,
        calendar=calendar or FakeCalendar(),
    )


def test_capabilities_are_versioned_and_do_not_offer_shell_or_file_access(tmp_path):
    app = service(tmp_path)
    capabilities = app.capabilities()

    assert capabilities == {
        "version": 1,
        "operations": ["upsert", "complete"],
        "destinations": ["tasks", "calendar"],
        "placements": ["tasks", "calendar", "both"],
    }
    assert "shell" not in str(capabilities).lower()
    assert "file" not in str(capabilities).lower()
    assert app.db_path.stat().st_mode & 0o777 == 0o600


def test_seeded_preferences_drive_the_three_placements(tmp_path):
    calendar = FakeCalendar()
    app = service(tmp_path, calendar)

    social = app.submit(
        request(
            "social-1",
            "social_plan",
            "Dinner with Yna",
            start="2026-09-12T19:00:00",
            end="2026-09-12T21:00:00",
            calendar={"profile": "personal", "id": "personal-id"},
        )
    )
    quick = app.submit(request("quick-1", "quick_task", "Buy toothpaste", area="personal"))
    school = app.submit(
        request(
            "school-1",
            "school_deadline",
            "Submit thesis draft",
            area="school",
            due="tomorrow",
            calendar={"profile": "dlsu", "id": "thesis-id"},
        )
    )

    assert social["placement"] == "calendar"
    assert [operation["destination"] for operation in social["applied"]] == ["calendar"]
    assert quick["placement"] == "tasks"
    assert [operation["destination"] for operation in quick["applied"]] == ["tasks"]
    assert school["placement"] == "both"
    assert {operation["destination"] for operation in school["applied"]} == {
        "tasks",
        "calendar",
    }
    assert "@2026-09-12" in app.tasks_path.read_text()
    assert calendar.insert_calls == 2
    timed = next(event for event in calendar.events.values() if event["summary"] == "Dinner with Yna")
    deadline = next(
        event for event in calendar.events.values() if event["summary"] == "Submit thesis draft"
    )
    assert timed["start"] == {
        "dateTime": "2026-09-12T19:00:00+08:00",
        "timeZone": "Asia/Manila",
    }
    assert deadline["start"] == {"date": "2026-09-12"}
    assert deadline["end"] == {"date": "2026-09-13"}


def test_date_alone_does_not_change_a_tasks_only_preference(tmp_path):
    app = service(tmp_path)

    receipt = app.submit(
        request(
            "ticket-1",
            "coding_ticket",
            "Fix parser",
            area="projects",
            due="2026-10-01",
        )
    )

    assert receipt["placement"] == "tasks"
    assert [operation["destination"] for operation in receipt["applied"]] == ["tasks"]


def test_explicit_placement_overrides_the_seeded_preference_for_one_item(tmp_path):
    app = service(tmp_path)

    receipt = app.submit(
        request(
            "social-task",
            "social_plan",
            "Plan reunion",
            area="personal",
            placement="tasks",
        )
    )

    assert receipt["placement"] == "tasks"
    assert app.context()["preferences"]["social_plan"] == "calendar"
    assert app.context("social_plan")["items"] == [
        {
            "item_id": receipt["item_id"],
            "category": "social_plan",
            "title": "Plan reunion",
            "state": "active",
            "due": None,
            "placement": "tasks",
        }
    ]


def test_task_identity_survives_title_and_date_changes_then_completion(tmp_path):
    app = service(tmp_path)
    first = app.submit(
        request(
            "task-create",
            "quick_task",
            "Draft outline",
            area="personal",
            due="2026-09-12",
            priority="high",
            tags=["achicore", "THS-ST2"],
        )
    )
    item_id = first["item_id"]
    first_task_id = first["applied"][0]["result"]["task_id"]

    changed = app.submit(
        request(
            "task-edit",
            "quick_task",
            "Draft final outline",
            item_id=item_id,
            area="personal",
            due="2026-09-14",
            priority="low",
            tags=["achicore", "THS-ST2"],
        )
    )
    completed_request = request(
        "task-complete", "quick_task", "ignored", item_id=item_id, area="personal"
    )
    completed_request["intent"] = {"action": "complete", "item_id": item_id}
    completed = app.submit(completed_request)

    content = app.tasks_path.read_text()
    assert changed["applied"][0]["result"]["task_id"] == first_task_id
    assert completed["applied"][0]["result"]["task_id"] == first_task_id
    assert content.count(f"<!-- task-id: {first_task_id} -->") == 1
    assert "- [x] Draft final outline #personal !low #achicore #THS-ST2 @2026-09-14" in content
    assert "(done 2026-09-11)" in content


def test_redelivery_after_partial_failure_retries_only_calendar(tmp_path):
    calendar = FailOnceCalendar()
    app = service(tmp_path, calendar)
    payload = request(
        "partial-1",
        "school_deadline",
        "Submit paper",
        area="school",
        due="tomorrow",
        calendar={"profile": "dlsu", "id": "course"},
    )

    first = app.submit(payload)
    second = app.submit(payload)

    assert [operation["destination"] for operation in first["applied"]] == ["tasks"]
    assert [operation["destination"] for operation in first["pending"]] == ["calendar"]
    assert {operation["destination"] for operation in second["applied"]} == {
        "tasks",
        "calendar",
    }
    task_operation = next(op for op in second["applied"] if op["destination"] == "tasks")
    assert task_operation["attempts"] == 1
    assert calendar.insert_calls == 2


def test_stale_calendar_redelivery_cannot_overwrite_a_newer_update(tmp_path):
    calendar = FailOnceCalendar()
    app = service(tmp_path, calendar)
    original = request(
        "stale-calendar-source",
        "school_deadline",
        "Old title",
        area="school",
        due="tomorrow",
        calendar={"profile": "dlsu", "id": "course"},
    )

    first = app.submit(original)
    item_id = first["item_id"]
    newer = app.submit(
        request(
            "new-calendar-source",
            "school_deadline",
            "New title",
            item_id=item_id,
            area="school",
            due="tomorrow",
            calendar={"profile": "dlsu", "id": "course"},
        )
    )
    replay = app.submit(original)

    assert [operation["destination"] for operation in first["applied"]] == ["tasks"]
    assert {operation["destination"] for operation in newer["applied"]} == {
        "tasks",
        "calendar",
    }
    assert [operation["destination"] for operation in replay["applied"]] == ["tasks"]
    assert replay["pending"] == []
    assert replay["superseded"][0]["error"] == "operation superseded by newer item update"
    assert app.context()["pending_count"] == 0
    event_id = next(
        operation for operation in newer["applied"] if operation["destination"] == "calendar"
    )["result"]["event_id"]
    assert calendar.update_calls == 0
    assert calendar.events[event_id]["summary"] == "New title"


def test_accepted_insert_timeout_is_reconciled_without_a_duplicate(tmp_path):
    calendar = AcceptedTimeoutCalendar()
    app = service(tmp_path, calendar)

    receipt = app.submit(
        request(
            "timeout-1",
            "social_plan",
            "Dinner",
            start="2026-09-12T19:00:00",
            end="2026-09-12T20:00:00",
            calendar={"profile": "personal", "id": "personal"},
        )
    )

    assert len(receipt["applied"]) == 1
    assert receipt["pending"] == []
    assert calendar.insert_calls == 1
    assert len(calendar.events) == 1


def test_same_item_update_preserves_calendar_identity_and_checks_ownership(tmp_path):
    calendar = FakeCalendar()
    app = service(tmp_path, calendar)
    first = app.submit(
        request(
            "event-create",
            "social_plan",
            "Dinner",
            start="2026-09-12T19:00:00",
            end="2026-09-12T20:00:00",
            calendar={"profile": "personal", "id": "personal"},
        )
    )
    item_id = first["item_id"]
    event_id = first["applied"][0]["result"]["event_id"]
    calendar.events[event_id]["extendedProperties"]["private"]["achios_item_id"] = "other"

    second = app.submit(
        request(
            "event-edit",
            "social_plan",
            "Late dinner",
            item_id=item_id,
            start="2026-09-12T20:00:00",
            end="2026-09-12T21:00:00",
            calendar={"profile": "personal", "id": "personal"},
        )
    )

    assert second["applied"] == []
    assert second["pending"][0]["error"] == "calendar event ownership is unknown"
    assert calendar.update_calls == 0


def test_existing_calendar_item_rejects_placement_change_without_writes(tmp_path):
    calendar = FakeCalendar()
    app = service(tmp_path, calendar)
    first = app.submit(
        request(
            "calendar-to-tasks-before",
            "social_plan",
            "Dinner",
            start="2026-09-12T19:00:00",
            end="2026-09-12T20:00:00",
            calendar={"profile": "personal", "id": "calendar-a"},
        )
    )
    item_id = first["item_id"]
    event_id = first["applied"][0]["result"]["event_id"]
    tasks_before = app.tasks_path.read_text()
    event_before = dict(calendar.events[event_id])

    second = app.submit(
        request(
            "calendar-to-tasks-after",
            "social_plan",
            "Dinner as a task",
            item_id=item_id,
            placement="tasks",
            area="personal",
        )
    )

    assert second["applied"] == []
    assert "placement or Calendar target change requires clarification" in second["pending"][0][
        "error"
    ]
    assert app.tasks_path.read_text() == tasks_before
    assert calendar.events[event_id] == event_before
    assert app.context()["items"] == [
        {
            "item_id": item_id,
            "category": "social_plan",
            "title": "Dinner",
            "state": "active",
            "due": None,
            "placement": "calendar",
        }
    ]


def test_existing_calendar_item_rejects_calendar_target_change_without_writes(tmp_path):
    calendar = FakeCalendar()
    app = service(tmp_path, calendar)
    first = app.submit(
        request(
            "calendar-target-before",
            "social_plan",
            "Dinner",
            start="2026-09-12T19:00:00",
            end="2026-09-12T20:00:00",
            calendar={"profile": "personal", "id": "calendar-a"},
        )
    )
    item_id = first["item_id"]
    event_id = first["applied"][0]["result"]["event_id"]

    second = app.submit(
        request(
            "calendar-target-after",
            "social_plan",
            "Dinner moved",
            item_id=item_id,
            placement="calendar",
            start="2026-09-12T20:00:00",
            end="2026-09-12T21:00:00",
            calendar={"profile": "personal", "id": "calendar-b"},
        )
    )

    assert second["applied"] == []
    assert "placement or Calendar target change requires clarification" in second["pending"][0][
        "error"
    ]
    assert calendar.insert_calls == 1
    assert calendar.update_calls == 0
    assert calendar.events[event_id]["summary"] == "Dinner"
    with app._connect() as connection:
        item = connection.execute(
            "SELECT calendar_id FROM items WHERE item_id = ?", (item_id,)
        ).fetchone()
    assert item["calendar_id"] == "calendar-a"


def test_calendar_update_refuses_a_concurrent_human_edit(tmp_path):
    calendar = FakeCalendar()
    app = service(tmp_path, calendar)
    first = app.submit(
        request(
            "event-before-human",
            "social_plan",
            "Dinner",
            start="2026-09-12T19:00:00",
            end="2026-09-12T20:00:00",
            calendar={"profile": "personal", "id": "personal"},
        )
    )
    item_id = first["item_id"]
    event_id = first["applied"][0]["result"]["event_id"]
    calendar.events[event_id]["etag"] = "human-edit"

    changed = app.submit(
        request(
            "event-after-human",
            "social_plan",
            "Late dinner",
            item_id=item_id,
            start="2026-09-12T20:00:00",
            end="2026-09-12T21:00:00",
            calendar={"profile": "personal", "id": "personal"},
        )
    )

    assert changed["applied"] == []
    assert "changed since the last applied operation" in changed["pending"][0]["error"]
    assert calendar.events[event_id]["summary"] == "Dinner"


def test_source_reuse_with_different_content_is_pending_and_writes_nothing(tmp_path):
    app = service(tmp_path)
    first = request("same-source", "quick_task", "First", area="personal")
    app.submit(first)
    before = app.tasks_path.read_text()
    changed = request("same-source", "quick_task", "Second", area="personal")

    receipt = app.submit(changed)

    assert receipt["applied"] == []
    assert receipt["item_id"] is None
    assert "different content" in receipt["pending"][0]["error"]
    assert app.tasks_path.read_text() == before


def test_empty_operation_result_is_retained(tmp_path, monkeypatch):
    app = service(tmp_path)
    monkeypatch.setattr(app, "_apply_task", lambda operation: ({}, "empty-result"))

    receipt = app.submit(request("empty-result", "quick_task", "No payload", area="personal"))

    assert receipt["applied"][0]["result"] == {}


def test_successful_redelivery_returns_the_receipt_without_repeating_writes(tmp_path):
    calendar = FakeCalendar()
    app = service(tmp_path, calendar)
    payload = request(
        "repeat-success",
        "school_deadline",
        "Submit slides",
        area="school",
        due="2026-09-15",
        calendar={"profile": "dlsu", "id": "course"},
    )

    first = app.submit(payload)
    second = app.submit(payload)

    assert first == second
    assert calendar.insert_calls == 1
    assert app.tasks_path.read_text().count("Submit slides") == 1


def test_calendar_completion_preserves_time_and_records_completed_state(tmp_path):
    calendar = FakeCalendar()
    app = service(tmp_path, calendar)
    first = app.submit(
        request(
            "deadline-create",
            "school_deadline",
            "Final paper",
            area="school",
            due="2026-09-15",
            calendar={"profile": "dlsu", "id": "course"},
        )
    )
    item_id = first["item_id"]
    event_id = next(op for op in first["applied"] if op["destination"] == "calendar")[
        "result"
    ]["event_id"]
    original_start = calendar.events[event_id]["start"]
    complete = request("deadline-complete", "school_deadline", "ignored")
    complete["intent"] = {"action": "complete", "item_id": item_id}

    receipt = app.submit(complete)

    assert receipt["pending"] == []
    assert calendar.events[event_id]["start"] == original_start
    private = calendar.events[event_id]["extendedProperties"]["private"]
    assert private["achios_item_state"] == "completed"
    assert calendar.events[event_id]["description"] == "achiOS item state: completed"


def test_manila_relative_date_uses_the_explicit_source_timestamp(tmp_path):
    app = service(tmp_path)
    payload = request("boundary", "quick_task", "Boundary task", area="personal", due="today")
    payload["source"]["timestamp"] = "2026-09-11T16:30:00+00:00"

    app.submit(payload)

    assert "@2026-09-12" in app.tasks_path.read_text()


def test_missing_calendar_values_return_pending_after_reserving_the_source(tmp_path):
    app = service(tmp_path)
    before = app.tasks_path.read_text()

    receipt = app.submit(request("missing-calendar", "social_plan", "Dinner"))

    assert receipt["applied"] == []
    assert "profile and id are required" in receipt["pending"][0]["error"]
    assert app.tasks_path.read_text() == before
    assert app.context()["source_count"] == 1
    assert app.context()["pending_count"] == 1


def test_concurrent_task_edit_leaves_the_operation_pending(tmp_path, monkeypatch):
    app = service(tmp_path)
    original_runner = app._run_pending

    def edit_then_run(source_id):
        app.tasks_path.write_text(app.tasks_path.read_text() + "Human note\n", encoding="utf-8")
        original_runner(source_id)

    monkeypatch.setattr(app, "_run_pending", edit_then_run)

    receipt = app.submit(
        request("concurrent-task", "quick_task", "Do not overwrite", area="personal")
    )

    assert receipt["applied"] == []
    assert "changed after operation reservation" in receipt["pending"][0]["error"]
    assert "Do not overwrite" not in app.tasks_path.read_text()


def test_completion_without_an_item_identity_is_pending_not_a_title_match(tmp_path):
    app = service(tmp_path)
    payload = request("ambiguous-completion", "quick_task", "Buy milk", area="personal")
    payload["intent"] = {"action": "complete", "title": "Buy milk"}

    receipt = app.submit(payload)

    assert receipt["applied"] == []
    assert "intent.item_id" in receipt["pending"][0]["error"]
    assert "Buy milk" not in app.tasks_path.read_text()


def test_cli_submit_and_context_are_json_and_survive_restart(tmp_path, capsys):
    tasks_path = tmp_path / "tasks.md"
    tasks_path.write_text("# Tasks\n\n## Active\n\n## Blocked\n\n## Done\n", encoding="utf-8")
    db_path = tmp_path / "cohesion.sqlite3"
    input_path = tmp_path / "request.json"
    input_path.write_text(
        json.dumps(request("cli-task", "quick_task", "CLI task", area="personal")),
        encoding="utf-8",
    )

    assert (
        cohesion.main(
            ["--db", str(db_path), "--tasks", str(tasks_path), "submit", "--input", str(input_path)]
        )
        == 0
    )
    submit_receipt = json.loads(capsys.readouterr().out)
    assert submit_receipt["applied"][0]["destination"] == "tasks"

    assert cohesion.main(["--db", str(db_path), "--tasks", str(tasks_path), "context"]) == 0
    context = json.loads(capsys.readouterr().out)
    assert context["source_count"] == 1
    assert context["items"][0]["title"] == "CLI task"


def test_upsert_on_a_completed_item_is_pending_and_keeps_the_done_line(tmp_path):
    app = service(tmp_path)
    first = app.submit(request("milk-1", "quick_task", "Buy milk", area="personal"))
    item_id = first["item_id"]
    completion = request("milk-done", "quick_task", "ignored")
    completion["intent"] = {"action": "complete", "item_id": item_id}
    app.submit(completion)
    after_completion = app.tasks_path.read_text()

    receipt = app.submit(
        request("milk-2", "quick_task", "Buy milk again", area="personal", item_id=item_id)
    )

    assert receipt["applied"] == []
    assert "completed item" in receipt["pending"][0]["error"]
    assert app.tasks_path.read_text() == after_completion
    assert "- [x] Buy milk " in after_completion
    assert "Buy milk again" not in after_completion
    assert app.context()["items"][0]["state"] == "completed"


def test_redelivery_after_a_concurrent_task_edit_finally_applies(tmp_path, monkeypatch):
    app = service(tmp_path)
    original_runner = app._run_pending

    def edit_then_run(source_id):
        app.tasks_path.write_text(app.tasks_path.read_text() + "Human note\n", encoding="utf-8")
        original_runner(source_id)

    monkeypatch.setattr(app, "_run_pending", edit_then_run)
    payload = request("retry-task", "quick_task", "Survives the edit", area="personal")
    first = app.submit(payload)
    monkeypatch.setattr(app, "_run_pending", original_runner)

    redelivery = app.submit(payload)

    assert first["applied"] == []
    assert "changed after operation reservation" in first["pending"][0]["error"]
    assert [operation["destination"] for operation in redelivery["applied"]] == ["tasks"]
    assert redelivery["applied"][0]["attempts"] == 2
    assert redelivery["pending"] == []
    content = app.tasks_path.read_text()
    assert "Survives the edit" in content
    assert "Human note" in content


def test_a_resolved_clarification_stops_counting_as_pending(tmp_path):
    app = service(tmp_path)
    incomplete = request("dinner-1", "social_plan", "Dinner")
    incomplete["source"]["native_id"] = "telegram-4417"
    corrected = request(
        "dinner-2",
        "social_plan",
        "Dinner",
        start="2026-09-12T19:00:00",
        end="2026-09-12T21:00:00",
        calendar={"profile": "personal", "id": "personal-id"},
    )
    corrected["source"]["native_id"] = "telegram-4417"

    rejected = app.submit(incomplete)
    assert app.context()["pending_count"] == 1

    accepted = app.submit(corrected)

    assert rejected["applied"] == []
    assert [operation["destination"] for operation in accepted["applied"]] == ["calendar"]
    assert app.context()["pending_count"] == 0


def test_repeated_completion_does_not_duplicate_the_calendar_note(tmp_path):
    calendar = FakeCalendar()
    app = service(tmp_path, calendar)
    first = app.submit(
        request(
            "dinner-repeat",
            "social_plan",
            "Dinner",
            start="2026-09-12T19:00:00",
            end="2026-09-12T21:00:00",
            calendar={"profile": "personal", "id": "personal-id"},
        )
    )
    item_id = first["item_id"]
    event_id = first["applied"][0]["result"]["event_id"]

    for source_id in ("dinner-done-1", "dinner-done-2"):
        completion = request(source_id, "social_plan", "ignored")
        completion["intent"] = {"action": "complete", "item_id": item_id}
        assert app.submit(completion)["pending"] == []

    assert calendar.events[event_id]["description"] == "achiOS item state: completed"


def test_all_day_deadlines_keep_the_calendar_default_reminders(tmp_path):
    calendar = FakeCalendar()
    app = service(tmp_path, calendar)

    receipt = app.submit(
        request(
            "reminder-1",
            "school_deadline",
            "Final paper",
            area="school",
            due="2026-09-15",
            calendar={"profile": "dlsu", "id": "course"},
        )
    )

    event_id = next(
        operation for operation in receipt["applied"] if operation["destination"] == "calendar"
    )["result"]["event_id"]
    assert calendar.events[event_id]["reminders"] == {"useDefault": True}


def test_submit_closes_every_database_connection(tmp_path, monkeypatch):
    opened = []
    real_connect = cohesion.sqlite3.connect

    def tracking_connect(*args, **kwargs):
        connection = real_connect(*args, **kwargs)
        opened.append(connection)
        return connection

    app = service(tmp_path)
    monkeypatch.setattr(cohesion.sqlite3, "connect", tracking_connect)
    app.submit(request("closed-1", "quick_task", "Close me", area="personal"))

    assert opened
    for connection in opened:
        with pytest.raises(cohesion.sqlite3.ProgrammingError):
            connection.execute("SELECT 1")


def test_accepting_an_item_clears_its_earlier_clarification(tmp_path):
    calendar = FakeCalendar()
    app = service(tmp_path, calendar)
    first = app.submit(
        request(
            "gig-1",
            "social_plan",
            "Gig",
            start="2026-09-12T19:00:00",
            end="2026-09-12T21:00:00",
            calendar={"profile": "personal", "id": "personal-id"},
        )
    )
    item_id = first["item_id"]
    rejected = app.submit(
        request("gig-2", "social_plan", "Gig", item_id=item_id, placement="tasks", area="personal")
    )
    assert "clarification" in rejected["pending"][0]["error"]
    assert app.context()["pending_count"] == 1

    app.submit(
        request(
            "gig-3",
            "social_plan",
            "Gig moved later",
            item_id=item_id,
            start="2026-09-12T20:00:00",
            end="2026-09-12T22:00:00",
            calendar={"profile": "personal", "id": "personal-id"},
        )
    )

    assert app.context()["pending_count"] == 0


def test_gws_transport_sends_the_event_id_and_reads_a_missing_event(monkeypatch):
    calls = []

    def fake_gws(profile, *args):
        calls.append((profile, args))
        if args[2] == "get":
            raise cohesion.gcal_add.GwsError("gws dlsu: 404 Not Found")
        return {"id": "abc", "etag": "v1"}

    monkeypatch.setattr(cohesion.gcal_add, "gws", fake_gws)
    transport = cohesion.GwsCalendarTransport()

    assert transport.get(profile="dlsu", calendar_id="course", event_id="abc") is None
    inserted = transport.insert(
        profile="dlsu", calendar_id="course", event_id="abc", body={"summary": "Paper"}
    )

    assert inserted["etag"] == "v1"
    assert json.loads(calls[0][1][4]) == {"calendarId": "course", "eventId": "abc"}
    assert json.loads(calls[1][1][6]) == {"summary": "Paper", "id": "abc"}


def test_gws_transport_reraises_a_non_missing_error(monkeypatch):
    def fake_gws(profile, *args):
        raise cohesion.gcal_add.GwsError("gws dlsu: 403 forbidden")

    monkeypatch.setattr(cohesion.gcal_add, "gws", fake_gws)

    with pytest.raises(cohesion.gcal_add.GwsError):
        cohesion.GwsCalendarTransport().get(
            profile="dlsu", calendar_id="course", event_id="abc"
        )


def test_a_retry_does_not_overwrite_a_human_edit_to_the_task_line(tmp_path, monkeypatch):
    app = service(tmp_path)
    first = app.submit(request("proposal-1", "quick_task", "Draft proposal", area="school"))
    update = request(
        "proposal-2", "quick_task", "Draft proposal v2", area="school", item_id=first["item_id"]
    )
    original_runner = app._run_pending

    def edit_then_run(source_id):
        app.tasks_path.write_text(app.tasks_path.read_text() + "Human note\n", encoding="utf-8")
        original_runner(source_id)

    monkeypatch.setattr(app, "_run_pending", edit_then_run)
    failed = app.submit(update)
    monkeypatch.setattr(app, "_run_pending", original_runner)
    lines = app.tasks_path.read_text().splitlines()
    index = next(number for number, line in enumerate(lines) if "Draft proposal" in line)
    lines[index] = lines[index].replace("Draft proposal", "Draft proposal (ASK DR CRUZ FIRST)")
    app.tasks_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    redelivery = app.submit(update)

    assert failed["applied"] == []
    assert redelivery["applied"] == []
    assert "task line changed" in redelivery["pending"][0]["error"]
    content = app.tasks_path.read_text()
    assert "(ASK DR CRUZ FIRST)" in content
    assert "Draft proposal v2" not in content


def test_a_retry_adopts_an_unrelated_edit_and_still_updates_the_task_line(tmp_path, monkeypatch):
    app = service(tmp_path)
    first = app.submit(request("memo-1", "quick_task", "Write memo", area="school"))
    update = request(
        "memo-2", "quick_task", "Write memo v2", area="school", item_id=first["item_id"]
    )
    original_runner = app._run_pending

    def edit_then_run(source_id):
        app.tasks_path.write_text(app.tasks_path.read_text() + "Human note\n", encoding="utf-8")
        original_runner(source_id)

    monkeypatch.setattr(app, "_run_pending", edit_then_run)
    failed = app.submit(update)
    monkeypatch.setattr(app, "_run_pending", original_runner)

    redelivery = app.submit(update)

    assert failed["applied"] == []
    assert [operation["destination"] for operation in redelivery["applied"]] == ["tasks"]
    content = app.tasks_path.read_text()
    assert "Write memo v2" in content
    assert "Human note" in content
    assert "Write memo #" not in content
