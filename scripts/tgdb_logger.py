#!/usr/bin/env python3
"""Universal Telegram Database (tgdb) Logger for achiOS.

Formats, sanitizes, and writes Telegram bot conversation sessions
into structured Markdown notes in achiMem/tgdb/YYYY-MM/.

Used across all Telegram bots:
- @achiOSClaudeBot
- @schoMemBot
- @achiAgyBot
- @schoMemAGYBot
"""

from __future__ import annotations

import datetime as dt
import html
import re
import sys
from pathlib import Path
from zoneinfo import ZoneInfo

LOCAL_TZ = ZoneInfo("Asia/Manila")

# Known secret patterns for automated redaction
SECRET_PATTERNS = [
    (re.compile(r"sk-ant-[a-zA-Z0-9_-]{20,}"), "[REDACTED_ANTHROPIC_KEY]"),
    (re.compile(r"AIzaSy[a-zA-Z0-9_-]{33}"), "[REDACTED_GOOGLE_KEY]"),
    (re.compile(r"\b[0-9]{8,10}:[a-zA-Z0-9_-]{35}\b"), "[REDACTED_TELEGRAM_TOKEN]"),
    (re.compile(r"\bghp_[a-zA-Z0-9]{36}\b"), "[REDACTED_GITHUB_TOKEN]"),
    (re.compile(r"Bearer\s+[a-zA-Z0-9._-]{20,}"), "Bearer [REDACTED_TOKEN]"),
    (re.compile(r"client_secret=[a-zA-Z0-9._-]+"), "client_secret=[REDACTED]"),
]

DEFAULT_VAULT_PATH = Path.home() / "Documents" / "Obsidian" / "achiMem"


def sanitize_secrets(text: str) -> str:
    """Strip API keys, bot tokens, and auth secrets from dialogue before saving."""
    if not text:
        return ""
    sanitized = text
    for pattern, replacement in SECRET_PATTERNS:
        sanitized = pattern.sub(replacement, sanitized)
    return sanitized


def format_tgdb_note(
    metadata: dict,
    messages: list[dict],
    takeaways: list[str] | None = None,
    tasks: list[str] | None = None,
) -> str:
    """Format a conversation into a structured Obsidian note with frontmatter.

    metadata keys:
        title: str
        bot: str (e.g. "@schoMemBot")
        engine: str (e.g. "Claude Sonnet" or "Gemini Pro")
        summary: str
        tags: list[str]
        timestamp: dt.datetime (optional, defaults to now)
    """
    timestamp = metadata.get("timestamp") or dt.datetime.now(LOCAL_TZ)
    date_str = timestamp.strftime("%Y-%m-%d %H:%M")
    date_heading = timestamp.strftime("%A, %b %d, %Y • %I:%M %p")

    title = metadata.get("title", "Telegram Conversation").strip()
    bot = metadata.get("bot", "@achiOSBot").strip()
    engine = metadata.get("engine", "AI Assistant").strip()
    channel = metadata.get("channel", "Telegram DM").strip()
    summary = metadata.get("summary", "").strip() or f"Conversation with {bot} on {date_str}."
    tags = metadata.get("tags", ["tgdb", "session"])
    if "tgdb" not in tags:
        tags.insert(0, "tgdb")

    tag_str = ", ".join(tags)

    lines = [
        "---",
        f'title: "{title}"',
        f'bot: "{bot}"',
        f'engine: "{engine}"',
        f'channel: "{channel}"',
        f"date: {date_str}",
        f"tags: [{tag_str}]",
        f'summary: "{summary}"',
        "---",
        "",
        f"# 💬 {title}",
        f"* **Bot:** `{bot}` ({engine})",
        f"* **Date:** {date_heading} Manila",
        f"* **Summary:** {summary}",
        "",
        "---",
        "",
    ]

    # Key Takeaways / Decisions
    if takeaways:
        lines.append("### 📌 Key Takeaways & Decisions")
        for item in takeaways:
            lines.append(f"* {item.strip()}")
        lines.append("")

    # Action items
    if tasks:
        lines.append("### ⚡ Extracted Action Items")
        for item in tasks:
            lines.append(f"- [ ] {item.strip()}")
        lines.append("")

    # Transcript block
    lines.append("### 📜 Full Dialogue Transcript")
    lines.append("<details open>")
    lines.append("<summary><b>Expand / Collapse Transcript</b></summary>")
    lines.append("")

    for msg in messages:
        role = msg.get("role", "user").lower()
        sender_label = "Aki" if role in ["user", "human"] else bot
        content = sanitize_secrets(msg.get("content", "").strip())
        
        # Format as blockquote with dialogue label
        formatted_content = "\n> ".join(content.splitlines())
        lines.append(f"> **{sender_label}:** {formatted_content}")
        lines.append(">")

    # Remove trailing empty quote line
    if lines[-1] == ">":
        lines.pop()

    lines.append("")
    lines.append("</details>")
    lines.append("")

    return "\n".join(lines).strip() + "\n"


def write_tgdb_session(
    vault_path: Path | None,
    bot_name: str,
    session_id: str,
    content: str,
    timestamp: dt.datetime | None = None,
) -> Path:
    """Save formatted markdown note to <vault_path>/tgdb/YYYY-MM/."""
    vault = vault_path or DEFAULT_VAULT_PATH
    ts = timestamp or dt.datetime.now(LOCAL_TZ)

    month_dir = vault / "tgdb" / ts.strftime("%Y-%m")
    month_dir.mkdir(parents=True, exist_ok=True)

    clean_bot = re.sub(r"[^a-zA-Z0-9_-]", "", bot_name.replace("@", "")).lower()
    clean_session = re.sub(r"[^a-zA-Z0-9_-]", "", session_id)[:8]
    date_prefix = ts.strftime("%Y-%m-%d")

    filename = f"{date_prefix}-{clean_bot}-{clean_session}.md"
    file_path = month_dir / filename

    file_path.write_text(content, encoding="utf-8")
    return file_path
