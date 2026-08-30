from pathlib import Path

SCRIPT = Path(__file__).resolve().parent.parent / "scripts" / "vault_inbox_sync.py"


class TestNoCorrectionHarvesting:
    """The v1 harvester read the tgdb notes this script writes, and those are built
    from agy's brain log, which stores the prompt with MEMORY.md prepended — so it
    ingested its own output and re-prefixed it every pass. Removed 2026-08-20.

    These pin the removal. Learning belongs to the turn-triggered loop in
    achiAgy/src/background_review.py, which sources candidates from the raw prompt
    where injected memory cannot reach them.
    """

    def test_does_not_import_the_harvester(self):
        source = SCRIPT.read_text(encoding="utf-8")
        assert "from extract_corrections import" not in source
        assert "import extract_corrections" not in source

    def test_does_not_call_harvesting_functions(self):
        source = SCRIPT.read_text(encoding="utf-8")
        assert "scan_vault_tgdb(" not in source
        assert "apply_corrections(" not in source

    def test_tgdb_export_and_sync_are_paused(self):
        source = SCRIPT.read_text(encoding="utf-8")
        assert "export_recent_sessions" not in source
        assert '"watch_dirs": ["inbox", "tgdb"]' not in source
        assert "check_and_sync_vault" in source
