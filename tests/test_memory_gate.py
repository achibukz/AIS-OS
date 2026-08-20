import memory_gate as mg


class TestPrefilter:
    def test_trigger_phrase_is_a_candidate(self):
        assert mg.is_candidate("never use the word leverage in my emails")

    def test_plain_chatter_is_not_a_candidate(self):
        assert not mg.is_candidate("what is the weather today")

    def test_matching_is_case_insensitive(self):
        assert mg.is_candidate("NEVER USE bullet points")

    def test_very_short_text_is_not_a_candidate(self):
        assert not mg.is_candidate("ok")


class TestProvenanceGuard:
    def test_rejects_v1_harvester_output(self):
        assert not mg.is_candidate(
            "Voice register adjustment: - can you make it less formal like this:"
        )

    def test_rejects_doubled_v1_output(self):
        assert not mg.is_candidate(
            "Voice register adjustment: Voice register adjustment: - can you "
            "make it less formal like this:"
        )

    def test_rejects_every_known_rule_prefix(self):
        for prefix in (
            "Voice register adjustment:",
            "Operational directive:",
            "Formatting override:",
            "Banned word / term:",
        ):
            assert not mg.is_candidate(f"{prefix} never use bullet points")

    def test_guard_is_case_insensitive(self):
        assert not mg.is_candidate("voice register adjustment: never use bullets")


class TestRuleValidation:
    def test_accepts_a_well_formed_rule(self):
        assert mg.validate_rule("Never use the word 'leverage' in emails.")

    def test_rejects_the_na_sentinel(self):
        assert not mg.validate_rule("N/A")

    def test_rejects_empty_and_whitespace(self):
        assert not mg.validate_rule("")
        assert not mg.validate_rule("   ")

    def test_rejects_too_short(self):
        assert not mg.validate_rule("no bullets")

    def test_rejects_too_long(self):
        assert not mg.validate_rule("x" * 121)

    def test_rejects_a_rule_carrying_a_harvester_prefix(self):
        assert not mg.validate_rule(
            "Voice register adjustment: never use bullet points in replies"
        )
