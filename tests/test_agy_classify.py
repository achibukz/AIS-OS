import json
import subprocess

import pytest

import agy_classify

SCHEMA = {"type": "object", "properties": {"decisions": {"type": "array"}}}


@pytest.fixture
def agy(tmp_path, monkeypatch):
    binary = tmp_path / "agy"
    binary.write_text("#!/bin/sh\n", encoding="utf-8")
    monkeypatch.setattr(agy_classify, "AGY_BIN", binary)
    return binary


def runner_for(result, *, code=0, stderr="", seen=None):
    def run(argv, **kwargs):
        if seen is not None:
            schema_path = argv[argv.index("--json-schema") + 1]
            seen.update(argv=argv, kwargs=kwargs,
                        schema=json.loads(open(schema_path, encoding="utf-8").read()))
        return subprocess.CompletedProcess(argv, code, json.dumps(result) if result is not None else "", stderr)
    return run


def success(**changes):
    return {"status": "SUCCESS", "structured_output": {"decisions": []},
            "usage": {"output_tokens": 20767, "thinking_tokens": 20630}, **changes}


def test_classifies_headless_with_no_key_and_no_open_stdin(agy):
    seen = {}

    result = agy_classify.classify("data", SCHEMA, runner=runner_for(success(), seen=seen))

    argv = seen["argv"]
    assert result == {"decisions": []}
    assert argv[:2] == [str(agy), "-p"] and argv[2].startswith(agy_classify.NO_TOOLS)
    assert argv[argv.index("--model") + 1] == "gemini-3.8-flash"
    assert argv[argv.index("--effort") + 1] == "high"
    assert "--sandbox" in argv and "--disable-slash-commands" in argv
    assert "--dangerously-skip-permissions" not in argv
    assert seen["kwargs"]["stdin"] is subprocess.DEVNULL
    assert seen["schema"] == SCHEMA
    assert not any("GEMINI" in str(part) for part in argv)


def test_an_attempted_tool_voids_the_answer(agy):
    denied = success(denied_actions=[{"action": "command", "display_name": "RunCommand"}])

    with pytest.raises(agy_classify.ClassifierUnavailable, match="attempted a tool"):
        agy_classify.classify("data", SCHEMA, runner=runner_for(denied))


@pytest.mark.parametrize("result, code, message", [
    (success(status="ERROR"), 0, "status ERROR"),
    (success(structured_output=None), 0, "no structured output"),
    (success(usage={"output_tokens": 3000, "thinking_tokens": 1000}), 0, "over the 1000 budget"),
    (None, 0, "no JSON result"),
    (success(), 1, "exited 1"),
])
def test_unusable_results_are_refused(agy, result, code, message):
    with pytest.raises(agy_classify.ClassifierUnavailable, match=message):
        agy_classify.classify("data", SCHEMA, runner=runner_for(result, code=code, stderr="boom"))


def test_oversized_prompt_and_missing_cli_fail_before_any_call(agy, monkeypatch):
    calls = []

    with pytest.raises(agy_classify.ClassifierUnavailable, match="6000-byte"):
        agy_classify.classify("x" * 7000, SCHEMA, runner=lambda *a, **k: calls.append(1))
    monkeypatch.setattr(agy_classify, "AGY_BIN", agy.parent / "missing")
    with pytest.raises(agy_classify.ClassifierUnavailable, match="not installed"):
        agy_classify.classify("data", SCHEMA, runner=lambda *a, **k: calls.append(1))
    assert calls == []
