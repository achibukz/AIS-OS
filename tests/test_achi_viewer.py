from pathlib import Path
import os
import pytest
from scripts.achi_viewer import is_blocked, is_secrets_allowed, ALLOW_SECRETS_FILE

def test_is_blocked_default(monkeypatch, tmp_path):
    fake_flag = tmp_path / "allow_secrets"
    monkeypatch.setattr("scripts.achi_viewer.ALLOW_SECRETS_FILE", fake_flag)
    monkeypatch.delenv("ACHI_VIEWER_ALLOW_SECRETS", raising=False)

    assert is_secrets_allowed() is False
    assert is_blocked(Path("/home/achibukz/.env")) is True
    assert is_blocked(Path("/home/achibukz/id_rsa")) is True
    assert is_blocked(Path("/home/achibukz/Documents/Files/personal/legal/doc.pdf")) is True
    assert is_blocked(Path("/home/achibukz/Code/GitHub/AIS-OS/README.md")) is False

def test_is_blocked_with_flag_file(monkeypatch, tmp_path):
    fake_flag = tmp_path / "allow_secrets"
    monkeypatch.setattr("scripts.achi_viewer.ALLOW_SECRETS_FILE", fake_flag)
    monkeypatch.delenv("ACHI_VIEWER_ALLOW_SECRETS", raising=False)

    fake_flag.touch()
    assert is_secrets_allowed() is True
    assert is_blocked(Path("/home/achibukz/.env")) is False
    assert is_blocked(Path("/home/achibukz/id_rsa")) is False
    assert is_blocked(Path("/home/achibukz/Documents/Files/personal/legal/doc.pdf")) is False

def test_is_blocked_with_env_var(monkeypatch, tmp_path):
    fake_flag = tmp_path / "allow_secrets"
    monkeypatch.setattr("scripts.achi_viewer.ALLOW_SECRETS_FILE", fake_flag)
    monkeypatch.setenv("ACHI_VIEWER_ALLOW_SECRETS", "1")

    assert is_secrets_allowed() is True
    assert is_blocked(Path("/home/achibukz/.env")) is False
