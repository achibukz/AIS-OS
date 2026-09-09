import json
from http.cookiejar import MozillaCookieJar

import pytest
import requests

from canvas_client import CanvasError, writer_lock
from canvas_reauth import canvas_cookies, replace_session


def cookie(**changes):
    return {"name": "session", "value": "new-secret", "domain": "dlsu.instructure.com",
            "path": "/", "secure": True, "httpOnly": True, "session": True, "expires": -1,
            **changes}


def response(body):
    result = requests.Response()
    result.status_code = 200
    result._content = json.dumps(body).encode()
    result._content_consumed = True
    return result


def test_import_preserves_scope_and_excludes_other_sites():
    jar = canvas_cookies([cookie(), cookie(name="path", domain=".dlsu.instructure.com", path="/api"),
                          cookie(domain=".google.com"), cookie(domain=".instructure.com"),
                          cookie(domain="evil.dlsu.instructure.com"), cookie(partitionKey={"topLevelSite": "x"})])
    assert len(jar) == 2
    host, scoped = list(jar)
    assert not host.domain_specified and host.secure and host.discard
    assert host.has_nonstandard_attr("HTTPOnly")
    assert scoped.domain_specified and scoped.path == "/api"


@pytest.mark.parametrize("changes", [{"name": "bad\nname"}, {"value": "secret\tvalue"},
    {"path": "bad"}, {"secure": "true"}, {"session": False, "expires": "bad"}])
def test_malformed_cookie_is_redacted(changes):
    with pytest.raises(CanvasError, match="invalid_browser_cookie") as error:
        canvas_cookies([cookie(**changes)])
    assert "secret" not in str(error.value)


def test_expired_or_empty_session_is_refused():
    for cookies in ([], [cookie(session=False, expires=1)]):
        with pytest.raises(CanvasError, match="no_canvas_session"):
            canvas_cookies(cookies)


def test_replacement_probes_candidate_under_writer_lock(tmp_path, monkeypatch):
    saved = tmp_path / "cookies.txt"
    saved.write_text("last usable jar")
    (tmp_path / "mappings.json").write_text('{"user_id":7}')
    def get(session, url, **kwargs):
        assert saved.read_text() == "last usable jar"
        assert session.cookies.filename != str(saved)
        assert url.endswith("/api/v1/users/self/profile")
        with pytest.raises(CanvasError, match="busy"):
            with writer_lock(tmp_path):
                pytest.fail("replacement did not lock sync")
        return response({"id": 7})
    monkeypatch.setattr(requests.Session, "get", get)
    result = replace_session([cookie()], tmp_path)
    assert result["authentication"] == "valid"
    jar = MozillaCookieJar(str(saved))
    jar.load(ignore_discard=True)
    assert [c.value for c in jar] == ["new-secret"]
    assert saved.stat().st_mode & 0o777 == 0o600
    assert not list(tmp_path.glob("reauth-candidate-*"))
    assert "secret" not in json.dumps(result)


@pytest.mark.parametrize("body,error", [({"id":8}, "wrong_canvas_account"),
    ({"id":True}, "malformed_profile"), ({}, "malformed_profile")])
def test_bad_probe_preserves_last_jar(tmp_path, monkeypatch, body, error):
    saved = tmp_path / "cookies.txt"
    saved.write_bytes(b"old jar")
    (tmp_path / "mappings.json").write_text('{"user_id":7}')
    monkeypatch.setattr(requests.Session, "get", lambda *a, **k: response(body))
    with pytest.raises(CanvasError, match=error):
        replace_session([cookie()], tmp_path)
    assert saved.read_bytes() == b"old jar"
    assert not list(tmp_path.glob("reauth-candidate-*"))


def test_network_failure_preserves_jar(tmp_path, monkeypatch):
    (tmp_path / "cookies.txt").write_bytes(b"old jar")
    monkeypatch.setattr("canvas_client.time.sleep", lambda _: None)
    def fail(*a, **k):
        raise requests.ConnectionError("secret")
    monkeypatch.setattr(requests.Session, "get", fail)
    with pytest.raises(CanvasError, match="transient_failure"):
        replace_session([cookie()], tmp_path)
    assert (tmp_path / "cookies.txt").read_bytes() == b"old jar"


def test_busy_sync_prevents_any_candidate(tmp_path):
    with writer_lock(tmp_path):
        with pytest.raises(CanvasError, match="busy"):
            replace_session([cookie()], tmp_path)
    assert not list(tmp_path.glob("reauth-candidate-*"))


def test_rename_failure_preserves_jar(tmp_path, monkeypatch):
    (tmp_path / "cookies.txt").write_bytes(b"old jar")
    monkeypatch.setattr(requests.Session, "get", lambda *a, **k: response({"id":7}))
    original = __import__("os").replace
    def fail(source, destination):
        if destination == tmp_path / "cookies.txt":
            raise OSError("disk error")
        original(source, destination)
    monkeypatch.setattr("canvas_client.os.replace", fail)
    with pytest.raises(OSError):
        replace_session([cookie()], tmp_path)
    assert (tmp_path / "cookies.txt").read_bytes() == b"old jar"


def test_expiry_during_probe_never_replaces_session(tmp_path, monkeypatch):
    import time
    (tmp_path / "cookies.txt").write_bytes(b"old jar")
    monkeypatch.setattr(requests.Session, "get", lambda *a, **k: response({"id":7}))
    with pytest.raises(CanvasError, match="login_expired"):
        replace_session([cookie()], tmp_path, deadline=time.monotonic()-1)
    assert (tmp_path / "cookies.txt").read_bytes() == b"old jar"
