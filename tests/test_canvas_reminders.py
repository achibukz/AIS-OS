import json
import sqlite3
from datetime import datetime, timedelta, timezone

import pytest

import canvas
from canvas_client import writer_lock
from canvas_events import SEPARATOR, format_event
from canvas_reminders import remind
from canvas_store import configure_courses, open_reader, open_writer, save_snapshot
from test_canvas_store import AT, MAPPING, assignment

URL = "https://dlsu.instructure.com/courses/42/assignments/1"


def utc(text):
    return datetime.fromisoformat(text).astimezone(timezone.utc)


def todo(item_id=1, due="2026-09-16T15:59:00Z", **changes):
    return assignment(item_id, due, **{"submission_status": "unsubmitted", "submitted_at": None,
                      "source_url": f"https://dlsu.instructure.com/courses/42/assignments/{item_id}", **changes})


def post(item_id, posted_at, title="Midterm moved"):
    return {"id": item_id, "title": title, "message": "body", "posted_at": posted_at,
            "source_url": f"https://dlsu.instructure.com/courses/42/discussion_topics/{item_id}"}


GRADE = {"id": 9, "current_grade": "A-", "current_score": 92.5, "final_grade": None,
         "final_score": None, "source_url": "https://dlsu.instructure.com/courses/42/grades"}


@pytest.fixture
def db(tmp_path):
    with open_writer(tmp_path / "cache.sqlite3") as db:
        configure_courses(db, MAPPING)
        yield db


@pytest.fixture
def quiet(db):
    with db:
        db.execute("INSERT INTO notices VALUES('catchup:v1',?)", (AT,))
    return db


def events(db):
    return [(row["kind"], json.loads(row["data"])) for row in db.execute("SELECT kind,data FROM events ORDER BY id")]


def test_catch_up_is_three_messages_queued_once(db):
    save_snapshot(db, 42, "assignments", [todo(), todo(2, submission_status="graded")], AT)
    save_snapshot(db, 42, "announcements", [post(1, "2026-09-01T00:00:00Z", "Old"), post(2, "2026-09-05T00:00:00Z")], AT)
    save_snapshot(db, 42, "grades", [GRADE], AT)
    now = utc("2026-09-12T07:00:00+08:00")
    assert remind(db, now)["queued"] == {"deadline_digest": 1, "announcement_digest": 1}
    assert remind(db, now)["queued"] == {}
    kinds = events(db)
    assert [kind for kind, _ in kinds] == ["deadline_digest", "announcement_digest"]
    assert [item["name"] for item in kinds[0][1]["items"]] == ["Lab"]
    assert [item["title"] for item in kinds[1][1]["items"]] == ["Midterm moved"]


def test_catch_up_run_claims_that_days_digest_without_sending_it(db):
    save_snapshot(db, 42, "announcements", [post(1, "2026-09-15T00:00:00Z"), post(2, "2026-09-15T12:00:00Z")], AT)
    remind(db, utc("2026-09-15T09:00:00+08:00"))
    assert [kind for kind, _ in events(db)] == ["deadline_digest", "announcement_digest"]
    assert db.execute("SELECT count(*) FROM notices WHERE key='daily:2026-09-15'").fetchone()[0] == 1
    remind(db, utc("2026-09-16T09:00:00+08:00"))
    assert [kind for kind, _ in events(db)][2:] == ["deadline_digest", "announcement_digest"]


def test_weekly_digest_starts_at_monday_eight_in_manila(quiet):
    save_snapshot(quiet, 42, "assignments", [todo(), todo(2, due="2026-09-21T01:00:00Z")], AT)
    assert remind(quiet, utc("2026-09-14T07:59:00+08:00"))["queued"] == {}
    queued = remind(quiet, utc("2026-09-14T08:00:00+08:00"))["queued"]
    assert queued == {"deadline_digest": 1, "announcement_digest": 1}
    weekly = events(quiet)[0][1]
    assert [item["due_at"] for item in weekly["items"]] == ["2026-09-16T15:59:00Z"]
    assert remind(quiet, utc("2026-09-14T20:00:00+08:00"))["queued"] == {}
    assert quiet.execute("SELECT count(*) FROM notices WHERE key LIKE 'daily:%'").fetchone()[0] == 0


def test_sunday_night_is_daily_and_monday_rolls_to_the_next_week(quiet):
    remind(quiet, utc("2026-09-20T23:59:00+08:00"))
    remind(quiet, utc("2026-09-21T08:00:00+08:00"))
    keys = [row[0] for row in quiet.execute("SELECT key FROM notices WHERE key!='catchup:v1' ORDER BY key")]
    assert keys == ["daily:2026-09-20", "weekly:2026-W39"]


def test_empty_days_and_weeks_still_send_a_message(quiet):
    remind(quiet, utc("2026-09-15T09:00:00+08:00"))
    remind(quiet, utc("2026-09-21T09:00:00+08:00"))
    now = utc("2026-09-21T09:00:00+08:00")
    texts = [format_event({"kind": kind, "data": json.dumps(data), "subject": None}, now)
             for kind, data in events(quiet) if kind == "deadline_digest"]
    assert [text.splitlines() for text in texts] == [
        [SEPARATOR, "<b>Nothing due today</b>"], [SEPARATOR, "<b>Week of Mon 21 Sep: nothing due</b>"]]


def test_daily_lists_work_due_before_tomorrow_eight_and_recent_announcements(quiet):
    save_snapshot(quiet, 42, "assignments", [todo(1, due="2026-09-15T23:00:00Z"),
                                             todo(2, due="2026-09-16T01:00:00Z")], AT)
    save_snapshot(quiet, 42, "announcements", [post(1, "2026-09-15T00:00:00Z"),
                                               post(2, "2026-09-10T00:00:00Z", "Old")], AT)
    remind(quiet, utc("2026-09-15T09:00:00+08:00"))
    (_, due), (_, news) = events(quiet)
    assert [item["due_at"] for item in due["items"]] == ["2026-09-15T23:00:00Z"]
    assert [item["title"] for item in news["items"]] == ["Midterm moved"]


def test_quiet_day_sends_no_announcement_message(quiet):
    save_snapshot(quiet, 42, "announcements", [post(1, "2026-09-01T00:00:00Z")], AT)
    remind(quiet, utc("2026-09-15T09:00:00+08:00"))
    assert [kind for kind, _ in events(quiet)] == ["deadline_digest"]


def test_weekly_announcements_cover_the_past_seven_days(quiet):
    save_snapshot(quiet, 42, "announcements", [post(1, "2026-09-07T01:00:00Z"),
                                               post(2, "2026-09-06T23:00:00Z", "Old")], AT)
    remind(quiet, utc("2026-09-14T08:00:00+08:00"))
    assert [item["title"] for item in events(quiet)[1][1]["items"]] == ["Midterm moved"]


@pytest.mark.parametrize("before,tag", [
    (timedelta(hours=3, minutes=1), None), (timedelta(hours=3), "3h"), (timedelta(minutes=61), "3h"),
    (timedelta(hours=1), "1h"), (timedelta(minutes=1), "1h"), (timedelta(0), None), (-timedelta(minutes=1), None),
])
def test_reminder_windows(quiet, before, tag):
    due = utc("2026-09-15T02:00:00+08:00")
    save_snapshot(quiet, 42, "assignments", [todo(due=due.isoformat())], AT)
    remind(quiet, due - before)
    keys = [row[0] for row in quiet.execute("SELECT key FROM notices WHERE key LIKE 'reminder:%'")]
    assert keys == ([f"reminder:42:1:{due.isoformat()}:{tag}"] if tag else [])


def test_each_reminder_is_sent_once_and_a_gap_skips_the_elapsed_window(quiet):
    due = utc("2026-09-15T02:00:00+08:00")
    save_snapshot(quiet, 42, "assignments", [todo(due=due.isoformat())], AT)
    for minutes in (30, 20, 10):
        remind(quiet, due - timedelta(minutes=minutes))
    assert [kind for kind, _ in events(quiet)] == ["deadline_reminder"]
    assert quiet.execute("SELECT count(*) FROM notices WHERE key LIKE '%:3h'").fetchone()[0] == 0


@pytest.mark.parametrize("changes", [
    {"submission_status": "submitted"}, {"submitted_at": "2026-09-14T00:00:00Z"}, {"excused": True},
])
def test_finished_work_gets_no_reminder(quiet, changes):
    due = utc("2026-09-15T02:00:00+08:00")
    save_snapshot(quiet, 42, "assignments", [todo(due=due.isoformat(), **changes)], AT)
    remind(quiet, due - timedelta(minutes=30))
    assert events(quiet) == []


def test_changed_due_date_re_arms_reminders(quiet):
    first = utc("2026-09-15T02:00:00+08:00")
    save_snapshot(quiet, 42, "assignments", [todo(due=first.isoformat())], AT)
    remind(quiet, first - timedelta(minutes=30))
    later = first + timedelta(days=1)
    save_snapshot(quiet, 42, "assignments", [todo(due=later.isoformat())], AT)
    remind(quiet, later - timedelta(minutes=30))
    reminders = [data["due_at"] for kind, data in events(quiet) if kind == "deadline_reminder"]
    assert reminders == [first.isoformat(), later.isoformat()]


def test_notice_and_events_commit_together(quiet):
    save_snapshot(quiet, 42, "assignments", [todo()], AT)
    quiet.execute("CREATE TRIGGER crash BEFORE INSERT ON events BEGIN SELECT RAISE(ABORT,'injected'); END")
    with pytest.raises(sqlite3.IntegrityError):
        remind(quiet, utc("2026-09-15T09:00:00+08:00"))
    assert quiet.execute("SELECT count(*) FROM notices WHERE key LIKE 'daily:%'").fetchone()[0] == 0


def test_version_one_cache_migrates_and_readers_accept_both(tmp_path):
    path = tmp_path / "cache.sqlite3"
    with open_writer(path) as db:
        configure_courses(db, MAPPING)
        save_snapshot(db, 42, "assignments", [todo()], AT)
        db.executescript("DROP TABLE notices; PRAGMA user_version=1;")
    with open_reader(path) as db:
        assert db.execute("SELECT count(*) FROM records").fetchone()[0] == 1
        assert db.execute("SELECT count(*) FROM sqlite_master WHERE name='notices'").fetchone()[0] == 0
    with open_writer(path) as db:
        assert db.execute("PRAGMA user_version").fetchone()[0] == 2
        assert db.execute("SELECT count(*) FROM records").fetchone()[0] == 1
    with open_reader(path) as db:
        assert db.execute("SELECT count(*) FROM notices").fetchone()[0] == 0


def anchor(url):
    return f'<a href="{url}">[link]</a>'


def test_formats_use_the_cron_layout_and_every_item_carries_a_short_link():
    now = utc("2026-09-14T08:00:00+08:00")
    lab = {"subject": "STDISCM", "name": "Lab 3", "due_at": "2026-09-15T15:59:00+00:00", "source_url": URL}
    digest = {"kind": "deadline_digest", "subject": None, "data": json.dumps(
        {"title": "Due this week", "empty": "", "as_of": "2026-09-13T23:30:00+00:00", "items": [lab]})}
    assert format_event(digest, now) == (
        f"{SEPARATOR}\n<b>Due this week (1)</b>\nData as of Mon 14 Sep, 07:30 AM\n\n"
        f"• in 39h  STDISCM  Lab 3 (Tue 11:59 PM) {anchor(URL)}")
    reminder = {"kind": "deadline_reminder", "subject": "STDISCM", "data": json.dumps(lab)}
    assert format_event(reminder, utc("2026-09-15T22:59:00+08:00")) == (
        f"{SEPARATOR}\n<b>Deadline reminder</b>\nin 1h  STDISCM  Lab 3 {anchor(URL)}\nDue 11:59 PM today")
    news = {"kind": "announcement_digest", "subject": None, "data": json.dumps({"title": "Latest announcements",
            "empty": "", "items": [{**post(1, "2026-09-05T00:00:00Z"), "subject": "STDISCM"}]})}
    assert format_event(news, now).splitlines()[3:] == [
        "• STDISCM  Midterm moved (Sat 05 Sep) "
        + anchor("https://dlsu.instructure.com/courses/42/discussion_topics/1")]


def test_change_alerts_escape_canvas_text_and_carry_a_short_link():
    event = {"kind": "new_assignment", "subject": "STDISCM", "data": json.dumps(
        {"name": "Q&A <draft>", "due_at": None, "source_url": URL + "?a=1&b=2"})}
    assert format_event(event).splitlines() == [
        SEPARATOR, "<b>New assignment</b>",
        f'STDISCM  Q&amp;A &lt;draft&gt; <a href="{URL}?a=1&amp;b=2">[link]</a>', "Due: no due date"]
    expired = format_event({"kind": "authentication_expired", "subject": None, "data": "{}"})
    assert expired.splitlines()[:2] == [SEPARATOR, "<b>Canvas session expired</b>"]


def test_remind_command_takes_the_writer_lock(tmp_path, capsys):
    path = tmp_path / "cache.sqlite3"
    config = tmp_path / "config"
    with open_writer(path) as db:
        configure_courses(db, MAPPING)
    args = ["--config", str(config), "--db", str(path), "remind"]
    assert canvas.main(args) == 0
    assert "queued" in json.loads(capsys.readouterr().out)
    with writer_lock(config):
        assert canvas.main(args) == 1
    assert json.loads(capsys.readouterr().err)["error"] == "busy"
