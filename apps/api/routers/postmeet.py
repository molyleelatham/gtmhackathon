"""Post-meet follow-up endpoints."""
from typing import Optional
from fastapi import APIRouter
from pydantic import BaseModel

from ..store import store
from ...lifecycle.postmeet import PostMeetPipeline
from ....packages.core.models.lead import Lead
from ....packages.core.models.meeting_signal import MeetingSignal

router = APIRouter(prefix="/api/v1", tags=["postmeet"])


class FollowUpRequest(BaseModel):
    lead_id: Optional[str] = None
    name: Optional[str] = None
    company: Optional[str] = None
    contact_email: Optional[str] = None
    interests: list[str] = []
    most_interesting: Optional[str] = None
    what_you_learned: list[str] = []


@router.post("/connections/{connection_id}/followup")
async def send_followup(connection_id: str, req: FollowUpRequest):
    """Draft a personalized post-meet follow-up and return a Gmail handoff link.

    Does not send: returns a `draft_ready` draft with a `gmail_compose_url` for
    the user to open in Gmail, where Lightfern completes/polishes it.
    """
    lead = store.leads.get(req.lead_id) if req.lead_id else None
    if lead is None:
        lead = Lead(
            company_name=req.company or "Unknown Company",
            contact_name=req.name,
            contact_email=req.contact_email,
        )

    signal = MeetingSignal(
        connection_id=connection_id,
        name=req.name,
        company=req.company,
        interests=req.interests,
        most_interesting=req.most_interesting,
        what_you_learned=req.what_you_learned,
    )

    pipeline = PostMeetPipeline()
    return await pipeline.send_followup(lead, signal)
