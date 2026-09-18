from __future__ import annotations

import datetime as dt
import json
import subprocess
from pathlib import Path

import pytest

import gcal

ROOT = Path(__file__).resolve().parents[1]


def entry(name, cid=None, profile="personal", owners=(), schedule=True, purpose=""):
    return {
        "name": name,
        "id": cid or f"{name.lower()}@group",
        "profile": profile,
        "purpose": purpose,
        "write_owner": list(owners),
        "schedule": schedule,
    }


def timed(eid, title, start, end=None, **extra):
    return {"id": eid, "summary": title, "start": {"dateTime": start},
            "end": {"dateTime": end or start}, **extra}


def all_day(eid, title, day, **extra):
    return {"id": eid, "summary": title, "start": {"date": day}, "end": {"date": day}, **extra}


class FakeGws:
    """In-memory stand-in for the gws binary, keyed by profile and calendar ID."""

    def __init__(self):
        self.calendars: dict[str, list[dict]] = {}
        self.events: dict[tuple[str, str], dict[str, dict]] = {}
        self.failing: dict[str, Exception] = {}
        self.calls: list[tuple] = []

    def add_calendar(self, profile, cid, name, role="owner"):
        self.calendars.setdefault(profile, []).append({"id": cid, "summary": name, "accessRole": role})

    def add_event(self, profile, cid, event):
        self.events.setdefault((profile, cid), {})[event["id"]] = event

    def writes(self):
        return [call for call in self.calls if call[1:3] == ("events", "insert")
                or call[1:3] == ("events", "patch") or call[1:3] == ("events", "delete")]

    def __call__(self, profile, *args, timeout=30):
        self.calls.append((profile, *args[1:3]))
        if profile in self.failing:
            raise self.failing[profile]
        params = json.loads(args[args.index("--params") + 1]) if "--params" in args else {}
        body = json.loads(args[args.index("--json") + 1]) if "--json" in args else {}
        kind = args[1:3]
        if kind == ("calendarList", "list"):
            return {"items": self.calendars.get(profile, [])}
        if kind == ("calendarList", "get"):
            for cal in self.calendars.get(profile, []):
                if cal["id"] == params["calendarId"]:
                    return cal
            raise gcal.GwsError("Not Found", profile=profile, status=404)
        events = self.events.setdefault((profile, params.get("calendarId")), {})
        if kind == ("events", "list"):
            assert params["singleEvents"] is True
            return {"items": list(events.values())}
        if kind == ("events", "get"):
            if params["eventId"] not in events:
                raise gcal.GwsError("Not Found", profile=profile, status=404)
            return events[params["eventId"]]
        if kind == ("events", "insert"):
            if body["id"] in events:
                raise gcal.GwsError("duplicate", profile=profile, status=409)
            events[body["id"]] = body
            return body
        if kind == ("events", "update"):
            assert all(value is not None for value in body["start"].values())
            events[params["eventId"]] = body
            return body
        if kind == ("events", "patch"):
            events[params["eventId"]].update(body)
            return events[params["eventId"]]
        if kind == ("events", "delete"):
            events.pop(params["eventId"])
            return {}
        raise AssertionError(args)


@pytest.fixture
def fake(monkeypatch):
    fake = FakeGws()
    monkeypatch.setattr(gcal, "gws", fake)
    return fake


# Config


def test_load_config_names_a_missing_file(tmp_path):
    with pytest.raises(gcal.GcalError) as raised:
        gcal.load_config(tmp_path / "calendars.json")
    assert raised.value.code == "config_missing"
    assert "calendars.json" in str(raised.value)


def test_load_config_rejects_an_unknown_owner(tmp_path):
    path = tmp_path / "calendars.json"
    path.write_text(json.dumps({"calendars": [entry("Personal", owners=["bob"])]}))
    with pytest.raises(gcal.GcalError, match="write_owner"):
        gcal.load_config(path)


def test_example_config_loads_and_holds_no_real_ids_or_emails():
    path = ROOT / "config" / "calendars.example.json"
    config = gcal.load_config(path)
    assert {"Personal", "workouts", "DLSU", "Canvas"} <= {item["name"] for item in config}
    text = path.read_text()
    assert "@gmail.com" not in text and "@dlsu.edu.ph" not in text
    for item in config:
        if item["name"] != "Holidays in Philippines":
            assert "_ID" in item["id"]


def test_find_calendar_refuses_an_unknown_name():
    with pytest.raises(gcal.GcalError) as raised:
        gcal.find_calendar([entry("Personal")], "Nope")
    assert raised.value.code == "unknown_calendar"


# gws transport


class FakeBin:
    def __init__(self, present):
        self.present = present

    def is_file(self):
        return self.present

    def __str__(self):
        return "/fake/gws"


def test_parse_json_skips_the_keyring_banner():
    assert gcal.parse_json('Using keyring backend: file\n{"items": []}') == {"items": []}


def test_parse_json_raises_without_a_body():
    with pytest.raises(gcal.GwsError):
        gcal.parse_json("Using keyring backend: file\n")


def test_gws_reports_a_missing_binary(monkeypatch):
    monkeypatch.setattr(gcal, "GWS_BIN", FakeBin(False))
    with pytest.raises(gcal.GcalError) as raised:
        gcal.gws("personal", "calendar", "calendarList", "list")
    assert raised.value.code == "gws_missing"


def _completed(returncode, stdout, stderr):
    return lambda *a, **k: subprocess.CompletedProcess(a, returncode, stdout=stdout, stderr=stderr)


def test_gws_error_skips_the_banner_and_keeps_the_api_status(monkeypatch):
    monkeypatch.setattr(gcal, "GWS_BIN", FakeBin(True))
    monkeypatch.setattr(gcal.subprocess, "run", _completed(
        1, '{"error": {"code": 404, "message": "Not Found", "reason": "notFound"}}',
        "Using keyring backend: file\nerror[api]: Not Found\n"))
    with pytest.raises(gcal.GwsError) as raised:
        gcal.gws("personal", "calendar", "events", "get")
    assert raised.value.status == 404
    assert raised.value.code == "gws_failed"
    assert str(raised.value) == "error[api]: Not Found"
    assert raised.value.profile == "personal"


def test_gws_classifies_an_auth_failure(monkeypatch):
    monkeypatch.setattr(gcal, "GWS_BIN", FakeBin(True))
    monkeypatch.setattr(gcal.subprocess, "run", _completed(
        2, '{"error": {"code": 401, "message": "Access denied.", "reason": "authError"}}',
        "error[auth]: Access denied.\n"))
    with pytest.raises(gcal.GwsError) as raised:
        gcal.gws("work", "calendar", "calendarList", "list")
    assert raised.value.code == "auth_failed"


def test_gws_error_without_a_body_has_no_status(monkeypatch):
    monkeypatch.setattr(gcal, "GWS_BIN", FakeBin(True))
    monkeypatch.setattr(gcal.subprocess, "run", _completed(3, "", "Using keyring backend: file\n"))
    with pytest.raises(gcal.GwsError) as raised:
        gcal.gws("personal", "calendar", "events", "get")
    assert raised.value.status is None
    assert str(raised.value) == "exit 3"


# Bodies and times


def test_all_day_body_uses_an_exclusive_end_date_and_no_reminders():
    body = gcal.all_day_body("Standup", dt.date(2026, 9, 2))
    assert body["start"] == {"date": "2026-09-02"}
    assert body["end"] == {"date": "2026-09-03"}
    assert body["reminders"] == {"useDefault": False, "overrides": []}
    assert "dateTime" not in json.dumps(body)


def test_timed_body_treats_naive_times_as_manila():
    body = gcal.timed_body("Lift", "2026-09-18T07:00", "2026-09-18T08:00")
    assert body["start"] == {"dateTime": "2026-09-18T07:00:00+08:00", "timeZone": "Asia/Manila"}
    assert "date" not in body["start"]


def test_timed_body_converts_utc_input_to_manila():
    assert gcal.timed_body("Call", "2026-09-17T23:30Z", "2026-09-18T00:30Z")["start"]["dateTime"] == (
        "2026-09-18T07:30:00+08:00"
    )


def test_timed_body_refuses_an_end_before_the_start():
    with pytest.raises(gcal.GcalError):
        gcal.timed_body("Call", "2026-09-18T09:00", "2026-09-18T08:00")


def test_window_covers_whole_manila_days():
    assert gcal.window(dt.date(2026, 9, 17), dt.date(2026, 9, 17)) == (
        "2026-09-17T00:00:00+08:00",
        "2026-09-18T00:00:00+08:00",
    )


def test_event_id_is_stable_and_valid_for_google():
    event_id = gcal.event_id_for("item_1")
    assert event_id == gcal.event_id_for("item_1")
    assert set(event_id) <= set("0123456789abcdefghijklmnopqrstuv")


# Agenda


def schedule_config():
    return [
        entry("THS-ST2", cid="course@group", profile="personal", purpose="course"),
        entry("THS-ST2 (work)", cid="course@group", profile="work", purpose="course"),
        entry("Personal", cid="personal@group", profile="personal", owners=["asa"]),
        entry("ING", cid="ing@group", profile="work"),
        entry("GCash", cid="gcash@group", profile="work", schedule=False),
    ]


def test_agenda_reads_a_calendar_shared_into_two_profiles_once(fake):
    fake.add_event("personal", "course@group", timed("e1", "Lecture", "2026-09-17T01:00:00Z"))
    fake.add_event("work", "course@group", timed("e1", "Lecture", "2026-09-17T01:00:00Z"))
    result = gcal.agenda(schedule_config(), dt.date(2026, 9, 17), dt.date(2026, 9, 17))
    assert [event["title"] for event in result["events"]] == ["Lecture"]
    assert result["events"][0]["start"] == "2026-09-17T09:00:00+08:00"
    listed = [call for call in fake.calls if call[1:] == ("events", "list")]
    assert len(listed) == 3
    assert result["status"] == "ok"


def test_agenda_skips_calendars_outside_the_schedule_set(fake):
    fake.add_event("work", "gcash@group", timed("g1", "Standup", "2026-09-17T09:00:00+08:00"))
    result = gcal.agenda(schedule_config(), dt.date(2026, 9, 17), dt.date(2026, 9, 17))
    assert result["events"] == []


def test_agenda_dedupes_by_event_id_across_calendars(fake):
    fake.add_event("personal", "personal@group", timed("same", "Dinner", "2026-09-17T19:00:00+08:00"))
    fake.add_event("work", "ing@group", timed("same", "Dinner copy", "2026-09-17T20:00:00+08:00"))
    result = gcal.agenda(schedule_config(), dt.date(2026, 9, 17), dt.date(2026, 9, 17))
    assert [event["title"] for event in result["events"]] == ["Dinner"]


def test_agenda_dedupes_by_title_and_start_when_ids_differ(fake):
    fake.add_event("personal", "personal@group", timed("p1", "Team sync", "2026-09-17T10:00:00+08:00"))
    fake.add_event("work", "ing@group", timed("w1", "team sync ", "2026-09-17T02:00:00Z"))
    fake.add_event("work", "ing@group", timed("w2", "Team sync", "2026-09-17T11:00:00+08:00"))
    result = gcal.agenda(schedule_config(), dt.date(2026, 9, 17), dt.date(2026, 9, 17))
    assert [event["event_id"] for event in result["events"]] == ["p1", "w2"]


def test_agenda_keeps_every_recurring_instance(fake):
    for day in (17, 18, 19):
        fake.add_event("personal", "personal@group", timed(
            f"gym_202609{day}", "Gym", f"2026-09-{day}T07:00:00+08:00", recurringEventId="gym"))
    result = gcal.agenda(schedule_config(), dt.date(2026, 9, 17), dt.date(2026, 9, 19))
    assert [event["start"][:10] for event in result["events"]] == ["2026-09-17", "2026-09-18", "2026-09-19"]
    assert {event["recurring_event_id"] for event in result["events"]} == {"gym"}


def test_agenda_marks_all_day_events_and_orders_them_first_in_a_day(fake):
    fake.add_event("personal", "personal@group", timed("t1", "Class", "2026-09-17T08:00:00+08:00"))
    fake.add_event("personal", "personal@group", all_day("a1", "Deadline", "2026-09-17"))
    result = gcal.agenda(schedule_config(), dt.date(2026, 9, 17), dt.date(2026, 9, 17))
    assert [(event["title"], event["all_day"]) for event in result["events"]] == [
        ("Deadline", True), ("Class", False)]


def test_agenda_query_uses_manila_day_boundaries(monkeypatch):
    seen = []

    def spy(profile, *args, timeout=30):
        seen.append(json.loads(args[args.index("--params") + 1]))
        return {"items": []}

    monkeypatch.setattr(gcal, "gws", spy)
    gcal.agenda([entry("Personal")], dt.date(2026, 9, 17), dt.date(2026, 9, 18))
    assert seen[0]["timeMin"] == "2026-09-17T00:00:00+08:00"
    assert seen[0]["timeMax"] == "2026-09-19T00:00:00+08:00"
    assert seen[0]["singleEvents"] is True


def test_agenda_skips_cancelled_instances(fake):
    fake.add_event("personal", "personal@group", timed("c1", "Gone", "2026-09-17T08:00:00+08:00", status="cancelled"))
    assert gcal.agenda(schedule_config(), dt.date(2026, 9, 17), dt.date(2026, 9, 17))["events"] == []


def test_one_failing_profile_does_not_hide_the_others(fake):
    fake.failing["work"] = gcal.GwsError("error[auth]: invalid_grant", profile="work", status=401)
    fake.add_event("personal", "personal@group", timed("p1", "Visible", "2026-09-17T08:00:00+08:00"))
    result = gcal.agenda(schedule_config(), dt.date(2026, 9, 17), dt.date(2026, 9, 17))
    assert [event["title"] for event in result["events"]] == ["Visible"]
    assert result["status"] == "partial"
    assert result["errors"] == [
        {"profile": "work", "calendar": "ING", "error": "auth_failed", "message": "error[auth]: invalid_grant"}
    ]


def test_a_calendar_falls_back_to_its_second_profile(fake):
    fake.failing["personal"] = gcal.GwsError("error[auth]: expired", profile="personal", status=401)
    fake.add_event("work", "course@group", timed("e1", "Lecture", "2026-09-17T09:00:00+08:00"))
    result = gcal.agenda(schedule_config(), dt.date(2026, 9, 17), dt.date(2026, 9, 17))
    assert [event["title"] for event in result["events"]] == ["Lecture"]


def test_every_profile_failing_is_an_error(fake):
    fake.failing["personal"] = subprocess.TimeoutExpired("gws", 30)
    fake.failing["work"] = gcal.GwsError("error[auth]: expired", profile="work", status=401)
    result = gcal.agenda(schedule_config(), dt.date(2026, 9, 17), dt.date(2026, 9, 17))
    assert result["status"] == "error"
    assert {error["profile"] for error in result["errors"]} == {"personal", "work"}


# Insert


def write_config():
    return [
        entry("Personal", cid="personal@group", owners=["asa", "cohesion"]),
        entry("workouts", cid="workouts@group", owners=["asta"]),
        entry("Canvas", cid="canvas@import", profile="dlsu"),
        entry("Shared", cid="shared@group", owners=["asa"]),
    ]


@pytest.fixture
def writable(fake):
    fake.add_calendar("personal", "personal@group", "Personal")
    fake.add_calendar("personal", "workouts@group", "workouts")
    fake.add_calendar("dlsu", "canvas@import", "Canvas", role="reader")
    fake.add_calendar("personal", "shared@group", "Shared", role="reader")
    return fake


def test_insert_tags_owner_and_item_id(writable):
    result = gcal.insert(write_config(), calendar="workouts", owner="asta", title="Upper A",
                         start="2026-09-18T07:00", end="2026-09-18T08:00", item_id="session_1")
    assert result["status"] == "ok"
    stored = writable.events[("personal", "workouts@group")][gcal.event_id_for("session_1")]
    assert stored["extendedProperties"]["private"] == {"achios_owner": "asta", "achios_item_id": "session_1"}
    assert stored["start"]["dateTime"] == "2026-09-18T07:00:00+08:00"


def test_insert_is_idempotent_for_the_same_item_id(writable):
    for _ in range(2):
        result = gcal.insert(write_config(), calendar="Personal", owner="asa", title="Pay rent",
                             date="2026-09-30", item_id="rent")
    assert result["status"] == "exists"
    assert len([c for c in writable.writes() if c[1:] == ("events", "insert")]) == 1
    assert len(writable.events[("personal", "personal@group")]) == 1


def test_insert_without_item_id_is_idempotent_on_the_same_title_and_time(writable):
    for _ in range(2):
        gcal.insert(write_config(), calendar="Personal", owner="asa", title="Pay rent", date="2026-09-30")
    assert len(writable.events[("personal", "personal@group")]) == 1


def test_insert_recovers_an_accepted_insert_that_timed_out(writable, monkeypatch):
    def accepted_then_timeout(profile, calendar_id, body):
        writable.add_event(profile, calendar_id, body)
        raise subprocess.TimeoutExpired("gws", 30)

    monkeypatch.setattr(gcal, "insert_event", accepted_then_timeout)
    result = gcal.insert(write_config(), calendar="Personal", owner="asa", title="Call", date="2026-09-30")
    assert result["status"] == "ok"


def test_insert_refuses_a_calendar_it_does_not_own(writable):
    result = gcal.insert(write_config(), calendar="workouts", owner="asa", title="x", date="2026-09-30")
    assert result["reason"] == "calendar_owner"
    assert writable.writes() == []


def test_insert_refuses_a_calendar_that_is_read_only_in_config(writable):
    result = gcal.insert(write_config(), calendar="Canvas", owner="asa", title="x", date="2026-09-30")
    assert result["reason"] == "read_only"
    assert writable.writes() == []


def test_insert_refuses_a_calendar_that_is_read_only_live(writable):
    result = gcal.insert(write_config(), calendar="Shared", owner="asa", title="x", date="2026-09-30")
    assert result["reason"] == "read_only"
    assert writable.writes() == []


# Update and delete guards


def seed(fake, event_id, owner=None, calendar="personal@group"):
    private = {"achios_owner": owner, "achios_item_id": "item"} if owner else {}
    event = all_day(event_id, "Seeded", "2026-09-30")
    if private:
        event["extendedProperties"] = {"private": private}
    fake.add_event("personal", calendar, event)


@pytest.mark.parametrize("action", ["update", "delete"])
def test_writes_refuse_an_untagged_event(writable, action):
    seed(writable, "human")
    result = _write(action, calendar="Personal", event_id="human", owner="asa")
    assert result["reason"] == "untagged"
    assert writable.writes() == []


@pytest.mark.parametrize("action", ["update", "delete"])
def test_writes_refuse_another_owners_event(writable, action):
    seed(writable, "theirs", owner="cohesion")
    result = _write(action, calendar="Personal", event_id="theirs", owner="asa")
    assert result["reason"] == "event_owner"
    assert writable.writes() == []


@pytest.mark.parametrize("action", ["update", "delete"])
def test_writes_refuse_a_calendar_owned_by_another_agent(writable, action):
    seed(writable, "mine", owner="asa", calendar="workouts@group")
    result = _write(action, calendar="workouts", event_id="mine", owner="asa")
    assert result["reason"] == "calendar_owner"
    assert writable.writes() == []


@pytest.mark.parametrize("action", ["update", "delete"])
def test_writes_refuse_a_read_only_calendar(writable, action):
    result = _write(action, calendar="Canvas", event_id="anything", owner="asa")
    assert result["reason"] == "read_only"
    result = _write(action, calendar="Shared", event_id="anything", owner="asa")
    assert result["reason"] == "read_only"
    assert writable.writes() == []


def _write(action, **kwargs):
    if action == "update":
        return gcal.update(write_config(), title="Changed", **kwargs)
    return gcal.delete(write_config(), **kwargs)


def test_update_moves_an_owned_event_to_a_new_day(writable):
    seed(writable, "mine", owner="asa")
    result = gcal.update(write_config(), calendar="Personal", event_id="mine", owner="asa", date="2026-10-01")
    assert result["status"] == "ok"
    assert result["event"]["start"] == "2026-10-01"


def test_delete_removes_an_owned_event(writable):
    seed(writable, "mine", owner="asa")
    assert gcal.delete(write_config(), calendar="Personal", event_id="mine", owner="asa")["status"] == "ok"
    assert "mine" not in writable.events[("personal", "personal@group")]


def test_update_of_a_missing_event_is_an_error(writable):
    result = gcal.update(write_config(), calendar="Personal", event_id="nope", owner="asa", title="x")
    assert result["error"] == "not_found"


def test_update_refuses_when_the_event_changed_since_it_was_read(writable):
    seed(writable, "mine", owner="asa")
    writable.events[("personal", "personal@group")]["mine"]["etag"] = "etag-1"
    result = gcal.update(write_config(), calendar="Personal", event_id="mine", owner="asa",
                         date="2026-10-01", if_match="etag-0")
    assert result["error"] == "conflict"
    assert writable.writes() == []


def test_update_with_a_matching_if_match_succeeds(writable):
    seed(writable, "mine", owner="asa")
    writable.events[("personal", "personal@group")]["mine"]["etag"] = "etag-1"
    result = gcal.update(write_config(), calendar="Personal", event_id="mine", owner="asa",
                         date="2026-10-01", if_match="etag-1")
    assert result["status"] == "ok"


# Drift check


def live(calendars, errors=()):
    return {"calendars": calendars, "errors": list(errors)}


def cal(name, cid, profile="personal", role="owner"):
    return {"id": cid, "name": name, "access_role": role, "profile": profile}


def test_check_reports_every_drift_kind_without_writing(fake):
    config = [
        entry("Personal", cid="personal@group"),
        entry("Deleted", cid="deleted@group"),
        entry("THS-ST2", cid="ths@group", purpose="course"),
        entry("CSOPESY", cid="csopesy@group", purpose="course"),
    ]
    report = gcal.check_calendars(
        config,
        live([
            cal("Personal", "personal@group"),
            cal("THS-ST2", "ths@group"),
            cal("CSOPESY", "csopesy@group"),
            cal("STDISCM", "stdiscm@group"),
            cal("Holidays", "holidays@group", role="reader"),
        ]),
        ["THS-ST2", "STDISCM"],
    )
    assert report["missing_calendars"] == [{"name": "Deleted", "profile": "personal"}]
    assert report["unconfigured_writable"] == [{"name": "STDISCM", "profiles": ["personal"]}]
    assert report["courses_without_calendar"] == ["STDISCM"]
    assert report["course_calendars_not_current"] == ["CSOPESY"]
    assert report["status"] == "drift"
    assert fake.calls == []


def test_check_matches_course_codes_without_hyphens():
    report = gcal.check_calendars(
        [entry("THS-ST2", cid="ths@group", purpose="course")], live([cal("THS-ST2", "ths@group")]), ["THSST2"]
    )
    assert report["status"] == "ok"
    assert report["drift"] is False


def test_check_does_not_call_calendars_missing_on_a_failed_profile():
    failure = {"profile": "work", "calendar": None, "error": "auth_failed", "message": "expired"}
    report = gcal.check_calendars(
        [entry("ING", cid="ing@group", profile="work")], live([cal("Personal", "p@group")], [failure]), []
    )
    assert report["missing_calendars"] == []
    assert report["status"] == "partial"


def test_check_reports_unreadable_courses():
    report = gcal.check_calendars([], live([]), None)
    assert report["courses_without_calendar"] is None
    assert any(error["error"] == "courses_unavailable" for error in report["errors"])


def test_drift_lines_name_each_problem():
    report = {
        "missing_calendars": [{"name": "Gone", "profile": "work"}],
        "unconfigured_writable": [{"name": "New", "profiles": ["personal"]}],
        "courses_without_calendar": ["STDISCM"],
        "course_calendars_not_current": ["CSOPESY"],
        "errors": [],
    }
    assert gcal.drift_lines(report) == [
        "configured calendar not found: Gone (work)",
        "writable calendar not in config: New (personal)",
        "current course has no calendar: STDISCM",
        "course calendar is not a current course: CSOPESY",
    ]


# CLI


def test_cli_reports_a_missing_config_as_json(tmp_path, capsys):
    assert gcal.main(["--config", str(tmp_path / "none.json"), "agenda", "--from", "2026-09-17", "--to", "2026-09-17"]) == 1
    result = json.loads(capsys.readouterr().out)
    assert result == {"status": "error", "error": "config_missing",
                      "message": f"calendar config not found at {tmp_path / 'none.json'} "
                                 "(set ACHIOS_HOME if this checkout is not under ~/Code/GitHub)"}


def test_cli_reports_a_missing_gws_binary_as_json(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(gcal, "GWS_BIN", FakeBin(False))
    monkeypatch.setattr(gcal, "profile_dir", lambda profile: tmp_path)
    path = tmp_path / "calendars.json"
    path.write_text(json.dumps({"calendars": [entry("Personal", owners=["asa"])]}))
    assert gcal.main(["--config", str(path), "insert", "--calendar", "Personal", "--owner", "asa",
                      "--title", "x", "--date", "2026-09-30"]) == 1
    assert json.loads(capsys.readouterr().out)["error"] == "gws_missing"


def test_cli_reports_an_auth_failure_with_its_profile(tmp_path, fake, capsys):
    fake.failing["personal"] = gcal.GwsError("error[auth]: expired", profile="personal", status=401)
    path = tmp_path / "calendars.json"
    path.write_text(json.dumps({"calendars": [entry("Personal", owners=["asa"])]}))
    assert gcal.main(["--config", str(path), "insert", "--calendar", "Personal", "--owner", "asa",
                      "--title", "x", "--date", "2026-09-30"]) == 1
    result = json.loads(capsys.readouterr().out)
    assert (result["error"], result["profile"]) == ("auth_failed", "personal")


def test_cli_agenda_prints_partial_results(tmp_path, fake, capsys):
    fake.failing["work"] = gcal.GwsError("error[auth]: expired", profile="work", status=401)
    fake.add_event("personal", "personal@group", timed("p1", "Visible", "2026-09-17T08:00:00+08:00"))
    path = tmp_path / "calendars.json"
    path.write_text(json.dumps({"calendars": schedule_config()}))
    assert gcal.main(["--config", str(path), "agenda", "--from", "2026-09-17", "--to", "2026-09-17"]) == 0
    result = json.loads(capsys.readouterr().out)
    assert result["status"] == "partial"
    assert [event["title"] for event in result["events"]] == ["Visible"]


def test_cli_insert_requires_a_date_or_a_start_and_end(tmp_path, fake, capsys):
    path = tmp_path / "calendars.json"
    path.write_text(json.dumps({"calendars": [entry("Personal", owners=["asa"])]}))
    assert gcal.main(["--config", str(path), "insert", "--calendar", "Personal", "--owner", "asa",
                      "--title", "x", "--start", "2026-09-30T09:00"]) == 1
    assert json.loads(capsys.readouterr().out)["error"] == "invalid_arguments"
    assert fake.calls == []


def test_cli_calendars_list_names_a_missing_profile(tmp_path, monkeypatch, fake, capsys):
    monkeypatch.setattr(gcal, "profile_dir", lambda profile: tmp_path / profile)
    (tmp_path / "personal").mkdir()
    fake.add_calendar("personal", "personal@group", "Personal")
    assert gcal.main(["calendars", "list"]) == 0
    result = json.loads(capsys.readouterr().out)
    assert result["status"] == "partial"
    assert result["calendars"] == [
        {"id": "personal@group", "name": "Personal", "access_role": "owner", "profile": "personal"}
    ]
    assert {error["profile"] for error in result["errors"]} == {"work", "main", "dlsu"}


def test_no_legacy_google_token_files_remain_in_the_achios_config_dir():
    config_dir = gcal.CONFIG_PATH.parent
    leftovers = sorted(path.name for path in config_dir.glob("google_token*.json"))
    assert leftovers == [], f"delete unused OAuth token files from {config_dir}: {leftovers}"


# Review fixes


def test_gws_omits_the_format_flag_when_asked(monkeypatch):
    seen = []
    monkeypatch.setattr(gcal, "GWS_BIN", FakeBin(True))

    def run(argv, **kwargs):
        seen.append(argv)
        return subprocess.CompletedProcess(argv, 0, stdout='{"token_valid": true}', stderr="")

    monkeypatch.setattr(gcal.subprocess, "run", run)
    gcal.gws("main", "auth", "status", json_format=False)
    gcal.gws("main", "calendar", "calendarList", "list")
    assert seen[0] == ["/fake/gws", "auth", "status"]
    assert seen[1][-2:] == ["--format", "json"]


def test_an_empty_readable_day_with_one_failed_profile_is_partial(fake):
    fake.failing["work"] = gcal.GwsError("error[auth]: expired", profile="work", status=401)
    result = gcal.agenda(schedule_config(), dt.date(2026, 9, 20), dt.date(2026, 9, 20))
    assert result["events"] == []
    assert result["status"] == "partial"


def test_calendars_list_with_an_empty_readable_profile_is_partial(monkeypatch, tmp_path, fake):
    monkeypatch.setattr(gcal, "profile_dir", lambda profile: tmp_path)
    fake.failing["work"] = gcal.GwsError("error[auth]: expired", profile="work", status=401)
    assert gcal.list_calendars(["personal", "work"])["status"] == "partial"


def test_inserting_a_deleted_item_again_restores_its_event(writable):
    config = write_config()
    first = gcal.insert(config, calendar="Personal", owner="asa", title="Gym", start="2026-09-18T07:00",
                        end="2026-09-18T08:00")
    stored = writable.events[("personal", "personal@group")][first["event"]["event_id"]]
    stored["status"] = "cancelled"

    again = gcal.insert(config, calendar="Personal", owner="asa", title="Gym", start="2026-09-18T07:00",
                        end="2026-09-18T08:00")

    assert again["status"] == "ok" and again["restored"] is True
    assert stored["status"] == "confirmed"
    assert stored["extendedProperties"]["private"]["achios_owner"] == "asa"
    assert len([c for c in writable.writes() if c[1:] == ("events", "insert")]) == 1


def test_a_deleted_event_of_another_owner_is_not_restored(writable):
    config = write_config()
    first = gcal.insert(config, calendar="Personal", owner="cohesion", title="Gym", date="2026-09-18",
                        item_id="shared")
    writable.events[("personal", "personal@group")][first["event"]["event_id"]]["status"] = "cancelled"
    result = gcal.insert(config, calendar="Personal", owner="asa", title="Gym", date="2026-09-18", item_id="shared")
    assert result["reason"] == "event_owner"


def test_moving_an_event_to_all_day_replaces_its_times_and_keeps_the_rest(writable, monkeypatch):
    writable.add_event("personal", "personal@group", {
        **timed("mine", "Gym", "2026-09-18T07:00:00+08:00"),
        "reminders": {"useDefault": True},
        "extendedProperties": {"private": {"achios_owner": "asa", "achios_item_id": "gym"}},
    })
    sent = []
    real_replace = gcal.replace_event
    monkeypatch.setattr(gcal, "replace_event", lambda *a: sent.append(a[3]) or real_replace(*a))

    result = gcal.update(write_config(), calendar="Personal", event_id="mine", owner="asa", date="2026-10-01")

    assert result["event"]["all_day"] is True
    assert sent[0]["start"] == {"date": "2026-10-01"}
    assert sent[0]["end"] == {"date": "2026-10-02"}
    assert sent[0]["reminders"] == {"useDefault": True}
    assert sent[0]["extendedProperties"]["private"]["achios_owner"] == "asa"


def test_moving_an_all_day_event_to_a_timed_slot(writable):
    seed(writable, "mine", owner="asa")
    result = gcal.update(write_config(), calendar="Personal", event_id="mine", owner="asa",
                         start="2026-10-01T09:00", end="2026-10-01T10:00")
    assert result["event"]["start"] == "2026-10-01T09:00:00+08:00"
    assert writable.events[("personal", "personal@group")]["mine"]["start"] == {
        "dateTime": "2026-10-01T09:00:00+08:00", "timeZone": "Asia/Manila"}


def test_gws_error_keeps_every_detail_line(monkeypatch):
    monkeypatch.setattr(gcal, "GWS_BIN", FakeBin(True))
    monkeypatch.setattr(gcal.subprocess, "run", _completed(
        1, "", "Using keyring backend: file\nerror[validation]: Request body failed schema validation:\n  start.dateTime: null\n"))
    with pytest.raises(gcal.GwsError) as raised:
        gcal.gws("personal", "calendar", "events", "patch")
    assert str(raised.value) == "error[validation]: Request body failed schema validation: start.dateTime: null"


def test_user_home_survives_a_scoped_home(monkeypatch, tmp_path):
    monkeypatch.delenv("ACHIOS_HOME", raising=False)
    monkeypatch.setattr(gcal, "SCRIPT_DIR", tmp_path / "Code" / "GitHub" / "AIS-OS" / "scripts")
    monkeypatch.setenv("HOME", str(tmp_path / "codex-home"))
    assert gcal.user_home() == tmp_path


def test_user_home_prefers_an_explicit_achios_home(monkeypatch, tmp_path):
    monkeypatch.setattr(gcal, "SCRIPT_DIR", tmp_path / "Code" / "review" / "AIS-OS" / "scripts")
    monkeypatch.setenv("ACHIOS_HOME", str(tmp_path / "real-home"))
    assert gcal.user_home() == tmp_path / "real-home"


def test_config_missing_names_achios_home(tmp_path):
    with pytest.raises(gcal.GcalError) as raised:
        gcal.load_config(tmp_path / "missing.json")
    assert raised.value.code == "config_missing"
    assert "ACHIOS_HOME" in str(raised.value)
