import json

import google_auth_health as health

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


def test_parse_json_skips_keyring_banner():
    assert health.parse_json('Using keyring backend: file\n{"token_valid": true}') == {"token_valid": True}


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
    monkeypatch.setattr(health, "GWS_BIN", missing)
    try:
        health.run_gws("main", "auth", "status")
    except RuntimeError as exc:
        assert str(missing) in str(exc)
    else:
        raise AssertionError("missing gws binary was accepted")
