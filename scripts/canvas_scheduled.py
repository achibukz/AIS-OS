#!/usr/bin/env python3
"""Scheduled Canvas refresh: sync every mapped course, then send pending notices.

Delivery follows every sync that was not blocked by the writer lock, including a
failed or partial one, because sync queues the session-expired notice before it
exits nonzero. The exit status is nonzero only for local faults an operator must
fix. Expired sessions, Canvas outages, partial categories and a held lock are
recorded in the cache and reach Aki through Canvas notices and stale flags, so
they do not fire a failure alert every 30 minutes.
"""
from __future__ import annotations

import io
import json
import sys
from contextlib import redirect_stderr, redirect_stdout

import canvas
from canvas_client import timestamp

REMOTE_ERRORS = frozenset({
    "authentication_expired", "transient_failure", "permission_denied", "http_failure",
    "redirect_refused", "malformed_response", "malformed_pagination", "pagination_limit",
    "response_too_large", "busy", "delivery_unconfirmed",
})


def run(argv):
    out, err = io.StringIO(), io.StringIO()
    with redirect_stdout(out), redirect_stderr(err):
        code = canvas.main(argv)
    lines = (out.getvalue() or err.getvalue()).strip().splitlines()
    try:
        result = json.loads(lines[-1]) if lines else {}
    except ValueError:
        result = {}
    if not isinstance(result, dict):
        result = {}
    if code and not result.get("error") and not result.get("failures"):
        result["error"] = "unreported_failure"
    return result


def local_fault(result):
    errors = [result.get("error")]
    errors += [item.get("error") for item in result.get("failures") or [] if isinstance(item, dict)]
    return any(error and error not in REMOTE_ERRORS for error in errors)


def main(argv=None):
    paths = sys.argv[1:] if argv is None else list(argv)
    report = {"sync": run(paths + ["sync"])}
    if report["sync"].get("error") != "busy":
        report["remind"] = run(paths + ["remind"])
        report["delivery"] = run(paths + ["deliver", "--send"])
    print(json.dumps({"at": timestamp(), **report}, ensure_ascii=False))
    return 1 if any(local_fault(result) for result in report.values()) else 0


if __name__ == "__main__":
    raise SystemExit(main())
