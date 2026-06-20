from datetime import datetime
from typing import Optional, list
from pydantic import BaseModel, Field
from enum import Enum


class AgentStatus(str, Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"


class AgentType(str, Enum):
    OUTREACH = "outreach"
    FOLLOWUP = "followup"
    NURTURING = "nurturing"
    RESEARCH = "research"


class AutoAgent(BaseModel):
    id: str = Field(default_factory=lambda: f"agent_{datetime.now().timestamp()}")
    name: str
    type: AgentType
    lead_id: str
    conversation_id: Optional[str] = None
    strategy: dict = Field(default_factory=dict)
    email_templates: list[str] = Field(default_factory=list)
    schedule: dict = Field(default_factory=dict)
    status: AgentStatus = AgentStatus.DRAFT
    emails_sent: int = 0
    responses_received: int = 0
    conversion_rate: float = 0.0
    created_by: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    next_action_at: Optional[datetime] = None
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }