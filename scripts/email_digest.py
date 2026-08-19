#!/usr/bin/env python3
"""Email Debrief -> Telegram (achinouncements & achiSchooNounce).

Scans authenticated Google inboxes and sends separate debrief messages:
1. 🎓 DLSU School Email (abram_bukuhan@dlsu.edu.ph) -> @achiSchooNounceBot (telegram_school.env)
2. 💼 Work / Career Email (akibukzwork@gmail.com) -> @achiOSBot (telegram.env)
3. 📬 Personal & Security Alerts (akibukuhan10@gmail.com) -> @achiOSBot (only if priority/security items exist)

Scheduled: 08:30 AM, 05:30 PM, and 09:00 PM Manila time.

Usage:
    python scripts/email_digest.py                  # Fetch, synthesize with LLM, and send
    python scripts/email_digest.py --dry-run        # Print only without sending
    python scripts/email_digest.py --raw            # Skip LLM pass and use deterministic fallback
    python scripts/email_digest.py --account dlsu   # Run only for a specific account
"""

from __future__ import annotations

import argparse
import datetime as dt
import html
import os
import re
import subprocess
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
LLM_DIR = Path.home() / ".local" / "share" / "achios" / "llm"
LOCAL_TZ = ZoneInfo("Asia/Manila")

ACCOUNT_CONFIGS = [
    {
        "id": "dlsu",
        "type": "school",
        "title": "🎓 DLSU School Email",
        "tokens": [CONFIG_DIR / "google_token_dlsu.json"],
        "env_file": CONFIG_DIR / "telegram_school.env",
    },
    {
        "id": "work",
        "type": "work",
        "title": "💼 Work / Career Email",
        "tokens": [CONFIG_DIR / "google_token_work.json"],
        "env_file": None,
    },
    {
        "id": "personal",
        "type": "personal",
        "title": "📬 Personal & Security Alerts",
        "tokens": [CONFIG_DIR / "google_token.json"],
        "env_file": None,
    },
]

# Automated blast & irrelevant marketing keywords to ignore
GENERAL_IGNORE_PATTERNS = [
    r"\bpromo\b",
    r"\bdiscount\b",
    r"off select",
    r"%\s*off",
    r"\bsale\b",
    r"billie eilish",
    r"codecademy",
    r"twitch\.tv",
    r"grammarly",
    r"newsletter",
    r"unsubscribe",
    r"terms of use",
    r"services agreement",
    r"privacy policy update",
    r"welcome to openrouter",
    r"welcome to google",
    r"welcome to",
    r"drops\?",
    r"support every gastos",
    r"cashback",
    r"voucher",
    r"points balance",
    r"weekly digest",
    r"what you missed",
    r"sales invoice is (now )?available",
    r"sales invoice is ready",
]

# LinkedIn / Indeed automated activity & job blasts to ignore
JOB_BOARD_IGNORE_PATTERNS = [
    r"jobalerts-noreply@linkedin\.com",
    r"jobs picked for you",
    r"more internship jobs",
    r"job alert",
    r"recommended jobs",
    r"new jobs matching",
    r"job opportunity from",
    r"hiring on linkedin",
    r"linkedin hiring",
    r"hiring pro",
    r"does hiring feel like",
    r"accepted your invitation",
    r"invitation to connect",
    r"viewed your profile",
    r"celebrates a work anniversary",
    r"is waiting for your response",
    r"explore their network",
    r"looks like your background could be a match",
    r"recommended for you on indeed",
    r"new job opportunities on indeed",
]

# HDA urgent / emergency keywords that MUST NOT be ignored
HDA_URGENT_KEYWORDS = [
    "suspension",
    "suspended",
    "weather",
    "typhoon",
    "flood",
    "signal no",
    "signal #",
    "urgent",
    "alert",
    "closure",
    "evacuation",
    "holiday",
    "emergency",
    "curfew",
    "cancelled",
    "canceled",
    "enrollment deadline",
    "grade submission",
]


@dataclass
class EmailItem:
    sender: str
    subject: str
    snippet: str
    category: str = "general"
    date_str: str = ""


def sanitize_text(text: str) -> str:
    """Strip zero-width characters and excessive whitespace."""
    text = html.unescape(text)
    # Remove zero-width spaces, joiners, and soft hyphens
    text = re.sub(r"[\ufeff\u200b\u200c\u200d\u200e\u200f\u034f\u00ad\xa0]+", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def clean_sender(raw: str) -> str:
    """Extract clean display name or email from 'Name <email>' format."""
    raw = sanitize_text(raw)
    match = re.match(r'^"?([^"<]+)"?\s*<.*>$', raw)
    if match:
        name = match.group(1).strip()
        return name if name else raw
    return raw.strip('"\'')


def is_noise(from_hdr: str, subject: str, snippet: str, account_type: str = "general") -> bool:
    """Detect if an email is marketing noise, automated job blast, or routine unneeded HDA."""
    combined = f"{from_hdr} {subject} {snippet}".lower()

    # 0. Whitelist active GitHub developer notifications (PRs, reviews, collaborator invites, mentions)
    is_github_dev = "github" in combined and any(k in combined for k in [
        "pull request", "pr #", "requested your review", "review requested", "collaborator",
        "issue #", "assigned", "mentioned in", "commented on", "[achibukz/",
    ])
    if is_github_dev:
        return False

    # 1. Check general noise patterns
    for pat in GENERAL_IGNORE_PATTERNS:
        if re.search(pat, combined):
            return True

    # 2. Check LinkedIn / Indeed automated alerts & connection spam
    for pat in JOB_BOARD_IGNORE_PATTERNS:
        if re.search(pat, combined):
            return True

    # 3. Check Laguna-only campus notices (Aki is DLSU Manila campus only)
    if account_type == "school":
        if "laguna" in combined and not any(k in combined for k in ["manila", "all campuses", "system-wide", "taft"]):
            return True

    # 4. Check Routine HDA (Help Desk Announcement) digests
    is_hda = (
        "help desk announcement" in from_hdr.lower()
        or "[hda for community]" in subject.lower()
        or (subject.lower().startswith("hda") and "community" in combined)
    )
    if is_hda:
        # Keep HDA ONLY if it mentions suspensions, weather, typhoons, or emergencies
        has_urgent_keyword = any(k in combined for k in HDA_URGENT_KEYWORDS)
        if not has_urgent_keyword:
            return True

    return False


def categorize_email(from_hdr: str, subject: str, snippet: str, account_type: str = "general") -> str:
    """Categorize email into priority, academic/work, or general."""
    combined = f"{from_hdr} {subject} {snippet}".lower()

    # --- SCHOOL ACCOUNT ---
    if account_type == "school":
        # 1. High Priority & VIP: Suspensions, emergency, professors & recommendation letters
        is_suspension = any(k in combined for k in ["suspension", "suspended", "typhoon", "weather advisory", "signal no", "campus closure"])
        is_prof_or_rec = any(k in combined for k in [
            "samson", "briane", "recommendation", "recommendation letter", "endorsement",
            "thesis 1", "ths-st1", "thsst1", "thesis adviser", "defense", "clearance",
        ])
        is_direct_prof_reply = "re:" in subject.lower() and "@dlsu.edu.ph" in from_hdr.lower() and not is_noise(from_hdr, subject, snippet, account_type)

        if is_suspension or is_prof_or_rec or is_direct_prof_reply:
            return "priority"

        # 2. Courses & Academics: AnimoSpace / Canvas, courses, ITEO, registrar
        is_course_or_lms = any(k in combined for k in [
            "animospace", "canvas", "instructure", "assignment", "quiz", "announcement:", "submission",
            "stcloud", "csopesy", "stsp001", "pedfour", "iteo", "online evaluation", "evaluation",
            "registrar", "enrollment", "course offering", "grades",
        ])
        if is_course_or_lms:
            return "academic"

        return "general"

    # --- WORK / CAREER ACCOUNT ---
    if account_type == "work":
        # 1. High Priority & VIP: ING Hubs Philippines, recruiters, interview invites, critical security, GitHub collaborator PR reviews
        is_ing = any(k in combined for k in ["ing hubs", "ing hub", "retail tech", "ing bank", "@ing.com", "vanscell", "nierra"])
        is_recruiter = any(k in combined for k in [
            "interview", "offer", "assessment", "application status", "recruiter", "invitation to interview",
            "next steps", "technical test", "take-home", "hiring manager",
        ])
        is_critical_security = any(k in combined for k in [
            "security alert", "unauthorized", "password reset", "verification code", "failed login",
            "action required", "breach", "critical alert", "security update is live",
        ])
        is_github_collab_action = "github" in combined and any(k in combined for k in [
            "requested your review", "review requested", "collaborator", "pull request", "pr #", "assigned",
        ])

        if is_ing or is_recruiter or is_critical_security or is_github_collab_action:
            return "priority"

        # 2. Work & Recruiting: Direct human messages & general GitHub/LinkedIn activity
        if "linkedin" in from_hdr.lower() or "application" in combined or "github" in combined:
            return "work_recruiting"

        return "general"

    # --- PERSONAL / SECURITY ACCOUNT ---
    if account_type == "personal":
        is_bank_or_security = any(k in combined for k in [
            "bpi", "tonik", "gcash", "security alert", "unauthorized", "fraud", "card blocked",
            "otp", "authentication", "aws", "gcp", "google cloud", "github security", "billing alert",
        ])
        if is_bank_or_security:
            return "priority"
        return "general"

    return "general"


def fetch_account_emails(token_paths: list[Path], account_type: str = "general") -> tuple[list[EmailItem], int]:
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
            res = service.users().messages().list(userId="me", q=query, maxResults=25).execute()
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
                from_hdr = sanitize_text(headers.get("From", "Unknown"))
                subject = sanitize_text(headers.get("Subject", "(No Subject)"))
                date_hdr = sanitize_text(headers.get("Date", ""))
                snippet = sanitize_text(msg.get("snippet", ""))

                if is_noise(from_hdr, subject, snippet, account_type=account_type):
                    filtered_noise_count += 1
                    continue

                category = categorize_email(from_hdr, subject, snippet, account_type=account_type)
                sender = clean_sender(from_hdr)
                actionable.append(
                    EmailItem(
                        sender=sender,
                        subject=subject,
                        snippet=snippet[:250].strip(),
                        category=category,
                        date_str=date_hdr,
                    )
                )
        except Exception as e:
            print(f"Error checking {token_path.name}: {e}", file=sys.stderr)

    return actionable, filtered_noise_count


def synthesize_account_emails_llm(title: str, account_type: str, items: list[EmailItem]) -> str | None:
    """Pass emails to Gemini via `agy -p` in ~/.local/share/achios/llm for smart contextual synthesis."""
    if not items:
        return None

    sec2_header = "📚 COURSES & ACADEMICS" if account_type == "school" else ("💼 WORK & RECRUITING" if account_type == "work" else "🔒 SECURITY & FINANCE")

    email_payloads = []
    for idx, it in enumerate(items, start=1):
        email_payloads.append(
            f"[{idx}] Sender: {it.sender}\n"
            f"    Subject: {it.subject}\n"
            f"    Initial Tag: {it.category}\n"
            f"    Snippet: {it.snippet}\n"
        )
    emails_text = "\n".join(email_payloads)

    prompt = f"""You are the email intelligence synthesis engine for Aki Bukuhan.
Aki's Context:
- Third-year BS Computer Science student at DLSU-Manila.
- Thesis (THS-ST1) advised by Dr. Briane Paul V. Samson.
- Current Term courses: STCLOUD, CSOPESY, STSP001, PEDFOUR, THS-ST1. Also alert to future term course notices.
- Incoming Retail Tech Intern at ING Hubs Philippines (starts October 2026).
- High priority to Aki: Manila campus class suspensions, professor replies (especially recommendation letters), ING internship onboarding/HR communications, recruiter interview invites, and bank/account security alerts.

Task:
Analyze and synthesize the following {len(items)} unread emails for account: {title}.

--- EMAILS RECEIVED ---
{emails_text}

--- OUTPUT FORMAT REQUIREMENTS ---
Group surfaced items under these standard section headers (include a section ONLY if there are items for it):
⚡ HIGH PRIORITY & VIP
{sec2_header}
📬 UPDATES & GENERAL

For each item, format strictly as:
• Sender — Subject
      Indented 1-line summary: concise, factual takeaway of what was communicated and what action Aki needs to take (e.g. reply needed, deadline date, confirmed recommendation, suspension details).

Rules:
1. Indent the summary line exactly 6 spaces under each bullet.
2. Filter out any remaining pure spam, marketing, or routine noise that slipped through.
3. If an email is routine or low priority (like ITEO evaluation or Canvas announcement), place it under {sec2_header} or 📬 UPDATES & GENERAL rather than HIGH PRIORITY.
4. Output ONLY the sections and bullets. Do not include markdown preamble, conversational filler, or greeting.
5. If all items were filtered out as noise, output exactly: INBOX_CLEAR
"""

    try:
        LLM_DIR.mkdir(parents=True, exist_ok=True)
        res = subprocess.run(
            ["agy", "-p", prompt],
            cwd=str(LLM_DIR),
            capture_output=True,
            text=True,
            timeout=45,
        )
        if res.returncode == 0 and res.stdout.strip():
            output = res.stdout.strip()
            if output == "INBOX_CLEAR":
                return "INBOX_CLEAR"
            # Ensure it contains bullet points
            if "•" in output or "HIGH PRIORITY" in output or "UPDATES" in output:
                return output
    except Exception as e:
        print(f"LLM synthesis warning: {e}", file=sys.stderr)

    return None


def build_account_message_raw(title: str, account_type: str, items: list[EmailItem], noise_count: int) -> str:
    """Deterministic fallback message builder when LLM is offline or in raw mode."""
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
            lines.append(f"\n💡 Filtered {noise_count} routine/promotional emails.")
        return "\n".join(lines).strip()

    sec2_title = "📚 COURSES & ACADEMICS" if account_type == "school" else ("💼 WORK & RECRUITING" if account_type == "work" else "🔒 SECURITY & FINANCE")

    priority_items = [it for it in items if it.category == "priority"]
    secondary_items = [it for it in items if it.category in ("academic", "work_recruiting")]
    general_items = [it for it in items if it.category == "general"]

    if priority_items:
        lines.append("⚡ HIGH PRIORITY & VIP:")
        for it in priority_items:
            lines.append(f"• {it.sender} — {it.subject}")
            if it.snippet:
                snippet_preview = it.snippet[:120].replace("\n", " ").strip()
                lines.append(f"      {snippet_preview}")
        lines.append("")

    if secondary_items:
        lines.append(f"{sec2_title}:")
        for it in secondary_items:
            lines.append(f"• {it.sender} — {it.subject}")
            if it.snippet:
                snippet_preview = it.snippet[:120].replace("\n", " ").strip()
                lines.append(f"      {snippet_preview}")
        lines.append("")

    if general_items and not priority_items and not secondary_items:
        lines.append("📬 UPDATES & GENERAL:")
        for it in general_items[:3]:
            lines.append(f"• {it.sender} — {it.subject}")
            if it.snippet:
                snippet_preview = it.snippet[:120].replace("\n", " ").strip()
                lines.append(f"      {snippet_preview}")
        lines.append("")

    total_surfaced = len(priority_items) + len(secondary_items) + (min(len(general_items), 3) if not priority_items and not secondary_items else 0)
    lines.append(f"💡 {total_surfaced} items surfaced • {noise_count} routine/promo emails filtered")
    return "\n".join(lines).strip()


def build_account_message(
    title: str,
    account_type: str,
    items: list[EmailItem],
    noise_count: int,
    raw_mode: bool = False,
) -> str:
    """Build the final account message using LLM synthesis or deterministic fallback."""
    now = dt.datetime.now(LOCAL_TZ)
    date_str = now.strftime("%b %d, %Y (%I:%M %p Manila)")

    if not items:
        lines = [
            "---------------------------------",
            f"{title} Debrief",
            f"🗓 {date_str}",
            "",
            "🍃 Inbox clear. No unread VIP action items or urgent correspondence.",
        ]
        if noise_count > 0:
            lines.append(f"\n💡 Filtered {noise_count} routine/promotional emails.")
        return "\n".join(lines).strip()

    if not raw_mode:
        llm_body = synthesize_account_emails_llm(title, account_type, items)
        if llm_body == "INBOX_CLEAR":
            lines = [
                "---------------------------------",
                f"{title} Debrief",
                f"🗓 {date_str}",
                "",
                "🍃 Inbox clear. All incoming items filtered as routine noise.",
            ]
            if noise_count > 0:
                lines.append(f"\n💡 Filtered {noise_count + len(items)} routine/promotional emails.")
            return "\n".join(lines).strip()

        if llm_body:
            # Count bullet points surfaced by LLM
            surfaced_count = llm_body.count("•")
            lines = [
                "---------------------------------",
                f"{title} Debrief",
                f"🗓 {date_str}",
                "",
                llm_body,
                "",
                f"💡 {surfaced_count} items surfaced • {noise_count} routine/promo emails filtered",
            ]
            return "\n".join(lines).strip()

    return build_account_message_raw(title, account_type, items, noise_count)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print the email debrief messages without sending to Telegram",
    )
    parser.add_argument(
        "--raw",
        action="store_true",
        help="Skip LLM synthesis pass and use deterministic fallback layout",
    )
    parser.add_argument(
        "--account",
        choices=["dlsu", "work", "personal"],
        help="Run only for a specific account",
    )
    args = parser.parse_args()

    messages_to_send: list[tuple[str, str, Path | None]] = []

    for acc in ACCOUNT_CONFIGS:
        if args.account and acc["id"] != args.account:
            continue

        existing_tokens = [p for p in acc["tokens"] if p.exists()]
        if not existing_tokens:
            continue

        items, noise_count = fetch_account_emails(existing_tokens, account_type=acc["type"])

        # For personal account: only dispatch if high-priority/security items exist
        if acc["type"] == "personal":
            priority_items = [it for it in items if it.category == "priority"]
            if not priority_items:
                if args.dry_run:
                    print(f"[{acc['title']}] Skipping personal email debrief (0 security/VIP items).")
                continue
            items = priority_items

        msg = build_account_message(
            title=acc["title"],
            account_type=acc["type"],
            items=items,
            noise_count=noise_count,
            raw_mode=args.raw,
        )
        messages_to_send.append((acc["title"], msg, acc.get("env_file")))

    if not messages_to_send:
        print("No debrief messages generated.")
        return 0

    if args.dry_run:
        print("=== DRY RUN (Separate Messages) ===\n")
        for title, msg, env_file in messages_to_send:
            dest = f" -> {env_file.name}" if env_file and env_file.exists() else " -> default telegram.env"
            print(f"--- [MESSAGE FOR {title}{dest}] ---")
            print(msg)
            print("\n" + "=" * 40 + "\n")
        return 0

    print(f"[{dt.datetime.now().isoformat()}] Sending {len(messages_to_send)} email debrief messages to Telegram...")
    total_sent = 0
    for title, msg, env_file in messages_to_send:
        env_target = env_file if env_file and env_file.exists() else None
        if env_target:
            print(f"Using dedicated credentials from {env_target} for {title}...")
        sent_count = send(msg, env_path=env_target)
        total_sent += sent_count
        time.sleep(0.5)

    print(f"Successfully sent {total_sent} message(s) to Telegram.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
