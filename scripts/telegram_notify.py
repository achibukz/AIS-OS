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
from pathlib import Path

CONFIG_DIR = Path.home() / ".config" / "achios"
TELEGRAM_ENV = CONFIG_DIR / "telegram.env"
TELEGRAM_LIMIT = 4096


def read_env() -> dict[str, str]:
    try:
        raw = TELEGRAM_ENV.read_text(encoding="utf-8", errors="replace")
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


def load_config() -> tuple[str, str]:
    """Bot token and chat id. Environment wins so a job can override per-run."""
    values = read_env()
    token = os.environ.get("TELEGRAM_BOT_TOKEN") or values.get("TELEGRAM_BOT_TOKEN", "")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID") or values.get("TELEGRAM_CHAT_ID", "")
    if not token or not chat_id:
        raise SystemExit(f"Missing TELEGRAM_BOT_TOKEN / TELEGRAM_CHAT_ID. Fill in {TELEGRAM_ENV}")
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


def send(*messages: str) -> int:
    """Send each message, splitting any that exceed Telegram's limit.

    Returns the number of Telegram messages actually sent.
    """
    import requests

    token, chat_id = load_config()
    parts = [part for message in messages for part in split_messages(message)]
    for part in parts:
        response = requests.post(
            f"https://api.telegram.org/bot{token}/sendMessage",
            json={"chat_id": chat_id, "text": part, "disable_web_page_preview": True},
            timeout=30,
        )
        if not response.ok:
            raise SystemExit(
                f"Telegram rejected the message: {response.status_code} {response.text}"
            )
    return len(parts)


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
