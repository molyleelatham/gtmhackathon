import os
from datetime import datetime
from typing import Optional

import httpx

from ...core.models.event import CalendarEvent, DetectedEvent, EventType


class GoogleCalendarClient:
    """Google Calendar access via the Google MCP server.

    Onboarding connects the user's email + Google Calendar through MCP. This
    client lists events, classifies which ones are conferences worth running the
    Warmth lifecycle on, and creates calendar events when meetings are booked.

    STUB: network calls target the MCP server but the conference-detection logic
    is heuristic. Wire real OAuth/MCP credentials via GOOGLE_MCP_* env vars.
    """

    CONFERENCE_HINTS = [
        "conference", "summit", "expo", "con ", "saastr", "meetup",
        "demo day", "hackathon", "keynote",
    ]

    def __init__(
        self,
        credentials: Optional[str] = None,
        mcp_server_url: Optional[str] = None,
    ):
        self.credentials = credentials or os.getenv("GOOGLE_MCP_CREDENTIALS")
        self.mcp_server_url = mcp_server_url or os.getenv(
            "GOOGLE_MCP_SERVER_URL", "http://localhost:3000"
        )

    async def list_events(
        self,
        time_min: Optional[datetime] = None,
        time_max: Optional[datetime] = None,
    ) -> list[CalendarEvent]:
        """List upcoming calendar events via MCP.

        TODO: implement the real MCP request/response mapping.
        """
        url = f"{self.mcp_server_url}/calendar/events"
        payload = {
            "credentials": self.credentials,
            "time_min": time_min.isoformat() if time_min else None,
            "time_max": time_max.isoformat() if time_max else None,
        }
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(url, json=payload)
                response.raise_for_status()
                data = response.json()
        except Exception as e:  # pragma: no cover - stub resilience
            print(f"GoogleCalendarClient.list_events stub fallback: {e}")
            return []

        return [self._to_calendar_event(item) for item in data.get("events", [])]

    def detect_conferences(
        self,
        events: list[CalendarEvent],
        user_id: str,
    ) -> list[DetectedEvent]:
        """Classify which calendar events look like conferences.

        STUB heuristic: keyword match on title/description + many attendees.
        """
        detected: list[DetectedEvent] = []
        for ev in events:
            text = f"{ev.title} {ev.description or ''}".lower()
            keyword_hit = any(h in text for h in self.CONFERENCE_HINTS)
            many_attendees = len(ev.attendees_emails) >= 10
            confidence = (0.6 if keyword_hit else 0.0) + (0.3 if many_attendees else 0.0)
            if confidence <= 0:
                continue
            detected.append(
                DetectedEvent(
                    user_id=user_id,
                    calendar_event_id=ev.id,
                    name=ev.title,
                    event_type=EventType.CONFERENCE,
                    location=ev.location,
                    start_date=ev.start_time,
                    end_date=ev.end_time,
                    confidence=round(min(confidence, 1.0), 2),
                    attendee_count=len(ev.attendees_emails),
                )
            )
        return detected

    async def create_event(
        self,
        title: str,
        start_time: datetime,
        end_time: datetime,
        attendees_emails: Optional[list[str]] = None,
        description: Optional[str] = None,
        location: Optional[str] = None,
    ) -> dict:
        """Create a calendar event (e.g. a booked conference meeting) via MCP."""
        url = f"{self.mcp_server_url}/calendar/events/create"
        payload = {
            "credentials": self.credentials,
            "title": title,
            "start_time": start_time.isoformat(),
            "end_time": end_time.isoformat(),
            "attendees": attendees_emails or [],
            "description": description,
            "location": location,
        }
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(url, json=payload)
                response.raise_for_status()
                return response.json()
        except Exception as e:  # pragma: no cover - stub resilience
            print(f"GoogleCalendarClient.create_event stub fallback: {e}")
            return {"status": "stubbed", "title": title}

    @staticmethod
    def _to_calendar_event(item: dict) -> CalendarEvent:
        def _parse(ts: Optional[str]) -> Optional[datetime]:
            if not ts:
                return None
            try:
                return datetime.fromisoformat(ts.replace("Z", "+00:00"))
            except ValueError:
                return None

        return CalendarEvent(
            external_id=item.get("id"),
            title=item.get("summary") or item.get("title") or "Untitled",
            description=item.get("description"),
            location=item.get("location"),
            attendees_emails=[
                a.get("email")
                for a in item.get("attendees", [])
                if a.get("email")
            ],
            start_time=_parse((item.get("start") or {}).get("dateTime")),
            end_time=_parse((item.get("end") or {}).get("dateTime")),
            raw=item,
        )
