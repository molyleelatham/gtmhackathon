"""iOS CapturedSignal schema (POST /api/signals).

Matches `Warmth-iOS/Warmth/Models/CapturedSignal.swift` from the Xcode app.
"""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class SignalUser(BaseModel):
    uid: str
    id_token: str


class SignalPerson(BaseModel):
    name: str
    org: Optional[str] = None
    role: Optional[str] = None


class SignalRelation(BaseModel):
    subject: str
    predicate: str
    object: str


class SignalDevice(BaseModel):
    model: str
    os: str


class CapturedSignalPayload(BaseModel):
    """Payload from the Warmth iOS app (`SignalClient`)."""
    user: SignalUser
    session_id: str
    captured_at: datetime
    person: SignalPerson
    relations: list[SignalRelation] = Field(default_factory=list)
    interests: list[str] = Field(default_factory=list)
    icp_keyword_score: int = Field(ge=0, le=100)
    transcript_excerpt: str
    device: SignalDevice

    @property
    def idempotency_key(self) -> str:
        return f"{self.session_id}:{self.person.name.lower()}:{self.captured_at.isoformat()}"
