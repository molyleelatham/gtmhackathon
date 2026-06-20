"""Read endpoints powering the web dashboard."""
from fastapi import APIRouter

from ..store import store, DEMO_USER_ID

router = APIRouter(prefix="/api/v1", tags=["data"])


@router.get("/dashboard")
async def dashboard(user_id: str = DEMO_USER_ID):
    """Summary stats + the current pipeline at a glance for the dashboard home."""
    events = store.list_events(user_id)
    all_connections = [
        c for e in events for c in store.connections_for_event(e.id)
    ]
    hot = [c for c in all_connections if c.predicted_warmth >= 70]
    return {
        "user_id": user_id,
        "events": len(events),
        "connections": len(all_connections),
        "hot_leads": len(hot),
        "leads_in_crm": len(store.list_leads()),
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
    return [l.model_dump() for l in store.list_leads()]


@router.get("/connections")
async def list_connections():
    return [c.model_dump() for c in store.pre_connections.values()]


@router.get("/connections/{connection_id}")
async def get_connection(connection_id: str):
    conn = store.pre_connections.get(connection_id)
    if not conn:
        return {"error": "not_found", "connection_id": connection_id}
    warmth = store.warmth_for_connection(connection_id)
    meet = store.meet_result_for(connection_id)
    return {
        "connection": conn.model_dump(),
        "warmth": warmth.model_dump() if warmth else None,
        "meet_result": meet,
        "gmail_draft": (meet or {}).get("gmail_draft"),
    }


@router.get("/community/members")
async def community_members():
    return store.community_members
