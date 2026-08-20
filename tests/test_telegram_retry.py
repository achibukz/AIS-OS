import pytest

import telegram_notify as tg

FAKE_TOKEN = "SECRET-TOKEN-123"


class _Resp:
    def __init__(self, status=200, text="ok", payload=None):
        self.status_code = status
        self.text = text
        self.ok = 200 <= status < 300
        self._payload = payload or {}

    def json(self):
        return self._payload


@pytest.fixture
def slept(tmp_path, monkeypatch):
    """telegram_notify with credentials stubbed and sleep made instant."""
    cfg = tmp_path / "telegram.env"
    cfg.write_text(f"TELEGRAM_BOT_TOKEN={FAKE_TOKEN}\nTELEGRAM_CHAT_ID=42\n")
    monkeypatch.setattr(tg, "TELEGRAM_ENV", cfg)
    recorded = []
    monkeypatch.setattr(tg, "RETRY_SLEEP", lambda s: recorded.append(s))
    return recorded


def _patch_post(monkeypatch, responses):
    """responses are consumed in order; the last one repeats."""
    import requests

    calls = []

    def post(url, **kwargs):
        calls.append(url)
        item = responses[min(len(calls) - 1, len(responses) - 1)]
        if isinstance(item, Exception):
            raise item
        return item

    monkeypatch.setattr(requests, "post", post)
    return calls


class TestRetry:
    """A DNS blip on 2026-08-20 killed four scheduled jobs at once, and took the
    failure-alert units with them, because send() had no retry at all."""

    def test_transient_network_error_is_retried_then_succeeds(self, slept, monkeypatch):
        import requests

        calls = _patch_post(monkeypatch, [requests.ConnectionError("dns went away"), _Resp()])
        assert tg.send("hello") == 1
        assert len(calls) == 2
        assert slept == [tg.RETRY_BACKOFF_S]

    def test_gives_up_after_max_attempts(self, slept, monkeypatch):
        import requests

        calls = _patch_post(monkeypatch, [requests.ConnectionError("still down")])
        with pytest.raises(SystemExit):
            tg.send("hello")
        assert len(calls) == tg.MAX_ATTEMPTS

    def test_backoff_grows_between_attempts(self, slept, monkeypatch):
        import requests

        _patch_post(monkeypatch, [requests.ConnectionError("down")])
        with pytest.raises(SystemExit):
            tg.send("hello")
        assert slept == sorted(slept)
        assert len(set(slept)) > 1

    def test_server_error_is_retried(self, slept, monkeypatch):
        calls = _patch_post(monkeypatch, [_Resp(502, "bad gateway"), _Resp()])
        assert tg.send("hello") == 1
        assert len(calls) == 2

    def test_client_error_is_not_retried(self, slept, monkeypatch):
        """A 400 means the message itself is wrong. Retrying cannot fix it."""
        calls = _patch_post(monkeypatch, [_Resp(400, "Bad Request: chat not found")])
        with pytest.raises(SystemExit):
            tg.send("hello")
        assert len(calls) == 1

    def test_rate_limit_honours_retry_after(self, slept, monkeypatch):
        calls = _patch_post(
            monkeypatch,
            [_Resp(429, "Too Many Requests", {"parameters": {"retry_after": 7}}), _Resp()],
        )
        assert tg.send("hello") == 1
        assert len(calls) == 2
        assert slept == [7]


class TestTokenRedaction:
    """requests embeds the request URL in its exceptions, and the URL carries the
    bot token. That is how the token reached journald in cleartext."""

    def test_token_absent_from_http_failure(self, slept, monkeypatch):
        _patch_post(monkeypatch, [_Resp(400, "Bad Request")])
        with pytest.raises(SystemExit) as exc:
            tg.send("hello")
        assert FAKE_TOKEN not in str(exc.value)

    def test_token_absent_from_network_failure(self, slept, monkeypatch):
        import requests

        boom = requests.ConnectionError(
            f"HTTPSConnectionPool(host='api.telegram.org') url: /bot{FAKE_TOKEN}/sendMessage"
        )
        _patch_post(monkeypatch, [boom])
        with pytest.raises(SystemExit) as exc:
            tg.send("hello")
        assert FAKE_TOKEN not in str(exc.value)
        assert "REDACTED" in str(exc.value)

    def test_redact_replaces_every_occurrence(self):
        assert "tok" not in tg.redact("a tok b tok", "tok")

    def test_redact_is_a_noop_without_a_token(self):
        assert tg.redact("nothing to hide", "") == "nothing to hide"
