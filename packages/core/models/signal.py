from datetime import datetime
from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field


class SignalType(str, Enum):
    HIRING = "hiring"
    FUNDING = "funding"
    TECH = "tech_adoption"
    INTENT = "intent"


class Signal(BaseModel):
    id: str = Field(default_factory=lambda: f"sig_{datetime.now().timestamp()}")
    company_name: str
    company_domain: Optional[str] = None
    signal_type: SignalType
    raw_text: str
    source: str  # "tavily_search"|"event_audio"
    keywords_hit: list[str] = Field(default_factory=list)
    detected_at: datetime = Field(default_factory=datetime.utcnow)
    icp_pre_score: Optional[float] = None

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }