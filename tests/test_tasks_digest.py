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


def test_tasks_digest_accepts_all_and_backlog(monkeypatch, tmp_path, capsys):
    register = tmp_path / "tasks.md"
    register.write_text(
        "## Active\n- [ ] Deploy service #systems !high\n## Backlog\n- [ ] Future feature #projects !low\n",
        encoding="utf-8",
    )
    calls = []
    monkeypatch.setattr(tasks_digest, "TASKS_FILE", register)
    monkeypatch.setattr(tasks_digest, "send", lambda message: calls.append(message))

    assert "all" in tasks_digest.FILTER_AREAS
    assert "backlog" in tasks_digest.FILTER_AREAS

    assert tasks_digest.main(["--dry-run", "--area", "all"]) == 0
    out_all = capsys.readouterr().out
    assert "Deploy service" in out_all
    assert "Future feature" not in out_all

    assert tasks_digest.main(["--dry-run", "--area", "backlog"]) == 0
    out_backlog = capsys.readouterr().out
    assert "Future feature" in out_backlog
    assert "Deploy service" not in out_backlog
    assert calls == []

