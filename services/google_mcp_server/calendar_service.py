"""Google Calendar API helpers for the MCP bridge server."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Optional

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

from .google_auth import GoogleAuthError, load_google_credentials


def _rfc3339(dt: datetime) -> str:
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def calendar_service(credentials: Credentials):
    return build("calendar", "v3", credentials=credentials, cache_discovery=False)


def list_events(
    credentials: Credentials,
    time_min: Optional[datetime] = None,
    time_max: Optional[datetime] = None,
    max_results: int = 20,
) -> list[dict[str, Any]]:
    """List upcoming calendar events for the authenticated user."""
    service = calendar_service(credentials)
    params: dict[str, Any] = {
        "calendarId": "primary",
        "singleEvents": True,
        "orderBy": "startTime",
        "maxResults": max_results,
    }
    if time_min:
        params["timeMin"] = _rfc3339(time_min)
    if time_max:
        params["timeMax"] = _rfc3339(time_max)

    result = service.events().list(**params).execute()
    return result.get("items", [])


def create_event(
    credentials: Credentials,
    title: str,
    start_time: datetime,
    end_time: datetime,
    attendees_emails: Optional[list[str]] = None,
    description: Optional[str] = None,
    location: Optional[str] = None,
) -> dict[str, Any]:
    """Create a calendar event on the user's primary calendar."""
    service = calendar_service(credentials)
    body: dict[str, Any] = {
        "summary": title,
        "start": {"dateTime": start_time.isoformat(), "timeZone": "UTC"},
        "end": {"dateTime": end_time.isoformat(), "timeZone": "UTC"},
    }
    if description:
        body["description"] = description
    if location:
        body["location"] = location
    if attendees_emails:
        body["attendees"] = [{"email": e} for e in attendees_emails]

    created = service.events().insert(calendarId="primary", body=body).execute()
    return {"id": created.get("id"), "status": "created", "htmlLink": created.get("htmlLink")}
