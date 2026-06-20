"""Meet stage endpoints (phrase trigger -> signals -> ML routing)."""
from typing import Optional
from fastapi import APIRouter
from pydantic import BaseModel

from ..store import store
from ...lifecycle.meet import MeetPipeline
from ....packages.core.models.meeting_signal import MeetingSignal, TopicTime
from ....packages.core.models.person import PersonNode

router = APIRouter(prefix="/api/v1", tags=["meet"])


class TopicTimeInput(BaseModel):
    topic: str
    seconds: float = 0.0


class MeetingSignalInput(BaseModel):
    event_id: Optional[str] = None
    connection_id: Optional[str] = None
    name: Optional[str] = None
    company: Optional[str] = None
    role: Optional[str] = None
    origin: Optional[str] = None
    interests: list[str] = []
    background: Optional[str] = None
    topic_time: list[TopicTimeInput] = []
    most_time_topic: Optional[str] = None
    what_you_learned: list[str] = []
    most_interesting: Optional[str] = None
    transcript_excerpt: Optional[str] = None
    personal_context: Optional[PersonNode] = None


@router.post("/meet/signals")
async def process_signal(payload: MeetingSignalInput):
    """Process captured meeting signals through the ML pipeline and route them.

    Returns the routing decision: push to CRM + outreach (warmth uplift) or
    route to the founder community (no uplift).
    """
    signal = MeetingSignal(
        event_id=payload.event_id,
        connection_id=payload.connection_id,
        name=payload.name,
        company=payload.company,
        role=payload.role,
        origin=payload.origin,
        interests=payload.interests,
        background=payload.background,
        topic_time=[TopicTime(**t.model_dump()) for t in payload.topic_time],
        most_time_topic=payload.most_time_topic,
        what_you_learned=payload.what_you_learned,
        most_interesting=payload.most_interesting,
        transcript_excerpt=payload.transcript_excerpt,
        personal_context=payload.personal_context,
    )

    prior = (
        store.warmth_for_connection(payload.connection_id)
        if payload.connection_id
        else None
    )

    pipeline = MeetPipeline()
    decision = await pipeline.process(
        signal,
        prior_warmth=prior,
        community_members=store.community_members,
    )
    return decision.model_dump()
