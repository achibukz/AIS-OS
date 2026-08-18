import datetime as dt
from pathlib import Path
import pytest
import sys

# Add scripts directory to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
from evening_debrief import (
    strip_markup,
    get_tasks_data,
    get_corrections_today,
    build_evening_debrief,
)


def test_strip_markup():
    assert strip_markup("[[Personal Wiki]]") == "Personal Wiki"
    assert strip_markup("**Important**") == "Important"
    assert strip_markup("`code snippet`") == "code snippet"


def test_build_evening_debrief_two_messages():
    test_date = dt.date(2026, 8, 18)
    main_msg, rules_msg = build_evening_debrief(test_date)

    assert "🌙 Evening Debrief" in main_msg
    assert "Day concluded: Aug 18, 2026" in main_msg
    assert "Rest well! 🌙" in main_msg

    if rules_msg:
        assert "🧠 Self-Learning & Harvested Rules" in rules_msg
        assert "Concluded: Aug 18, 2026" in rules_msg
