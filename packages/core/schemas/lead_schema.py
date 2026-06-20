from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class LeadCreate(BaseModel):
    contact_name: Optional[str] = None
    contact_email: Optional[str] = None
    company_name: str
    company_domain: Optional[str] = None
    company_size: Optional[int] = None
    arr_usd: Optional[int] = None
    funding_stage: Optional[str] = None
    signal_source: str = "tavily_search"


class LeadResponse(BaseModel):
    id: str
    contact_name: Optional[str] = None
    contact_email: Optional[str] = None
    company_name: str
    company_domain: Optional[str] = None
    company_size: Optional[int] = None
    arr_usd: Optional[int] = None
    funding_stage: Optional[str] = None
    icp_score: int
    buying_signals: dict
    signal_source: str
    tags: list[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True