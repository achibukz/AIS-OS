import json
from http.cookiejar import Cookie, MozillaCookieJar

import pytest
import requests

from canvas_client import CanvasClient, CanvasError, ORIGIN, api_url, match_courses, next_page, writer_lock


@pytest.fixture
def client(tmp_path, monkeypatch):
    jar = MozillaCookieJar(str(tmp_path / "cookies.txt"))
    jar.save()
    (tmp_path / "cookies.txt").chmod(0o600)
    monkeypatch.setattr("canvas_client.time.sleep", lambda _: None)
    with CanvasClient(tmp_path) as client:
        yield client


def response(body="[]", status=200, **headers):
    result = requests.Response()
    result.status_code = status
    result._content = body.encode()
    result._content_consumed = True
    result.headers.update(headers)
    return result


@pytest.mark.parametrize("url", [
    "https://evil.test/api/v1/courses", "//evil.test/api/v1/courses",
    "http://dlsu.instructure.com/api/v1/courses", "https://user@dlsu.instructure.com/api/v1/courses",
    "/api/v1/../login", "/api/v1/%2e%2e/login", "/login", "/api/v1/courses#secret",
    "https://dlsu.instructure.com:444/api/v1/courses", "/api/v1/\\evil",
])
def test_rejects_unsafe_initial_and_pagination_urls(url):
    with pytest.raises(CanvasError, match="unsafe_url"):
        api_url(url)
    with pytest.raises(CanvasError, match="unsafe_url"):
        next_page(f'<{url}>; rel="next"', ORIGIN + "/api/v1/courses")


def test_follows_link_without_guessing_pages(client, monkeypatch):
    calls = []
    pages = iter([response('[{"id":1}]', Link='</api/v1/courses?cursor=abc>; rel="next"'), response('[{"id":2}]')])
    def get(url, **kwargs):
        calls.append((url, kwargs))
        return next(pages)
    monkeypatch.setattr(client.session, "get", get)
    assert client.list("/api/v1/courses") == [{"id": 1}, {"id": 2}]
    assert calls[1][0].endswith("cursor=abc")
    assert calls[0][1]["allow_redirects"] is False
    assert client.session.trust_env is False


@pytest.mark.parametrize("body,status,headers,kind", [
    ('{}', 401, {}, 'authentication_expired'), ('{}', 403, {}, 'permission_denied'),
    ('<html>login secret</html>', 200, {}, 'authentication_expired'),
    ('', 302, {'Location': 'https://evil.test/private?token=secret'}, 'redirect_refused'),
    ('', 302, {'Location': '/login/google'}, 'authentication_expired'),
    ('secret', 200, {}, 'malformed_response'), ('null', 200, {}, 'malformed_response'),
    ('{}', 404, {}, 'http_failure'),
])
def test_errors_are_distinct_and_do_not_leak(client, monkeypatch, body, status, headers, kind):
    monkeypatch.setattr(client.session, "get", lambda *a, **k: response(body, status, **headers))
    with pytest.raises(CanvasError) as error:
        client.get("/api/v1/courses")
    assert error.value.kind == kind
    assert "secret" not in str(error.value)


def test_retry_bounded_and_sanitized(client, monkeypatch):
    calls = []
    def fail(*a, **k):
        calls.append(1)
        raise requests.ConnectionError("https://secret-cookie-value")
    monkeypatch.setattr(client.session, "get", fail)
    with pytest.raises(CanvasError, match="transient_failure") as error:
        client.get("/api/v1/courses")
    assert len(calls) == 3
    assert "secret" not in str(error.value)


def test_xssi_and_retry(client, monkeypatch):
    pages = iter([response('', 429), response('while(1);[{"id":1}]')])
    monkeypatch.setattr(client.session, "get", lambda *a, **k: next(pages))
    assert client.list("/api/v1/courses") == [{"id": 1}]


def test_cookie_updates_survive_reopen(client, monkeypatch):
    def get(*a, **k):
        client.jar.set_cookie(Cookie(0, 'session', 'updated', None, False, 'dlsu.instructure.com', False,
                                     False, '/', True, True, None, True, None, None, {}))
        return response()
    monkeypatch.setattr(client.session, "get", get)
    client.get("/api/v1/courses")
    jar = MozillaCookieJar(str(client.config / "cookies.txt"))
    jar.load(ignore_discard=True)
    assert [c.value for c in jar] == ['updated']
    assert (client.config / "cookies.txt").stat().st_mode & 0o777 == 0o600


def test_partial_pagination_never_returns_partial_list(client, monkeypatch):
    pages = iter([response('[{"id":1}]', Link='</api/v1/courses?page=2>; rel="next"'), response('{}', 403)])
    monkeypatch.setattr(client.session, "get", lambda *a, **k: next(pages))
    with pytest.raises(CanvasError, match="permission_denied"):
        client.list("/api/v1/courses")


def test_lock_refuses_second_writer(client):
    with pytest.raises(CanvasError, match="busy"):
        with writer_lock(client.config):
            pytest.fail("second writer entered")


def test_matching_requires_course_section_and_term():
    manifest = {"term": "AY2627-T1", "subjects": [{"code": "STDISCM", "section": "S03"}]}
    course = {"id": 42, "course_code": "STDISCM S03", "term": {"name": "AY 2026-2027 Term 1"}}
    assert match_courses(manifest, [course])["subjects"][0]["course_id"] == 42
    for courses in ([], [course, course], [{**course, "term": {"name": "2025-2026 Term 1"}}],
                    [{**course, "course_code": "STDISCM S030"}]):
        with pytest.raises(CanvasError, match="mapping_missing_or_ambiguous"):
            match_courses(manifest, courses)


@pytest.mark.parametrize("header", ["garbage", '<https://dlsu.instructure.com/api/v1/courses>',
    '</api/v1/courses?p=2>; rel="next", </api/v1/courses?p=3>; rel="next"'])
def test_malformed_pagination_is_not_complete(header):
    with pytest.raises(CanvasError, match="malformed_pagination"):
        next_page(header, ORIGIN + '/api/v1/courses')


def test_repeated_page_is_refused(client, monkeypatch):
    monkeypatch.setattr(client.session, "get", lambda *a, **k: response('[]', Link='</api/v1/courses>; rel="next"'))
    with pytest.raises(CanvasError, match="pagination_limit"):
        client.list('/api/v1/courses')


def test_response_size_is_bounded(client, monkeypatch):
    monkeypatch.setattr('canvas_client.MAX_RESPONSE_BYTES', 8)
    monkeypatch.setattr(client.session, 'get', lambda *a, **k: response('[{"id":12345}]'))
    with pytest.raises(CanvasError, match="response_too_large"):
        client.list('/api/v1/courses')


def test_failed_atomic_cookie_save_preserves_previous_file(client, monkeypatch):
    before = (client.config / 'cookies.txt').read_bytes()
    def fail(*args):
        raise OSError('injected rename failure')
    monkeypatch.setattr('canvas_client.os.replace', fail)
    monkeypatch.setattr(client.session, 'get', lambda *a, **k: response())
    with pytest.raises(OSError):
        client.get('/api/v1/courses')
    assert (client.config / 'cookies.txt').read_bytes() == before
    assert not list(client.config.glob('.cookies-*'))
    assert not list(client.config.glob('.canvas-*'))
