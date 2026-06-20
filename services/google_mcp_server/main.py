"""Google MCP bridge — local HTTP server for Gmail draft/create.

Warmth's Python client calls this on GOOGLE_MCP_SERVER_URL (default :3000).
Auth is OAuth for the Warmth Gmail inbox (getwarmth@gmail.com by default).
"""
from __future__ import annotations

import os
from typing import Any, Optional

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

load_dotenv()

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


def _resolve_credentials(body_creds: Optional[dict[str, Any]]):
    try:
        if body_creds:
            return load_gmail_credentials(inline=body_creds)
        return load_gmail_credentials()
    except GmailAuthError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.get("/health")
async def health():
    configured = bool(os.getenv("GOOGLE_MCP_CREDENTIALS"))
    return {
        "status": "healthy",
        "service": "google-mcp-bridge",
        "credentials_configured": configured,
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


if __name__ == "__main__":
    import uvicorn

    port = int(os.getenv("GOOGLE_MCP_PORT", "3000"))
    uvicorn.run(app, host="0.0.0.0", port=port)
