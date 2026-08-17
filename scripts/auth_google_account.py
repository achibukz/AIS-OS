#!/usr/bin/env python3
"""Google OAuth Authenticator for achiOS.

Authenticates a Google account (DLSU, Personal, Work) and generates
a token in ~/.config/achios/google_token_<name>.json.

Usage:
    python scripts/auth_google_account.py dlsu
"""

from __future__ import annotations

import argparse
import json
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
    parser.add_argument(
        "--port",
        type=int,
        default=8085,
        help="Local server port for OAuth redirect callback (default: 8085)",
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
    )

    print(f"\n🔑 Authenticating Google Account for [{args.name.upper()}]...")
    print(f"Destination: {output_token_path}\n")

    # Run local server flow
    creds = flow.run_local_server(
        port=args.port,
        prompt="consent",
        open_browser=False,
        authorization_prompt_message="Open this link in your browser to sign in:\n\n{url}\n",
        success_message="Authentication complete! You can now close this browser tab.",
    )

    output_token_path.write_text(creds.to_json(), encoding="utf-8")
    output_token_path.chmod(0o600)
    print(f"\n✅ Successfully saved token to {output_token_path} (mode 600)!")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
