"""Gmail API helpers for the Google MCP bridge server."""
from __future__ import annotations

import base64
import json
import os
from email.mime.text import MIMEText
from pathlib import Path
from typing import Any, Optional

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

GMAIL_SCOPES = [
    "https://www.googleapis.com/auth/gmail.compose",
    "https://www.googleapis.com/auth/gmail.modify",
]


class GmailAuthError(ValueError):
    pass


def _load_json(path: str) -> dict[str, Any]:
    return json.loads(Path(path).read_text())


def load_gmail_credentials(
    credentials_path: Optional[str] = None,
    inline: Optional[dict[str, Any]] = None,
) -> Credentials:
    """Load OAuth user credentials for Gmail (personal inbox like getwarmth@gmail.com)."""
    data = inline or {}
    if not data:
        path = credentials_path or os.getenv("GOOGLE_MCP_CREDENTIALS", "")
        if not path or not os.path.exists(path):
            raise GmailAuthError(
                "Gmail MCP credentials not found. Run: "
                "python warmth/scripts/setup_gmail_oauth.py"
            )
        data = _load_json(path)

    cred_type = data.get("type")
    if cred_type == "service_account":
        raise GmailAuthError(
            "GOOGLE_MCP_CREDENTIALS points to a service account. Gmail for "
            "getwarmth@gmail.com requires OAuth. Run: "
            "python warmth/scripts/setup_gmail_oauth.py"
        )

    if cred_type == "authorized_user":
        creds = Credentials.from_authorized_user_info(data, scopes=GMAIL_SCOPES)
    elif "installed" in data or "web" in data:
        token_path = os.getenv(
            "GOOGLE_MCP_TOKEN_PATH",
            str(Path(credentials_path or "").with_name("google-gmail-oauth.json")),
        )
        if not os.path.exists(token_path):
            raise GmailAuthError(
                f"OAuth token missing at {token_path}. Run setup_gmail_oauth.py"
            )
        creds = Credentials.from_authorized_user_info(_load_json(token_path), scopes=GMAIL_SCOPES)
    else:
        creds = Credentials.from_authorized_user_info(data, scopes=GMAIL_SCOPES)

    if creds.expired and creds.refresh_token:
        creds.refresh(Request())
    if not creds.valid:
        raise GmailAuthError("Gmail OAuth token invalid or expired. Re-run setup_gmail_oauth.py")
    return creds


def gmail_service(credentials: Credentials):
    return build("gmail", "v1", credentials=credentials, cache_discovery=False)


def _message_raw(to: str, subject: str, body: str, cc: Optional[list[str]] = None) -> str:
    msg = MIMEText(body, "plain", "utf-8")
    msg["to"] = to
    msg["subject"] = subject
    if cc:
        msg["cc"] = ", ".join(cc)
    return base64.urlsafe_b64encode(msg.as_bytes()).decode()


def create_draft(
    credentials: Credentials,
    to: str,
    subject: str,
    body: str,
    cc: Optional[list[str]] = None,
) -> dict[str, Any]:
    service = gmail_service(credentials)
    raw = _message_raw(to, subject, body, cc=cc)
    draft = (
        service.users()
        .drafts()
        .create(userId="me", body={"message": {"raw": raw}})
        .execute()
    )
    return {
        "id": draft.get("id"),
        "message_id": draft.get("message", {}).get("id"),
        "status": "created",
    }


def send_message(
    credentials: Credentials,
    to: str,
    subject: str,
    body: str,
    cc: Optional[list[str]] = None,
) -> dict[str, Any]:
    service = gmail_service(credentials)
    raw = _message_raw(to, subject, body, cc=cc)
    sent = service.users().messages().send(userId="me", body={"raw": raw}).execute()
    return {"id": sent.get("id"), "status": "sent"}
