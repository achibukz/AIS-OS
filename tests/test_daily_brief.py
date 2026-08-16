import datetime as dt
from zoneinfo import ZoneInfo

import daily_brief as brief
import pytest

TZ = ZoneInfo("Asia/Manila")
TODAY = dt.date(2026, 8, 16)


def event(summary, when, all_day=False, calendar="Personal", location="", color="#3f51b5"):
    return {
        "when": when,
        "all_day": all_day,
        "calendar": calendar,
        "color": color,
        "summary": summary,
        "location": location,
    }


class TestParseTasks:
    def test_reads_state_area_priority_and_due(self):
        (task,) = brief.parse_tasks("- [ ] Ship the brief #achios !high @2026-08-20")
        assert task.text == "Ship the brief"
        assert task.state == "active"
        assert task.areas == ["achios"]
        assert task.priority == "high"
        assert task.due == dt.date(2026, 8, 20)

    def test_defaults_to_medium_priority_and_no_due_date(self):
        (task,) = brief.parse_tasks("- [ ] Plain task")
        assert task.priority == "med"
        assert task.due is None
        assert task.areas == []

    @pytest.mark.parametrize(
        "marker,state", [(" ", "active"), ("x", "done"), ("~", "blocked")]
    )
    def test_markers_map_to_states(self, marker, state):
        (task,) = brief.parse_tasks(f"- [{marker}] Something")
        assert task.state == state

    def test_skips_non_task_lines(self):
        body = "# Tasks\n\nSome prose.\n\n- a bullet\n- [ ] Real one\n"
        assert [t.text for t in brief.parse_tasks(body)] == ["Real one"]

    def test_ignores_example_lines_inside_fenced_code_blocks(self):
        body = "```\n- [ ] What to do #area !high @2026-08-20\n```\n\n- [ ] Real one\n"
        assert [t.text for t in brief.parse_tasks(body)] == ["Real one"]

    def test_strips_markdown_markup_from_text(self):
        (task,) = brief.parse_tasks("- [ ] Fix **`profile.yml`** for [[career-ops-hub]]")
        assert task.text == "Fix profile.yml for career-ops-hub"

    def test_multiple_areas_are_all_captured(self):
        (task,) = brief.parse_tasks("- [ ] Cross-cutting #thesis #school")
        assert task.areas == ["thesis", "school"]

    def test_sorts_by_due_then_priority_then_text(self):
        tasks = brief.parse_tasks(
            "- [ ] Later @2026-09-01\n"
            "- [ ] Undated low !low\n"
            "- [ ] Sooner @2026-08-18\n"
            "- [ ] Undated high !high\n"
        )
        order = [t.text for t in sorted(tasks, key=lambda t: t.sort_key)]
        assert order == ["Sooner", "Later", "Undated high", "Undated low"]


class TestColorDot:
    @pytest.mark.parametrize(
        "hex_color,dot",
        [
            ("#d50000", "🔴"),  # tomato
            ("#0b8043", "🟢"),  # basil
            ("#33b679", "🟢"),  # sage
            ("#3f51b5", "🔵"),  # blueberry
            ("#039be5", "🔵"),  # peacock
            ("#f6bf26", "🟡"),  # banana
            ("#8e24aa", "🟣"),  # grape
            ("#616161", "⚫"),  # graphite
        ],
    )
    def test_google_calendar_colors_map_to_the_nearest_circle(self, hex_color, dot):
        assert brief.color_dot(hex_color) == dot

    def test_dark_saturated_greens_do_not_collapse_to_black(self):
        assert brief.color_dot("#0b8043") != "⚫"

    def test_near_black_is_black_and_near_white_is_white(self):
        assert brief.color_dot("#000000") == "⚫"
        assert brief.color_dot("#f5f5f5") == "⚪"

    def test_accepts_hex_without_the_leading_hash(self):
        assert brief.color_dot("d50000") == "🔴"

    @pytest.mark.parametrize("value", ["", "nope", "#12345", "#gggggg"])
    def test_unusable_values_fall_back_to_the_default_dot(self, value):
        assert brief.color_dot(value) == brief.DEFAULT_DOT


class TestScheduleMessage:
    def test_today_shows_dot_time_summary_and_calendar(self):
        events = [
            event(
                "ONLINE Session",
                dt.datetime(2026, 8, 16, 9, 15, tzinfo=TZ),
                calendar="STCLOUD",
                color="#0b8043",
            )
        ]
        message = brief.schedule_message(events, TODAY)
        assert "🟢  09:15   ONLINE Session" in message
        assert "      STCLOUD" in message

    def test_today_all_day_event_is_labelled(self):
        events = [
            event("END OF TERM", dt.datetime(2026, 8, 16, 0, 0, tzinfo=TZ), all_day=True)
        ]
        assert "all day   END OF TERM" in brief.schedule_message(events, TODAY)

    def test_today_shows_location_on_its_own_line(self):
        events = [
            event("Checkin", dt.datetime(2026, 8, 16, 18, 30, tzinfo=TZ), location="ALTDSI")
        ]
        assert "      📍 ALTDSI" in brief.schedule_message(events, TODAY)

    def test_week_groups_events_under_one_dotted_calendar_heading(self):
        events = [
            event("Session A", dt.datetime(2026, 8, 18, 11, 0, tzinfo=TZ), calendar="CSOPESY"),
            event("Session B", dt.datetime(2026, 8, 20, 11, 0, tzinfo=TZ), calendar="CSOPESY"),
            event("Deadline", dt.datetime(2026, 8, 18, 0, 0, tzinfo=TZ), all_day=True, calendar="Canvas"),
        ]
        message = brief.schedule_message(events, TODAY)
        assert message.count("CSOPESY") == 1
        assert "      Tue 18, 11:00   Session A" in message
        assert "      Thu 20, 11:00   Session B" in message
        assert "      Tue 18   Deadline" in message

    def test_birthdays_are_pulled_into_their_own_section(self):
        events = [
            event("Aji Bday", dt.datetime(2026, 8, 16, 0, 0, tzinfo=TZ), all_day=True, calendar="Bdayy"),
            event("Gym", dt.datetime(2026, 8, 16, 7, 0, tzinfo=TZ)),
        ]
        message = brief.schedule_message(events, TODAY)
        today_block = message[message.index("☀️") : message.index("🗓")]
        assert "Gym" in today_block
        assert "Aji Bday" not in today_block
        assert "🎂  BIRTHDAYS" in message
        assert "      Sun 16   Aji Bday" in message

    def test_birthday_section_is_omitted_when_there_are_none(self):
        assert "BIRTHDAYS" not in brief.schedule_message([], TODAY)

    def test_empty_schedule_says_so_for_today_and_the_week(self):
        assert brief.schedule_message([], TODAY).count("Nothing scheduled. 🎉") == 2

    def test_sections_are_separated_by_blank_lines(self):
        message = brief.schedule_message([], TODAY)
        assert "\n\n\n" in message


class TestTasksMessage:
    def test_groups_by_area_with_an_emoji_and_numbers_within_each(self):
        message = brief.tasks_message(
            brief.parse_tasks(
                "- [ ] Enlist #school\n- [ ] Read syllabus #school\n- [ ] Email HR #work\n"
            ),
            TODAY,
        )
        assert "🎓  SCHOOL" in message
        assert "💼  WORK" in message
        assert "1.  Enlist" in message and "2.  Read syllabus" in message
        assert "1.  Email HR" in message

    def test_unknown_area_gets_the_default_emoji(self):
        message = brief.tasks_message(brief.parse_tasks("- [ ] Thing #weird"), TODAY)
        assert f"{brief.DEFAULT_AREA_EMOJI}  WEIRD" in message

    def test_untagged_tasks_land_under_other(self):
        assert "OTHER" in brief.tasks_message(brief.parse_tasks("- [ ] No tag"), TODAY)

    def test_due_dates_render_on_their_own_line(self):
        message = brief.tasks_message(
            brief.parse_tasks(
                "- [ ] Late @2026-08-01\n- [ ] Now @2026-08-16\n- [ ] Soon @2026-08-20\n"
            ),
            TODAY,
        )
        assert "      ⚠️ overdue since Aug 01" in message
        assert "      🔥 due today" in message
        assert "      🗓 due Aug 20" in message

    def test_undated_tasks_get_no_due_line(self):
        message = brief.tasks_message(brief.parse_tasks("- [ ] Plain"), TODAY)
        assert "1.  Plain" in message
        assert "due" not in message

    def test_header_counts_only_active_tasks(self):
        message = brief.tasks_message(
            brief.parse_tasks("- [ ] A #work\n- [ ] B #work\n- [~] Stuck\n- [x] Done\n"), TODAY
        )
        assert "2 active" in message

    def test_blocked_tasks_get_their_own_group_and_done_are_dropped(self):
        message = brief.tasks_message(
            brief.parse_tasks("- [ ] Active #work\n- [~] Stuck\n- [x] Finished\n"), TODAY
        )
        assert "🚧  BLOCKED" in message
        assert "1.  Stuck" in message
        assert "Finished" not in message

    def test_empty_register_says_so(self):
        assert "Nothing on the register. 🎉" in brief.tasks_message([], TODAY)
