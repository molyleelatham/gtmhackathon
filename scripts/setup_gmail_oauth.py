#!/usr/bin/env python3
"""One-time OAuth setup for Gmail MCP (getwarmth@gmail.com inbox).

Steps:
  1. Google Cloud Console → APIs & Services → Credentials
  2. Create OAuth 2.0 Client ID (Desktop app) for project warmth-gtm-hackathon
  3. Enable Gmail API for the project
  4. Download JSON → save as warmth/google-oauth-client.json
  5. Run this script and sign in as getwarmth@gmail.com

Writes warmth/google-gmail-oauth.json and prints the .env lines to set.
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT.parent))

SCOPES = [
    "https://www.googleapis.com/auth/gmail.compose",
    "https://www.googleapis.com/auth/gmail.modify",
    "https://www.googleapis.com/auth/calendar.readonly",
    "https://www.googleapis.com/auth/calendar.events",
]

CLIENT_DEFAULT = ROOT / "google-oauth-client.json"
TOKEN_OUT = ROOT / "google-gmail-oauth.json"


def main() -> int:
    try:
        from google_auth_oauthlib.flow import InstalledAppFlow
    except ImportError:
        print("Install Gmail deps first:")
        print("  cd warmth && uv pip install google-api-python-client google-auth-oauthlib")
        return 1

    client_path = Path(os.getenv("GOOGLE_OAUTH_CLIENT_PATH", str(CLIENT_DEFAULT)))
    if not client_path.exists():
        print(f"Missing OAuth client file: {client_path}")
        print("Download Desktop OAuth JSON from Google Cloud Console and save it there.")
        return 1

    print(f"Opening browser — sign in as {os.getenv('WARMTH_CLIENT_EMAIL', 'getwarmth@gmail.com')}")
    flow = InstalledAppFlow.from_client_secrets_file(str(client_path), SCOPES)
    creds = flow.run_local_server(port=int(os.getenv("GOOGLE_OAUTH_CALLBACK_PORT", "8090")))

    token_data = {
        "type": "authorized_user",
        "client_id": creds.client_id,
        "client_secret": creds.client_secret,
        "refresh_token": creds.refresh_token,
        "token": creds.token,
        "scopes": list(creds.scopes or SCOPES),
    }
    TOKEN_OUT.write_text(json.dumps(token_data, indent=2))
    print(f"\nSaved OAuth token → {TOKEN_OUT}")
    print("\nAdd to warmth/.env:")
    print(f"GOOGLE_MCP_CREDENTIALS={TOKEN_OUT}")
    print("GOOGLE_MCP_SERVER_URL=http://localhost:3000")
    print("WARMTH_CLIENT_EMAIL=getwarmth@gmail.com")
    print("\nThen start the bridge:")
    print("  make run-gmail-mcp")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
