"""Ingest iOS signals into the meet pipeline + get_store()."""
from __future__ import annotations

from typing import Any, Optional

from ...packages.core.auth import auth_required
from ...packages.core.models.event import DetectedEvent, EventType, LifecycleStage
from ...packages.core.models.lead import Lead
from ...packages.core.models.pre_connection import PreMeetConnection, PreMeetStatus
from ...packages.core.models.warmth import WarmthBand, WarmthScore
from ...packages.core.schemas.captured_signal import CapturedSignalPayload
from ...packages.core.schemas.event_audio_signal import EventAudioSignal
from ..agent.meet_pipeline import MeetStageAgent
from ..api.integration_helpers import use_agent_extraction, zero_client_optional
from ..api.interest_helpers import interests_from_meet_summary
from ..api.store import DEMO_USER_ID, get_store
from ..api.user_context import get_user_id

# Idempotency cache: client signal key -> connection id (process-local fallback)
_ingested: dict[str, str] = {}


def _existing_connection_for_signal(signal_key: str, user_id: str) -> Optional[str]:
    store = get_store(user_id)
    if signal_key in store.signal_index:
        return store.signal_index[signal_key]
    if signal_key in _ingested:
        return _ingested[signal_key]
    from ..api.store import _get_repo, _use_firestore_store

    if _use_firestore_store():
        conn_id = _get_repo().signal_index_lookup(user_id, signal_key)
        if conn_id:
            store.signal_index[signal_key] = conn_id
            _ingested[signal_key] = conn_id
            return conn_id
    return None


def _band_from_score(score: float) -> WarmthBand:
    if score >= 70:
        return WarmthBand.HOT
    if score >= 40:
        return WarmthBand.WARM
    return WarmthBand.COLD


def _default_event(user_id: str) -> DetectedEvent:
    store = get_store(user_id)
    events = store.list_events(user_id)
    if events:
        return events[0]
    event = DetectedEvent(
        id="event_live_capture",
        user_id=user_id,
        name="Live Event",
        event_type=EventType.EVENT,
        location="On-site",
        confidence=1.0,
        stage=LifecycleStage.MEET,
    )
    store.upsert_event(event)
    return event


def _duplicate_response(conn_id: str, user_id: str) -> dict[str, Any]:
    store = get_store(user_id)
    conn = store.pre_connections.get(conn_id)
    warmth = store.warmth_for_connection(conn_id)
    meet = store.meet_result_for(conn_id)
    return {
        "status": "duplicate",
        "connection_id": conn_id,
        "connection": conn.model_dump() if conn else None,
        "warmth": warmth.model_dump() if warmth else None,
        "gmail_draft": (meet or {}).get("gmail_draft"),
    }


async def _run_meet_pipeline(
    *,
    signal_key: str,
    turns: list[dict],
    speaker_attrs: dict[int, dict],
    self_speaker_id: int,
    name: str,
    title: Optional[str],
    company_name: Optional[str],
    interests: list[str],
    icp_pre_score: float,
    user_id: str = DEMO_USER_ID,
    relations: Optional[list[dict]] = None,
) -> dict[str, Any]:
    store = get_store(user_id)
    existing = _existing_connection_for_signal(signal_key, user_id)
    if existing:
        return _duplicate_response(existing, user_id)

    event = _default_event(user_id)
    agent = MeetStageAgent(
        use_agent=use_agent_extraction(),
        zero_client=zero_client_optional(),
    )
    summary = await agent.run(
        turns=turns,
        speaker_attrs=speaker_attrs,
        self_speaker_id=self_speaker_id,
        community_members=store.community_members,
    )

    decision = summary["decision"]
    warmth_data = decision.get("warmth") or {}
    actual = warmth_data.get("actual_score") or icp_pre_score
    predicted = warmth_data.get("predicted_score") or icp_pre_score
    merged_interests = interests_from_meet_summary(summary, interests)

    conn = PreMeetConnection(
        event_id=event.id,
        user_id=user_id,
        name=name,
        title=title,
        company_name=company_name or "Unknown Company",
        interests=merged_interests,
        icp_score=int(icp_pre_score),
        predicted_warmth=float(predicted),
        intent_score=int(icp_pre_score),
        status=PreMeetStatus.MET if summary["pushed_to_crm"] else PreMeetStatus.SCORED,
        source="event_audio",
        draft_subject=(summary.get("gmail_draft") or {}).get("subject"),
        draft_body=(summary.get("gmail_draft") or {}).get("body"),
    )
    store.upsert_connection(conn)

    warmth = WarmthScore(
        connection_id=conn.id,
        icp_score=int(warmth_data.get("icp_score") or icp_pre_score),
        warmth_score=float(warmth_data.get("warmth_score") or icp_pre_score),
        predicted_score=float(predicted),
        actual_score=float(actual),
        band=_band_from_score(float(actual)),
    )
    store.upsert_warmth(warmth)

    lead = Lead(
        company_name=company_name or "Unknown Company",
        contact_name=name,
        icp_score=int(icp_pre_score),
        signal_source="event_audio",
        tags=merged_interests,
    )
    store.upsert_lead(lead)

    store.record_meet_result(
        connection_id=conn.id,
        signal_id=signal_key,
        routed_to=summary["routed_to"],
        narrative=summary.get("narrative"),
        gmail_draft=summary.get("gmail_draft"),
        outreach_sequence=summary.get("outreach_sequence"),
        interests=merged_interests,
        relations=relations or [],
        knowledge_graph=summary.get("people") or [],
        matched_candidates=(summary.get("decision") or {}).get("matched_candidates") or [],
    )

    _ingested[signal_key] = conn.id

    return {
        "status": "accepted",
        "connection_id": conn.id,
        "lead_id": lead.id,
        "interests": merged_interests,
        "routed_to": summary["routed_to"],
        "pushed_to_crm": summary["pushed_to_crm"],
        "handoff": summary.get("handoff", "gmail_lightfern"),
        "narrative": summary.get("narrative"),
        "gmail_draft": summary.get("gmail_draft"),
        "outreach_sequence": summary.get("outreach_sequence"),
        "scores": summary.get("scores"),
        "decision": decision,
    }


def _legacy_signal_to_turns(
    payload: EventAudioSignal,
) -> tuple[list[dict], dict[int, dict], int]:
    speaker_id = 1
    attrs = {
        speaker_id: {
            "name": payload.person.name,
            "company": payload.company.name if payload.company else payload.person.company,
            "role": payload.person.title,
        }
    }
    turns = [
        {"speaker": 0, "text": "..."},
        {"speaker": speaker_id, "text": payload.raw_text},
    ]
    return turns, attrs, 0


def _captured_signal_to_turns(
    payload: CapturedSignalPayload,
) -> tuple[list[dict], dict[int, dict], int]:
    speaker_id = 1
    attrs = {
        speaker_id: {
            "name": payload.person.name,
            "company": payload.person.org,
            "role": payload.person.role,
        }
    }
    text = payload.transcript_excerpt.strip() or " ".join(payload.interests)
    turns = [{"speaker": 0, "text": "..."}, {"speaker": speaker_id, "text": text}]
    return turns, attrs, 0


async def ingest_captured_signal(payload: CapturedSignalPayload) -> dict[str, Any]:
    """Run the Xcode app's CapturedSignal through MeetStageAgent → Gmail handoff."""
    uid = get_user_id()
    claimed_uid = payload.user.uid or uid
    if auth_required() and claimed_uid != uid:
        return {
            "status": "error",
            "reason": "user_mismatch",
            "detail": "Signal user uid does not match authenticated user",
        }
    turns, attrs, self_speaker = _captured_signal_to_turns(payload)
    return await _run_meet_pipeline(
        signal_key=payload.idempotency_key,
        turns=turns,
        speaker_attrs=attrs,
        self_speaker_id=self_speaker,
        name=payload.person.name,
        title=payload.person.role,
        company_name=payload.person.org,
        interests=list(payload.interests),
        icp_pre_score=float(payload.icp_keyword_score),
        user_id=uid,
        relations=[r.model_dump() for r in payload.relations],
    )


async def ingest_ios_signal(payload: EventAudioSignal) -> dict[str, Any]:
    """Run legacy wake-word pipeline Signal through MeetStageAgent."""
    user_id = get_user_id()
    claimed_uid = payload.user_uid or user_id
    if auth_required() and claimed_uid != user_id:
        return {
            "status": "error",
            "reason": "user_mismatch",
            "detail": "Signal user uid does not match authenticated user",
        }
    turns, attrs, self_speaker = _legacy_signal_to_turns(payload)
    return await _run_meet_pipeline(
        signal_key=str(payload.id),
        turns=turns,
        speaker_attrs=attrs,
        self_speaker_id=self_speaker,
        name=payload.person.name,
        title=payload.person.title,
        company_name=(
            payload.company.name if payload.company else payload.person.company
        ),
        interests=list(payload.person.icp_keywords_hit),
        icp_pre_score=float(payload.icp_pre_score),
        user_id=user_id,
    )
