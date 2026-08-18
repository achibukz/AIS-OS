import telegram_notify as tg


class TestSplitMessages:
    def test_short_message_stays_whole(self):
        assert tg.split_messages("one\n\ntwo") == ["one\n\ntwo"]

    def test_splits_on_blank_lines_without_exceeding_the_limit(self):
        blocks = ["x" * 90 for _ in range(5)]
        parts = tg.split_messages("\n\n".join(blocks), limit=200)
        assert all(len(p) <= 200 for p in parts)
        assert "".join(parts).replace("\n", "") == "".join(blocks)

    def test_a_single_oversized_block_is_broken_on_newlines(self):
        block = "\n".join("y" * 40 for _ in range(10))
        parts = tg.split_messages(block, limit=100)
        assert all(len(p) <= 100 for p in parts)
        assert len(parts) > 1


class TestReadEnv:
    def test_parses_keys_and_ignores_comments_and_blanks(self, tmp_path, monkeypatch):
        env = tmp_path / "telegram.env"
        env.write_text("# a comment\n\nTELEGRAM_BOT_TOKEN=abc123\nTELEGRAM_CHAT_ID = 42 \n")
        monkeypatch.setattr(tg, "TELEGRAM_ENV", env)
        assert tg.read_env() == {"TELEGRAM_BOT_TOKEN": "abc123", "TELEGRAM_CHAT_ID": "42"}

    def test_missing_file_is_not_an_error(self, tmp_path, monkeypatch):
        monkeypatch.setattr(tg, "TELEGRAM_ENV", tmp_path / "nope.env")
        assert tg.read_env() == {}


class TestLoadConfig:
    def test_env_file_takes_precedence_over_ambient_env(self, tmp_path, monkeypatch):
        env = tmp_path / "telegram.env"
        env.write_text("TELEGRAM_BOT_TOKEN=from_file\nTELEGRAM_CHAT_ID=1\n")
        monkeypatch.setattr(tg, "TELEGRAM_ENV", env)
        monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "from_env")
        assert tg.load_config() == ("from_file", "1")

    def test_custom_env_path_is_supported(self, tmp_path):
        custom_env = tmp_path / "custom_finance.env"
        custom_env.write_text("TELEGRAM_BOT_TOKEN=finance_token\nTELEGRAM_CHAT_ID=999\n")
        assert tg.load_config(env_path=custom_env) == ("finance_token", "999")

    def test_missing_credentials_exit_with_the_config_path(self, tmp_path, monkeypatch):
        monkeypatch.setattr(tg, "TELEGRAM_ENV", tmp_path / "nope.env")
        monkeypatch.delenv("TELEGRAM_BOT_TOKEN", raising=False)
        monkeypatch.delenv("TELEGRAM_CHAT_ID", raising=False)
        try:
            tg.load_config()
        except SystemExit as exc:
            assert "telegram.env" in str(exc) or "nope.env" in str(exc)
        else:
            raise AssertionError("expected SystemExit")
