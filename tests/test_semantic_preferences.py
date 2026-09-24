from pathlib import Path

import pytest

import learning_ledger
from semantic_preferences import PreferenceError, PreferenceStore


def source(source_id="message:1:r1", kind="telegram_user", revision=1):
    return {
        "id": source_id,
        "kind": kind,
        "native_id": "chat:1:message:1",
        "revision": revision,
        "timestamp": "2026-09-21T12:00:00+08:00",
    }


def preference(kind, value, **changes):
    return {
        "kind": kind,
        "scope": "global",
        "scope_value": "",
        "value": value,
        "evidence": "Show me the file",
        "evidence_validated": True,
        "explicit": True,
        "exceptions": [],
        **changes,
    }


@pytest.fixture
def store(tmp_path: Path):
    return PreferenceStore(tmp_path / "cohesion.sqlite3")


def test_viewer_preference_activates_and_current_paste_request_can_override(store):
    receipt = store.record(source(), preference("viewer_delivery", "viewer_link"))

    assert receipt["activated"] is True
    learned = store.effective("viewer_delivery")
    assert learned["value"] == "viewer_link"
    assert learned["revision"] == 1

    current_instruction = "paste"
    delivery = current_instruction or learned["value"]
    assert delivery == "paste"


def test_category_placement_is_narrower_than_global(store):
    store.record(source("message:global:r1"), preference("placement", "tasks"))
    store.record(
        source("message:school:r1"),
        preference(
            "placement",
            "both",
            scope="category",
            scope_value="school_deadline",
            evidence="Put school deadlines in both",
        ),
    )

    assert store.effective("placement", category="quick_task")["value"] == "tasks"
    school = store.effective("placement", category="school_deadline")
    assert school["value"] == "both" and school["scope_type"] == "category"


def test_this_item_activates_only_for_that_item(store):
    receipt = store.record(
        source(),
        preference(
            "placement",
            "tasks",
            scope="item",
            scope_value="item_123",
            evidence="Only put this one in tasks",
        ),
    )

    assert receipt["status"] == "active"
    assert receipt["activated"] is True
    assert store.effective("placement", category="school_deadline") is None
    assert store.effective("placement", item_id="item_123")["value"] == "tasks"
    assert store.effective("placement", item_id="item_456") is None


def test_ambiguous_scope_asks_one_concise_question_and_replay_is_idempotent(store):
    proposal = preference(
        "placement",
        "tasks",
        scope="ambiguous",
        evidence="Do that instead",
    )
    first = store.record(source(), proposal)
    second = store.record(source(), proposal)

    assert first == second
    assert first["status"] == "pending"
    assert first["question"].count("?") == 1
    assert len(store.pending()) == 1


def test_replaying_an_activated_event_does_not_bump_its_revision(store):
    store.record(source(), preference("viewer_delivery", "viewer_link"))

    replay = store.record(source(), preference("viewer_delivery", "viewer_link"))

    assert replay["activated"] is False
    assert store.effective("viewer_delivery")["revision"] == 1


def test_correction_keeps_source_history_and_increments_revision(store):
    first = store.record(source("message:1:r1"), preference("viewer_delivery", "viewer_link"))
    second = store.record(
        source("message:2:r1"),
        preference("viewer_delivery", "paste", evidence="Always paste file contents"),
    )

    assert first["revision"] == 1 and second["revision"] == 2
    assert store.effective("viewer_delivery")["value"] == "paste"
    context = store.context()
    assert context["active"]["viewer_delivery"]["revision"] == 2


def test_unvalidated_source_and_model_echo_never_activate(store):
    unvalidated = store.record(
        source("message:1:r1"),
        preference("viewer_delivery", "viewer_link", evidence_validated=False),
    )
    echo = store.record(
        source("assistant:1:r1", kind="telegram_assistant"),
        preference("viewer_delivery", "paste", evidence="I will always paste files"),
    )

    assert unvalidated["status"] == "pending"
    assert echo["status"] == "rejected"
    assert store.effective("viewer_delivery") is None
    with pytest.raises(PreferenceError, match="unsupported evidence"):
        store.activate(echo["event_id"])


def test_revocation_removes_the_rule_without_erasing_evidence(store):
    store.record(source("message:1:r1"), preference("placement", "calendar"))
    revoked = store.record(
        source("message:2:r1"),
        preference(
            "placement",
            None,
            action="revoke",
            evidence="Stop using that placement",
        ),
    )

    assert revoked["status"] == "revoked"
    assert store.effective("placement") is None
    assert len(store.context()["inspectable"]) == 0


def test_each_semantic_event_keeps_source_scope_exceptions_and_state_in_the_ledger(store):
    receipt = store.record(
        source(),
        preference(
            "viewer_delivery",
            "viewer_link",
            exceptions=["Paste when explicitly requested"],
        ),
    )

    latest = learning_ledger.latest(receipt["event_id"], path=store.ledger_path)
    assert latest["state"] == "activated"
    assert latest["source_envelope"]["id"] == "message:1:r1"
    assert latest["raw"] == "Show me the file"
    assert latest["preference"] == {
        "kind": "viewer_delivery",
        "scope": "global",
        "scope_value": "",
        "value": "viewer_link",
        "exceptions": ["Paste when explicitly requested"],
    }
