"""Google MCP bridge — local HTTP server for Gmail + Calendar.

Warmth's Python client calls this on GOOGLE_MCP_SERVER_URL (default :3000).
Auth is OAuth for the Warmth Gmail inbox (getwarmth@gmail.com by default).
"""
from __future__ import annotations

import os
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

load_dotenv()
# Also load warmth/.env when started from repo root
_warmth_env = Path(__file__).resolve().parents[2] / ".env"
if _warmth_env.exists():
    load_dotenv(_warmth_env, override=False)

from .calendar_service import create_event as cal_create_event, list_events as cal_list_events
from .gmail_service import (  # noqa: E402
    GmailAuthError,
    create_draft,
    load_gmail_credentials,
    send_message,
)

app = FastAPI(title="Warmth Google MCP", version="0.1.0")


class GmailDraftRequest(BaseModel):
    to: str
    subject: str
    body: str
    cc: Optional[list[str]] = None
    bcc: Optional[list[str]] = None
    credentials: Optional[dict[str, Any]] = None


class GmailSendRequest(GmailDraftRequest):
    pass


class CalendarListRequest(BaseModel):
    credentials: Optional[dict[str, Any]] = None
    time_min: Optional[str] = None
    time_max: Optional[str] = None
    max_results: int = 20


class CalendarCreateRequest(BaseModel):
    credentials: Optional[dict[str, Any]] = None
    title: str
    start_time: str
    end_time: str
    attendees: list[str] = []
    description: Optional[str] = None
    location: Optional[str] = None


def _resolve_credentials(body_creds: Optional[dict[str, Any]]):
    try:
        if body_creds:
            return load_gmail_credentials(inline=body_creds)
        return load_gmail_credentials()
    except GmailAuthError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.get("/health")
async def health():
    cred_path = os.getenv("GOOGLE_MCP_CREDENTIALS", "")
    token_ready = bool(cred_path and os.path.exists(cred_path))
    return {
        "status": "healthy",
        "service": "google-mcp-bridge",
        "credentials_configured": bool(cred_path),
        "token_ready": token_ready,
        "credentials_path": cred_path or None,
        "client_email": os.getenv("WARMTH_CLIENT_EMAIL", "getwarmth@gmail.com"),
    }


@app.post("/gmail/drafts")
async def gmail_drafts(req: GmailDraftRequest):
    """Create a draft in the authenticated Gmail inbox."""
    creds = _resolve_credentials(req.credentials)
    result = create_draft(creds, req.to, req.subject, req.body, cc=req.cc)
    result["client_email"] = os.getenv("WARMTH_CLIENT_EMAIL", "getwarmth@gmail.com")
    return result


@app.post("/gmail/send")
async def gmail_send(req: GmailSendRequest):
    """Send email (Warmth normally uses drafts only — human sends in Gmail)."""
    creds = _resolve_credentials(req.credentials)
    return send_message(creds, req.to, req.subject, req.body, cc=req.cc)


def _parse_iso(ts: Optional[str]) -> Optional[datetime]:
    if not ts:
        return None
    try:
        return datetime.fromisoformat(ts.replace("Z", "+00:00"))
    except ValueError:
        return None


@app.post("/calendar/events")
async def calendar_list(req: CalendarListRequest):
    """List upcoming calendar events."""
    creds = _resolve_credentials(req.credentials)
    events = cal_list_events(
        creds,
        time_min=_parse_iso(req.time_min),
        time_max=_parse_iso(req.time_max),
        max_results=req.max_results,
    )
    return {"events": events}


@app.post("/calendar/events/create")
async def calendar_create(req: CalendarCreateRequest):
    """Create a calendar event."""
    creds = _resolve_credentials(req.credentials)
    start = _parse_iso(req.start_time)
    end = _parse_iso(req.end_time)
    if not start or not end:
        raise HTTPException(status_code=400, detail="Invalid start_time or end_time")
    return cal_create_event(
        creds,
        title=req.title,
        start_time=start,
        end_time=end,
        attendees_emails=req.attendees or None,
        description=req.description,
        location=req.location,
    )


if __name__ == "__main__":
    import uvicorn

    port = int(os.getenv("GOOGLE_MCP_PORT", "3000"))
    uvicorn.run(app, host="0.0.0.0", port=port)
