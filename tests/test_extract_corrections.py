import datetime as dt
from pathlib import Path
import pytest
import sys

# Add scripts directory to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
from extract_corrections import (
    clean_quote_text,
    extract_corrections_from_text,
    is_rule_duplicate,
    apply_corrections,
    HarvestedCorrection,
)


def test_clean_quote_text():
    assert clean_quote_text("> **Aki:** hello") == "**Aki:** hello"
    assert clean_quote_text("<USER_REQUEST>some request</USER_REQUEST>") == "some request"
    assert clean_quote_text("   multiple    spaces   ") == "multiple spaces"


def test_extract_banned_word(tmp_path):
    sample_path = tmp_path / "2026-08-18-test.md"
    sample_text = """---
title: "Testing"
date: 2026-08-18 20:00
---

> **Aki:** can we not use the word amenable, did you use message-writer skill to make this?
>
> **@achiAgyOSBot:** I will avoid it.
"""
    corrections = extract_corrections_from_text(sample_text, sample_path)
    assert len(corrections) >= 1
    banned = [c for c in corrections if c.trigger_type == "banned_word"]
    assert len(banned) == 1
    assert "amenable" in banned[0].rule_text.lower()
    assert banned[0].domain == "voice"


def test_extract_directive(tmp_path):
    sample_path = tmp_path / "2026-08-18-test.md"
    sample_text = """---
title: "Testing"
date: 2026-08-18 20:00
---

> **Aki:** take note that i have to get a med cert in an outside clinic
>
> **@achiAgyOSBot:** Noted.
"""
    corrections = extract_corrections_from_text(sample_text, sample_path)
    assert len(corrections) == 1
    assert corrections[0].trigger_type == "directive"
    assert "med cert in an outside clinic" in corrections[0].rule_text
    assert corrections[0].domain == "tasks"


def test_extract_formatting_change(tmp_path):
    sample_path = tmp_path / "2026-08-18-test.md"
    sample_text = """---
title: "Testing"
date: 2026-08-18 20:00
---

> **Aki:** change the subject to Abram Aki Bukuhan than Abram Bukuhan
>
> **@achiAgyOSBot:** Done.
"""
    corrections = extract_corrections_from_text(sample_text, sample_path)
    assert len(corrections) == 1
    assert corrections[0].trigger_type == "preference"
    assert "Abram Aki Bukuhan" in corrections[0].rule_text
    assert corrections[0].domain == "voice"


def test_extract_style_adjustment(tmp_path):
    sample_path = tmp_path / "2026-08-18-test.md"
    sample_text = """---
title: "Testing"
date: 2026-08-18 20:00
---

> **Aki:** can you make it less formal like this:
>
> **@achiAgyOSBot:** Sure.
"""
    corrections = extract_corrections_from_text(sample_text, sample_path)
    assert len(corrections) == 1
    assert corrections[0].trigger_type == "style"
    assert corrections[0].domain == "voice"


def test_is_rule_duplicate():
    corpus = "Banned words: leverage, passionate, synergy, amenable, holistic."
    assert is_rule_duplicate("Banned word: amenable", corpus) is True
    assert is_rule_duplicate("Banned word: proactive", corpus) is False


def test_apply_corrections_dry_run(tmp_path):
    item = HarvestedCorrection(
        source_file=tmp_path / "sample.md",
        date_str="2026-08-18",
        raw_quote="can we not use the word unapproved",
        trigger_type="banned_word",
        rule_text="Banned word: unapproved",
        domain="voice",
    )
    count, summaries = apply_corrections([item], dry_run=True)
    assert count == 1
    assert len(summaries) == 1
