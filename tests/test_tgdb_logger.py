import datetime as dt
import pytest
from pathlib import Path
import sys

# Add scripts directory to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
from tgdb_logger import sanitize_secrets, format_tgdb_note, write_tgdb_session


def test_sanitize_secrets_redacts_anthropic_and_telegram_keys():
    raw_text = "Here is my key sk-ant-api03-123456789012345678901234 and bot token 123456789:ABCdefGHIjklMNOpqrSTUvwxYZ123456789"
    sanitized = sanitize_secrets(raw_text)
    assert "sk-ant-" not in sanitized
    assert "[REDACTED_ANTHROPIC_KEY]" in sanitized
    assert "[REDACTED_TELEGRAM_TOKEN]" in sanitized


def test_sanitize_secrets_redacts_google_key():
    raw_text = "My google api key is AIzaSyD12345678901234567890123456789012"
    sanitized = sanitize_secrets(raw_text)
    assert "AIzaSy" not in sanitized
    assert "[REDACTED_GOOGLE_KEY]" in sanitized


def test_format_tgdb_note_generates_valid_structure():
    meta = {
        "title": "Thesis Discussion",
        "bot": "@schoMemBot",
        "engine": "Claude Sonnet",
        "summary": "Discussed STSP001 thesis deliverables.",
        "tags": ["thesis", "school"],
        "timestamp": dt.datetime(2026, 8, 18, 3, 30),
    }
    messages = [
        {"role": "user", "content": "When are the final deliverables due?"},
        {"role": "assistant", "content": "They are due on August 18 by 11:59 PM."},
    ]
    takeaways = ["Final deliverable deadline confirmed for August 18."]
    tasks = ["Submit thesis PDF packet @2026-08-18"]

    note = format_tgdb_note(meta, messages, takeaways, tasks)

    assert "---" in note
    assert 'title: "Thesis Discussion"' in note
    assert 'bot: "@schoMemBot"' in note
    assert "tags: [tgdb, thesis, school]" in note
    assert "### 📌 Key Takeaways & Decisions" in note
    assert "### ⚡ Extracted Action Items" in note
    assert "<details open>" in note
    assert "**Aki:** When are the final deliverables due?" in note
    assert "**@schoMemBot:** They are due on August 18 by 11:59 PM." in note


def test_write_tgdb_session(tmp_path):
    vault_dir = tmp_path / "achiMem"
    content = "# Test Note Content"
    ts = dt.datetime(2026, 8, 18, 10, 0)

    file_path = write_tgdb_session(vault_dir, "@schoMemAGYBot", "sess12345678", content, timestamp=ts)

    assert file_path.exists()
    assert file_path.parent.name == "2026-08"
    assert file_path.name == "2026-08-18-schomemagybot-sess1234.md"
    assert file_path.read_text(encoding="utf-8") == content
