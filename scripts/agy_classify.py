"""One structured classification call through the native Antigravity CLI.

No API key is involved. The call runs headless in an empty directory with
stdin closed. Headless print mode auto-denies every tool that needs
permission, and the result reports each denial under `denied_actions`. Any
denial rejects the whole answer, so a classifier that tried to act cannot
decide anything. `agy` has no output-token flag, so the answer's own tokens
(output minus thinking) are checked after the call.
"""

from __future__ import annotations

import json
import subprocess
import tempfile
from pathlib import Path
from typing import Any, Callable

AGY_BIN = Path.home() / ".local" / "bin" / "agy"
MODEL = "gemini-3.8-flash"
EFFORT = "high"
MAX_PROMPT_BYTES = 6_000
MAX_ANSWER_TOKENS = 1_000
# Measured 2026-09-24: one event took 92 seconds at high effort, 81 of them
# thinking, and two events took 132 seconds. The spec's 90-second API figure
# does not fit agy.
TIMEOUT_SECONDS = 300
NO_TOOLS = (
    "You have no tools and must not call any. Do not inspect files or run commands. "
    "Answer only from the data in this message with one JSON object that matches the schema.\n\n"
)


class ClassifierUnavailable(RuntimeError):
    pass


def classify(
    prompt: str,
    schema: dict[str, Any],
    *,
    runner: Callable[..., subprocess.CompletedProcess] = subprocess.run,
) -> dict[str, Any]:
    if len(prompt.encode("utf-8")) > MAX_PROMPT_BYTES:
        raise ClassifierUnavailable("classifier input exceeds the 6000-byte budget")
    if not AGY_BIN.is_file():
        raise ClassifierUnavailable(f"agy is not installed at {AGY_BIN}")
    with tempfile.TemporaryDirectory(prefix="achios-classify-") as scratch:
        schema_path = Path(scratch) / "schema.json"
        schema_path.write_text(json.dumps(schema), encoding="utf-8")
        workdir = Path(scratch) / "empty"
        workdir.mkdir()
        argv = [
            str(AGY_BIN), "-p", NO_TOOLS + prompt,
            "--model", MODEL, "--effort", EFFORT,
            "--sandbox", "--disable-slash-commands",
            "--output-format", "json", "--json-schema", str(schema_path),
            "--print-timeout", f"{TIMEOUT_SECONDS}s",
        ]
        try:
            # An inherited open pipe on stdin makes agy print nothing and exit 0.
            completed = runner(
                argv, cwd=str(workdir), stdin=subprocess.DEVNULL,
                capture_output=True, text=True, timeout=TIMEOUT_SECONDS + 30, check=False,
            )
        except (OSError, subprocess.TimeoutExpired) as exc:
            raise ClassifierUnavailable(f"agy did not finish: {exc}") from exc
    if completed.returncode != 0:
        lines = [line for line in (completed.stderr or "").splitlines() if line.strip()]
        raise ClassifierUnavailable(f"agy exited {completed.returncode}: {lines[-1][:200] if lines else ''}")
    try:
        result = json.loads(completed.stdout)
    except json.JSONDecodeError as exc:
        raise ClassifierUnavailable("agy returned no JSON result") from exc
    if result.get("denied_actions"):
        raise ClassifierUnavailable("classifier attempted a tool; its answer was discarded")
    if result.get("status") != "SUCCESS":
        raise ClassifierUnavailable(f"agy status {result.get('status')}")
    usage = result.get("usage") or {}
    answer_tokens = int(usage.get("output_tokens") or 0) - int(usage.get("thinking_tokens") or 0)
    if answer_tokens > MAX_ANSWER_TOKENS:
        raise ClassifierUnavailable(f"classifier answer used {answer_tokens} tokens, over the 1000 budget")
    structured = result.get("structured_output")
    if not isinstance(structured, dict):
        raise ClassifierUnavailable("agy returned no structured output")
    return structured
