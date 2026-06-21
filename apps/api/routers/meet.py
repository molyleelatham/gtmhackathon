"""Meet stage endpoints — encode, route, Gmail handoff for Lightfern."""
import asyncio
from typing import Optional

from fastapi import APIRouter
from pydantic import BaseModel

from ....packages.core.models.meeting_signal import MeetingSignal, TopicTime
from ....packages.core.models.person import PersonNode
from ....packages.core.models.warmth import WarmthBand, WarmthScore
from ...agent.meet_pipeline import MeetStageAgent
from ..integration_helpers import (
    lead_from_connection,
    lead_from_signal,
    use_agent_extraction,
    zero_client_optional,
)
from ..interest_helpers import interests_from_meet_summary
from ..store import get_store

router = APIRouter(prefix="/api/v1", tags=["meet"])


class TopicTimeInput(BaseModel):
    topic: str
    seconds: float = 0.0


class Turn(BaseModel):
    speaker: int
    text: str


class SpeakerAttr(BaseModel):
    name: Optional[str] = None
    company: Optional[str] = None
    role: Optional[str] = None


class EncodeRequest(BaseModel):
    turns: list[Turn]
    self_speaker_id: int = 0
    speaker_attrs: dict[int, SpeakerAttr] = {}
    event_id: Optional[str] = None
    connection_id: Optional[str] = None
    use_agent: bool = False


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


def _attrs(req: EncodeRequest) -> dict[int, dict]:
    return {sid: a.model_dump() for sid, a in req.speaker_attrs.items()}


def _agent(use_agent: Optional[bool] = None) -> MeetStageAgent:
    return MeetStageAgent(
        use_agent=use_agent if use_agent is not None else use_agent_extraction(),
        zero_client=zero_client_optional(),
    )


def _persist_meet_result(connection_id: str, summary: dict) -> None:
    decision = summary.get("decision") or {}
    warmth_data = decision.get("warmth") or {}
    conn = get_store().get_connection(connection_id)
    if conn and warmth_data:
        actual = warmth_data.get("actual_score")
        if actual is not None:
            conn.predicted_warmth = float(actual)
            get_store().upsert_connection(conn)
        band = warmth_data.get("band", "warm")
        try:
            warmth_band = WarmthBand(band)
        except ValueError:
            warmth_band = WarmthBand.WARM
        get_store().upsert_warmth(
            WarmthScore(
                connection_id=connection_id,
                icp_score=int(warmth_data.get("icp_score") or 0),
                warmth_score=float(warmth_data.get("warmth_score") or 0),
                predicted_score=warmth_data.get("predicted_score"),
                actual_score=actual,
                band=warmth_band,
            )
        )
    draft = summary.get("gmail_draft") or {}
    if conn and draft:
        conn.draft_subject = draft.get("subject")
        conn.draft_body = draft.get("body")
        get_store().upsert_connection(conn)
    merged_interests = interests_from_meet_summary(summary, list(conn.interests) if conn else [])
    if conn and merged_interests:
        conn.interests = merged_interests
        get_store().upsert_connection(conn)
    get_store().record_meet_result(
        connection_id=connection_id,
        signal_id=connection_id,
        routed_to=summary.get("routed_to", "unknown"),
        narrative=summary.get("narrative"),
        gmail_draft=summary.get("gmail_draft"),
        outreach_sequence=summary.get("outreach_sequence"),
        interests=merged_interests,
        knowledge_graph=summary.get("people") or [],
        matched_candidates=decision.get("matched_candidates") or [],
    )


@router.post("/meet/encode")
async def encode_meet(req: EncodeRequest):
    """Diarized transcript → MeetingSignal + knowledge graph."""
    agent = _agent(req.use_agent)
    signal, kg = await asyncio.to_thread(
        agent.encoder.encode,
        [t.model_dump() for t in req.turns],
        req.self_speaker_id,
        _attrs(req),
        req.event_id,
        req.connection_id,
    )
    return {
        "engine": "cursor-agent" if req.use_agent else "heuristic",
        "signal": signal.model_dump(),
        "people": [p.model_dump() for p in kg.people()],
    }


@router.post("/meet/process")
async def process_meet(req: EncodeRequest):
    """Encode + score + Gmail draft (scoring/lead/person context for Lightfern)."""
    agent = _agent(req.use_agent)
    summary = await agent.run(
        turns=[t.model_dump() for t in req.turns],
        speaker_attrs=_attrs(req),
        self_speaker_id=req.self_speaker_id,
        connection_id=req.connection_id,
        prior_warmth=(
            get_store().warmth_for_connection(req.connection_id)
            if req.connection_id
            else None
        ),
        community_members=get_store().community_members,
        lead=(
            lead_from_connection(get_store().get_connection(req.connection_id))
            if req.connection_id and get_store().get_connection(req.connection_id)
            else None
        ),
    )
    if req.connection_id:
        _persist_meet_result(req.connection_id, summary)
    return summary


@router.post("/meet/signals")
async def process_signal(payload: MeetingSignalInput):
    """Structured MeetingSignal → routing + Gmail handoff."""
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
        get_store().warmth_for_connection(payload.connection_id)
        if payload.connection_id
        else None
    )
    conn = get_store().get_connection(payload.connection_id) if payload.connection_id else None
    agent = _agent()
    summary = await agent.run(
        turns=[
            {"speaker": 0, "text": "..."},
            {"speaker": 1, "text": signal.transcript_excerpt or " ".join(signal.interests)},
        ],
        speaker_attrs={
            1: {"name": signal.name, "company": signal.company, "role": signal.role}
        },
        connection_id=payload.connection_id,
        prior_warmth=prior,
        lead=lead_from_signal(signal, conn),
        community_members=get_store().community_members,
    )
    if payload.connection_id:
        _persist_meet_result(payload.connection_id, summary)
    return summary
