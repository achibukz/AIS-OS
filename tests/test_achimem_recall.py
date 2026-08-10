import json

import achimem_recall as recall
import pytest


@pytest.fixture
def sessions(tmp_path, monkeypatch):
    folder = tmp_path / "achiMem" / "raw" / "sessions"
    folder.mkdir(parents=True)
    monkeypatch.setattr(recall, "SESSIONS", folder)
    return folder


def enriched(folder, name, happened, threads=()):
    body = f'---\ntitle: "achiOS session"\nstatus: enriched\n---\n\n## What happened\n- {happened}\n'
    if threads:
        body += "\n## Open threads\n" + "".join(f"- {t}\n" for t in threads)
    (folder / name).write_text(body, encoding="utf-8")


def unenriched(folder, name, ask):
    (folder / name).write_text(
        f'---\ntitle: "achiOS session"\nstatus: unenriched\n---\n\n'
        f'## Mechanical record\n- Opening ask: "{ask}"\n',
        encoding="utf-8",
    )


def test_empty_vault_returns_placeholder(sessions):
    assert "No achiOS sessions logged yet" in recall.build_context()


def test_missing_folder_does_not_crash(tmp_path, monkeypatch):
    monkeypatch.setattr(recall, "SESSIONS", tmp_path / "nope")
    assert "No achiOS sessions logged yet" in recall.build_context()


def test_headline_prefers_first_what_happened_bullet(sessions):
    enriched(sessions, "2026-08-09-achios-aaaa1111.md", "wired the capture hook")
    assert recall.headline(sessions / "2026-08-09-achios-aaaa1111.md") == "wired the capture hook"


def test_headline_falls_back_to_opening_ask(sessions):
    unenriched(sessions, "2026-08-09-achios-bbbb2222.md", "make the logging work")
    assert recall.headline(sessions / "2026-08-09-achios-bbbb2222.md") == "make the logging work"


def test_headline_is_truncated(sessions):
    enriched(sessions, "2026-08-09-achios-cccc3333.md", "y" * 200)
    assert len(recall.headline(sessions / "2026-08-09-achios-cccc3333.md")) == 70


def test_lists_three_most_recent_newest_first(sessions):
    for day in ("06", "07", "08", "09"):
        enriched(sessions, f"2026-08-{day}-achios-aaaa{day}11.md", f"work on {day}")
    context = recall.build_context()
    assert "work on 09" in context
    assert "work on 07" in context
    assert "work on 06" not in context
    assert context.index("work on 09") < context.index("work on 08")


def test_counts_open_threads_across_files(sessions):
    enriched(sessions, "2026-08-08-achios-aaaa1111.md", "a", threads=["one", "two"])
    enriched(sessions, "2026-08-09-achios-bbbb2222.md", "b", threads=["three"])
    assert "Open threads: 3" in recall.build_context()


def test_counts_unenriched(sessions):
    enriched(sessions, "2026-08-08-achios-aaaa1111.md", "a")
    unenriched(sessions, "2026-08-09-achios-bbbb2222.md", "b")
    assert "Unenriched logs: 1" in recall.build_context()


def test_main_emits_valid_hook_json(sessions, capsys):
    enriched(sessions, "2026-08-09-achios-aaaa1111.md", "did a thing")
    recall.main()
    payload = json.loads(capsys.readouterr().out)
    assert payload["hookSpecificOutput"]["hookEventName"] == "SessionStart"
    assert "did a thing" in payload["hookSpecificOutput"]["additionalContext"]
