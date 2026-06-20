from typing import Optional
from pydantic import BaseModel, Field


class ZeroCRMPayload(BaseModel):
    contact_name: Optional[str] = None
    contact_email: Optional[str] = None
    company_name: str
    company_size: Optional[int] = None
    arr_usd: Optional[int] = None
    funding_stage: Optional[str] = None
    icp_score: int
    buying_signals: dict
    signal_source: str  # "tavily_search"|"event_audio"
    tags: list[str] = Field(default_factory=list)

    # Per-person context accumulated during the meet stage. `personal_context`
    # is the human-readable narrative pushed onto the CRM record; the structured
    # fields back automations / segmentation.
    personal_context: Optional[str] = None
    communication_style: list[str] = Field(default_factory=list)
    values: list[str] = Field(default_factory=list)
    dominant_topic: Optional[str] = None
    pain_points: list[str] = Field(default_factory=list)