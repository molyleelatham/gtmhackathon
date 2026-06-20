from datetime import datetime
from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field


class EventSource(str, Enum):
    GOOGLE_CALENDAR = "google_calendar"
    EMAIL = "email"
    MANUAL = "manual"


class EventType(str, Enum):
    EVENT = "event"
    MEETING = "meeting"
    MEETUP = "meetup"
    UNKNOWN = "unknown"

    @classmethod
    def _missing_(cls, value: object):
        if value == "event":
            return cls.EVENT
        return None


class LifecycleStage(str, Enum):
    """Stage of the warmth lifecycle a connection/event is currently in."""
    BEFORE_MEET = "before_meet"
    MEET = "meet"
    POST_MEET = "post_meet"


class CalendarEvent(BaseModel):
    """A calendar event ingested from Google Calendar / email via MCP."""
    id: str = Field(default_factory=lambda: f"cal_{datetime.now().timestamp()}")
    external_id: Optional[str] = None  # provider event id
    title: str
    description: Optional[str] = None
    location: Optional[str] = None
    source: EventSource = EventSource.GOOGLE_CALENDAR
    attendees_emails: list[str] = Field(default_factory=list)
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    raw: dict = Field(default_factory=dict)

    class Config:
        json_encoders = {datetime: lambda v: v.isoformat()}


class DetectedEvent(BaseModel):
    """An event Warmth has classified as worth running the lifecycle on.

    For the demo this is a tech event detected from the user's calendar.
    """
    id: str = Field(default_factory=lambda: f"event_{datetime.now().timestamp()}")
    user_id: str
    calendar_event_id: Optional[str] = None
    name: str
    event_type: EventType = EventType.EVENT
    location: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    directory_url: Optional[str] = None  # event attendee directory to scrape
    confidence: float = 0.0  # how confident detection is that this is an event
    stage: LifecycleStage = LifecycleStage.BEFORE_MEET
    attendee_count: int = 0
    premeet_completed: bool = False
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        json_encoders = {datetime: lambda v: v.isoformat()}
