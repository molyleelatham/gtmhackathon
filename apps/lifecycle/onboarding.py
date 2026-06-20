"""Onboarding stage.

When a user enters the app we connect their email + Google Calendar via MCP,
pull their events, and detect which ones are conferences worth running the
Warmth lifecycle on (e.g. the demo tech conference).
"""
from datetime import datetime, timedelta
from typing import Optional

from ...packages.integrations.google_calendar.client import GoogleCalendarClient
from ...packages.core.models.event import CalendarEvent, DetectedEvent


class OnboardingService:
    def __init__(self, calendar_client: Optional[GoogleCalendarClient] = None):
        self.calendar_client = calendar_client or GoogleCalendarClient()

    async def connect(self, user_id: str) -> dict:
        """Establish the calendar/email connection via MCP.

        STUB: real implementation performs the OAuth/MCP handshake and stores
        the connection for the user.
        """
        return {
            "user_id": user_id,
            "calendar_connected": bool(self.calendar_client.credentials),
            "status": "connected" if self.calendar_client.credentials else "needs_auth",
        }

    async def discover_events(
        self,
        user_id: str,
        lookahead_days: int = 60,
    ) -> list[DetectedEvent]:
        """Pull calendar events and return the ones detected as conferences."""
        now = datetime.utcnow()
        events: list[CalendarEvent] = await self.calendar_client.list_events(
            time_min=now,
            time_max=now + timedelta(days=lookahead_days),
        )
        return self.calendar_client.detect_conferences(events, user_id=user_id)
