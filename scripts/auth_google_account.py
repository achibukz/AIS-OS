#!/usr/bin/env python3
"""Google OAuth Authenticator for achiOS.

Authenticates a Google account (DLSU, Personal, Work, Main) and generates
a token in ~/.config/achios/google_token_<name>.json.

Supports pasting the redirect URL directly from your browser!

Usage:
    python3 scripts/auth_google_account.py dlsu
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

# Automatically switch to achiOS venv if run with system python
VENV_PYTHON = Path.home() / ".local" / "share" / "achios" / "venv" / "bin" / "python"
if VENV_PYTHON.exists() and sys.executable != str(VENV_PYTHON):
    os.execv(str(VENV_PYTHON), [str(VENV_PYTHON)] + sys.argv)

from google_auth_oauthlib.flow import InstalledAppFlow

SCOPES = [
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/calendar",
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/documents",
    "https://www.googleapis.com/auth/contacts.readonly",
]

CLIENT_SECRET_FILE = Path.home() / ".hermes" / "google_client_secret.json"
CONFIG_DIR = Path.home() / ".config" / "achios"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "name",
        choices=["dlsu", "main", "work", "personal"],
        help="Account identifier (e.g. dlsu -> google_token_dlsu.json)",
    )
    args = parser.parse_args()

    if not CLIENT_SECRET_FILE.exists():
        print(f"Error: Client secret file not found at {CLIENT_SECRET_FILE}", file=sys.stderr)
        return 1

    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    token_filename = "google_token.json" if args.name == "personal" else f"google_token_{args.name}.json"
    output_token_path = CONFIG_DIR / token_filename

    flow = InstalledAppFlow.from_client_secrets_file(
        str(CLIENT_SECRET_FILE),
        scopes=SCOPES,
        redirect_uri="http://localhost:8085/",
    )

    auth_url, _ = flow.authorization_url(prompt="consent", access_type="offline")

    print("==================================================================")
    print(f"🔑 AUTHENTICATING GOOGLE ACCOUNT: [{args.name.upper()}]")
    print("==================================================================")
    print("\n1. Copy and open this URL in your browser:\n")
    print(auth_url)
    print("\n------------------------------------------------------------------")
    print("2. Sign in with your account and click 'Allow'.")
    print("3. Your browser will redirect to a page that looks like:")
    print("   'http://localhost:8085/?state=...&code=...'")
    print("4. Copy that FULL URL from your browser's address bar and paste it below:\n")

    try:
        redirect_response = input("Paste redirect URL here: ").strip()
        if not redirect_response:
            print("Error: No URL provided.", file=sys.stderr)
            return 1

        print("\nExchanging authorization code for token...")
        flow.fetch_token(authorization_response=redirect_response)
        creds = flow.credentials

        output_token_path.write_text(creds.to_json(), encoding="utf-8")
        output_token_path.chmod(0o600)
        print(f"\n✅ SUCCESS! Token securely saved to: {output_token_path} (mode 600)")
        return 0
    except Exception as e:
        print(f"\n❌ Authentication failed: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
