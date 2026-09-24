import datetime as dt
import json
import sqlite3
import subprocess

import pytest

import learning_reports as reports
import notify_outbox
import semantic_review as review
import sync_completed_tickets
from notify_outbox import Outbox
from semantic_preferences import PreferenceStore

MANILA = reports.MANILA
NOW = dt.datetime(2026, 9, 24, 3, 5, tzinfo=MANILA)


def source(source_id, kind="telegram_user"):
    return {
        "id": source_id,
        "kind": kind,
        "native_id": f"chat:{source_id}",
        "revision": 1,
        "timestamp": "2026-09-23T12:00:00+08:00",
    }


def preference(**changes):
    return {
        "kind": "viewer_delivery",
        "scope": "global",
        "scope_value": "",
        "value": "viewer_link",
        "evidence": "Show me the file",
        "evidence_validated": True,
        "explicit": True,
        "exceptions": [],
        **changes,
    }


@pytest.fixture
def store(tmp_path):
    return PreferenceStore(tmp_path / "cohesion.sqlite3")


class Recorder:
    def __init__(self, *failures):
        self.failures = list(failures)
        self.sent = []

    def __call__(self, body, html=False, thread_id=None):
        if self.failures:
            raise SystemExit(self.failures.pop(0))
        self.sent.append(body)
        return 1


def test_idle_daily_run_sends_a_short_receipt_without_a_model_call(store, tmp_path):
    sender = Recorder()
    outbox = Outbox(tmp_path / "outbox.sqlite3", sender)

    calls = []
    result = review.run_review(store, runner=lambda prompt: calls.append(prompt))
    sent = reports.send_daily(result, NOW, db=store.path, outbox=outbox)

    assert calls == []
    assert sent["delivery"]["sent"] == ["learning-daily:2026-09-24"]
    assert sender.sent == [
        "-" * 33 + "\nLearning receipt, Sep 24\n\nNo new learning. No model call.\n\n"
        "learning-daily:2026-09-24"
    ]


def test_daily_receipt_separates_learned_from_pending(store):
    store.record(source("m1"), preference())
    store.record(source("m2"), preference(kind="placement", value="tasks", scope="ambiguous",
                                          evidence="put it in tasks"))
    store.record(source("m3"), preference(kind="placement", value="both", explicit=False,
                                          scope="category", scope_value="school_deadline",
                                          evidence="school deadlines in both"))
    data = reports.daily_data({"status": "pending", "calls": 1, "rejected": 2, "pending": 1},
                              dt.datetime.now(dt.UTC), db=store.path)

    text = reports.render_daily(data)

    assert "Accepted 1 · Updated 0 · Revoked 0" in text
    assert "Rejected 2 · Awaiting review 1" in text
    assert "Model calls 1 of 24" in text
    assert "Needs you:" in text and '("put it in tasks")' in text
    assert "No new learning" not in text


def test_a_rerun_or_restart_catch_up_sends_one_daily_receipt(store, tmp_path):
    sender = Recorder()
    outbox = Outbox(tmp_path / "outbox.sqlite3", sender)
    idle = {"status": "idle", "calls": 0}

    first = reports.send_daily(idle, NOW, db=store.path, outbox=outbox)
    second = reports.send_daily(idle, NOW + dt.timedelta(hours=2), db=store.path,
                                outbox=Outbox(tmp_path / "outbox.sqlite3", sender))

    assert first["queued"] is True and second["queued"] is False
    assert len(sender.sent) == 1


def test_outage_retries_with_backoff_and_survives_restart(tmp_path):
    sender = Recorder("Telegram send failed after 4 attempts. ConnectionError")
    path = tmp_path / "outbox.sqlite3"
    Outbox(path, sender).enqueue("learning-daily:2026-09-24", "body", now=NOW)

    first = Outbox(path, sender).deliver(NOW)
    early = Outbox(path, sender).deliver(NOW + dt.timedelta(minutes=1))
    later = Outbox(path, sender).deliver(NOW + dt.timedelta(minutes=6))

    assert first["retrying"] == ["learning-daily:2026-09-24"]
    assert early == {"sent": [], "retrying": [], "failed": []}
    assert later["sent"] == ["learning-daily:2026-09-24"]
    assert sender.sent == ["body"]


def test_permanent_rejection_stops_retrying(tmp_path):
    sender = Recorder("Telegram rejected the message: 400 chat not found")
    outbox = Outbox(tmp_path / "outbox.sqlite3", sender)
    outbox.enqueue("learning-weekly:2026-09-20", "body", now=NOW)

    first = outbox.deliver(NOW)
    again = outbox.deliver(NOW + dt.timedelta(days=1))

    assert first["failed"] == ["learning-weekly:2026-09-20"]
    assert again == {"sent": [], "retrying": [], "failed": []}
    assert outbox.health(NOW)["recent_failures"][0]["error"].startswith("Telegram rejected")


def test_retries_are_bounded(tmp_path):
    sender = Recorder(*["Telegram send failed after 4 attempts."] * 20)
    outbox = Outbox(tmp_path / "outbox.sqlite3", sender)
    outbox.enqueue("id", "body", now=NOW)

    moment = NOW
    for _ in range(notify_outbox.MAX_ATTEMPTS + 3):
        outbox.deliver(moment)
        moment += notify_outbox.MAX_BACKOFF

    assert outbox.health(moment)["counts"] == {"failed": 1}
    assert len(sender.failures) == 20 - notify_outbox.MAX_ATTEMPTS


def test_uncertain_send_is_retried_and_a_sent_message_never_repeats(tmp_path):
    sender = Recorder()
    path = tmp_path / "outbox.sqlite3"
    Outbox(path, sender).enqueue("uncertain", "body", now=NOW)
    Outbox(path, sender).enqueue("done", "sent body", now=NOW)
    with sqlite3.connect(path) as connection:
        connection.execute("UPDATE messages SET state='sending' WHERE message_id='uncertain'")
        connection.execute("UPDATE messages SET state='sent' WHERE message_id='done'")

    result = Outbox(path, sender).deliver(NOW)

    assert result["sent"] == ["uncertain"]
    assert sender.sent == ["body"]


@pytest.mark.parametrize("moment, end", [
    (dt.datetime(2026, 9, 20, 19, 59, tzinfo=MANILA), "2026-09-13"),
    (dt.datetime(2026, 9, 20, 20, 0, tzinfo=MANILA), "2026-09-20"),
    (dt.datetime(2026, 9, 22, 9, 0, tzinfo=MANILA), "2026-09-20"),
    (dt.datetime(2026, 9, 20, 12, 30, tzinfo=dt.UTC), "2026-09-20"),
])
def test_weekly_window_follows_sunday_20_manila(moment, end):
    start, finish = reports.week_window(moment)

    assert finish.date().isoformat() == end
    assert finish - start == dt.timedelta(days=7)
    assert reports.weekly_id(finish) == f"learning-weekly:{end}"


def test_zero_learning_week_is_a_valid_report(store):
    data = reports.weekly_data(dt.datetime(2026, 9, 21, 9, 0, tzinfo=MANILA), db=store.path)

    text = reports.render_weekly(data)

    assert "Learning week, Sep 13 to Sep 20" in text
    assert "No verified learning this week." in text
    assert "Deployed and live-verified: not tracked" in text
    assert text.endswith("learning-weekly:2026-09-20")


def test_weekly_report_cites_learning_reuse_tickets_and_pain_points(store, tmp_path, monkeypatch):
    week_now = dt.datetime.now(dt.UTC) + dt.timedelta(days=8)
    store.record(source("m1"), preference(kind="placement", value="tasks", scope="category",
                                          scope_value="quick_task", evidence="quick stuff in tasks"))
    learned = store.effective("placement", category="quick_task")
    store.record_use(learned, "telegram:9:r1")
    store.record_use(learned, "telegram:9:r1")
    store.record_use(learned, "telegram:10:r1")
    store.record(source("m2"), preference(evidence_validated=False))

    completions = tmp_path / "completions.sqlite3"
    tracker = sync_completed_tickets.Store(completions)
    at = dt.datetime.now(dt.UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
    for kind, number, outcome in (("issue", 225, "completed"), ("pull", 232, "merged")):
        tracker.record(sync_completed_tickets.WorkItem(
            key=sync_completed_tickets.item_key("achibukz/achiCore", kind, number),
            repo="achibukz/achiCore", kind=kind, number=number, title="t", url="u",
            outcome=outcome, at=at), dt.datetime.now(dt.UTC))
    tracker.conflict("k", "ambiguous_task_match", "", dt.datetime.now(dt.UTC))
    tracker.close()
    monkeypatch.setattr(sync_completed_tickets, "DEFAULT_DB", completions)
    monkeypatch.setattr(reports, "week_window",
                        lambda now: (dt.datetime.now(dt.UTC) - dt.timedelta(days=1), week_now))

    data = reports.weekly_data(week_now, db=store.path)
    text = reports.render_weekly(data)

    assert data["states"]["captured"] == 2 and data["states"]["accepted"] == 1
    assert data["states"]["applied"] == 2
    assert 'Learned: placement=tasks (quick_task) from "quick stuff in tasks"' in text
    assert "Reused: placement=tasks (quick_task) x2" in text
    assert "Pain points: completion ambiguous_task_match x1" in text
    assert "Closed: achiCore #225 · Merged: achiCore PR #232" in text


def test_cohesion_records_a_use_when_a_learned_placement_decides_a_write(tmp_path):
    import cohesion
    from test_cohesion import FakeCalendar, write_calendars

    tasks = tmp_path / "tasks.md"
    tasks.write_text("# Tasks\n\n## Active\n\n## Blocked\n\n## Done\n", encoding="utf-8")
    calendars = tmp_path / "calendars.json"
    write_calendars(calendars)
    service = cohesion.CohesionService(db_path=tmp_path / "c.sqlite3", tasks_path=tasks,
                                       calendar=FakeCalendar(), calendars_path=calendars)
    service.semantic_preferences.record(source("m1"), preference(
        kind="placement", value="tasks", scope="category", scope_value="quick_task",
        evidence="quick stuff in tasks"))
    request = {"version": 1, "source": {**source("telegram:1:r1"), "kind": "telegram_message",
                                        "timestamp": "2026-09-24T08:00:00+08:00"},
               "intent": {"action": "upsert", "category": "quick_task", "title": "Buy milk",
                          "area": "personal"}}

    service.submit(request)
    service.submit(request)

    with sqlite3.connect(tmp_path / "c.sqlite3") as connection:
        assert connection.execute("SELECT count(*) FROM semantic_preference_uses").fetchone()[0] == 1


def test_health_reports_queue_budget_auth_persistence_delivery_and_dirty_vault(store, tmp_path):
    vault = tmp_path / "vault"
    remote = tmp_path / "vault.git"
    subprocess.run(["git", "init", "-q", "--bare", "-b", "main", str(remote)], check=True)
    subprocess.run(["git", "clone", "-q", str(remote), str(vault)], check=True, capture_output=True)
    (vault / "note.md").write_text("x\n", encoding="utf-8")
    subprocess.run(["git", "-C", str(vault), "-c", "user.name=t", "-c", "user.email=t@t",
                    "commit", "-q", "--allow-empty", "-m", "init"], check=True)
    subprocess.run(["git", "-C", str(vault), "push", "-q", "-u", "origin", "HEAD:main"],
                   check=True, capture_output=True)
    subprocess.run(["git", "-C", str(vault), "branch", "-q", "-u", "origin/main"], check=True)
    store.record(source("m1"), preference(explicit=False))
    outbox = Outbox(tmp_path / "outbox.sqlite3", Recorder())
    outbox.enqueue("waiting", "body", now=NOW)

    result = reports.health(NOW + dt.timedelta(minutes=10), db=store.path, outbox=outbox,
                            vaults=[vault])

    assert result["review_queue"]["pending"] == 1
    assert result["budget"] == {"manila_day": "2026-09-24", "used": 0, "failed": 0, "limit": 24}
    assert result["auth"] == {"gemini_key_configured": False}
    assert result["delivery"]["oldest_pending_seconds"] == 600
    assert result["vaults"][0]["dirty_files"] == 1
    assert result["vaults"][0]["ahead"] == 0
    json.dumps(result)


def test_review_main_queues_its_receipt_and_keeps_its_own_exit(monkeypatch, tmp_path):
    queued = []
    monkeypatch.setattr(review, "run_review", lambda store: {"status": "idle", "calls": 0})
    monkeypatch.setattr(reports, "send_daily", lambda report, db=None: queued.append(dict(report)) or {})

    assert review.main(["--db", str(tmp_path / "c.sqlite3")]) == 0
    assert queued == [{"status": "idle", "calls": 0}]
