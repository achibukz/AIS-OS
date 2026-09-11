import importlib
import sys

import tasks_digest


def test_importing_digest_does_not_send(monkeypatch):
    calls = []
    monkeypatch.setattr("telegram_notify.send", lambda message: calls.append(message))
    sys.modules.pop("tasks_digest", None)

    importlib.import_module("tasks_digest")

    assert calls == []


def test_dry_run_filters_by_area_without_sending(monkeypatch, tmp_path, capsys):
    register = tmp_path / "tasks.md"
    register.write_text(
        "## Active\n- [ ] Class work #school\n- [ ] Deploy service #systems\n",
        encoding="utf-8",
    )
    calls = []
    monkeypatch.setattr(tasks_digest, "TASKS_FILE", register)
    monkeypatch.setattr(tasks_digest, "send", lambda message: calls.append(message))

    assert tasks_digest.main(["--dry-run", "--area", "school"]) == 0

    output = capsys.readouterr().out
    assert "Class work" in output
    assert "Deploy service" not in output
    assert calls == []
