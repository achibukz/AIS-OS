import datetime as dt

import gcal_add
import pytest

DATE = dt.date(2026, 8, 29)


class TestAllDayBody:
    def test_end_date_is_exclusive_so_a_one_day_event_ends_tomorrow(self):
        body = gcal_add.all_day_body("Buy Codex", DATE)
        assert body["start"] == {"date": "2026-08-29"}
        assert body["end"] == {"date": "2026-08-30"}

    def test_reminders_are_off_because_the_daily_brief_already_surfaces_it(self):
        assert gcal_add.all_day_body("x", DATE)["reminders"] == {"useDefault": False, "overrides": []}

    def test_description_is_omitted_when_empty(self):
        assert "description" not in gcal_add.all_day_body("x", DATE)
        assert gcal_add.all_day_body("x", DATE, "why")["description"] == "why"


class TestPickCalendar:
    CALS = [
        {"summary": "Personal", "id": "p", "accessRole": "owner"},
        {"summary": "PEDFOUR", "id": "pe", "accessRole": "owner"},
        {"summary": "ING", "id": "i", "accessRole": "owner"},
    ]

    def test_exact_match_wins(self):
        assert gcal_add.pick_calendar(self.CALS, "ING")["id"] == "i"

    def test_unique_case_insensitive_prefix_matches(self):
        assert gcal_add.pick_calendar(self.CALS, "ing")["id"] == "i"

    def test_ambiguous_prefix_matches_nothing(self):
        assert gcal_add.pick_calendar(self.CALS, "pe") is None

    def test_exact_match_beats_a_competing_prefix(self):
        cals = [{"summary": "PE", "id": "a"}, {"summary": "PEDFOUR", "id": "b"}]
        assert gcal_add.pick_calendar(cals, "PE")["id"] == "a"

    def test_unknown_name_returns_none(self):
        assert gcal_add.pick_calendar(self.CALS, "Nope") is None
