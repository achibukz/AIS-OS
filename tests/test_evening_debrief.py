import datetime as dt
from pathlib import Path
import pytest
import sys

# Add scripts directory to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
import gcal
from evening_debrief import (
    strip_markup,
    get_tasks_data,
    get_corrections_today,
    build_evening_debrief,
)


def test_strip_markup():
    assert strip_markup("[[Personal Wiki]]") == "Personal Wiki"
    assert strip_markup("**Important**") == "Important"
    assert strip_markup("`code snippet`") == "code snippet"


def test_build_evening_debrief_two_messages(monkeypatch):
    import evening_debrief as debrief

    monkeypatch.setattr(debrief, "fetch_tomorrow_events", lambda tomorrow: ([], []))
    test_date = dt.date(2026, 8, 18)
    main_msg, rules_msg = build_evening_debrief(test_date)

    assert "🌙 Evening Debrief" in main_msg
    assert "Day concluded: Aug 18, 2026" in main_msg
    assert "Rest well! 🌙" in main_msg

    if rules_msg:
        assert "🧠 Self-Learning & Harvested Rules" in rules_msg
        assert "Concluded: Aug 18, 2026" in rules_msg


def test_missing_gws_binary_is_a_hard_error(monkeypatch, tmp_path):
    import evening_debrief as debrief

    missing = tmp_path / "gws"
    monkeypatch.setattr(gcal, "GWS_BIN", missing)
    monkeypatch.setattr(gcal, "load_config", lambda path=None: [
        {"name": "Personal", "id": "p", "profile": "personal", "purpose": "", "write_owner": [], "schedule": True}
    ])
    try:
        debrief.fetch_tomorrow_events(dt.date(2026, 8, 19))
    except RuntimeError as exc:
        assert str(missing) in str(exc)
    else:
        raise AssertionError("missing gws binary was accepted")


def test_no_code_path_attempts_to_read_a_token_file():
    source = (Path(__file__).resolve().parents[1] / "scripts" / "evening_debrief.py").read_text()
    assert "google_token" not in source
    for banned in ("google.oauth2", "googleapiclient", "google.auth"):
        assert banned not in source



def _agenda_fake(failing=()):
    events = {
        ("personal", "course@group"): [
            {"id": "lec", "summary": "Lecture", "start": {"dateTime": "2026-08-19T09:00:00+08:00"},
             "end": {"dateTime": "2026-08-19T10:00:00+08:00"}},
        ],
        ("work", "course@group"): [
            {"id": "lec", "summary": "Lecture", "start": {"dateTime": "2026-08-19T09:00:00+08:00"},
             "end": {"dateTime": "2026-08-19T10:00:00+08:00"}},
        ],
        ("work", "ing@group"): [
            {"id": "w1", "summary": "Standup", "start": {"dateTime": "2026-08-19T10:00:00+08:00"},
             "end": {"dateTime": "2026-08-19T10:15:00+08:00"}},
            {"id": "w2", "summary": "Laguna shuttle", "start": {"date": "2026-08-19"}, "end": {"date": "2026-08-20"}},
        ],
    }

    def fake(profile, *args, timeout=30):
        if profile in failing:
            raise gcal.GwsError("error[auth]: invalid_grant", profile=profile, status=401)
        import json

        params = json.loads(args[args.index("--params") + 1])
        assert params["timeMin"] == "2026-08-19T00:00:00+08:00"
        return {"items": events.get((profile, params["calendarId"]), [])}

    return fake


CONFIG = [
    {"name": "THS-ST2", "id": "course@group", "profile": "personal", "purpose": "course", "write_owner": [], "schedule": True},
    {"name": "THS-ST2 work", "id": "course@group", "profile": "work", "purpose": "course", "write_owner": [], "schedule": True},
    {"name": "ING", "id": "ing@group", "profile": "work", "purpose": "", "write_owner": [], "schedule": True},
]


def test_tomorrow_lists_a_duplicated_course_calendar_once(monkeypatch):
    import evening_debrief as debrief

    monkeypatch.setattr(gcal, "load_config", lambda path=None: CONFIG)
    monkeypatch.setattr(gcal, "gws", _agenda_fake())
    assert debrief.fetch_tomorrow_events(dt.date(2026, 8, 19)) == (["Lecture", "Standup"], [])


def test_tomorrow_keeps_a_partial_agenda_when_a_profile_fails(monkeypatch):
    import evening_debrief as debrief

    monkeypatch.setattr(gcal, "load_config", lambda path=None: CONFIG)
    monkeypatch.setattr(gcal, "gws", _agenda_fake(failing={"work"}))
    titles, errors = debrief.fetch_tomorrow_events(dt.date(2026, 8, 19))
    assert titles == ["Lecture"]
    assert errors == ["work (error[auth]: invalid_grant)"]


def test_tomorrow_total_failure_returns_only_warnings(monkeypatch):
    import evening_debrief as debrief

    monkeypatch.setattr(gcal, "load_config", lambda path=None: CONFIG)
    monkeypatch.setattr(gcal, "gws", _agenda_fake(failing={"work", "personal"}))
    titles, errors = debrief.fetch_tomorrow_events(dt.date(2026, 8, 19))
    assert titles == []
    assert len(errors) == 2
