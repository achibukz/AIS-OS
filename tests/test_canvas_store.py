import json
import sqlite3
import subprocess
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from canvas_client import CanvasError
from canvas_store import (configure_courses, open_reader, open_writer, project_record, query,
                          save_auth, save_failure, save_snapshot)
from canvas_sync import sync

AT = "2026-09-08T10:00:00+00:00"
NOW = datetime.fromisoformat(AT)
MAPPING = {"term": "AY2627-T1", "user_id": 7, "subjects": [
    {"course_id": 42, "code": "STDISCM", "section": "S03"}]}


@pytest.fixture
def db(tmp_path):
    with open_writer(tmp_path / "private/cache.sqlite3") as db:
        configure_courses(db, MAPPING)
        yield db


def assignment(item_id=1, due="2026-09-08T00:00:00Z", **changes):
    return {"id": item_id, "name": "Lab", "due_at": due, "description": "notes",
            "submission_status": "submitted", "submitted_at": "2026-09-07T00:00:00Z",
            "excused": False, "grade": None, "score": None, "points_possible": 10,
            "source_url": "https://dlsu.instructure.com/courses/42/assignments/1", **changes}


def test_failure_preserves_snapshot_and_per_category_freshness(db):
    save_snapshot(db, 42, "assignments", [assignment()], AT)
    save_failure(db, 42, "assignments", "permission_denied", "2026-09-08T11:00:00+00:00")
    result = query(db, "due", now=NOW)
    assert len(result["data"]) == 1
    assert result["coverage"][0]["success_at"] == AT
    assert result["coverage"][0]["coverage"] == "saved_after_failure"
    grades = query(db, "grades", now=NOW)
    assert next(c for c in grades["coverage"] if c["category"] == "grades")["success_at"] is None
    assert "incomplete_coverage" in result["warnings"]


def test_empty_is_complete_but_unavailable_is_not(db):
    assert query(db, "assignments", now=NOW)["coverage"][0]["coverage"] == "unavailable"
    save_snapshot(db, 42, "assignments", [], AT)
    result = query(db, "assignments", now=NOW)
    assert result["data"] == []
    assert result["coverage"][0]["coverage"] == "complete"
    assert result["warnings"] == []


def test_week_is_manila_monday_with_exclusive_end_and_submitted_items(db):
    rows = [assignment(1, "2026-09-06T15:59:59Z"), assignment(2, "2026-09-06T16:00:00Z"),
            assignment(3, "2026-09-13T15:59:59Z"), assignment(4, "2026-09-13T16:00:00Z"),
            assignment(5, None)]
    save_snapshot(db, 42, "assignments", rows, AT)
    assert [r["id"] for r in query(db, "due", now=NOW)["data"]] == [2, 3]
    assert [r["id"] for r in query(db, "due", now=NOW, period="next-seven-days")["data"]] == [3, 4]
    assert query(db, "due", now=NOW, unfinished=True)["data"] == []


def test_auth_restoration_does_not_refresh_saved_facts(db):
    save_snapshot(db, 42, "assignments", [assignment()], AT)
    save_auth(db, "expired", AT)
    assert "authentication_expired" in query(db, "due", now=NOW)["warnings"]
    save_auth(db, "valid", (NOW + timedelta(hours=5)).isoformat())
    result = query(db, "due", now=NOW + timedelta(hours=5))
    assert "authentication_expired" not in result["warnings"]
    assert "stale_data" in result["warnings"]
    assert result["coverage"][0]["success_at"] == AT
    assert "stale_data" not in query(db, "due", now=NOW + timedelta(hours=4))["warnings"]


def test_repeat_upsert_removal_and_transaction_rollback(db):
    save_snapshot(db, 42, "assignments", [assignment(), assignment(2)], AT)
    save_snapshot(db, 42, "assignments", [assignment()], AT)
    assert len(query(db, "assignments", now=NOW)["data"]) == 1
    db.execute("""CREATE TRIGGER fail_insert BEFORE INSERT ON records WHEN NEW.id=3
                  BEGIN SELECT RAISE(ABORT,'injected crash'); END""")
    with pytest.raises(sqlite3.IntegrityError):
        save_snapshot(db, 42, "assignments", [assignment(2), assignment(3)], AT)
    assert [r["id"] for r in query(db, "assignments", now=NOW)["data"]] == [1]


def test_read_only_open_does_not_create_database_or_sidecars(tmp_path):
    path = tmp_path / "missing.sqlite3"
    with pytest.raises(sqlite3.OperationalError):
        with open_reader(path):
            pytest.fail("created missing database")
    assert not path.exists()
    with open_writer(path) as db:
        configure_courses(db, MAPPING)
        save_snapshot(db, 42, "assignments", [assignment()], AT)
    before = {p.name: p.read_bytes() for p in tmp_path.iterdir()}
    with open_reader(path) as db:
        assert len(query(db, "assignments", now=NOW)["data"]) == 1
        with pytest.raises(sqlite3.OperationalError):
            db.execute("DELETE FROM records")
    assert {p.name: p.read_bytes() for p in tmp_path.iterdir()} == before


def test_queries_under_actual_achicore_write_boundary(tmp_path):
    boundary = Path(__file__).resolve().parents[2] / "achiCore/src/write_boundary.py"
    assert boundary.is_file(), "achiCore sibling is required for the boundary acceptance test"
    path = tmp_path / "protected/cache.sqlite3"
    with open_writer(path) as db:
        configure_courses(db, MAPPING)
        save_snapshot(db, 42, "assignments", [assignment()], AT)
    scripts = Path(__file__).resolve().parents[1] / "scripts"
    program = """
import json, sys
from pathlib import Path
sys.path.insert(0, sys.argv[1])
from canvas_store import open_reader, query
path = Path(sys.argv[2])
try:
    (path.parent / 'forbidden').write_text('must fail')
except PermissionError:
    pass
else:
    raise AssertionError('write boundary did not deny writes')
with open_reader(path) as db:
    assert len(query(db, 'assignments')['data']) == 1
print('read-only query passed behind enforced boundary')
"""
    result = subprocess.run([sys.executable, str(boundary), "--protect", str(path.parent), "--",
                             sys.executable, "-c", program, str(scripts), str(path)],
                            capture_output=True, text=True, timeout=30)
    assert result.returncode == 0, result.stderr
    assert "passed behind enforced boundary" in result.stdout
    assert list(path.parent.iterdir()) == [path]


def test_projection_uses_effective_due_date_and_only_personal_submission():
    raw = {"id": 1, "name": "Lab", "due_at": "2026-09-09T00:00:00Z", "description": '<a href="https://secret?token=x">Read</a>',
           "submission": {"user_id": 7, "workflow_state": "unsubmitted", "grade": None, "score": None}}
    item = project_record("assignments", raw, 42, 7)
    assert item["due_at"] == "2026-09-09T00:00:00+00:00"
    assert item["grade"] is None and item["score"] is None
    assert "secret" not in json.dumps(item)
    with pytest.raises(CanvasError, match="submission_unavailable"):
        project_record("assignments", raw, 42, 8)
    raw["due_at"] = "September 9"
    with pytest.raises(CanvasError, match="malformed_timestamp"):
        project_record("assignments", raw, 42, 7)


class FakeClient:
    def get(self, path):
        return ({"id": 7} if "profile" in path else {"id": 42, "name": "Distributed Computing"}), None

    def list(self, path):
        if "assignments" in path:
            return [{"id": 1, "name": "Lab", "due_at": None,
                     "submission": {"user_id": 7, "workflow_state": "unsubmitted"}}]
        if "enrollments" in path:
            raise CanvasError("permission_denied")
        return []


def test_sync_advances_only_complete_categories(db):
    result = sync(FakeClient(), db, MAPPING)
    assert result["complete_categories"] == 3
    assert result["failures"] == [{"subject": "STDISCM", "category": "grades", "error": "permission_denied"}]
    coverage = query(db, "status")["coverage"]
    assert next(c for c in coverage if c["category"] == "grades")["baseline"] == 0
    assert next(c for c in coverage if c["category"] == "announcements")["baseline"] == 1


def test_auth_expiry_preserves_all_categories(db):
    sync(FakeClient(), db, MAPPING)
    class Expired(FakeClient):
        def get(self, path):
            raise CanvasError("authentication_expired")
    assert sync(Expired(), db, MAPPING)["error"] == "authentication_expired"
    result = query(db, "assignments")
    assert len(result["data"]) == 1
    assert "authentication_expired" in result["warnings"]
