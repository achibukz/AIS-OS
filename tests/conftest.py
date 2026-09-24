import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))


@pytest.fixture(autouse=True)
def _no_real_persistence(tmp_path_factory, monkeypatch):
    """No test may read the operator's persistence policy or receipts."""
    import owned_persist

    scratch = tmp_path_factory.mktemp("persistence")
    monkeypatch.setattr(owned_persist, "CONFIG_PATH", scratch / "absent.json")
    monkeypatch.setattr(owned_persist, "DEFAULT_DB", scratch / "persistence.sqlite3")
