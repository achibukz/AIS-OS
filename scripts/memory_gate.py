#!/usr/bin/env python3
"""LLM gate for the self-learning loop.

Classifies candidate lines as durable preferences or one-off remarks using
`agy` running gemini-3.7-flash-high with an enforced JSON schema. This module
performs NO writes — it only decides. background_review.py owns the writing.

v1's mistake was shipping regexes as the decision-maker while the docstring
claimed an LLM gate that was never built. Here the regexes are only a cheap,
high-recall prefilter; every judgment call belongs to the model.
"""

from __future__ import annotations

import re

MIN_RULE_CHARS = 15
MAX_RULE_CHARS = 120
MIN_CANDIDATE_CHARS = 4

# High-recall, zero-judgment prefilter. Inherited from v1's extract_corrections.py,
# which is the one part of that file worth keeping.
CANDIDATE_TRIGGERS = (
    "banned", "don't use", "do not use", "never use", "stop using", "avoid using",
    "not use", "less formal", "more casual", "too formal", "take note",
    "make sure to", "remember that", "always make sure", "rule:", "change the",
    "replace the", "update the", "my favorite", "i prefer", "always use",
)

# Text shaped like v1 harvester output is by definition not something Aki said.
# Defence in depth: candidates now come from the raw turn prompt, which injected
# memory never reaches, so this should be unreachable. It fails closed if a future
# change reintroduces a transcript-sourced path.
RULE_PREFIXES = re.compile(
    r"^\s*(voice register adjustment|operational directive|formatting override|banned word)",
    re.IGNORECASE,
)


def looks_like_rule_output(text: str) -> bool:
    """True if the text carries a v1 harvester prefix."""
    return bool(RULE_PREFIXES.match(text or ""))


def is_candidate(text: str) -> bool:
    """Cheap prefilter: worth spending a model call on?"""
    if not text:
        return False
    stripped = text.strip()
    if len(stripped) < MIN_CANDIDATE_CHARS:
        return False
    if looks_like_rule_output(stripped):
        return False
    lowered = stripped.lower()
    return any(trigger in lowered for trigger in CANDIDATE_TRIGGERS)


def validate_rule(rule: str) -> bool:
    """Fail closed. A schema-valid response can still be junk — gemini returned
    the literal string 'N/A' on rejects during testing."""
    if not rule:
        return False
    stripped = rule.strip()
    if not stripped or stripped.upper() == "N/A":
        return False
    if not (MIN_RULE_CHARS <= len(stripped) <= MAX_RULE_CHARS):
        return False
    if looks_like_rule_output(stripped):
        return False
    return True
