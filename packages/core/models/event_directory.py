from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class EventAttendee(BaseModel):
    id: str
    name: str
    title: Optional[str] = None
    company: Optional[str] = None
    email: Optional[str] = None
    linkedin: Optional[str] = None
    interests: list[str] = Field(default_factory=list)
    funding_stage: Optional[str] = None
    investor_type: Optional[str] = None  # VC, angel, etc.
    founder: bool = False
    notes: Optional[str] = None


class EventDirectory(BaseModel):
    id: str = Field(default_factory=lambda: f"conf_{datetime.now().timestamp()}")
    name: str
    url: Optional[str] = None
    directory_url: Optional[str] = None
    directory_type: str = "web"  # web, pdf, api
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    location: Optional[str] = None
    attendees: list[EventAttendee] = Field(default_factory=list)
    scraped_at: Optional[datetime] = None
    total_attendees: int = 0
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }