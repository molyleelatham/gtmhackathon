"""iOS event-audio signal schema (POST /api/signals).

Distinct from packages/core/models/signal.py (Tavily GTM passive listening).
Matches iOS Signal.swift CodingKeys.
"""
from datetime import datetime
from enum import Enum
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field, field_validator


class RelationshipKind(str, Enum):
    works_with = "works_with"
    works_at = "works_at"
    reports_to = "reports_to"
    knows = "knows"
    introduced_by = "introduced_by"


class IOSPersonNode(BaseModel):
    name: str
    company: Optional[str] = None
    title: Optional[str] = None
    related_names: list[str] = Field(default_factory=list)
    icp_keywords_hit: list[str] = Field(default_factory=list)
    first_seen: Optional[datetime] = None
    last_seen: Optional[datetime] = None
    mention_count: int = 1


class IOSCompanyMention(BaseModel):
    name: str
    icp_keywords_hit: list[str] = Field(default_factory=list)


class IOSRelationship(BaseModel):
    subject: str
    kind: RelationshipKind
    object: str


class EventAudioSignal(BaseModel):
    """Payload from iOS SignalAPIClient (POST /api/signals)."""
    id: UUID
    person: IOSPersonNode
    company: Optional[IOSCompanyMention] = None
    relationships: list[IOSRelationship] = Field(default_factory=list)
    icp_pre_score: float = Field(ge=0, le=100)
    raw_text: str
    source: str = "event_audio"
    detected_at: datetime = Field(default_factory=datetime.utcnow)

    @field_validator("source", mode="before")
    @classmethod
    def normalize_source(cls, value: object) -> str:
        if value in ("event_audio", "event"):
            return "event_audio"
        return str(value) if value is not None else "event_audio"
