#!/usr/bin/env python3
"""VIP Email & Action Item Triage -> Telegram (achinouncements).

Scans authenticated Google inboxes (Personal & Work) for unread, high-signal
messages (professors, recruiters, direct correspondence, financial notices, security alerts),
filtering out marketing spam, job board blasts, and newsletter noise.

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
from dataclasses import dataclass
from pathlib import Path
from zoneinfo import ZoneInfo

# Add scripts directory to sys.path to import telegram_notify
SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))
from telegram_notify import send

CONFIG_DIR = Path.home() / ".config" / "achios"
GOOGLE_TOKENS = [
    (CONFIG_DIR / "google_token_dlsu.json", "🎓 DLSU School"),
    (CONFIG_DIR / "google_token_work.json", "💼 Work / Career"),
    (CONFIG_DIR / "google_token.json", "📬 Personal"),
    (CONFIG_DIR / "google_token_main.json", "👤 Main Personal"),
]
LOCAL_TZ = ZoneInfo("Asia/Manila")

# Automated blast keywords to ignore
IGNORE_PATTERNS = [
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
    account: str
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
    if any(k in combined for k in ["application", "interview", "rohde", "ing", "failed", "security", "bank", "bpi", "tonik", "dlsu", "professor"]):
        return "priority"
    if any(k in combined for k in ["invitation", "accepted your", "connection", "linkedin"]):
        return "network"
    return "general"


def fetch_actionable_emails() -> tuple[list[EmailItem], int]:
    """Fetch unread actionable emails across all accounts."""
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials
    from googleapiclient.discovery import build

    actionable: list[EmailItem] = []
    filtered_noise_count = 0

    for token_path, account_label in GOOGLE_TOKENS:
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
                        account=account_label,
                        sender=sender,
                        subject=subject,
                        snippet=snippet[:100].strip(),
                        category=category,
                    )
                )
        except Exception as e:
            print(f"Error checking {account_label}: {e}", file=sys.stderr)

    return actionable, filtered_noise_count


def build_email_digest(items: list[EmailItem], noise_count: int) -> str:
    now = dt.datetime.now(LOCAL_TZ)
    date_str = now.strftime("%b %d, %Y (%I:%M %p Manila)")

    lines = [
        "---------------------------------",
        "📬 Email Debrief",
        f"🗓 {date_str}",
        "",
    ]

    if not items:
        lines.append("🍃 Inboxes clear. No unread VIP action items or urgent correspondence.")
        if noise_count > 0:
            lines.append(f"\n💡 Filtered {noise_count} promotional/automated emails.")
        return "\n".join(lines).strip()

    priority_items = [it for it in items if it.category == "priority"]
    network_items = [it for it in items if it.category == "network"]
    general_items = [it for it in items if it.category == "general"]

    if priority_items:
        lines.append("🚨 PRIORITY & ACTION ITEMS:")
        for it in priority_items[:4]:
            lines.append(f"• {it.sender} — {it.subject} ({it.account})")
        lines.append("")

    if network_items:
        lines.append("👥 NETWORK & CORRESPONDENCE:")
        for it in network_items[:4]:
            lines.append(f"• {it.sender} — {it.subject}")
        lines.append("")

    if general_items and not priority_items:
        lines.append("📌 OTHER RECENT INBOX:")
        for it in general_items[:3]:
            lines.append(f"• {it.sender} — {it.subject}")
        lines.append("")

    total_shown = min(len(priority_items), 4) + min(len(network_items), 4) + (min(len(general_items), 3) if not priority_items else 0)
    lines.append(f"💡 {total_shown} action items surfaced • {noise_count} promotional/noise emails filtered")
    return "\n".join(lines).strip()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print the email digest without sending to Telegram",
    )
    args = parser.parse_args()

    items, noise_count = fetch_actionable_emails()
    digest = build_email_digest(items, noise_count)

    if args.dry_run:
        print("=== DRY RUN (Not sending) ===")
        print(digest)
        return 0

    print(f"[{dt.datetime.now().isoformat()}] Sending email triage digest to Telegram...")
    count = send(digest)
    print(f"Successfully sent {count} message(s) to Telegram.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
