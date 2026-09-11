import json
from pathlib import Path

import pytest

import canvas
import canvas_scheduled
from canvas_client import writer_lock
from canvas_events import deliver as real_deliver
from canvas_store import open_reader
from test_canvas_cli import online  # noqa: F401

SYSTEMD = Path(__file__).resolve().parent.parent / "systemd"


@pytest.fixture
def sent(monkeypatch):
    messages = []
    sender = {"fail": False}
    def send(message):
        if sender["fail"]:
            raise SystemExit(1)
        messages.append(message)
        return 1
    monkeypatch.setattr(canvas, "deliver", lambda db: real_deliver(db, sender=send))
    return messages, sender


def scheduled(args, capsys):
    code = canvas_scheduled.main(args)
    return code, json.loads(capsys.readouterr().out.strip().splitlines()[-1])


def test_first_sync_is_a_silent_baseline_and_an_unchanged_sync_sends_nothing(online, sent, capsys):
    Client, config, db, args = online
    assert canvas.main(args + ["map"]) == 0
    capsys.readouterr()
    for _ in range(2):
        code, report = scheduled(args, capsys)
        assert code == 0
        assert report["sync"] == {"complete_categories": 4, "failures": []}
        assert report["delivery"] == {"sent": 0, "remaining": 0}
    assert sent[0] == []


def test_expired_session_still_delivers_the_expiry_notice_and_is_not_a_fault(online, sent, capsys):
    Client, config, db, args = online
    assert canvas.main(args + ["map"]) == 0
    capsys.readouterr()
    Client.error = "authentication_expired"
    code, report = scheduled(args, capsys)
    assert code == 0
    assert report["sync"]["error"] == "authentication_expired"
    assert report["delivery"]["sent"] == 1
    assert "Canvas session expired" in sent[0][0]
    code, report = scheduled(args, capsys)
    assert code == 0 and report["delivery"]["sent"] == 0


def test_partial_category_failure_is_reported_without_a_fault(online, sent, capsys, monkeypatch):
    Client, config, db, args = online
    assert canvas.main(args + ["map"]) == 0
    capsys.readouterr()
    original = Client.list
    def flaky(self, path):
        if "enrollments" in path:
            from canvas_client import CanvasError
            raise CanvasError("transient_failure")
        return original(self, path)
    monkeypatch.setattr(Client, "list", flaky)
    code, report = scheduled(args, capsys)
    assert code == 0
    assert report["sync"]["failures"] == [
        {"subject": "STDISCM", "category": "grades", "error": "transient_failure"}]
    assert "delivery" in report


def test_unconfirmed_delivery_is_retried_on_the_next_run(online, sent, capsys):
    Client, config, db, args = online
    messages, sender = sent
    assert canvas.main(args + ["map"]) == 0
    capsys.readouterr()
    Client.error = "authentication_expired"
    sender["fail"] = True
    code, report = scheduled(args, capsys)
    assert code == 0 and report["delivery"]["error"] == "delivery_unconfirmed"
    assert messages == []
    sender["fail"] = False
    code, report = scheduled(args, capsys)
    assert code == 0 and report["delivery"] == {"sent": 1, "remaining": 0}
    with open_reader(db) as connection:
        assert connection.execute("SELECT state FROM events").fetchall()[0][0] == "sent"


def test_a_held_writer_lock_skips_the_run_without_a_fault(online, sent, capsys):
    Client, config, db, args = online
    assert canvas.main(args + ["map"]) == 0
    capsys.readouterr()
    with writer_lock(config):
        code, report = scheduled(args, capsys)
    assert code == 0
    assert report["sync"]["error"] == "busy"
    assert "delivery" not in report


def test_missing_mapping_is_a_local_fault(online, sent, capsys):
    Client, config, db, args = online
    code, report = scheduled(args, capsys)
    assert code == 1
    assert report["sync"]["error"] == "invalid_or_unavailable_local_data"


def unit(name):
    sections = {}
    current = None
    for line in (SYSTEMD / name).read_text().splitlines():
        if line.startswith("["):
            current = sections.setdefault(line.strip("[]"), [])
        elif "=" in line:
            current.append(tuple(line.split("=", 1)))
    return sections


def test_timer_fires_every_thirty_minutes_and_catches_up_once():
    timer = dict(unit("achios-canvas-sync.timer")["Timer"])
    assert timer["OnCalendar"] == "*:0/30"
    assert timer["Persistent"] == "true"


def test_service_is_a_bounded_private_oneshot_without_restart_loops():
    service = unit("achios-canvas-sync.service")
    body = dict(service["Service"])
    assert body["Type"] == "oneshot"
    assert body["TimeoutStartSec"] == "10min"
    assert body["UMask"] == "0077"
    assert "Restart" not in body
    assert body["ExecStart"].endswith("@REPO@/scripts/canvas_scheduled.py")
    assert dict(service["Unit"])["OnFailure"] == "achios-failure-alert@%n.service"
