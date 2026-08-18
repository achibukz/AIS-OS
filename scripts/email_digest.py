#!/usr/bin/env python3
"""Email Debrief -> Telegram (achinouncements).

Scans authenticated Google inboxes and sends THREE separate messages:
1. 🎓 DLSU School Email (abram_bukuhan@dlsu.edu.ph)
2. 💼 Work / Career Email (akibukzwork@gmail.com)
3. 📬 Personal / Main Email (akibukuhan10@gmail.com / aki.bukz12@gmail.com)

Scheduled twice daily: 08:30 AM & 05:30 PM Manila time.

Usage:
    python scripts/email_digest.py           # Fetch and send
    python scripts/email_digest.py --dry-run # Print only
"""

from __future__ import annotations

import argparse
import datetime as dt
import html
import re
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from zoneinfo import ZoneInfo

# Add scripts directory to sys.path to import telegram_notify
SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))
from telegram_notify import send

CONFIG_DIR = Path.home() / ".config" / "achios"

ACCOUNT_CONFIGS = [
    {
        "id": "dlsu",
        "title": "🎓 DLSU School Email",
        "tokens": [CONFIG_DIR / "google_token_dlsu.json"],
        "env_file": CONFIG_DIR / "telegram_school.env",
    },
    {
        "id": "work",
        "title": "💼 Work / Career Email",
        "tokens": [CONFIG_DIR / "google_token_work.json"],
        "env_file": None,
    },
]

LOCAL_TZ = ZoneInfo("Asia/Manila")

# Automated blast & irrelevant keywords to ignore
IGNORE_PATTERNS = [
    r"laguna",  # Aki is Manila campus only
    r"promo",
    r"discount",
    r"off select",
    r"% off",
    r"sale\b",
    r"billie eilish",
    r"codecademy",
    r"twitch\.tv",
    r"newsletter",
    r"unsubscribe",
    r"terms of use",
    r"services agreement",
    r"jobs picked for you",
    r"more internship jobs",
    r"is waiting for your response",
    r"welcome to openrouter",
    r"welcome to google",
    r"drops\?",
]


@dataclass
class EmailItem:
    sender: str
    subject: str
    snippet: str
    category: str = "general"


def clean_sender(raw: str) -> str:
    """Extract clean display name or email from 'Name <email>' format."""
    raw = html.unescape(raw).strip()
    match = re.match(r'^"?([^"<]+)"?\s*<.*>$', raw)
    if match:
        name = match.group(1).strip()
        return name if name else raw
    return raw


def is_noise(from_hdr: str, subject: str, snippet: str) -> bool:
    """Detect if an email is marketing noise, automated job blast, or promo."""
    combined = f"{from_hdr} {subject} {snippet}".lower()
    for pat in IGNORE_PATTERNS:
        if re.search(pat, combined):
            return True
    return False


def categorize_email(from_hdr: str, subject: str, snippet: str) -> str:
    """Categorize into priority vs network vs general."""
    combined = f"{from_hdr} {subject} {snippet}".lower()
    if any(k in combined for k in ["application", "interview", "rohde", "ing", "failed", "security", "bank", "bpi", "tonik", "dlsu", "professor", "hda", "ovplc", "final exam", "evaluation"]):
        return "priority"
    if any(k in combined for k in ["invitation", "accepted your", "connection", "linkedin"]):
        return "network"
    return "general"


def fetch_account_emails(token_paths: list[Path]) -> tuple[list[EmailItem], int]:
    """Fetch unread actionable emails for a specific account."""
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials
    from googleapiclient.discovery import build

    actionable: list[EmailItem] = []
    filtered_noise_count = 0

    for token_path in token_paths:
        if not token_path.exists():
            continue

        try:
            creds = Credentials.from_authorized_user_file(str(token_path))
            if creds.expired and creds.refresh_token:
                creds.refresh(Request())
                token_path.write_text(creds.to_json(), encoding="utf-8")

            service = build("gmail", "v1", credentials=creds, cache_discovery=False)
            
            # Query unread messages in inbox from last 2 days
            query = "in:inbox is:unread newer_than:2d"
            res = service.users().messages().list(userId="me", q=query, maxResults=20).execute()
            messages = res.get("messages", [])

            for m in messages:
                msg = (
                    service.users()
                    .messages()
                    .get(
                        userId="me",
                        id=m["id"],
                        format="metadata",
                        metadataHeaders=["From", "Subject", "Date"],
                    )
                    .execute()
                )
                headers = {h["name"]: h["value"] for h in msg.get("payload", {}).get("headers", [])}
                from_hdr = headers.get("From", "Unknown")
                subject = headers.get("Subject", "(No Subject)")
                snippet = html.unescape(msg.get("snippet", ""))

                if is_noise(from_hdr, subject, snippet):
                    filtered_noise_count += 1
                    continue

                category = categorize_email(from_hdr, subject, snippet)
                sender = clean_sender(from_hdr)
                actionable.append(
                    EmailItem(
                        sender=sender,
                        subject=subject,
                        snippet=snippet[:100].strip(),
                        category=category,
                    )
                )
        except Exception as e:
            print(f"Error checking {token_path.name}: {e}", file=sys.stderr)

    return actionable, filtered_noise_count


def build_account_message(title: str, items: list[EmailItem], noise_count: int) -> str:
    now = dt.datetime.now(LOCAL_TZ)
    date_str = now.strftime("%b %d, %Y (%I:%M %p Manila)")

    lines = [
        "---------------------------------",
        f"{title} Debrief",
        f"🗓 {date_str}",
        "",
    ]

    if not items:
        lines.append("🍃 Inbox clear. No unread VIP action items or urgent correspondence.")
        if noise_count > 0:
            lines.append(f"\n💡 Filtered {noise_count} promotional/automated emails.")
        return "\n".join(lines).strip()

    priority_items = [it for it in items if it.category == "priority"]
    network_items = [it for it in items if it.category == "network"]
    general_items = [it for it in items if it.category == "general"]

    if priority_items:
        lines.append("🚨 PRIORITY & ACTION ITEMS:")
        for it in priority_items[:4]:
            lines.append(f"• {it.sender} — {it.subject}")
        lines.append("")

    if network_items:
        lines.append("👥 NETWORK & CORRESPONDENCE:")
        for it in network_items[:4]:
            lines.append(f"• {it.sender} — {it.subject}")
        lines.append("")

    if general_items and not priority_items and not network_items:
        lines.append("📌 RECENT INBOX:")
        for it in general_items[:3]:
            lines.append(f"• {it.sender} — {it.subject}")
        lines.append("")

    total_shown = min(len(priority_items), 4) + min(len(network_items), 4) + (min(len(general_items), 3) if not priority_items and not network_items else 0)
    lines.append(f"💡 {total_shown} action items surfaced • {noise_count} promotional emails filtered")
    return "\n".join(lines).strip()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print the three email debrief messages without sending to Telegram",
    )
    args = parser.parse_args()

    messages_to_send = []

    for acc in ACCOUNT_CONFIGS:
        # Check if at least one token exists for this account
        existing_tokens = [p for p in acc["tokens"] if p.exists()]
        if not existing_tokens:
            continue

        items, noise_count = fetch_account_emails(existing_tokens)
        msg = build_account_message(acc["title"], items, noise_count)
        messages_to_send.append((acc["title"], msg, acc.get("env_file")))

    if args.dry_run:
        print("=== DRY RUN (Separate Messages) ===\n")
        for title, msg, env_file in messages_to_send:
            dest = f" -> {env_file.name}" if env_file and env_file.exists() else " -> default telegram.env"
            print(f"--- [MESSAGE FOR {title}{dest}] ---")
            print(msg)
            print("\n" + "="*40 + "\n")
        return 0

    print(f"[{dt.datetime.now().isoformat()}] Sending {len(messages_to_send)} email debrief messages to Telegram...")
    total_sent = 0
    for title, msg, env_file in messages_to_send:
        env_target = env_file if env_file and env_file.exists() else None
        if env_target:
            print(f"Using dedicated credentials from {env_target} for {title}...")
        sent_count = send(msg, env_path=env_target)
        total_sent += sent_count
        time.sleep(0.5)  # Slight pause between messages for clean delivery

    print(f"Successfully sent {total_sent} message(s) to Telegram.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
