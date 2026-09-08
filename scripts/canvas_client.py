"""GET-only Canvas access with private cookies and serialized writers."""
from __future__ import annotations

import fcntl
import json
import os
import re
import tempfile
import time
from contextlib import contextmanager
from datetime import datetime, timezone
from http.cookiejar import MozillaCookieJar
from pathlib import Path
from urllib.parse import unquote, urljoin, urlsplit

import requests

ORIGIN = "https://dlsu.instructure.com"
CONFIG = Path.home() / ".config/achios/canvas"
MAX_RESPONSE_BYTES = 16 * 1024 * 1024


class CanvasError(Exception):
    def __init__(self, kind: str):
        self.kind = kind
        super().__init__(f"Canvas {kind}")


def timestamp() -> str:
    return datetime.now(timezone.utc).isoformat()


def private_directory(path: Path) -> None:
    path.mkdir(mode=0o700, parents=True, exist_ok=True)
    if path.is_symlink() or path.stat().st_uid != os.getuid():
        raise CanvasError("unsafe_private_directory")
    path.chmod(0o700)


def atomic_write(path: Path, content: str) -> None:
    private_directory(path.parent)
    fd, name = tempfile.mkstemp(prefix=".canvas-", dir=path.parent)
    try:
        with os.fdopen(fd, "w") as stream:
            stream.write(content)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(name, path)
        directory = os.open(path.parent, os.O_DIRECTORY)
        try:
            os.fsync(directory)
        finally:
            os.close(directory)
    finally:
        Path(name).unlink(missing_ok=True)


@contextmanager
def writer_lock(config: Path = CONFIG):
    private_directory(config)
    fd = os.open(config / "writer.lock", os.O_CREAT | os.O_RDWR | os.O_NOFOLLOW, 0o600)
    try:
        try:
            fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            raise CanvasError("busy") from None
        yield
    finally:
        os.close(fd)


def api_url(value: str) -> str:
    try:
        url = urljoin(ORIGIN + "/", value)
        parts = urlsplit(url)
        if (parts.scheme != "https" or parts.hostname != "dlsu.instructure.com"
                or parts.port not in (None, 443) or parts.username or parts.password
                or parts.fragment or not parts.path.startswith("/api/v1/")
                or any(c in value for c in "\\\r\n\t")
                or ".." in unquote(parts.path).split("/")):
            raise ValueError
    except ValueError:
        raise CanvasError("unsafe_url") from None
    return url


def next_page(header: str, current: str) -> str | None:
    if not header:
        return None
    links = re.split(r",\s*(?=<)", header)
    next_urls = []
    for link in links:
        match = re.fullmatch(r'\s*<([^<>]+)>\s*((?:;\s*[^;]+)*)', link)
        if not match:
            raise CanvasError("malformed_pagination")
        relations = re.findall(r';\s*rel\s*=\s*(?:"([^"]+)"|([^;\s]+))', match[2])
        if not relations:
            raise CanvasError("malformed_pagination")
        target = api_url(urljoin(current, match[1]))
        if any("next" in (quoted or bare).split() for quoted, bare in relations):
            next_urls.append(target)
    if len(next_urls) > 1:
        raise CanvasError("malformed_pagination")
    return next_urls[0] if next_urls else None


class CanvasClient:
    def __init__(self, config: Path = CONFIG):
        self.config = config
        self.session = requests.Session()
        self.session.trust_env = False
        self.jar = MozillaCookieJar(str(config / "cookies.txt"))
        self.session.cookies = self.jar
        self.session.headers.update({"Accept": "application/json", "User-Agent": "achiOS-Canvas/1"})
        self.lock = None

    def __enter__(self):
        self.lock = writer_lock(self.config)
        self.lock.__enter__()
        try:
            cookie_path = self.config / "cookies.txt"
            if cookie_path.is_symlink() or cookie_path.stat().st_mode & 0o077:
                raise CanvasError("unsafe_cookie_permissions")
            self.jar.load(ignore_discard=True)
            for cookie in list(self.jar):
                if cookie.domain.lstrip(".") != "dlsu.instructure.com":
                    self.jar.clear(cookie.domain, cookie.path, cookie.name)
        except (OSError, ValueError):
            self.__exit__(None, None, None)
            raise CanvasError("cookie_store_unavailable") from None
        except BaseException:
            self.__exit__(None, None, None)
            raise
        return self

    def __exit__(self, *args):
        self.session.close()
        if self.lock is not None:
            self.lock.__exit__(*args)
            self.lock = None

    def _save_cookies(self):
        fd, name = tempfile.mkstemp(prefix=".cookies-", dir=self.config)
        os.close(fd)
        try:
            self.jar.save(name, ignore_discard=True)
            atomic_write(self.config / "cookies.txt", Path(name).read_text())
        finally:
            Path(name).unlink(missing_ok=True)

    def get(self, value: str) -> tuple[object, str | None]:
        if self.lock is None:
            raise CanvasError("client_not_locked")
        url = api_url(value)
        for attempt in range(3):
            try:
                with self.session.get(url, timeout=(10, 30), allow_redirects=False, stream=True) as response:
                    self._save_cookies()
                    status = response.status_code
                    if status == 401:
                        raise CanvasError("authentication_expired")
                    if status == 403:
                        raise CanvasError("permission_denied")
                    if 300 <= status < 400:
                        location = urlsplit(urljoin(url, response.headers.get("Location", "")))
                        if location.hostname == "dlsu.instructure.com" and location.path.startswith("/login"):
                            raise CanvasError("authentication_expired")
                        raise CanvasError("redirect_refused")
                    if status == 429 or 500 <= status <= 599:
                        raise CanvasError("transient_failure")
                    if status != 200:
                        raise CanvasError("http_failure")
                    raw = bytearray()
                    for chunk in response.iter_content(65536):
                        raw.extend(chunk)
                        if len(raw) > MAX_RESPONSE_BYTES:
                            raise CanvasError("response_too_large")
                    body = raw.decode("utf-8-sig").lstrip()
                    if body.startswith("<") or "text/html" in response.headers.get("Content-Type", ""):
                        raise CanvasError("authentication_expired")
                    if body.startswith("while(1);"):
                        body = body[len("while(1);"):]
                    data = json.loads(body)
                    if not isinstance(data, (dict, list)):
                        raise CanvasError("malformed_response")
                    return data, next_page(response.headers.get("Link", ""), url)
            except (requests.RequestException, TimeoutError):
                error = CanvasError("transient_failure")
            except (UnicodeError, ValueError):
                raise CanvasError("malformed_response") from None
            except CanvasError as exc:
                if exc.kind != "transient_failure":
                    raise
                error = exc
            if attempt < 2:
                time.sleep(2 ** attempt)
        raise error from None

    def list(self, path: str) -> list[dict]:
        rows = []
        seen = set()
        url = api_url(path)
        while url:
            if url in seen or len(seen) >= 100:
                raise CanvasError("pagination_limit")
            seen.add(url)
            page, url = self.get(url)
            if not isinstance(page, list) or any(not isinstance(row, dict) for row in page):
                raise CanvasError("malformed_response")
            rows.extend(page)
        return rows


def match_courses(manifest: dict, courses: list[dict]) -> dict:
    term_match = re.fullmatch(r"AY(\d{2})(\d{2})-T([123])", manifest["term"])
    if not term_match:
        raise CanvasError("invalid_term")
    start, end, term = term_match.groups()
    term_pattern = rf"(?:AY\s*)?(?:20)?{start}\s*[-/]\s*(?:20)?{end}.*?(?:TERM\s*|T){term}(?!\d)"
    mappings = []
    for subject in manifest["subjects"]:
        matches = []
        code = re.escape(subject["code"]).replace(r"\-", "-?")
        for course in courses:
            label = str(course.get("course_code", "")).upper()
            name = str(course.get("name", "")).upper()
            term_name = str((course.get("term") or {}).get("name", "")).upper()
            if (re.search(rf"(?<![A-Z0-9]){code}(?![A-Z0-9])", label)
                    and re.search(rf"(?<![A-Z0-9]){re.escape(subject['section'])}(?![A-Z0-9])", label + " " + name)
                    and re.search(term_pattern, term_name)):
                if type(course.get("id")) is not int or course["id"] <= 0:
                    raise CanvasError("malformed_course")
                matches.append(course)
        if len(matches) != 1:
            raise CanvasError("course_mapping_missing_or_ambiguous")
        course = matches[0]
        mappings.append({**subject, "course_id": course["id"], "course_code": course["course_code"],
                         "course_name": course.get("name"), "canvas_term": course["term"]["name"]})
    if len({row["course_id"] for row in mappings}) != len(mappings):
        raise CanvasError("duplicate_course_mapping")
    return {"term": manifest["term"], "verified_at": timestamp(), "subjects": mappings}
