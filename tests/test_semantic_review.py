import datetime as dt
import json
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pytest

import semantic_review as review
from semantic_preferences import PreferenceStore


def source(source_id="message:1:r1", kind="telegram_user"):
    return {
        "id": source_id,
        "kind": kind,
        "native_id": "chat:1:message:1",
        "revision": 1,
        "timestamp": "2026-09-21T12:00:00+08:00",
    }


def candidate(store, source_id="message:1:r1", **changes):
    payload = {
        "kind": "viewer_delivery",
        "scope": "global",
        "scope_value": "",
        "value": "viewer_link",
        "evidence": "Show me the file",
        "evidence_validated": True,
        "explicit": False,
        "exceptions": ["Paste when I explicitly ask for contents"],
        **changes,
    }
    return store.record(source(source_id), payload)


@pytest.fixture
def store(tmp_path: Path):
    return PreferenceStore(tmp_path / "cohesion.sqlite3")


def test_idle_review_makes_zero_model_calls(store):
    calls = []

    report = review.run_review(store, runner=lambda prompt: calls.append(prompt))

    assert report["status"] == "idle" and report["calls"] == 0
    assert calls == []


def test_daily_review_activates_validated_evidence_and_updates_checkpoint(store):
    receipt = candidate(store)

    report = review.run_review(
        store,
        runner=lambda _prompt: {
            "decisions": [
                {"event_id": receipt["event_id"], "verdict": "activate", "reason": "explicit"}
            ]
        },
    )

    assert report["activated"] == 1 and report["pending"] == 0
    assert store.effective("viewer_delivery")["value"] == "viewer_link"
    with store._connect() as connection:
        checkpoint = connection.execute(
            "SELECT checkpoint FROM semantic_review_state WHERE singleton=1"
        ).fetchone()[0]
    assert checkpoint == 1


def test_pending_decision_replays_after_restart_even_past_checkpoint(store):
    receipt = candidate(store)
    pending = {
        "decisions": [
            {"event_id": receipt["event_id"], "verdict": "pending", "reason": "unclear scope"}
        ]
    }
    first = review.run_review(store, runner=lambda _prompt: pending)
    second_calls = []
    second = review.run_review(
        PreferenceStore(store.path),
        runner=lambda _prompt: second_calls.append(1) or pending,
    )

    assert first["pending"] == 1 and second["pending"] == 1
    assert second_calls == [1]


@pytest.mark.parametrize(
    "changes", [{"evidence_validated": False}, {"scope": "ambiguous"}]
)
def test_events_the_classifier_cannot_activate_are_never_sent(store, changes):
    receipt = candidate(store, **changes)
    calls = []

    report = review.run_review(
        store,
        runner=lambda _prompt: calls.append(1)
        or {
            "decisions": [
                {"event_id": receipt["event_id"], "verdict": "activate", "reason": "claimed"}
            ]
        },
    )

    assert report["status"] == "idle" and calls == []
    assert store.effective("viewer_delivery") is None


@pytest.mark.parametrize(
    "report, status",
    [
        ({"status": "pending", "pending": 1}, 0),
        ({"status": "pending", "error": "GEMINI_API_KEY is unavailable"}, 1),
    ],
)
def test_only_an_error_fails_the_unit(monkeypatch, tmp_path, report, status):
    monkeypatch.setattr(review, "run_review", lambda _store: report)

    assert review.main(["--db", str(tmp_path / "cohesion.sqlite3")]) == status


def test_failed_review_retries_once_and_leaves_the_event_pending(store):
    candidate(store)
    calls = []

    def unavailable(_prompt):
        calls.append(1)
        raise review.ReviewUnavailable("offline")

    report = review.run_review(store, runner=unavailable)

    assert calls == [1, 1]
    assert report["calls"] == 2 and report["pending"] == 1
    assert report["error"] == "offline"


def test_manila_midnight_starts_a_new_atomic_call_budget(store):
    candidate(store)
    before_midnight = dt.datetime(2026, 9, 21, 15, 59, tzinfo=dt.UTC)
    after_midnight = dt.datetime(2026, 9, 21, 16, 1, tzinfo=dt.UTC)
    with store._connect() as connection:
        for index in range(review.MAX_CALLS_PER_DAY):
            connection.execute(
                "INSERT INTO semantic_review_calls VALUES(?,?,?,?)",
                (f"old-{index}", "2026-09-21", before_midnight.isoformat(), "failed"),
            )

    blocked = review.run_review(store, runner=lambda _prompt: {}, now=before_midnight)
    allowed = review.run_review(
        store,
        runner=lambda _prompt: {"decisions": []},
        now=after_midnight,
    )

    assert blocked["calls"] == 0 and "budget exhausted" in blocked["error"]
    assert allowed["calls"] == 1


def test_direct_gemini_transport_declares_no_tools_and_bounds_output():
    captured = {}

    class Response:
        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return False

        def read(self):
            result = json.dumps({"decisions": []})
            return json.dumps(
                {"candidates": [{"content": {"parts": [{"text": result}]}}]}
            ).encode()

    def opener(request, timeout):
        captured["url"] = request.full_url
        captured["body"] = json.loads(request.data)
        captured["timeout"] = timeout
        return Response()

    result = review.GeminiInference(api_key="test-key", opener=opener)("classify")

    assert result == {"decisions": []}
    assert captured["url"].endswith("/models/gemini-3.8-flash:generateContent")
    assert captured["body"]["generationConfig"]["thinkingConfig"] == {"thinkingLevel": "high"}
    assert "tools" not in captured["body"]
    assert captured["body"]["generationConfig"]["maxOutputTokens"] == 1000
    assert captured["timeout"] == 90


def test_prompt_refuses_more_than_the_input_budget(store):
    event = {
        "event_id": "one",
        "source_kind": "telegram_user",
        "evidence": "x" * review.MAX_INPUT_BYTES,
        "kind": "viewer_delivery",
        "scope_type": "global",
        "scope_value": "",
        "value": "viewer_link",
        "exceptions_json": "[]",
    }
    with pytest.raises(review.ReviewUnavailable, match="6000-token"):
        review.build_prompt([event])


def test_call_budget_reservation_is_atomic_under_race(store):
    now = dt.datetime(2026, 9, 21, 12, tzinfo=dt.UTC)
    with ThreadPoolExecutor(max_workers=12) as pool:
        reservations = list(
            pool.map(lambda _index: review._reserve_call(store.path, now), range(40))
        )

    assert sum(call_id is not None for call_id in reservations) == review.MAX_CALLS_PER_DAY


def test_only_one_classifier_lock_can_be_held(store):
    with review._single_reviewer(store.path):
        with pytest.raises(review.ReviewUnavailable, match="already running"):
            with review._single_reviewer(store.path):
                pass


def test_timer_is_persistent_and_uses_manila_time():
    timer = (
        Path(__file__).resolve().parents[1]
        / "systemd"
        / "achios-semantic-review.timer"
    ).read_text(encoding="utf-8")
    assert "OnCalendar=03:00 Asia/Manila" in timer
    assert "Persistent=true" in timer
