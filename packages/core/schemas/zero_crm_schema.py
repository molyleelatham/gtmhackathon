from typing import Optional, list
from pydantic import BaseModel


class ZeroCRMPayload(BaseModel):
    contact_name: Optional[str] = None
    contact_email: Optional[str] = None
    company_name: str
    company_size: Optional[int] = None
    arr_usd: Optional[int] = None
    funding_stage: Optional[str] = None
    icp_score: int
    buying_signals: dict
    signal_source: str  # "tavily_search"|"conference_audio"
    tags: list[str] = Field(default_factory=list)