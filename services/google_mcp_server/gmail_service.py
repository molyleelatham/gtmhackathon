"""Gmail API helpers for the Google MCP bridge server."""
from __future__ import annotations

import base64
import json
import os
from email.mime.text import MIMEText
from pathlib import Path
from typing import Any, Optional

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

from .google_auth import GoogleAuthError, load_google_credentials

GmailAuthError = GoogleAuthError


def load_gmail_credentials(
    credentials_path: Optional[str] = None,
    inline: Optional[dict[str, Any]] = None,
) -> Credentials:
    """Load OAuth user credentials for Gmail (personal inbox like getwarmth@gmail.com)."""
    return load_google_credentials(credentials_path, inline)


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
