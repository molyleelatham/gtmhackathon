"""Warmth user profile persisted in Firestore users/{uid}."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class UserProfile(BaseModel):
    uid: str
    email: str | None = None
    display_name: str | None = None
    photo_url: str | None = None
    demo_seeded: bool = False
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
