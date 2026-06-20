"""Post-meet follow-up endpoints."""
from typing import Optional
from fastapi import APIRouter
from pydantic import BaseModel

from ..store import store
from ..integration_helpers import gmail_client_optional, lead_from_connection, warmth_client_email, warmth_client_name
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
    """Draft a post-meet follow-up with scoring + lead + person context for Lightfern.

    Does not send: returns a `draft_ready` draft with a `gmail_compose_url` for
    the user to open in Gmail, where Lightfern completes/polishes it.
    """
    conn = store.get_connection(connection_id)
    warmth = store.warmth_for_connection(connection_id)

    lead = store.leads.get(req.lead_id) if req.lead_id else None
    if lead is None and conn:
        lead = lead_from_connection(conn)
    if lead is None:
        lead = Lead(
            company_name=req.company or "Unknown Company",
            contact_name=req.name,
            contact_email=req.contact_email,
        )

    signal = MeetingSignal(
        connection_id=connection_id,
        name=req.name or (conn.name if conn else None),
        company=req.company or (conn.company_name if conn else None),
        interests=req.interests,
        most_interesting=req.most_interesting,
        what_you_learned=req.what_you_learned,
    )

    scores = None
    if warmth:
        scores = {
            "icp_score": warmth.icp_score,
            "warmth_score": warmth.warmth_score,
            "predicted_score": warmth.predicted_score,
            "actual_score": warmth.actual_score,
            "band": warmth.band.value,
        }

    pipeline = PostMeetPipeline(gmail_client=gmail_client_optional())
    draft = await pipeline.send_followup(
        lead,
        signal,
        extra_context={
            "scores": scores,
            "lead": lead.model_dump(),
            "client_email": warmth_client_email(),
            "client_name": warmth_client_name(),
        },
    )
    if conn:
        conn.draft_subject = draft.get("subject")
        conn.draft_body = draft.get("body")
        store.upsert_connection(conn)
    return draft
