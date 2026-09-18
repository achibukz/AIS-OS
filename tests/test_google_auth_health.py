import json

import pytest

import gcal
import google_auth_health as health

REAL_DRIFT_CHECK = health.check_calendar_drift


@pytest.fixture(autouse=True)
def no_drift(monkeypatch):
    monkeypatch.setattr(health, "check_calendar_drift", lambda: [])

def _auth(scopes=None):
    return {
        "token_valid": True,
        "has_refresh_token": True,
        "scopes": scopes
        if scopes is not None
        else [health.CALENDAR_SCOPE, next(iter(health.GMAIL_SCOPES)), next(iter(health.DRIVE_SCOPES))],
    }


def _healthy_gws(_profile, *args):
    if args[:2] == ("auth", "status"):
        return _auth()
    if args[:3] == ("calendar", "calendarList", "list"):
        return {"items": [{"accessRole": "owner"}]}
    return {}


def test_healthy_profile_checks_auth_calendar_gmail_and_drive(monkeypatch):
    calls = []

    def fake_gws(profile, *args):
        calls.append((profile, args))
        return _healthy_gws(profile, *args)

    monkeypatch.setattr(health, "run_gws", fake_gws)

    status = health.check_profile("main")

    assert status.healthy
    assert [args[0] for _, args in calls] == ["auth", "calendar", "gmail", "drive"]


def test_profile_names_each_failed_live_check(monkeypatch):
    def failing_gws(profile, *args):
        if args[0] == "auth":
            return _auth()
        raise RuntimeError(f"{args[0]} unavailable")

    monkeypatch.setattr(health, "run_gws", failing_gws)

    status = health.check_profile("work")

    assert not status.healthy
    assert status.failures == (
        "calendar read: calendar unavailable",
        "gmail read: gmail unavailable",
        "drive read: drive unavailable",
    )


def test_missing_scope_and_no_writable_calendar_are_failures(monkeypatch):
    def limited_gws(profile, *args):
        if args[0] == "auth":
            return _auth(scopes=[])
        if args[0] == "calendar":
            return {"items": [{"accessRole": "reader"}]}
        return {}

    monkeypatch.setattr(health, "run_gws", limited_gws)

    status = health.check_profile("dlsu")

    assert "calendar scope: full Calendar scope is missing" in status.failures
    assert "gmail scope: Gmail read scope is missing" in status.failures
    assert "drive scope: Drive scope is missing" in status.failures
    assert "calendar write: no owner or writer calendar found" in status.failures


def test_default_healthy_run_is_silent(monkeypatch, capsys):
    statuses = [health.ProfileStatus(profile) for profile in health.GWS_PROFILES]
    monkeypatch.setattr(health, "check_all_profiles", lambda: statuses)
    monkeypatch.setattr(health, "send", lambda _message: (_ for _ in ()).throw(AssertionError("sent")))
    monkeypatch.setattr("sys.argv", ["google_auth_health.py"])

    assert health.main() == 0
    assert capsys.readouterr().out == ""


def test_weekly_always_reports_each_profile(monkeypatch, capsys):
    statuses = [health.ProfileStatus(profile) for profile in health.GWS_PROFILES]
    monkeypatch.setattr(health, "check_all_profiles", lambda: statuses)
    monkeypatch.setattr("sys.argv", ["google_auth_health.py", "--weekly", "--dry-run"])

    assert health.main() == 0
    output = capsys.readouterr().out
    assert "Google OAuth weekly heartbeat" in output
    for profile in health.GWS_PROFILES:
        assert f"{profile}: healthy" in output


def test_warning_banner_names_only_failed_profiles():
    statuses = [
        health.ProfileStatus("main"),
        health.ProfileStatus("personal", ("gmail read: invalid_grant",)),
        health.ProfileStatus("work"),
        health.ProfileStatus("dlsu", ("drive read: forbidden",)),
    ]
    assert health.failed_profile_names(statuses) == ["personal", "dlsu"]
    assert health.auth_warning_banner(["personal", "dlsu"]) == "⚠️ Google auth failed: personal, dlsu"


def test_calendar_probe_filters_for_writable_calendars(monkeypatch):
    captured = []

    def fake_gws(profile, *args):
        captured.append(args)
        return _healthy_gws(profile, *args)

    monkeypatch.setattr(health, "run_gws", fake_gws)
    health.check_profile("personal")

    calendar_call = next(args for args in captured if args[0] == "calendar")
    params = json.loads(calendar_call[calendar_call.index("--params") + 1])
    assert params["minAccessRole"] == "writer"


def test_run_gws_reports_missing_binary(monkeypatch, tmp_path):
    missing = tmp_path / "gws"
    monkeypatch.setattr(gcal, "GWS_BIN", missing)
    monkeypatch.setattr(gcal, "profile_dir", lambda profile: tmp_path)
    with pytest.raises(RuntimeError, match=str(missing)):
        health.run_gws("main", "auth", "status")


def test_run_gws_reports_a_missing_profile(monkeypatch, tmp_path):
    monkeypatch.setattr(gcal, "profile_dir", lambda profile: tmp_path / profile)
    with pytest.raises(RuntimeError, match="gws profile missing"):
        health.run_gws("main", "auth", "status")


def test_drift_makes_a_default_run_report(monkeypatch, capsys):
    statuses = [health.ProfileStatus(profile) for profile in health.GWS_PROFILES]
    sent = []
    monkeypatch.setattr(health, "check_all_profiles", lambda: statuses)
    monkeypatch.setattr(health, "check_calendar_drift", lambda: ["current course has no calendar: STDISCM"])
    monkeypatch.setattr(health, "send", sent.append)
    monkeypatch.setattr("sys.argv", ["google_auth_health.py"])

    assert health.main() == 0
    assert sent and "Google OAuth needs attention" in sent[0]
    assert "calendars: DRIFT\n  - current course has no calendar: STDISCM" in sent[0]


def test_weekly_report_includes_drift_and_a_clean_calendar_line():
    statuses = [health.ProfileStatus("main")]
    assert "calendars: matches config" in health.build_report(statuses, weekly=True)
    drifted = health.build_report(statuses, weekly=True, drift=["writable calendar not in config: New (personal)"])
    assert "Google OAuth weekly heartbeat" in drifted
    assert "  - writable calendar not in config: New (personal)" in drifted


def test_drift_check_uses_the_shared_calendars_check(monkeypatch):
    config = [{"name": "CSOPESY", "id": "c@group", "profile": "work", "purpose": "course",
               "write_owner": [], "schedule": False}]
    monkeypatch.setattr(gcal, "load_config", lambda path=None: config)
    monkeypatch.setattr(gcal, "read_current_courses", lambda wiki=gcal.WIKI_PATH: ["STDISCM"])
    monkeypatch.setattr(gcal, "list_calendars", lambda profiles: {
        "calendars": [{"id": "c@group", "name": "CSOPESY", "access_role": "owner", "profile": "work"}],
        "errors": [],
    })
    assert REAL_DRIFT_CHECK() == [
        "current course has no calendar: STDISCM",
        "course calendar is not a current course: CSOPESY",
    ]


def test_drift_check_is_empty_when_calendars_match(monkeypatch):
    config = [{"name": "STDISCM", "id": "s@group", "profile": "personal", "purpose": "course",
               "write_owner": [], "schedule": True}]
    monkeypatch.setattr(gcal, "load_config", lambda path=None: config)
    monkeypatch.setattr(gcal, "read_current_courses", lambda wiki=gcal.WIKI_PATH: ["STDISCM"])
    monkeypatch.setattr(gcal, "list_calendars", lambda profiles: {
        "calendars": [{"id": "s@group", "name": "STDISCM", "access_role": "owner", "profile": "personal"}],
        "errors": [],
    })
    assert REAL_DRIFT_CHECK() == []


def test_drift_check_reports_a_missing_config(monkeypatch, tmp_path):
    monkeypatch.setattr(gcal, "CONFIG_PATH", tmp_path / "calendars.json")
    assert REAL_DRIFT_CHECK() == [
        f"check failed: calendar config not found at {tmp_path / 'calendars.json'} "
        "(set ACHIOS_HOME if this checkout is not under ~/Code/GitHub)"
    ]


def test_auth_status_is_called_without_the_format_flag(monkeypatch, tmp_path):
    argvs = []
    gws = tmp_path / "gws"
    gws.write_text("")
    monkeypatch.setattr(gcal, "GWS_BIN", gws)
    monkeypatch.setattr(gcal, "profile_dir", lambda profile: tmp_path)

    def run(argv, **kwargs):
        argvs.append(argv)
        if argv[1:3] == ["auth", "status"]:
            if "--format" in argv:
                return gcal.subprocess.CompletedProcess(argv, 3, stdout="", stderr="error[validation]: --format")
            return gcal.subprocess.CompletedProcess(argv, 0, stdout=json.dumps(_auth()), stderr="")
        if argv[1:4] == ["calendar", "calendarList", "list"]:
            return gcal.subprocess.CompletedProcess(argv, 0, stdout='{"items": [{"accessRole": "owner"}]}', stderr="")
        return gcal.subprocess.CompletedProcess(argv, 0, stdout="{}", stderr="")

    monkeypatch.setattr(gcal.subprocess, "run", run)

    status = health.check_profile("main")

    assert status.healthy, status.failures
    assert argvs[0] == [str(gws), "auth", "status"]
