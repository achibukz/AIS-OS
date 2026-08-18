#!/usr/bin/env python3
"""ETF Daily Digest (VOO, VXUS, QQQM) -> Telegram (achinouncements).

Fetches key performance and price metrics for core ETF holdings:
- VOO (Vanguard S&P 500 ETF)
- VXUS (Vanguard Total International Stock ETF)
- QQQM (Invesco NASDAQ 100 ETF)

Usage:
    python scripts/voo_digest.py           # Fetch and send
    python scripts/voo_digest.py --dry-run # Print only
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


def fetch_ticker_data(ticker: str) -> dict:
    """Fetch current price, daily change, 52-week range, and 1-year return."""
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }

    url_5d = f"https://query1.finance.yahoo.com/v8/finance/chart/{ticker}?interval=1d&range=5d"
    r_5d = requests.get(url_5d, headers=headers, timeout=15)
    r_5d.raise_for_status()
    data_5d = r_5d.json()["chart"]["result"][0]
    meta_5d = data_5d["meta"]

    current_price = meta_5d.get("regularMarketPrice", 0.0)
    prev_close = meta_5d.get("chartPreviousClose") or meta_5d.get("previousClose", current_price)

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

    daily_change = (current_price - prev_close) if prev_close else 0.0
    daily_pct = (daily_change / prev_close * 100) if prev_close else 0.0
    one_yr_return = ((current_price - y1_start) / y1_start * 100) if y1_start and current_price else 0.0

    return {
        "ticker": ticker,
        "price": current_price,
        "prev_close": prev_close,
        "daily_change": daily_change,
        "daily_pct": daily_pct,
        "high_52w": high_52w,
        "low_52w": low_52w,
        "one_yr_return": one_yr_return,
    }


def build_digest(results: list[tuple[str, dict]]) -> str:
    """Format the ETF digest with only a top separator bar."""
    now = dt.datetime.now(dt.timezone(dt.timedelta(hours=8)))
    date_str = now.strftime("%b %d, %Y (%I:%M %p Manila)")

    lines = [
        "---------------------------------",
        "📊 ETF Market Digest",
        f"🗓 {date_str}",
        "",
    ]

    for label, data in results:
        sign = "+" if data["daily_change"] >= 0 else ""
        yr_sign = "+" if data["one_yr_return"] >= 0 else ""

        lines.extend([
            f"{label}",
            f"• Price: ${data['price']:.2f}",
            f"• Daily Change: {sign}${data['daily_change']:.2f} ({sign}{data['daily_pct']:.2f}%)",
            f"• 1-Year Return: {yr_sign}{data['one_yr_return']:.2f}%",
            f"• 52W Range: ${data['low_52w']:.2f} - ${data['high_52w']:.2f}",
            "",
        ])

    return "\n".join(lines).strip()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print the digest without sending to Telegram",
    )
    args = parser.parse_args()

    print(f"[{dt.datetime.now().isoformat()}] Fetching ETF data for VOO, VXUS, QQQM...")
    results = []
    for ticker, label in TICKERS:
        try:
            data = fetch_ticker_data(ticker)
            results.append((label, data))
        except Exception as e:
            print(f"Error fetching {ticker}: {e}", file=sys.stderr)
            results.append((
                label,
                {
                    "ticker": ticker,
                    "price": 0.0,
                    "prev_close": 0.0,
                    "daily_change": 0.0,
                    "daily_pct": 0.0,
                    "high_52w": 0.0,
                    "low_52w": 0.0,
                    "one_yr_return": 0.0,
                }
            ))

    digest = build_digest(results)

    if args.dry_run:
        print("=== DRY RUN (Not sending) ===")
        print(digest)
        return 0

    env_target = FINANCE_ENV if FINANCE_ENV.exists() else None
    if env_target:
        print(f"Using finance bot credentials from {FINANCE_ENV}...")
    print("Sending digest to Telegram...")
    count = send(digest, env_path=env_target)
    print(f"Successfully sent {count} message(s) to Telegram.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
