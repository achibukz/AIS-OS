import datetime as dt
import json
from pathlib import Path
from zoneinfo import ZoneInfo

import pytest

import daily_brief as brief
import gcal

TZ = ZoneInfo("Asia/Manila")
TODAY = dt.date(2026, 8, 16)


def event(
    summary: str,
    day: int = 16,
    hour: int = 9,
    minute: int = 0,
    *,
    all_day: bool = False,
    calendar: str = "Personal",
) -> brief.CalendarEvent:
    return brief.CalendarEvent(
        summary=summary,
        start_dt=dt.datetime(2026, 8, day, hour, minute, tzinfo=TZ),
        is_all_day=all_day,
        calendar_name=calendar,
    )


def task(text: str, *, priority: str = "med", due: dt.date | None = None) -> brief.Task:
    return brief.Task(text=text, state="active", priority=priority, due=due)


class TestParseActiveTasks:
    def test_reads_only_open_tasks_in_the_active_section(self):
        body = """# Tasks

## Active
- [ ] Ship the brief #achios !high @2026-08-20
- [~] Waiting on access #achios

## Done
- [x] Old work #achios
"""
        assert brief.parse_active_tasks(body) == [
            brief.Task(
                text="Ship the brief",
                state="active",
                priority="high",
                due=dt.date(2026, 8, 20),
            )
        ]

    def test_defaults_to_medium_priority_and_no_due_date(self):
        assert brief.parse_active_tasks("## Active\n- [ ] Plain task") == [
            brief.Task(text="Plain task", state="active")
        ]

    def test_ignores_task_examples_inside_fenced_code(self):
        body = """## Active
```
- [ ] Example #area !high @2026-08-20
```
- [ ] Real task
"""
        assert [item.text for item in brief.parse_active_tasks(body)] == ["Real task"]

    def test_strips_tags_and_supported_markdown_markup(self):
        body = "## Active\n- [ ] Fix **`profile.yml`** for [[career-ops-hub]] #career !low"
        assert brief.parse_active_tasks(body) == [
            brief.Task(text="Fix profile.yml for career-ops-hub", state="active", priority="low")
        ]


class TestCleaning:
    def test_clean_summary_removes_canvas_course_prefixes(self):
        assert brief.clean_summary("[MERGED_1253_THS-ST1_S08]  Adviser meeting") == "Adviser meeting"
        assert brief.clean_summary("[THS-ST1_S08] Adviser meeting") == "Adviser meeting"

    def test_clean_summary_decodes_html_and_collapses_spaces(self):
        assert brief.clean_summary("Research &amp;   Writing") == "Research & Writing"


def calendar(name, cid, profile):
    return {"name": name, "id": cid, "profile": profile, "purpose": "", "write_owner": [], "schedule": True}


TWO_PROFILE_CONFIG = [
    calendar("THS-ST2", "course@group", "personal"),
    calendar("THS-ST2 work", "course@group", "work"),
    calendar("Personal", "personal@group", "personal"),
    calendar("ING", "ing@group", "work"),
]


class FakeCalendars:
    """Serves events per profile and calendar through a stand-in for gcal.gws."""

    def __init__(self, events, failing=()):
        self.events = events
        self.failing = set(failing)

    def __call__(self, profile, *args, timeout=30):
        if profile in self.failing:
            raise gcal.GwsError("error[auth]: invalid_grant", profile=profile, status=401)
        params = json.loads(args[args.index("--params") + 1])
        return {"items": self.events.get((profile, params["calendarId"]), [])}


def timed(eid, title, start):
    return {"id": eid, "summary": title, "start": {"dateTime": start}, "end": {"dateTime": start}}


@pytest.fixture
def two_profiles(monkeypatch):
    monkeypatch.setattr(gcal, "load_config", lambda path=None: TWO_PROFILE_CONFIG)
    events = {
        ("personal", "course@group"): [timed("lec", "Lecture", "2026-08-16T09:00:00+08:00")],
        ("work", "course@group"): [timed("lec", "Lecture", "2026-08-16T09:00:00+08:00")],
        ("personal", "personal@group"): [
            timed("p1", "Dinner", "2026-08-17T19:00:00+08:00"),
            timed("p2", "DLSU Laguna closure", "2026-08-17T08:00:00+08:00"),
        ],
        ("work", "ing@group"): [
            timed("w1", "Standup", "2026-08-16T10:00:00+08:00"),
            {"id": "w2", "summary": "Enrollment", "start": {"date": "2026-08-16"}, "end": {"date": "2026-08-17"}},
        ],
    }

    def install(failing=()):
        monkeypatch.setattr(gcal, "gws", FakeCalendars(events, failing))

    install()
    return install


class TestCalendarFetch:
    START = dt.datetime(2026, 8, 16, tzinfo=TZ)

    def test_duplicated_course_calendar_is_listed_once(self, two_profiles):
        events, errors = brief.fetch_calendar_events(self.START, self.START + dt.timedelta(days=7))
        assert [e.summary for e in events] == ["Enrollment", "Lecture", "Standup", "Dinner"]
        assert errors == []
        assert events[0].is_all_day and events[1].start_dt == dt.datetime(2026, 8, 16, 9, tzinfo=TZ)

    def test_laguna_filter_still_applies(self, two_profiles):
        events, _ = brief.fetch_calendar_events(self.START, self.START + dt.timedelta(days=7))
        assert not any("Laguna" in e.summary for e in events)

    def test_failing_profile_yields_a_partial_agenda_and_the_warning(self, two_profiles):
        two_profiles(failing={"work"})
        events, errors = brief.fetch_calendar_events(self.START, self.START + dt.timedelta(days=7))
        assert [e.summary for e in events] == ["Lecture", "Dinner"]
        assert errors == ["work (error[auth]: invalid_grant)"]
        message = brief.build_daily_brief(events, [], TODAY, errors=errors)
        assert "Partial sync warning: work (error[auth]: invalid_grant)" in message

    def test_total_failure_names_every_profile(self, two_profiles):
        two_profiles(failing={"work", "personal"})
        events, errors = brief.fetch_calendar_events(self.START, self.START + dt.timedelta(days=7))
        assert events == []
        assert errors == ["personal (error[auth]: invalid_grant)", "work (error[auth]: invalid_grant)"]
        assert "Calendar sync failed" in brief.build_daily_brief(events, [], TODAY, errors=errors)

    def test_missing_calendar_config_is_a_hard_error(self, monkeypatch, tmp_path):
        monkeypatch.setattr(gcal, "CONFIG_PATH", tmp_path / "calendars.json")
        with pytest.raises(gcal.GcalError, match="calendars.json"):
            brief.fetch_calendar_events(self.START, self.START + dt.timedelta(days=1))


class TestGoogleAuthPath:
    def test_missing_gws_binary_is_a_hard_error(self, monkeypatch, tmp_path):
        missing = tmp_path / "gws"
        monkeypatch.setattr(gcal, "GWS_BIN", missing)
        monkeypatch.setattr(gcal, "load_config", lambda path=None: TWO_PROFILE_CONFIG)
        start = dt.datetime(2026, 8, 16, tzinfo=TZ)

        try:
            brief.fetch_calendar_events(start, start + dt.timedelta(days=7))
        except RuntimeError as exc:
            assert str(missing) in str(exc)
        else:
            raise AssertionError("missing gws binary was accepted")

    def test_no_code_path_attempts_to_read_a_token_file(self):
        source = (Path(__file__).resolve().parents[1] / "scripts" / "daily_brief.py").read_text()
        assert "google_token" not in source
        for banned in ("google.oauth2", "googleapiclient", "google.auth"):
            assert banned not in source

    def test_calendar_fetch_never_accesses_token_files(self, monkeypatch, two_profiles):
        opened_files = []
        real_open = Path.open

        def tracking_open(path_obj, *args, **kwargs):
            opened_files.append(str(path_obj))
            return real_open(path_obj, *args, **kwargs)

        monkeypatch.setattr(Path, "open", tracking_open)
        start = dt.datetime(2026, 8, 16, tzinfo=TZ)
        events, errors = brief.fetch_calendar_events(start, start + dt.timedelta(days=1))
        assert not any("google_token" in f for f in opened_files)


class TestDailyBriefMessage:
    def test_renders_the_current_single_message_skeleton(self):
        message = brief.build_daily_brief([], [], TODAY)
        assert message.startswith("---------------------------------\n🌅 Daily Briefing • Sun, Aug 16, 2026")
        assert "⏰ TODAY'S TIMELINE:" in message
        assert "⚡ KEY ACTIONS TODAY:" in message
        assert "📅 COMING UP NEXT:" in message

    def test_today_lists_timed_events_before_all_day_events(self):
        message = brief.build_daily_brief(
            [event("Standup", hour=9, minute=15), event("Enrollment", hour=0, all_day=True)],
            [],
            TODAY,
        )
        assert "09:15 AM  Standup" in message
        assert "All Day   Enrollment" in message
        assert message.index("Standup") < message.index("Enrollment")

    def test_due_tasks_come_before_undated_high_priority_tasks(self):
        message = brief.build_daily_brief(
            [],
            [
                task("Due today", due=TODAY),
                task("Overdue", due=TODAY - dt.timedelta(days=1)),
                task("High later", priority="high"),
            ],
            TODAY,
        )
        assert message.index("Due today") < message.index("Overdue") < message.index("High later")
        assert "Due today (Due Today)" in message
        assert "High later [!high]" in message

    def test_falls_back_to_the_first_three_tasks_when_none_are_due_or_high(self):
        tasks = [task(f"Task {index}") for index in range(1, 5)]
        message = brief.build_daily_brief([], tasks, TODAY)
        assert "1. Task 1" in message
        assert "3. Task 3" in message
        assert "Task 4" not in message

    def test_upcoming_events_are_limited_to_four(self):
        events = [event(f"Event {index}", day=17 + index) for index in range(5)]
        message = brief.build_daily_brief(events, [], TODAY)
        assert "Event 0" in message
        assert "Event 3" in message
        assert "Event 4" not in message

    def test_total_calendar_failure_does_not_hide_tasks(self):
        message = brief.build_daily_brief(
            [],
            [task("Still visible", priority="high")],
            TODAY,
            errors=["personal (invalid_grant)", "work (invalid_grant)"],
        )
        assert "Calendar sync failed: personal (invalid_grant), work (invalid_grant)" in message
        assert "1. Still visible [!high]" in message
        assert "Upcoming schedule unavailable due to calendar sync error." in message

    def test_partial_calendar_failure_keeps_events_and_names_the_error(self):
        message = brief.build_daily_brief(
            [event("Visible event")],
            [],
            TODAY,
            errors=["dlsu (forbidden)"],
        )
        assert "Visible event" in message
        assert "Partial sync warning: dlsu (forbidden)" in message

    def test_sections_keep_the_existing_blank_line_separator(self):
        message = brief.build_daily_brief([], [], TODAY)
        assert "today.\n\n⚡ KEY ACTIONS TODAY:" in message
        assert "TODAY:\n\n📅 COMING UP NEXT:" in message
