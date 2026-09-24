import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))


@pytest.fixture(autouse=True)
def _no_real_completion_state(tmp_path_factory, monkeypatch):
    """No test may read or advance the operator's completion cursors."""
    import sync_completed_tickets

    scratch = tmp_path_factory.mktemp("completions")
    monkeypatch.setattr(sync_completed_tickets, "DEFAULT_DB", scratch / "completions.sqlite3")
    monkeypatch.setattr(sync_completed_tickets, "TOWORK_JOBS", scratch / "absent.json")


@pytest.fixture(autouse=True)
def _no_real_persistence(tmp_path_factory, monkeypatch):
    """No test may read the operator's persistence policy or receipts."""
    import owned_persist

    scratch = tmp_path_factory.mktemp("persistence")
    monkeypatch.setattr(owned_persist, "CONFIG_PATH", scratch / "absent.json")
    monkeypatch.setattr(owned_persist, "DEFAULT_DB", scratch / "persistence.sqlite3")


@pytest.fixture(autouse=True)
def _no_real_vaults(tmp_path_factory, monkeypatch):
    """No test may write the operator's vaults or read their write switches."""
    import vault_notes

    scratch = tmp_path_factory.mktemp("vaults")
    monkeypatch.setattr(vault_notes, "DEFAULT_DB", scratch / "vault_notes.sqlite3")
    monkeypatch.setattr(vault_notes, "CONFIG_PATH", scratch / "absent.json")
    monkeypatch.setattr(vault_notes, "VAULTS", {
        "achimem": scratch / "achiMem", "schoolmem": scratch / "schoolMem",
    })


@pytest.fixture(autouse=True)
def _no_real_notifications(tmp_path_factory, monkeypatch):
    """No test may send to Telegram or read the operator's learning state."""
    import learning_reports
    import notify_outbox

    def refuse(*_args, **_kwargs):
        raise SystemExit("Missing TELEGRAM credentials in tests")

    scratch = tmp_path_factory.mktemp("learning")
    monkeypatch.setattr(notify_outbox, "DEFAULT_DB", scratch / "outbox.sqlite3")
    monkeypatch.setattr(
        notify_outbox.Outbox, "sender", property(lambda self: self._sender or refuse)
    )
    monkeypatch.setattr(learning_reports, "COHESION_DB", scratch / "cohesion.sqlite3")
    monkeypatch.setattr(learning_reports, "VAULTS", ())


@pytest.fixture(autouse=True)
def _no_real_agy(tmp_path_factory, monkeypatch):
    """No test may spend a real agy call."""
    import agy_classify

    monkeypatch.setattr(agy_classify, "AGY_BIN", tmp_path_factory.mktemp("agy") / "absent-agy")
