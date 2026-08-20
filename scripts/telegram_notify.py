#!/usr/bin/env python3
"""Send text to Aki's achiOS Telegram bot.

Shared by every scheduled job on achibuntu that reports to Telegram. Import it
rather than re-implementing the send — one place holds the credential contract
and the 4096-character split.

    from telegram_notify import send
    send("job finished, 3 rows changed")

Credentials live in ~/.config/achios/telegram.env (mode 600), never in the repo.
"""

from __future__ import annotations

import os
import time
from pathlib import Path

CONFIG_DIR = Path.home() / ".config" / "achios"
TELEGRAM_ENV = CONFIG_DIR / "telegram.env"
TELEGRAM_LIMIT = 4096

MAX_ATTEMPTS = 4
RETRY_BACKOFF_S = 2
RETRY_STATUSES = frozenset({429, 500, 502, 503, 504})
RETRY_SLEEP = time.sleep


def redact(text: str, token: str) -> str:
    """Strip the bot token out of anything heading for a log.

    requests puts the request URL in its exception messages, and the URL carries
    the token. Unredacted, a single network blip writes the credential into
    journald in cleartext, which is exactly what happened on 2026-08-20.
    """
    if not token:
        return text
    return text.replace(token, "<REDACTED>")


def read_env(env_path: Path | str | None = None) -> dict[str, str]:
    target = Path(env_path) if env_path else TELEGRAM_ENV
    try:
        raw = target.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return {}
    return dict(
        (key.strip(), value.strip())
        for key, value in (
            line.split("=", 1)
            for line in raw.splitlines()
            if "=" in line and not line.lstrip().startswith("#")
        )
    )


def load_config(env_path: Path | str | None = None) -> tuple[str, str]:
    """Bot token and chat id. Prioritizes the env file to avoid parent daemon env hijacking."""
    target = Path(env_path) if env_path else TELEGRAM_ENV
    values = read_env(target)
    token = values.get("TELEGRAM_BOT_TOKEN") or os.environ.get("TELEGRAM_BOT_TOKEN", "")
    chat_id = values.get("TELEGRAM_CHAT_ID") or os.environ.get("TELEGRAM_CHAT_ID", "")
    if not token or not chat_id:
        raise SystemExit(f"Missing TELEGRAM_BOT_TOKEN / TELEGRAM_CHAT_ID. Fill in {target}")
    return token, chat_id



def split_messages(message: str, limit: int = TELEGRAM_LIMIT) -> list[str]:
    """Split on blank lines so a section never straddles two Telegram messages."""
    chunks: list[str] = []
    current = ""
    for block in message.split("\n\n"):
        candidate = f"{current}\n\n{block}" if current else block
        if len(candidate) <= limit:
            current = candidate
            continue
        if current:
            chunks.append(current)
        while len(block) > limit:
            head, _, block = block[:limit].rpartition("\n")
            chunks.append(head or block[:limit])
        current = block
    if current:
        chunks.append(current)
    return chunks


def send(*messages: str, env_path: Path | str | None = None) -> int:
    """Send each message, splitting any that exceed Telegram's limit.

    Returns the number of Telegram messages actually sent.
    """
    import requests

    token, chat_id = load_config(env_path=env_path)
    parts = [part for message in messages for part in split_messages(message)]
    for part in parts:
        _send_one(requests, token, chat_id, part)
    return len(parts)


def _send_one(requests, token: str, chat_id: str, part: str) -> None:
    """Post one message, retrying only what a retry can actually fix.

    Network errors, 429 and 5xx are transient, so they are retried with a growing
    backoff. Every other 4xx means the request itself is wrong and retrying would
    just burn the same failure three more times.
    """
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    last_error = ""

    for attempt in range(1, MAX_ATTEMPTS + 1):
        try:
            response = requests.post(
                url,
                json={"chat_id": chat_id, "text": part, "disable_web_page_preview": True},
                timeout=30,
            )
        except requests.RequestException as exc:
            last_error = redact(f"{type(exc).__name__}: {exc}", token)
        else:
            if response.ok:
                return
            last_error = redact(
                f"Telegram rejected the message: {response.status_code} {response.text}",
                token,
            )
            if response.status_code not in RETRY_STATUSES:
                raise SystemExit(last_error)
            if response.status_code == 429:
                delay = _retry_after(response)
                if delay is not None:
                    if attempt < MAX_ATTEMPTS:
                        RETRY_SLEEP(delay)
                    continue

        if attempt < MAX_ATTEMPTS:
            RETRY_SLEEP(RETRY_BACKOFF_S ** attempt)

    raise SystemExit(f"Telegram send failed after {MAX_ATTEMPTS} attempts. {last_error}")


def _retry_after(response) -> int | None:
    """Telegram tells you how long to wait on a 429. Honour it rather than guess."""
    try:
        value = response.json().get("parameters", {}).get("retry_after")
    except Exception:
        return None
    return value if isinstance(value, int) else None


def find_chat_ids() -> int:
    """Print chat ids that have messaged the bot. Never prints the token."""
    import requests

    token = os.environ.get("TELEGRAM_BOT_TOKEN") or read_env().get("TELEGRAM_BOT_TOKEN", "")
    if not token:
        raise SystemExit(f"No TELEGRAM_BOT_TOKEN set. Fill it in at {TELEGRAM_ENV}")

    response = requests.get(f"https://api.telegram.org/bot{token}/getUpdates", timeout=30)
    if not response.ok:
        raise SystemExit(f"Telegram said {response.status_code}. Is the token right?")

    chats = {}
    for update in response.json().get("result", []):
        chat = next((v["chat"] for v in update.values() if isinstance(v, dict) and "chat" in v), None)
        if chat:
            name = chat.get("username") or chat.get("title") or chat.get("first_name", "?")
            chats[chat["id"]] = f"{name} ({chat.get('type', '?')})"

    if not chats:
        print("No messages yet. Send your bot any message from Telegram, then re-run this.")
        return 1
    for chat_id, label in chats.items():
        print(f"{chat_id}\t{label}")
    print(f"\nPut the id in TELEGRAM_CHAT_ID= in {TELEGRAM_ENV}")
    return 0


if __name__ == "__main__":
    raise SystemExit(find_chat_ids())
