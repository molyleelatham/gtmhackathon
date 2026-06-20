"""Shared OAuth credential loading for Gmail + Calendar MCP bridge."""
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Optional

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials

GOOGLE_OAUTH_SCOPES = [
    "https://www.googleapis.com/auth/gmail.compose",
    "https://www.googleapis.com/auth/gmail.modify",
    "https://www.googleapis.com/auth/calendar.readonly",
    "https://www.googleapis.com/auth/calendar.events",
]


class GoogleAuthError(ValueError):
    pass


def _load_json(path: str) -> dict[str, Any]:
    return json.loads(Path(path).read_text())


def load_google_credentials(
    credentials_path: Optional[str] = None,
    inline: Optional[dict[str, Any]] = None,
) -> Credentials:
    """Load OAuth user credentials for Gmail + Calendar."""
    data = inline or {}
    if not data:
        path = credentials_path or os.getenv("GOOGLE_MCP_CREDENTIALS", "")
        if not path or not os.path.exists(path):
            raise GoogleAuthError(
                "Google MCP credentials not found. Run: "
                "python warmth/scripts/setup_gmail_oauth.py"
            )
        data = _load_json(path)

    cred_type = data.get("type")
    if cred_type == "service_account":
        raise GoogleAuthError(
            "GOOGLE_MCP_CREDENTIALS points to a service account. Personal "
            "Gmail/Calendar requires OAuth. Run setup_gmail_oauth.py"
        )

    if cred_type == "authorized_user":
        creds = Credentials.from_authorized_user_info(data, scopes=GOOGLE_OAUTH_SCOPES)
    elif "installed" in data or "web" in data:
        token_path = os.getenv(
            "GOOGLE_MCP_TOKEN_PATH",
            str(Path(credentials_path or "").with_name("google-gmail-oauth.json")),
        )
        if not os.path.exists(token_path):
            raise GoogleAuthError(
                f"OAuth token missing at {token_path}. Run setup_gmail_oauth.py"
            )
        creds = Credentials.from_authorized_user_info(
            _load_json(token_path), scopes=GOOGLE_OAUTH_SCOPES
        )
    else:
        creds = Credentials.from_authorized_user_info(data, scopes=GOOGLE_OAUTH_SCOPES)

    if creds.expired and creds.refresh_token:
        creds.refresh(Request())
    if not creds.valid:
        raise GoogleAuthError(
            "Google OAuth token invalid or expired. Re-run setup_gmail_oauth.py"
        )
    return creds
