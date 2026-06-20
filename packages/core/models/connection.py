from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field
from enum import Enum


class ConnectionStatus(str, Enum):
    PENDING = "pending"
    INITIATED = "initiated"
    EMAIL_DRAFTED = "email_drafted"
    EMAIL_SENT = "email_sent"
    RESPONDED = "responded"
    CONVERTED = "converted"
    FAILED = "failed"


class FirstConnection(BaseModel):
    id: str = Field(default_factory=lambda: f"conn_{datetime.now().timestamp()}")
    conference_id: Optional[str] = None
    attendee_id: str
    attendee_name: str
    attendee_email: Optional[str] = None
    attendee_company: Optional[str] = None
    attendee_interests: list[str] = Field(default_factory=list)
    match_score: float = 0.0
    connection_reason: str  # Why this connection was suggested
    email_draft: Optional[str] = None
    email_subject: Optional[str] = None
    status: ConnectionStatus = ConnectionStatus.PENDING
    initiated_at: Optional[datetime] = None
    responded_at: Optional[datetime] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }