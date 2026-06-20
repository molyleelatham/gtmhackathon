"""Read endpoints powering the web dashboard."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Optional

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel

from ..integration_helpers import (
    gmail_client_optional,
    hubspot_client_optional,
    unify_client_optional,
    zero_client_optional,
)
from ..store import get_store
from ..user_context import get_user_id
from ...lifecycle.contact_sync import ContactSyncPipeline
from ....packages.core.models.icp import ICPConfig
from ....packages.core.models.lead import Lead
from ....packages.core.models.pre_connection import PreMeetConnection

router = APIRouter(prefix="/api/v1", tags=["data"])


def _derive_signals(
    connections: list[PreMeetConnection], leads: list[Lead]
) -> list[dict[str, Any]]:
    """Lightweight signal feed derived from roster + CRM leads (no extra service)."""
    signals: list[dict[str, Any]] = []
    for conn in connections:
        company = conn.company_name or "Unknown"
        if conn.funding_stage:
            signals.append(
                {
                    "id": f"sig_{conn.id}_fund",
                    "company": company,
                    "type": "funding",
                    "desc": f"{conn.funding_stage} — {conn.name or 'Attendee'} on your roster.",
                    "time": "Today",
                }
            )
        if conn.intent_score >= 60:
            note = ""
            if conn.research_notes:
                note = conn.research_notes[0][:120]
            signals.append(
                {
                    "id": f"sig_{conn.id}_intent",
                    "company": company,
                    "type": "intent",
                    "desc": note or f"High intent ({int(conn.intent_score)}) — worth a pre-meet note.",
                    "time": "Today",
                }
            )
        if any("hiring" in i.lower() for i in conn.interests):
            signals.append(
                {
                    "id": f"sig_{conn.id}_hire",
                    "company": company,
                    "type": "hiring",
                    "desc": f"{conn.name or company} flagged hiring / team expansion.",
                    "time": "Today",
                }
            )
    for lead in leads:
        for tag in lead.tags[:2]:
            signals.append(
                {
                    "id": f"sig_lead_{lead.id}_{tag}",
                    "company": lead.company_name,
                    "type": "intent",
                    "desc": f"CRM signal: {tag.replace('_', ' ')}.",
                    "time": "Recent",
                }
            )
    # De-dupe by company+type, cap feed length
    seen: set[tuple[str, str]] = set()
    unique: list[dict[str, Any]] = []
    for s in signals:
        key = (s["company"], s["type"])
        if key in seen:
            continue
        seen.add(key)
        unique.append(s)
    return unique[:12]


@router.get("/dashboard")
async def dashboard():
    user_id = get_user_id()
    """Summary stats + the current pipeline at a glance for the dashboard home."""
    events = get_store().list_events(user_id)
    all_connections = [
        c for e in events for c in get_store().connections_for_event(e.id)
    ]
    hot = [c for c in all_connections if c.predicted_warmth >= 70]
    return {
        "user_id": user_id,
        "events": len(events),
        "connections": len(all_connections),
        "hot_leads": len(hot),
        "leads_in_crm": len(get_store().list_leads()),
        "upcoming_events": [e.model_dump() for e in events],
        "top_leads": [
            c.model_dump()
            for c in sorted(
                all_connections, key=lambda x: x.predicted_warmth, reverse=True
            )[:5]
        ],
    }


@router.get("/leads")
async def list_leads():
    return [l.model_dump() for l in get_store().list_leads()]


@router.get("/connections")
async def list_connections():
    user_id = get_user_id()
    return [c.model_dump() for c in get_store().list_connections(user_id)]


@router.get("/connections/{connection_id}")
async def get_connection(connection_id: str):
    user_id = get_user_id()
    conn = get_store().get_connection(connection_id)
    if not conn or conn.user_id != user_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Connection not found")
    warmth = get_store().warmth_for_connection(connection_id)
    meet = get_store().meet_result_for(connection_id)
    return {
        "connection": conn.model_dump(),
        "warmth": warmth.model_dump() if warmth else None,
        "meet_result": meet,
        "gmail_draft": (meet or {}).get("gmail_draft"),
    }


@router.get("/community/members")
async def community_members():
    return get_store().community_members


@router.post("/dashboard/sync-gtm-hackathon")
async def sync_gtm_hackathon_dashboard():
    """Refresh in-memory dashboard roster from GTM Hackathon calendar + Tavily data."""
    event = get_store().refresh_gtm_hackathon(user_id=get_user_id())
    connections = get_store().connections_for_event(event.id)
    return {
        "status": "ok",
        "event": event.model_dump(),
        "connections": len(connections),
        "attendees": [c.model_dump() for c in connections],
    }


@router.post("/contacts/sync")
async def sync_contacts():
    """Run ContactSyncPipeline on GTM Hackathon attendees JSON."""
    data_file = Path(__file__).resolve().parents[3] / "data" / "gtm_hackathon_attendees.json"
    attendees: list[dict[str, Any]] = []
    if data_file.exists():
        attendees = json.loads(data_file.read_text())

    event = get_store().refresh_gtm_hackathon(attendees, user_id=get_user_id())
    pipeline = ContactSyncPipeline(
        hubspot_client=hubspot_client_optional(),
        unify_client=unify_client_optional(),
        zero_client=zero_client_optional(),
    )
    sync_result = await pipeline.process_batch(
        attendees=attendees,
        event_id=event.id,
        event_name=event.name,
    )
    connections = sync_result.get("connections", [])
    get_store().refresh_gtm_hackathon(
        attendees,
        user_id=get_user_id(),
        premeet_results=connections,
        sync_results=sync_result,
    )
    return {
        "status": "ok",
        "event": event.model_dump(),
        "attendees": len(attendees),
        "connections": len(connections),
        "hubspot": sync_result.get("hubspot", {}),
        "zero": sync_result.get("zero", {}),
    }


@router.get("/dashboard/roster")
async def dashboard_roster():
    user_id = get_user_id()
    """Attending + met tabs and signal feed for the dashboard home."""
    events = get_store().list_events(user_id)
    primary = events[0] if events else None
    connections = (
        get_store().connections_for_event(primary.id)
        if primary
        else get_store().list_connections(user_id)
    )
    sorted_attendees = sorted(connections, key=lambda c: c.icp_score, reverse=True)
    met: list[dict[str, Any]] = []
    for conn in connections:
        meet = get_store().meet_result_for(conn.id)
        if meet:
            met.append(
                {
                    "connection": conn.model_dump(),
                    "meet_result": meet,
                }
            )
    met.sort(
        key=lambda row: row["meet_result"].get("recorded_at") or "",
        reverse=True,
    )
    return {
        "event": primary.model_dump() if primary else None,
        "attendees": [c.model_dump() for c in sorted_attendees],
        "met": met,
        "signals": _derive_signals(connections, get_store().list_leads()),
    }


@router.get("/integrations")
async def list_integrations():
    """Integration status for the settings page (env-gated clients)."""
    import os

    def status(name: str, connected: bool, pending: bool = False) -> dict[str, str]:
        if connected:
            st = "connected"
        elif pending:
            st = "pending"
        else:
            st = "offline"
        return {"name": name, "status": st}

    gmail = gmail_client_optional()
    return [
        status("HubSpot", hubspot_client_optional() is not None),
        status("Zero CRM", zero_client_optional() is not None),
        status("UnifyGTM", unify_client_optional() is not None),
        status(
            "Google MCP",
            gmail is not None,
            pending=bool(os.getenv("GOOGLE_MCP_SERVER_URL")) and gmail is None,
        ),
        status("Deepgram", bool(os.getenv("DEEPGRAM_API_KEY"))),
        status("Tavily", bool(os.getenv("TAVILY_API_KEY"))),
        status("Lightfern", True),
    ]


@router.get("/icp")
async def get_icp_profile():
    icp = ICPConfig()
    industries = icp.target_industries or ["B2B SaaS", "Fintech", "DevTools"]
    return [
        {
            "label": "Company size",
            "value": f"{icp.size_range[0]}–{icp.size_range[1]} employees",
        },
        {
            "label": "ARR",
            "value": f"${icp.arr_range[0] // 1_000_000}M – ${icp.arr_range[1] // 1_000_000}M",
        },
        {"label": "Industries", "value": ", ".join(industries)},
        {"label": "Tech stack", "value": ", ".join(icp.tech_stack)},
        {"label": "Keywords", "value": ", ".join(icp.keywords[:6])},
    ]


class MatchAttendeeRequest(BaseModel):
    name: str
    company: Optional[str] = None
    transcript: Optional[str] = None


@router.post("/match/attendee")
async def match_attendee(req: MatchAttendeeRequest):
    """Match a live 'hi {name}' detection to a known event attendee."""
    from ...listener.intelligence.attendee_matcher import AttendeeMatcher
    from ....packages.core.models.meeting_signal import MeetingSignal

    pipeline_leads = [c.model_dump() for c in get_store().pre_connections.values()]
    signal = MeetingSignal(name=req.name, company=req.company)
    matcher = AttendeeMatcher()
    result = matcher.match(signal, matcher.candidates_from_pipeline(pipeline_leads))

    if result is None:
        return {
            "matched": False,
            "name": req.name,
            "message": f"No roster match for “{req.name}” yet.",
        }

    conn_id = result.candidate.external_id
    conn = get_store().get_connection(conn_id) if conn_id else None
    warmth = get_store().warmth_for_connection(conn_id) if conn_id else None
    meet = get_store().meet_result_for(conn_id) if conn_id else None
    kg = (meet or {}).get("knowledge_graph") or []
    interests = list(conn.interests) if conn else []

    return {
        "matched": True,
        "score": result.score,
        "matched_on": result.matched_on,
        "message": f"You're now connected with {result.candidate.name}.",
        "connection": conn.model_dump() if conn else result.candidate.raw,
        "warmth": warmth.model_dump() if warmth else None,
        "interests": interests,
        "knowledge_graph": kg,
    }
