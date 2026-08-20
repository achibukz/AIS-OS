import json
from pathlib import Path

import pytest

import learning_ledger as ll


@pytest.fixture
def ledger(tmp_path):
    return tmp_path / "ledger.jsonl"


class TestAppendAndRead:
    def test_append_returns_an_id_and_record_is_pending(self, ledger):
        rid = ll.append_candidate(914, "never use leverage", 3, path=ledger)
        assert rid
        (c,) = ll.pending(914, path=ledger)
        assert c.record_id == rid
        assert c.raw == "never use leverage"
        assert c.turn_index == 3

    def test_pending_is_scoped_to_the_chat(self, ledger):
        ll.append_candidate(914, "a", 1, path=ledger)
        ll.append_candidate(915, "b", 1, path=ledger)
        assert [c.raw for c in ll.pending(914, path=ledger)] == ["a"]

    def test_pending_respects_the_limit(self, ledger):
        for i in range(30):
            ll.append_candidate(914, f"line {i}", i, path=ledger)
        assert len(ll.pending(914, limit=25, path=ledger)) == 25

    def test_missing_file_yields_no_pending(self, ledger):
        assert ll.pending(914, path=ledger) == []


class TestStateTransitions:
    def test_written_record_is_no_longer_pending(self, ledger):
        rid = ll.append_candidate(914, "never use leverage", 1, path=ledger)
        ll.mark_written(rid, "Never use 'leverage'.", "add", "memory", path=ledger)
        assert ll.pending(914, path=ledger) == []

    def test_rejected_record_is_no_longer_pending(self, ledger):
        rid = ll.append_candidate(914, "buy milk", 1, path=ledger)
        ll.mark_rejected(rid, "one_off", path=ledger)
        assert ll.pending(914, path=ledger) == []

    def test_transitions_append_rather_than_mutate(self, ledger):
        rid = ll.append_candidate(914, "x", 1, path=ledger)
        ll.mark_written(rid, "X.", "add", "memory", path=ledger)
        lines = ledger.read_text().strip().splitlines()
        assert len(lines) == 2
        assert json.loads(lines[0])["state"] == "pending"
        assert json.loads(lines[1])["state"] == "written"

    def test_latest_record_wins_on_read(self, ledger):
        rid = ll.append_candidate(914, "x", 1, path=ledger)
        ll.mark_rejected(rid, "one_off", path=ledger)
        ll.mark_written(rid, "X.", "add", "memory", path=ledger)
        assert ll.latest(rid, path=ledger)["state"] == "written"


class TestStats:
    def test_writes_today_counts_only_written_records(self, ledger):
        a = ll.append_candidate(914, "a", 1, path=ledger)
        b = ll.append_candidate(914, "b", 2, path=ledger)
        ll.mark_written(a, "A.", "add", "memory", path=ledger)
        ll.mark_rejected(b, "one_off", path=ledger)
        assert ll.writes_today(path=ledger) == 1

    def test_writes_today_uses_the_manila_date_not_the_system_date(self, ledger):
        """The box runs UTC and records are stamped Asia/Manila. If this uses
        date.today() the cap silently reads zero for eight hours a day."""
        from datetime import datetime
        from zoneinfo import ZoneInfo
        rid = ll.append_candidate(914, "a", 1, path=ledger)
        ll.mark_written(rid, "A.", "add", "memory", path=ledger)
        stamped = ll.latest(rid, path=ledger)["ts"]
        manila_today = datetime.now(ZoneInfo("Asia/Manila")).date().isoformat()
        assert stamped.startswith(manila_today)
        assert ll.writes_today(path=ledger) == 1

    def test_stats_counts_by_state(self, ledger):
        a = ll.append_candidate(914, "a", 1, path=ledger)
        b = ll.append_candidate(914, "b", 2, path=ledger)
        ll.mark_written(a, "A.", "add", "memory", path=ledger)
        ll.mark_rejected(b, "one_off", path=ledger)
        s = ll.stats(path=ledger)
        assert s["written"] == 1
        assert s["rejected"] == 1
