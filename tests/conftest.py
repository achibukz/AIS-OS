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
