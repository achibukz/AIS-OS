import datetime as dt
from zoneinfo import ZoneInfo

import daily_brief as brief

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


class TestGoogleAuthPath:
    def test_missing_gws_binary_is_a_hard_error(self, monkeypatch, tmp_path):
        missing = tmp_path / "gws"
        monkeypatch.setattr(brief, "GWS_BIN", missing)
        start = dt.datetime(2026, 8, 16, tzinfo=TZ)

        try:
            brief.fetch_calendar_events(start, start + dt.timedelta(days=7))
        except RuntimeError as exc:
            assert str(missing) in str(exc)
        else:
            raise AssertionError("missing gws binary was accepted")


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
