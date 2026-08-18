#!/usr/bin/env python3
"""Weekly ETF Performance Recap (VOO, VXUS, QQQM) -> Telegram (achiFinance).

Runs every Sunday at 18:00 Manila time (6:00 PM) before the new trading week opens.
Summarizes 5-day weekly performance, weekly trading ranges, and 1-year returns.

Usage:
    python scripts/etf_weekly_digest.py           # Fetch and send
    python scripts/etf_weekly_digest.py --dry-run # Print only
"""

from __future__ import annotations

import argparse
import datetime as dt
import sys
from pathlib import Path
import requests

# Add scripts directory to sys.path to import telegram_notify
SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))
from telegram_notify import CONFIG_DIR, send

FINANCE_ENV = CONFIG_DIR / "telegram_finance.env"

TICKERS = [
    ("VOO", "🇺🇸 VOO (Vanguard S&P 500)"),
    ("VXUS", "🌍 VXUS (Vanguard Total International)"),
    ("QQQM", "⚡ QQQM (Invesco NASDAQ 100)"),
]


def fetch_weekly_data(ticker: str) -> dict:
    """Fetch 5-day weekly performance, weekly range, and 1-year stats."""
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }

    url_5d = f"https://query1.finance.yahoo.com/v8/finance/chart/{ticker}?interval=1d&range=5d"
    r_5d = requests.get(url_5d, headers=headers, timeout=15)
    r_5d.raise_for_status()
    data_5d = r_5d.json()["chart"]["result"][0]
    meta_5d = data_5d["meta"]

    quotes_5d = data_5d["indicators"]["quote"][0]
    closes_5d = [c for c in quotes_5d.get("close", []) if c is not None]
    highs_5d = [h for h in quotes_5d.get("high", []) if h is not None]
    lows_5d = [l for l in quotes_5d.get("low", []) if l is not None]

    current_price = meta_5d.get("regularMarketPrice") or (closes_5d[-1] if closes_5d else 0.0)
    week_open = closes_5d[0] if closes_5d else current_price
    week_high = max(highs_5d) if highs_5d else current_price
    week_low = min(lows_5d) if lows_5d else current_price

    week_change = current_price - week_open
    week_pct = (week_change / week_open * 100) if week_open else 0.0

    url_1y = f"https://query1.finance.yahoo.com/v8/finance/chart/{ticker}?interval=1d&range=1y"
    r_1y = requests.get(url_1y, headers=headers, timeout=15)
    r_1y.raise_for_status()
    data_1y = r_1y.json()["chart"]["result"][0]
    meta_1y = data_1y["meta"]

    high_52w = meta_1y.get("fiftyTwoWeekHigh", 0.0)
    low_52w = meta_1y.get("fiftyTwoWeekLow", 0.0)

    closes_1y = [
        c for c in data_1y["indicators"]["quote"][0]["close"] if c is not None
    ]
    y1_start = closes_1y[0] if closes_1y else None
    one_yr_return = ((current_price - y1_start) / y1_start * 100) if y1_start and current_price else 0.0

    return {
        "ticker": ticker,
        "price": current_price,
        "week_open": week_open,
        "week_change": week_change,
        "week_pct": week_pct,
        "week_high": week_high,
        "week_low": week_low,
        "high_52w": high_52w,
        "low_52w": low_52w,
        "one_yr_return": one_yr_return,
    }


def build_weekly_digest(results: list[tuple[str, dict]]) -> str:
    """Format the weekly ETF performance recap."""
    now = dt.datetime.now(dt.timezone(dt.timedelta(hours=8)))
    date_str = now.strftime("%b %d, %Y (%I:%M %p Manila)")

    lines = [
        "---------------------------------",
        "📈 Weekly ETF Performance Recap",
        f"🗓 {date_str}",
        "5-Day Trading Week Wrap-up",
        "",
    ]

    green_count = 0

    for label, data in results:
        is_green = data["week_change"] >= 0
        if is_green:
            green_count += 1
        sign = "+" if is_green else ""
        icon = "🟢" if is_green else "🔴"
        yr_sign = "+" if data["one_yr_return"] >= 0 else ""

        lines.extend([
            f"{label}",
            f"• Week Close: ${data['price']:.2f}",
            f"• 5-Day Move: {sign}${data['week_change']:.2f} ({sign}{data['week_pct']:.2f}%) {icon}",
            f"• Weekly Range: ${data['week_low']:.2f} - ${data['week_high']:.2f}",
            f"• 1-Year Return: {yr_sign}{data['one_yr_return']:.2f}%",
            f"• 52W Range: ${data['low_52w']:.2f} - ${data['high_52w']:.2f}",
            "",
        ])

    lines.append(f"💡 Summary: {green_count} of {len(results)} core ETFs closed green this week. Markets reopen Monday at 9:30 PM Manila.")
    return "\n".join(lines).strip()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print the weekly digest without sending to Telegram",
    )
    args = parser.parse_args()

    print(f"[{dt.datetime.now().isoformat()}] Fetching weekly ETF data for VOO, VXUS, QQQM...")
    results = []
    for ticker, label in TICKERS:
        try:
            data = fetch_weekly_data(ticker)
            results.append((label, data))
        except Exception as e:
            print(f"Error fetching weekly data for {ticker}: {e}", file=sys.stderr)
            results.append((
                label,
                {
                    "ticker": ticker,
                    "price": 0.0,
                    "week_open": 0.0,
                    "week_change": 0.0,
                    "week_pct": 0.0,
                    "week_high": 0.0,
                    "week_low": 0.0,
                    "high_52w": 0.0,
                    "low_52w": 0.0,
                    "one_yr_return": 0.0,
                }
            ))

    digest = build_weekly_digest(results)

    if args.dry_run:
        print("=== DRY RUN (Not sending) ===")
        print(digest)
        return 0

    env_target = FINANCE_ENV if FINANCE_ENV.exists() else None
    if env_target:
        print(f"Using finance bot credentials from {FINANCE_ENV}...")
    print("Sending weekly performance recap to Telegram...")
    count = send(digest, env_path=env_target)
    print(f"Successfully sent {count} message(s) to Telegram.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
