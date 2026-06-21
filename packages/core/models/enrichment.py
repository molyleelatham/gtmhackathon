from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class EnrichedLead(BaseModel):
    company_name: str
    company_domain: Optional[str] = None
    firmographics: dict = Field(default_factory=dict)
    contacts: list[dict] = Field(default_factory=list)
    funding: Optional[dict] = None
    technographics: list[str] = Field(default_factory=list)
    enriched_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
