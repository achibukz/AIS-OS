from __future__ import annotations

import datetime as dt
import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

import gcal_add  # noqa: E402


class FakeBin:
    """Stands in for GWS_BIN, whose exists() cannot be patched on a PosixPath."""

    def __init__(self, present: bool):
        self.present = present

    def exists(self) -> bool:
        return self.present

    def __str__(self) -> str:
        return "/fake/gws"


def cal(summary: str, role: str = "owner", cid: str | None = None) -> dict:
    return {"summary": summary, "accessRole": role, "id": cid or f"{summary.lower()}@group.calendar.google.com"}


def test_all_day_body_uses_date_not_datetime():
    body = gcal_add.all_day_body("Standup", dt.date(2026, 9, 2))
    assert body["start"] == {"date": "2026-09-02"}
    assert body["end"] == {"date": "2026-09-03"}
    assert "dateTime" not in json.dumps(body)


def test_all_day_body_disables_reminders():
    body = gcal_add.all_day_body("Standup", dt.date(2026, 9, 2))
    assert body["reminders"] == {"useDefault": False, "overrides": []}


def test_all_day_body_omits_empty_description():
    assert "description" not in gcal_add.all_day_body("Standup", dt.date(2026, 9, 2))
    assert gcal_add.all_day_body("Standup", dt.date(2026, 9, 2), "why")["description"] == "why"


def test_parse_json_skips_the_keyring_banner():
    assert gcal_add.parse_json('Using keyring backend: file\n{"items": []}') == {"items": []}


def test_parse_json_raises_when_there_is_no_body():
    with pytest.raises(gcal_add.GwsError):
        gcal_add.parse_json("Using keyring backend: file\n")


def test_pick_calendar_prefers_an_exact_match_over_a_prefix():
    cals = [cal("DLSU"), cal("DLSU Laguna")]
    assert gcal_add.pick_calendar(cals, "DLSU")["summary"] == "DLSU"


def test_pick_calendar_takes_a_unique_case_insensitive_prefix():
    assert gcal_add.pick_calendar([cal("Personal")], "personal")["summary"] == "Personal"


def test_pick_calendar_refuses_an_ambiguous_prefix():
    assert gcal_add.pick_calendar([cal("STSP001"), cal("STSP002")], "STSP") is None


def test_find_calendar_searches_profiles_in_order(monkeypatch):
    seen: list[str] = []

    def fake(profile: str) -> list[dict]:
        seen.append(profile)
        return [cal("Personal")] if profile == "main" else []

    monkeypatch.setattr(gcal_add.Path, "exists", lambda self: True)
    monkeypatch.setattr(gcal_add, "writable_calendars", fake)
    profile, _ = gcal_add.find_calendar("Personal")
    assert profile == "main"
    assert seen == ["personal", "work", "main"]


def test_find_calendar_ignores_a_calendar_it_cannot_write_to(monkeypatch):
    monkeypatch.setattr(gcal_add.Path, "exists", lambda self: True)
    monkeypatch.setattr(gcal_add, "calendars", lambda p: [cal("Holidays", role="reader")])
    assert gcal_add.find_calendar("Holidays") is None


def test_find_calendar_skips_a_profile_that_errors(monkeypatch):
    def fake(profile: str) -> list[dict]:
        if profile == "personal":
            raise gcal_add.GwsError("token dead")
        return [cal("Personal")]

    monkeypatch.setattr(gcal_add.Path, "exists", lambda self: True)
    monkeypatch.setattr(gcal_add, "writable_calendars", fake)
    assert gcal_add.find_calendar("Personal")[0] == "work"


def test_find_calendar_returns_none_when_nothing_matches(monkeypatch):
    monkeypatch.setattr(gcal_add.Path, "exists", lambda self: True)
    monkeypatch.setattr(gcal_add, "writable_calendars", lambda p: [cal("Personal")])
    assert gcal_add.find_calendar("NoSuchCal") is None


def test_already_there_matches_only_an_exact_summary(monkeypatch):
    monkeypatch.setattr(
        gcal_add,
        "gws",
        lambda *a, **k: {"items": [{"summary": "Pay rent later", "htmlLink": "x"}]},
    )
    assert gcal_add.already_there("work", "cid", "Pay rent", dt.date(2026, 9, 2)) is None


def test_already_there_returns_the_link_on_a_hit(monkeypatch):
    monkeypatch.setattr(
        gcal_add,
        "gws",
        lambda *a, **k: {"items": [{"summary": "Pay rent", "htmlLink": "http://event"}]},
    )
    assert gcal_add.already_there("work", "cid", "Pay rent", dt.date(2026, 9, 2)) == "http://event"


def test_gws_raises_when_the_binary_is_missing(monkeypatch):
    monkeypatch.setattr(gcal_add, "GWS_BIN", FakeBin(False))
    with pytest.raises(gcal_add.GwsError, match="gws binary not found"):
        gcal_add.gws("work", "calendar", "calendarList", "list")


def test_main_exits_one_when_the_binary_is_missing(monkeypatch, capsys):
    monkeypatch.setattr(gcal_add, "GWS_BIN", FakeBin(False))
    monkeypatch.setattr(sys, "argv", ["gcal_add.py", "--list"])
    assert gcal_add.main() == 1
    assert "gws binary not found" in capsys.readouterr().err


def test_main_exits_one_on_an_unknown_calendar(monkeypatch, capsys):
    monkeypatch.setattr(gcal_add, "GWS_BIN", FakeBin(True))
    monkeypatch.setattr(gcal_add, "find_calendar", lambda name: None)
    monkeypatch.setattr(sys, "argv", ["gcal_add.py", "Title", "2026-09-02", "--calendar", "Nope"])
    assert gcal_add.main() == 1
    assert "no writable calendar named 'Nope'" in capsys.readouterr().err


def test_main_is_a_no_op_when_the_event_already_exists(monkeypatch, capsys):
    inserted: list[dict] = []
    monkeypatch.setattr(gcal_add, "GWS_BIN", FakeBin(True))
    monkeypatch.setattr(gcal_add, "find_calendar", lambda name: ("work", "cid"))
    monkeypatch.setattr(gcal_add, "already_there", lambda *a: "http://event")
    monkeypatch.setattr(gcal_add, "insert_event", lambda *a: inserted.append(a) or "")
    monkeypatch.setattr(sys, "argv", ["gcal_add.py", "Title", "2026-09-02", "--calendar", "ING"])
    assert gcal_add.main() == 0
    assert inserted == []
    assert "already on ING" in capsys.readouterr().out


def test_main_inserts_an_all_day_event_when_it_is_new(monkeypatch, capsys):
    captured: dict = {}

    def fake_insert(profile, calendar_id, body):
        captured.update(body=body, calendar_id=calendar_id)
        return "http://new"

    monkeypatch.setattr(gcal_add, "GWS_BIN", FakeBin(True))
    monkeypatch.setattr(gcal_add, "find_calendar", lambda name: ("work", "cid"))
    monkeypatch.setattr(gcal_add, "already_there", lambda *a: None)
    monkeypatch.setattr(gcal_add, "insert_event", fake_insert)
    monkeypatch.setattr(sys, "argv", ["gcal_add.py", "Title", "2026-09-02", "--calendar", "ING"])
    assert gcal_add.main() == 0
    assert captured["body"]["start"] == {"date": "2026-09-02"}
    assert "added to ING" in capsys.readouterr().out


def test_main_exits_one_when_the_insert_fails(monkeypatch, capsys):
    def boom(*a):
        raise gcal_add.GwsError("gws work: quota exceeded")

    monkeypatch.setattr(gcal_add, "GWS_BIN", FakeBin(True))
    monkeypatch.setattr(gcal_add, "find_calendar", lambda name: ("work", "cid"))
    monkeypatch.setattr(gcal_add, "already_there", lambda *a: None)
    monkeypatch.setattr(gcal_add, "insert_event", boom)
    monkeypatch.setattr(sys, "argv", ["gcal_add.py", "Title", "2026-09-02"])
    assert gcal_add.main() == 1
    assert "quota exceeded" in capsys.readouterr().err


def test_no_google_auth_imports_remain():
    source = (Path(__file__).resolve().parents[1] / "scripts" / "gcal_add.py").read_text()
    for banned in ("google.oauth2", "googleapiclient", "google.auth"):
        assert banned not in source
