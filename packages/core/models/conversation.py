from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class ConversationIntelligence(BaseModel):
    id: str = Field(default_factory=lambda: f"conv_{datetime.now().timestamp()}")
    lead_id: str
    event_id: Optional[str] = None
    transcript: str
    topics: list[str] = Field(default_factory=list)
    interests: list[str] = Field(default_factory=list)
    values: list[str] = Field(default_factory=list)
    pain_points: list[str] = Field(default_factory=list)
    goals: list[str] = Field(default_factory=list)
    what_you_learned: list[str] = Field(default_factory=list)
    sentiment: str = "neutral"  # positive, neutral, negative
    key_insights: list[str] = Field(default_factory=list)
    follow_up_actions: list[str] = Field(default_factory=list)
    recording_started_at: datetime
    recording_ended_at: Optional[datetime] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }