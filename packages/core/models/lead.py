from datetime import datetime
from typing import Optional, list
from pydantic import BaseModel, Field
from .signal import Signal, SignalType


class Lead(BaseModel):
    id: str = Field(default_factory=lambda: f"lead_{datetime.now().timestamp()}")
    contact_name: Optional[str] = None
    contact_email: Optional[str] = None
    company_name: str
    company_domain: Optional[str] = None
    company_size: Optional[int] = None
    arr_usd: Optional[int] = None
    funding_stage: Optional[str] = None
    signals: list[Signal] = Field(default_factory=list)
    icp_score: int = 0
    buying_signals: dict = Field(default_factory=dict)
    signal_source: str = "tavily_search"
    tags: list[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }