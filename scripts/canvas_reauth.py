"""Validate a browser's Canvas cookies before replacing the private client session."""
from __future__ import annotations

import json
import math
import tempfile
import time
from http.cookiejar import Cookie, MozillaCookieJar
from pathlib import Path

from canvas_client import CONFIG, CanvasClient, CanvasError, atomic_write, timestamp, writer_lock

HOST = "dlsu.instructure.com"


def canvas_cookies(rows: list[dict]) -> MozillaCookieJar:
    jar = MozillaCookieJar()
    for row in rows:
        if row.get("domain") not in (HOST, "." + HOST) or "partitionKey" in row:
            continue
        try:
            name, value, path = row["name"], row["value"], row["path"]
            if (not all(isinstance(v, str) for v in (name, value, path)) or not name
                    or not path.startswith("/") or any(ord(c) < 32 or ord(c) == 127 for c in name + value + path)
                    or type(row["secure"]) is not bool or type(row["session"]) is not bool
                    or type(row["httpOnly"]) is not bool):
                raise ValueError
            expires = None
            if not row["session"]:
                expiry = row["expires"]
                if type(expiry) not in (int, float) or not math.isfinite(expiry):
                    raise ValueError
                expires = int(expiry)
                if expires <= time.time():
                    continue
            domain = row["domain"]
            jar.set_cookie(Cookie(0, name, value, None, False, domain, domain.startswith("."),
                                 domain.startswith("."), path, True, row["secure"], expires,
                                 row["session"], None, None, {"HTTPOnly": ""} if row["httpOnly"] else {}))
        except (KeyError, TypeError, ValueError, OverflowError):
            raise CanvasError("invalid_browser_cookie") from None
    if not len(jar):
        raise CanvasError("no_canvas_session")
    return jar


def replace_session(rows: list[dict], config: Path = CONFIG, *, deadline: float | None = None) -> dict:
    with writer_lock(config):
        jar = canvas_cookies(rows)
        with tempfile.TemporaryDirectory(prefix="reauth-candidate-", dir=config) as directory:
            candidate = Path(directory)
            path = candidate / "cookies.txt"
            jar.save(str(path), ignore_discard=True)
            path.chmod(0o600)
            with CanvasClient(candidate) as client:
                profile, _ = client.get("/api/v1/users/self/profile")
                if not isinstance(profile, dict) or type(profile.get("id")) is not int or profile["id"] <= 0:
                    raise CanvasError("malformed_profile")
                mapping = config / "mappings.json"
                if mapping.exists():
                    expected = json.loads(mapping.read_text())["user_id"]
                    if type(expected) is not int or expected != profile["id"]:
                        raise CanvasError("wrong_canvas_account")
                for cookie in list(client.jar):
                    if cookie.domain not in (HOST, "." + HOST):
                        client.jar.clear(cookie.domain, cookie.path, cookie.name)
                client._save_cookies()
            if deadline is not None and time.monotonic() >= deadline:
                raise CanvasError("login_expired")
            atomic_write(config / "cookies.txt", path.read_text())
    return {"authentication": "valid", "checked_at": timestamp()}
