from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field
from enum import Enum


class PermissionLevel(str, Enum):
    READ = "read"
    COMMENT = "comment"
    EDIT = "edit"
    ADMIN = "admin"


class CommunityGroup(BaseModel):
    id: str = Field(default_factory=lambda: f"group_{datetime.now().timestamp()}")
    name: str
    description: Optional[str] = None
    members: list[str] = Field(default_factory=list)  # User IDs
    type: str = "friends"  # friends, founders, team, custom
    created_by: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class CommunityShare(BaseModel):
    id: str = Field(default_factory=lambda: f"share_{datetime.now().timestamp()}")
    conversation_id: str
    lead_id: Optional[str] = None
    shared_with_groups: list[str] = Field(default_factory=list)  # Group IDs
    shared_with_users: list[str] = Field(default_factory=list)  # User IDs
    permission_level: PermissionLevel = PermissionLevel.READ
    shared_by: str
    message: Optional[str] = None
    shared_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }