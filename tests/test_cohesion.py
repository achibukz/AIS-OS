import json
import subprocess

import cohesion
import pytest

CALENDARS = [
    ("Course", "course", "dlsu"),
    ("Thesis", "thesis-id", "dlsu"),
    ("Calendar A", "calendar-a", "personal"),
    ("Calendar B", "calendar-b", "personal"),
    ("Personal", "personal", "personal"),
    ("Personal ID", "personal-id", "personal"),
]

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
        event = {**current, **body, "id": event_id, "etag": f"updated-{self.update_calls}"}
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


class VersionlessCalendar(FakeCalendar):
    """A provider that stops reporting an etag once the event exists."""

    def update(self, *, profile, calendar_id, event_id, body, expected_version):
        current = self.events[event_id]
        if current.get("etag") != expected_version:
            raise cohesion.ConcurrentEdit("calendar event changed")
        self.update_calls += 1
        event = {**current, **body, "id": event_id}
        event.pop("etag", None)
        self.events[event_id] = event
        return event


class AcceptedTimeoutCalendar(FakeCalendar):
    def insert(self, **kwargs):
        super().insert(**kwargs)
        raise subprocess.TimeoutExpired("calendar insert", 30)


class ImportedCalendar(FakeCalendar):
    def find_conflict(self, **kwargs):
        return {"id": "imported", "summary": kwargs["body"]["summary"]}


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


def write_calendars(path, extra=()):
    calendars = [
        {"name": name, "id": cid, "profile": profile, "write_owner": ["cohesion"], "schedule": True}
        for name, cid, profile in CALENDARS
    ]
    path.write_text(json.dumps({"calendars": calendars + list(extra)}), encoding="utf-8")


def service(tmp_path, calendar=None):
    tasks_path = tmp_path / "tasks.md"
    tasks_path.write_text("# Tasks\n\n## Active\n\n## Blocked\n\n## Done\n", encoding="utf-8")
    calendars_path = tmp_path / "calendars.json"
    if not calendars_path.exists():
        write_calendars(calendars_path)
    return cohesion.CohesionService(
        db_path=tmp_path / "cohesion.sqlite3",
        tasks_path=tasks_path,
        calendar=calendar or FakeCalendar(),
        calendars_path=calendars_path,
    )


def test_capabilities_are_versioned_and_do_not_offer_shell_or_file_access(tmp_path):
    app = service(tmp_path)
    capabilities = app.capabilities()

    assert capabilities == {
        "version": 1,
        "operations": ["upsert", "complete"],
        "destinations": ["tasks", "calendar"],
        "placements": ["tasks", "calendar", "both"],
        "preference_kinds": ["viewer_delivery", "placement", "linked_completion"],
    }
    assert "shell" not in str(capabilities).lower()
    assert "file" not in str(capabilities).lower()
    assert app.db_path.stat().st_mode & 0o777 == 0o600


def test_learned_category_placement_applies_but_current_instruction_wins(tmp_path):
    app = service(tmp_path)
    preference_request = {
        "version": 1,
        "source": {
            **request("preference-1", "quick_task", "unused")["source"],
            "kind": "fixture_user",
        },
        "preference": {
            "kind": "placement",
            "scope": "category",
            "scope_value": "quick_task",
            "value": "calendar",
            "evidence": "Put quick tasks on my Personal calendar",
            "evidence_validated": True,
            "explicit": True,
            "exceptions": [],
        },
    }
    assert app.record_preference(preference_request)["activated"] is True

    learned = app.submit(
        request(
            "quick-calendar",
            "quick_task",
            "Buy toothpaste",
            start="2026-09-12T19:00:00",
            end="2026-09-12T19:15:00",
            calendar="Personal",
        )
    )
    explicit = app.submit(
        request(
            "quick-explicit",
            "quick_task",
            "Buy floss",
            area="personal",
            placement="tasks",
        )
    )

    assert learned["placement"] == "calendar"
    assert explicit["placement"] == "tasks"
    assert app.context("quick_task")["semantic_preferences"]["active"]["placement"][
        "value"
    ] == "calendar"


def test_item_placement_suppression_prevents_calendar_recreation(tmp_path):
    app = service(tmp_path)
    item_id = "school-one"
    app.record_preference(
        {
            "version": 1,
            "source": {
                **request("correction-1", "quick_task", "unused")["source"],
                "kind": "fixture_user",
            },
            "preference": {
                "kind": "placement",
                "scope": "item",
                "scope_value": item_id,
                "value": "tasks",
                "evidence": "Keep this one out of Calendar",
                "evidence_validated": True,
                "explicit": True,
                "exceptions": [],
            },
        }
    )

    receipt = app.submit(
        request(
            "school-suppressed",
            "school_deadline",
            "Submit paper",
            item_id=item_id,
            area="school",
            due="tomorrow",
            calendar="Course",
        )
    )

    assert receipt["placement"] == "tasks"
    assert [item["destination"] for item in receipt["applied"]] == ["tasks"]


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
            calendar="Personal ID",
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
            calendar="Thesis",
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
        calendar="Course",
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
        calendar="Course",
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
            calendar="Course",
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
            calendar="Personal",
        )
    )

    assert len(receipt["applied"]) == 1
    assert receipt["pending"] == []
    assert calendar.insert_calls == 1
    assert len(calendar.events) == 1


def test_matching_imported_calendar_event_is_not_duplicated_or_mutated(tmp_path):
    calendar = ImportedCalendar()
    app = service(tmp_path, calendar)

    receipt = app.submit(
        request(
            "imported-deadline",
            "school_deadline",
            "Submit paper",
            area="school",
            due="tomorrow",
            calendar="Course",
        )
    )

    assert [item["destination"] for item in receipt["applied"]] == ["tasks"]
    assert receipt["pending"][0]["destination"] == "calendar"
    assert receipt["pending"][0]["error"] == "matching calendar event is imported or unowned"
    assert calendar.insert_calls == 0 and calendar.update_calls == 0


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
            calendar="Personal",
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
            calendar="Personal",
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
            calendar="Calendar A",
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
            calendar="Calendar A",
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
            calendar="Calendar B",
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
            calendar="Personal",
        )
    )
    item_id = first["item_id"]
    event_id = first["applied"][0]["result"]["event_id"]
    calendar.events[event_id].update(summary="Dinner with Mia", etag="human-edit")
    later = request(
        "event-after-human",
        "social_plan",
        "Late dinner",
        item_id=item_id,
        start="2026-09-12T20:00:00",
        end="2026-09-12T21:00:00",
        calendar="Personal",
    )

    changed = app.submit(later)
    redelivered = app.submit(later)

    assert changed["applied"] == []
    assert "changed since the last applied operation" in changed["pending"][0]["error"]
    assert redelivered["pending"][0]["attempts"] == 2
    assert calendar.events[event_id]["summary"] == "Dinner with Mia"

    calendar.events[event_id].update(summary="Dinner", etag="human-restore")
    restored = app.submit(later)

    assert restored["pending"] == []
    assert calendar.events[event_id]["summary"] == "Late dinner"


def test_a_calendar_edit_outside_the_managed_fields_is_adopted_and_kept(tmp_path):
    calendar = FakeCalendar()
    app = service(tmp_path, calendar)
    first = app.submit(
        request(
            "room-before",
            "social_plan",
            "Dinner",
            start="2026-09-12T19:00:00",
            end="2026-09-12T20:00:00",
            calendar="Personal",
        )
    )
    event_id = first["applied"][0]["result"]["event_id"]
    calendar.events[event_id].update(location="Room 301", etag="human-edit")

    moved = app.submit(
        request(
            "room-after",
            "social_plan",
            "Dinner",
            item_id=first["item_id"],
            start="2026-09-12T20:00:00",
            end="2026-09-12T21:00:00",
            calendar="Personal",
        )
    )

    assert moved["pending"] == []
    assert calendar.events[event_id]["location"] == "Room 301"
    assert calendar.events[event_id]["start"]["dateTime"].startswith("2026-09-12T20:00")


@pytest.mark.parametrize("action", ["upsert", "complete"])
def test_a_cancelled_calendar_event_is_reported_missing(tmp_path, action):
    calendar = FakeCalendar()
    app = service(tmp_path, calendar)
    first = app.submit(
        request(
            "deleted-in-calendar",
            "social_plan",
            "Dinner",
            start="2026-09-12T19:00:00",
            end="2026-09-12T20:00:00",
            calendar="Personal",
        )
    )
    event_id = first["applied"][0]["result"]["event_id"]
    calendar.events[event_id].update(status="cancelled", etag="deleted")
    later = request(
        "after-delete",
        "social_plan",
        "Late dinner",
        item_id=first["item_id"],
        start="2026-09-12T20:00:00",
        end="2026-09-12T21:00:00",
        calendar="Personal",
    )
    if action == "complete":
        later["intent"] = {"action": "complete", "item_id": first["item_id"]}

    receipt = app.submit(later)

    assert receipt["applied"] == []
    assert receipt["pending"][0]["error"] == "owned calendar event no longer exists"
    assert calendar.update_calls == 0


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
        calendar="Course",
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
            calendar="Course",
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
    assert "must name a configured calendar" in receipt["pending"][0]["error"]
    assert app.tasks_path.read_text() == before
    assert app.context()["source_count"] == 1
    assert app.context()["pending_count"] == 1


def test_a_first_attempt_refuses_a_concurrent_edit_to_the_task_line(tmp_path):
    app = service(tmp_path)
    first = app.submit(request("concurrent-task", "quick_task", "Do not overwrite", area="personal"))
    lines = app.tasks_path.read_text().splitlines()
    index = next(number for number, line in enumerate(lines) if "Do not overwrite" in line)
    lines[index] = lines[index].replace("Do not overwrite", "Do not overwrite (MINE)")
    app.tasks_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    receipt = app.submit(
        request(
            "concurrent-task-2",
            "quick_task",
            "Overwritten",
            area="personal",
            item_id=first["item_id"],
        )
    )

    assert receipt["applied"] == []
    assert receipt["pending"][0]["attempts"] == 1
    assert "task line changed" in receipt["pending"][0]["error"]
    content = app.tasks_path.read_text()
    assert "Do not overwrite (MINE)" in content
    assert "Overwritten" not in content


def test_an_unrelated_edit_is_adopted_on_create_and_on_update(tmp_path, monkeypatch):
    app = service(tmp_path)
    original_runner = app._run_pending

    def edit_then_run(source_id):
        app.tasks_path.write_text(app.tasks_path.read_text() + "Human note\n", encoding="utf-8")
        original_runner(source_id)

    monkeypatch.setattr(app, "_run_pending", edit_then_run)
    created = app.submit(request("unrelated-edit", "quick_task", "Write it", area="personal"))
    updated = app.submit(
        request(
            "unrelated-edit-2",
            "quick_task",
            "Write it better",
            area="personal",
            item_id=created["item_id"],
        )
    )

    assert [operation["destination"] for operation in created["applied"]] == ["tasks"]
    assert [operation["destination"] for operation in updated["applied"]] == ["tasks"]
    content = app.tasks_path.read_text()
    assert "Write it better" in content
    assert content.count("Human note") == 2
    assert "Write it #" not in content


def test_an_applied_operation_without_a_version_does_not_strand_the_next_update(tmp_path):
    calendar = VersionlessCalendar()
    app = service(tmp_path, calendar)
    first = app.submit(
        request(
            "versionless-1",
            "social_plan",
            "Dinner",
            start="2026-09-12T19:00:00",
            end="2026-09-12T21:00:00",
            calendar="Personal ID",
        )
    )
    item_id = first["item_id"]

    def move(source_id, title, hour):
        return app.submit(
            request(
                source_id,
                "social_plan",
                title,
                item_id=item_id,
                start=f"2026-09-12T{hour}:00:00",
                end="2026-09-12T23:00:00",
                calendar="Personal ID",
            )
        )

    move("versionless-2", "Dinner moved", "20")
    third = move("versionless-3", "Dinner moved again", "21")

    assert [operation["destination"] for operation in third["applied"]] == ["calendar"]
    assert third["pending"] == []
    assert calendar.events[third["applied"][0]["result"]["event_id"]]["summary"] == (
        "Dinner moved again"
    )


def test_a_crash_after_the_task_write_reconciles_on_redelivery(tmp_path, monkeypatch):
    app = service(tmp_path)
    payload = request("crash-1", "quick_task", "Buy milk", area="personal")
    original_finish = app._finish_operation

    def lose_the_applied_record(operation_id, status, result, version, error):
        if status != "applied":
            original_finish(operation_id, status, result, version, error)

    monkeypatch.setattr(app, "_finish_operation", lose_the_applied_record)
    crashed = app.submit(payload)
    monkeypatch.setattr(app, "_finish_operation", original_finish)

    redelivery = app.submit(payload)

    assert crashed["applied"] == []
    assert "Buy milk" in app.tasks_path.read_text()
    assert [operation["destination"] for operation in redelivery["applied"]] == ["tasks"]
    assert redelivery["pending"] == []
    assert app.tasks_path.read_text().count("Buy milk") == 1


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


def test_a_concurrent_edit_to_the_task_line_stays_pending_until_it_is_resolved(tmp_path):
    app = service(tmp_path)
    first = app.submit(request("retry-task", "quick_task", "Survives the edit", area="personal"))
    original_line = next(
        line for line in app.tasks_path.read_text().splitlines() if "Survives the edit" in line
    )
    edited = original_line.replace("Survives the edit", "Survives the edit (MINE)")
    app.tasks_path.write_text(
        app.tasks_path.read_text().replace(original_line, edited), encoding="utf-8"
    )
    update = request(
        "retry-task-2", "quick_task", "Renamed", area="personal", item_id=first["item_id"]
    )

    attempt = app.submit(update)
    redelivery = app.submit(update)
    app.tasks_path.write_text(
        app.tasks_path.read_text().replace(edited, original_line), encoding="utf-8"
    )
    resolved = app.submit(update)

    assert attempt["applied"] == []
    assert "task line changed" in attempt["pending"][0]["error"]
    assert redelivery["applied"] == []
    assert redelivery["pending"][0]["attempts"] == 2
    assert "task line changed" in redelivery["pending"][0]["error"]
    assert [operation["destination"] for operation in resolved["applied"]] == ["tasks"]
    assert resolved["applied"][0]["attempts"] == 3
    content = app.tasks_path.read_text()
    assert "Renamed" in content
    assert "Survives the edit" not in content


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
        calendar="Personal ID",
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
            calendar="Personal ID",
        )
    )
    item_id = first["item_id"]
    event_id = first["applied"][0]["result"]["event_id"]

    for source_id in ("dinner-done-1", "dinner-done-2"):
        completion = request(source_id, "social_plan", "ignored")
        completion["intent"] = {"action": "complete", "item_id": item_id}
        assert app.submit(completion)["pending"] == []

    assert calendar.events[event_id]["description"] == "achiOS item state: completed"
    assert calendar.update_calls == 1


def test_a_later_completion_keeps_the_original_done_date(tmp_path):
    calendar = FakeCalendar()
    app = service(tmp_path, calendar)
    first = app.submit(
        request(
            "paper",
            "school_deadline",
            "Final paper",
            area="school",
            due="2026-09-15",
            calendar="Course",
        )
    )
    item_id = first["item_id"]
    for source_id, timestamp in (
        ("paper-done", SOURCE_TIME),
        ("paper-done-again", "2026-09-20T10:00:00+08:00"),
    ):
        completion = request(source_id, "school_deadline", "ignored")
        completion["intent"] = {"action": "complete", "item_id": item_id}
        completion["source"]["timestamp"] = timestamp
        assert app.submit(completion)["pending"] == []
    after_first = app.tasks_path.read_text()

    assert "(done 2026-09-11)" in after_first
    assert "(done 2026-09-20)" not in after_first
    assert calendar.update_calls == 1


def test_an_unparseable_date_is_pending_and_its_correction_applies(tmp_path):
    app = service(tmp_path)
    bad = request("bad-date", "quick_task", "Pay rent", area="personal", due="next friday")

    refused = app.submit(bad)
    corrected = request("bad-date", "quick_task", "Pay rent", area="personal", due="2026-09-18")
    accepted = app.submit(corrected)

    assert refused["applied"] == []
    assert "due" in refused["pending"][0]["error"]
    assert accepted["pending"] == []
    assert "Pay rent #personal !med @2026-09-18" in app.tasks_path.read_text()
    assert app.context()["pending_count"] == 0


def test_a_clarification_for_a_known_item_names_the_item(tmp_path):
    app = service(tmp_path)
    first = app.submit(request("known", "quick_task", "Pay rent", area="personal"))
    completion = request("known-done", "quick_task", "ignored")
    completion["intent"] = {"action": "complete", "item_id": first["item_id"]}
    app.submit(completion)

    reopened = app.submit(
        request("known-reopen", "quick_task", "Pay rent", item_id=first["item_id"], area="personal")
    )

    assert reopened["item_id"] == first["item_id"]
    assert "reopening" in reopened["pending"][0]["error"]


def test_a_calendar_only_event_carries_no_task_identity(tmp_path):
    calendar = FakeCalendar()
    app = service(tmp_path, calendar)

    receipt = app.submit(
        request(
            "calendar-only",
            "social_plan",
            "Dinner",
            start="2026-09-12T19:00:00",
            end="2026-09-12T20:00:00",
            calendar="Personal",
        )
    )

    private = calendar.events[receipt["applied"][0]["result"]["event_id"]]["extendedProperties"][
        "private"
    ]
    assert "achios_task_id" not in private
    assert private["achios_item_id"] == receipt["item_id"]


def test_all_day_deadlines_send_the_reminders_google_stores(tmp_path):
    calendar = FakeCalendar()
    app = service(tmp_path, calendar)

    receipt = app.submit(
        request(
            "reminder-1",
            "school_deadline",
            "Final paper",
            area="school",
            due="2026-09-15",
            calendar="Course",
        )
    )

    event_id = next(
        operation for operation in receipt["applied"] if operation["destination"] == "calendar"
    )["result"]["event_id"]
    assert calendar.events[event_id]["reminders"] == {"useDefault": False, "overrides": []}


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
            calendar="Personal ID",
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
            calendar="Personal ID",
        )
    )

    assert app.context()["pending_count"] == 0


def test_gws_transport_sends_the_event_id_and_reads_a_missing_event(monkeypatch):
    calls = []

    def fake_gws(profile, *args):
        calls.append((profile, args))
        if args[2] == "get":
            raise cohesion.gcal.GwsError("error[api]: Not Found", profile=profile, status=404)
        return {"id": "abc", "etag": "v1"}

    monkeypatch.setattr(cohesion.gcal, "gws", fake_gws)
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
        raise cohesion.gcal.GwsError("error[api]: 404 in a message", profile=profile, status=403)

    monkeypatch.setattr(cohesion.gcal, "gws", fake_gws)

    with pytest.raises(cohesion.gcal.GwsError):
        cohesion.GwsCalendarTransport().get(
            profile="dlsu", calendar_id="course", event_id="abc"
        )


def dinner(source_id, calendar="Personal", **intent):
    return request(
        source_id,
        "social_plan",
        "Dinner",
        start="2026-09-12T19:00:00",
        end="2026-09-12T20:00:00",
        calendar=calendar,
        **intent,
    )


class RecordingCalendar(FakeCalendar):
    def __init__(self):
        super().__init__()
        self.targets = []

    def insert(self, *, profile, calendar_id, event_id, body):
        self.targets.append((profile, calendar_id))
        return super().insert(profile=profile, calendar_id=calendar_id, event_id=event_id, body=body)


def test_created_events_carry_the_cohesion_owner_key(tmp_path):
    calendar = FakeCalendar()
    receipt = service(tmp_path, calendar).submit(dinner("owner-key"))

    event = calendar.events[receipt["applied"][0]["result"]["event_id"]]
    assert event["extendedProperties"]["private"]["achios_owner"] == "cohesion"


def test_calendar_names_resolve_to_profile_and_id_through_config(tmp_path):
    calendar = RecordingCalendar()
    receipt = service(tmp_path, calendar).submit(dinner("resolve", calendar="Course"))

    assert calendar.targets == [("dlsu", "course")]
    assert receipt["applied"][0]["result"]["calendar_id"] == "course"


def test_unknown_calendar_name_stays_pending_without_a_write(tmp_path):
    calendar = FakeCalendar()
    receipt = service(tmp_path, calendar).submit(dinner("unknown", calendar="Nope"))

    assert receipt["applied"] == []
    assert "no configured calendar named 'Nope'" in receipt["pending"][0]["error"]
    assert calendar.insert_calls == 0


def test_raw_calendar_ids_are_no_longer_accepted(tmp_path):
    calendar = FakeCalendar()
    receipt = service(tmp_path, calendar).submit(
        dinner("raw-id", calendar={"profile": "personal", "id": "personal"})
    )

    assert "must name a configured calendar" in receipt["pending"][0]["error"]
    assert calendar.insert_calls == 0


def test_a_calendar_cohesion_does_not_write_is_refused_without_a_write(tmp_path):
    write_calendars(
        tmp_path / "calendars.json",
        [{"name": "workouts", "id": "workouts", "profile": "personal", "write_owner": ["asta"]}],
    )
    calendar = FakeCalendar()
    receipt = service(tmp_path, calendar).submit(dinner("not-ours", calendar="workouts"))

    assert "is not written by cohesion" in receipt["pending"][0]["error"]
    assert calendar.insert_calls == 0


def test_missing_calendar_config_stays_pending_without_a_write(tmp_path):
    calendar = FakeCalendar()
    app = service(tmp_path, calendar)
    (tmp_path / "calendars.json").unlink()

    receipt = app.submit(dinner("no-config"))

    assert "calendar config not found" in receipt["pending"][0]["error"]
    assert calendar.insert_calls == 0


def test_legacy_event_without_owner_key_is_recognized_and_tagged(tmp_path):
    calendar = FakeCalendar()
    app = service(tmp_path, calendar)
    first = app.submit(dinner("legacy-1"))
    event_id = first["applied"][0]["result"]["event_id"]
    del calendar.events[event_id]["extendedProperties"]["private"]["achios_owner"]
    with app._connect() as connection:
        connection.execute(
            "UPDATE operations SET destination_version = ? WHERE item_id = ?",
            (cohesion._calendar_version(calendar.events[event_id]), first["item_id"]),
        )

    moved = app.submit(
        request(
            "legacy-2",
            "social_plan",
            "Dinner moved",
            item_id=first["item_id"],
            start="2026-09-12T20:00:00",
            end="2026-09-12T21:00:00",
            calendar="Personal",
        )
    )

    assert moved["pending"] == []
    assert calendar.update_calls == 1
    private = calendar.events[event_id]["extendedProperties"]["private"]
    assert private["achios_owner"] == "cohesion"
    assert calendar.events[event_id]["summary"] == "Dinner moved"


def test_event_owned_by_another_agent_is_refused(tmp_path):
    calendar = FakeCalendar()
    app = service(tmp_path, calendar)
    first = app.submit(dinner("foreign-1"))
    event_id = first["applied"][0]["result"]["event_id"]
    calendar.events[event_id]["extendedProperties"]["private"]["achios_owner"] = "asa"

    moved = app.submit(
        request(
            "foreign-2",
            "social_plan",
            "Dinner moved",
            item_id=first["item_id"],
            start="2026-09-12T20:00:00",
            end="2026-09-12T21:00:00",
            calendar="Personal",
        )
    )

    assert moved["pending"][0]["error"] == "calendar event ownership is unknown"
    assert calendar.update_calls == 0


def test_completion_resolves_the_stored_calendar_back_through_config(tmp_path):
    calendar = FakeCalendar()
    app = service(tmp_path, calendar)
    first = app.submit(dinner("complete-1"))
    complete = request("complete-2", "social_plan", "ignored")
    complete["intent"] = {"action": "complete", "item_id": first["item_id"]}

    receipt = app.submit(complete)

    assert receipt["pending"] == []
    event = calendar.events[first["applied"][0]["result"]["event_id"]]
    assert event["extendedProperties"]["private"]["achios_item_state"] == "completed"


def test_no_file_imports_gcal_add():
    from pathlib import Path

    root = Path(__file__).resolve().parents[1]
    for path in [*root.glob("scripts/*.py"), *root.glob("tests/*.py")]:
        if path.name != "test_cohesion.py":
            assert "gcal_add" not in path.read_text(encoding="utf-8"), path
