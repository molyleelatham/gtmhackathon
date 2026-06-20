from datetime import datetime
from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field


class PreMeetStatus(str, Enum):
    IDENTIFIED = "identified"          # found in attendee dataset
    ENRICHED = "enriched"              # Unify research applied
    SCORED = "scored"                  # warmth predicted
    OUTREACH_DRAFTED = "outreach_drafted"  # Gmail draft created via MCP
    OUTREACH_SENT = "outreach_sent"
    MEETING_SET = "meeting_set"        # calendar event created


class PreMeetConnection(BaseModel):
    """A potential connection identified BEFORE a conference.

    Built from the attendee dataset (calendar-derived attendees and/or scraped
    conference directory), enriched via UnifyGTM, then scored for warmth so we
    can surface the highest-intent leads for pre-conference outreach.
    """
    id: str = Field(default_factory=lambda: f"premeet_{datetime.now().timestamp()}")
    event_id: str
    user_id: str

    # identity
    name: Optional[str] = None
    email: Optional[str] = None
    title: Optional[str] = None
    linkedin: Optional[str] = None

    # firmographics (enriched via UnifyGTM)
    company_name: Optional[str] = None
    company_domain: Optional[str] = None
    company_size: Optional[int] = None
    industry: Optional[str] = None
    funding_stage: Optional[str] = None
    arr_usd: Optional[int] = None
    technographics: list[str] = Field(default_factory=list)

    # "parasocial" pre-meet context used to personalize outreach
    interests: list[str] = Field(default_factory=list)
    research_notes: list[str] = Field(default_factory=list)

    # scoring (see packages/ml + WarmthScore)
    icp_score: float = 0.0
    predicted_warmth: float = 0.0
    intent_score: float = 0.0

    # outreach
    draft_subject: Optional[str] = None
    draft_body: Optional[str] = None
    gmail_draft_id: Optional[str] = None

    source: str = "calendar"  # "calendar" | "directory_scrape" | "manual"
    status: PreMeetStatus = PreMeetStatus.IDENTIFIED
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        json_encoders = {datetime: lambda v: v.isoformat()}
