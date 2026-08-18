import datetime as dt
from pathlib import Path
import pytest
import sys

# Add scripts directory to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
from export_transcripts import (
    clean_title,
    clean_claude_text,
    clean_antigravity_text,
    extract_takeaways_and_tasks,
    parse_claude_jsonl,
    parse_antigravity_transcript,
)


def test_clean_title():
    assert clean_title("<command-message>telegram:access</command-message>") == "telegram:access"
    assert clean_title("# 💬 Can you check my connections?") == "Can you check my connections?"
    assert clean_title("") == "Session"
    long_text = "This is a very long prompt that should be truncated gracefully around sixty-five characters without cutting mid-word"
    truncated = clean_title(long_text)
    assert len(truncated) <= 65
    assert not truncated.endswith(" ")


def test_clean_claude_text():
    raw_channel = '<channel source="plugin:telegram:telegram" chat_id="123">Hello Claude</channel>'
    assert clean_claude_text(raw_channel) == "Hello Claude"

    raw_command = "<command-name>/model</command-name><local-command-stdout>Set model to Haiku</local-command-stdout>"
    assert clean_claude_text(raw_command) == ""

    skill_dump = "Base directory for this skill: /home/achibukz/skills\n# /telegram:access"
    assert clean_claude_text(skill_dump) == ""


def test_clean_antigravity_text():
    raw_user = "<USER_REQUEST>\ncan you check the tgdb?\n</USER_REQUEST>\n<ADDITIONAL_METADATA>\ntime=now\n</ADDITIONAL_METADATA>"
    assert clean_antigravity_text(raw_user) == "can you check the tgdb?"

    raw_resp = "<thought>Thinking about answer...</thought>Here is your tgdb status."
    assert clean_antigravity_text(raw_resp) == "Here is your tgdb status."


def test_extract_takeaways_and_tasks():
    messages = [
        {"role": "user", "content": "What needs to be done?"},
        {
            "role": "assistant",
            "content": "Here is the plan:\n* **Decision**: Use monthly partitioned directories.\n- [ ] Update export_transcripts.py\n- [ ] Run pytest",
        },
    ]
    takeaways, tasks = extract_takeaways_and_tasks(messages)
    assert "Decision: Use monthly partitioned directories." in takeaways
    assert "Update export_transcripts.py" in tasks
    assert "Run pytest" in tasks


def test_parse_antigravity_transcript(tmp_path):
    log_dir = tmp_path / "conv123" / ".system_generated" / "logs"
    log_dir.mkdir(parents=True)
    transcript_file = log_dir / "transcript.jsonl"

    content = '\n'.join([
        '{"type":"USER_INPUT","source":"USER_EXPLICIT","content":"<USER_REQUEST>How do I test tgdb?</USER_REQUEST>","created_at":"2026-08-18T10:00:00Z"}',
        '{"type":"PLANNER_RESPONSE","source":"MODEL","tool_calls":[{"name":"run_command"}]}',
        '{"type":"GENERIC","source":"MODEL","content":"Command stdout dump that should be ignored"}',
        '{"type":"PLANNER_RESPONSE","source":"MODEL","content":"You can run pytest tests/test_tgdb_logger.py."}',
    ])
    transcript_file.write_text(content, encoding="utf-8")

    parsed = parse_antigravity_transcript(transcript_file)
    assert parsed is not None
    meta, messages, takeaways, tasks = parsed

    assert meta["title"] == "How do I test tgdb?"
    assert meta["bot"] == "@achiAgyBot"
    assert len(messages) == 2
    assert messages[0]["role"] == "user"
    assert messages[0]["content"] == "How do I test tgdb?"
    assert messages[1]["role"] == "assistant"
    assert messages[1]["content"] == "You can run pytest tests/test_tgdb_logger.py."
