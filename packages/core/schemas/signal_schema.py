from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field

from ..models.signal import SignalType


class SignalCreate(BaseModel):
    company_name: str
    company_domain: Optional[str] = None
    signal_type: SignalType
    raw_text: str
    source: str
    keywords_hit: list[str] = Field(default_factory=list)


class SignalResponse(BaseModel):
    id: str
    company_name: str
    company_domain: Optional[str] = None
    signal_type: SignalType
    raw_text: str
    source: str
    keywords_hit: list[str]
    detected_at: datetime
    icp_pre_score: Optional[float] = None

    class Config:
        from_attributes = True
