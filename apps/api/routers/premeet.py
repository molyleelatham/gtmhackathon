"""Before-meet pipeline endpoints."""
from typing import Optional
from fastapi import APIRouter
from pydantic import BaseModel

from ..store import store
from ...lifecycle.premeet import PreMeetPipeline

router = APIRouter(prefix="/api/v1", tags=["premeet"])


class AttendeeInput(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    title: Optional[str] = None
    company: Optional[str] = None
    company_domain: Optional[str] = None
    interests: list[str] = []
    source: str = "manual"


class PreMeetRequest(BaseModel):
    manual_attendees: list[AttendeeInput] = []
    top_n: int = 10


@router.post("/events/{event_id}/premeet")
async def run_premeet(event_id: str, req: PreMeetRequest):
    """Run the before-meet pipeline: enrich -> warmth-score -> draft outreach."""
    event = store.get_event(event_id)
    if not event:
        return {"error": "not_found", "event_id": event_id}

    pipeline = PreMeetPipeline()
    top = await pipeline.run(
        event,
        manual_attendees=[a.model_dump() for a in req.manual_attendees],
        top_n=req.top_n,
    )
    for c in top:
        store.upsert_connection(c)
    store.upsert_event(event)
    return {"event_id": event_id, "ranked_leads": [c.model_dump() for c in top]}


@router.get("/events/{event_id}/leads")
async def get_event_leads(event_id: str):
    """Highest-intent pre-meet leads for an event, ranked by predicted warmth."""
    conns = store.connections_for_event(event_id)
    conns.sort(key=lambda c: (c.predicted_warmth, c.icp_score), reverse=True)
    return [c.model_dump() for c in conns]
