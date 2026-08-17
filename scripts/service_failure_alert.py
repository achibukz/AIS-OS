#!/usr/bin/env python3
"""Service Failure Alert -> Telegram (achinouncements).

Invoked by systemd `OnFailure=achios-failure-alert@%n.service` or process trap
handlers when an achiOS or achiAgy service exits unexpectedly.

Usage:
    python scripts/service_failure_alert.py <unit_or_bot_name> [--reason REASON]
"""

from __future__ import annotations

import argparse
import datetime as dt
import re
import subprocess
import sys
from pathlib import Path

# Add scripts directory to sys.path to import telegram_notify
SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))
from telegram_notify import send


def sanitize_log_output(text: str) -> str:
    """Redact any sensitive tokens or secrets from logs before sending to Telegram."""
    # Redact Telegram bot tokens (e.g. bot123456:ABC-DEF...)
    text = re.sub(r"bot\d+:[A-Za-z0-9_-]+", "bot<REDACTED_TOKEN>", text)
    # Redact common auth headers or tokens
    text = re.sub(r"(token|secret|password|api_key)=['\"]?[A-Za-z0-9_\-\.]+['\"]?", r"\1=<REDACTED>", text, flags=re.IGNORECASE)
    return text


def get_recent_logs(service_name: str, max_lines: int = 8) -> str:
    """Fetch recent log lines from ~/.local/state/achios/, repo logs, or journalctl."""
    raw_unit = service_name.lower().replace(".service", "")
    
    # Map service names to exact log file paths
    log_map = {
        "achios-bot": Path.home() / ".local" / "state" / "achios" / "achios_bot.log",
        "achios-schoolmem-bot": Path.home() / ".local" / "state" / "achios" / "schoolmem_bot.log",
        "achios-daily-brief": Path.home() / ".local" / "state" / "achios" / "daily_brief.log",
        "achios-voo-digest": Path.home() / ".local" / "state" / "achios" / "voo_digest.log",
        "achi-agy": Path.home() / "Code" / "GitHub" / "achiAgy" / "achi_agy.log",
        "achi-agy-schoolmem": Path.home() / "Code" / "GitHub" / "achiAgy" / "achiagy.log",
    }

    log_path = log_map.get(raw_unit)
    if log_path and log_path.exists():
        try:
            lines = log_path.read_text(encoding="utf-8", errors="replace").splitlines()
            if lines:
                tail = [l for l in lines[-max_lines:] if l.strip()]
                if tail:
                    return sanitize_log_output("\n".join(tail))
        except Exception:
            pass

    # Fall back to journalctl
    try:
        unit_name = service_name if service_name.endswith(".service") else f"{service_name}.service"
        res = subprocess.run(
            ["journalctl", "--user", "-u", unit_name, "-n", str(max_lines), "--no-pager"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        if res.returncode == 0 and res.stdout.strip():
            return sanitize_log_output(res.stdout.strip())
    except Exception:
        pass

    return "No log output available."


def build_alert_message(service_name: str, reason: str = "") -> str:
    """Format the failure alert message for Telegram."""
    now = dt.datetime.now(dt.timezone(dt.timedelta(hours=8)))
    date_str = now.strftime("%b %d, %Y (%I:%M:%S %p Manila)")

    logs = get_recent_logs(service_name)
    if len(logs) > 1500:
        logs = logs[-1500:]

    lines = [
        "🚨 SYSTEM ALERT: Service Failure Detected",
        f"🗓 {date_str}",
        f"💻 Host: achibuntu",
        f"⚙️ Service: {service_name}",
    ]

    if reason:
        lines.append(f"⚠️ Reason: {reason}")

    lines.extend([
        "",
        "📋 Recent Log Output:",
        logs,
        "",
        f"💡 Check status: `systemctl --user status {service_name}`",
    ])

    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("service", help="Name of the failed systemd service or bot")
    parser.add_argument("--reason", default="", help="Optional error description or exit code")
    parser.add_argument("--dry-run", action="store_true", help="Print instead of sending")
    args = parser.parse_args()

    message = build_alert_message(args.service, args.reason)

    if args.dry_run:
        print("=== DRY RUN ALERT ===")
        print(message)
        return 0

    print(f"[{dt.datetime.now().isoformat()}] Sending failure alert for {args.service}...")
    try:
        count = send(message)
        print(f"Alert sent successfully ({count} msg).")
    except Exception as e:
        print(f"Failed to send Telegram alert: {e}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
