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
