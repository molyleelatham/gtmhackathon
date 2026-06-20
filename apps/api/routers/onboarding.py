"""Onboarding + event discovery endpoints."""
from fastapi import APIRouter
from pydantic import BaseModel

from ..store import store, DEMO_USER_ID
from ...lifecycle.onboarding import OnboardingService

router = APIRouter(prefix="/api/v1", tags=["onboarding"])


class ConnectRequest(BaseModel):
    user_id: str = DEMO_USER_ID


@router.post("/connect")
async def connect(req: ConnectRequest):
    """Connect the user's email + Google Calendar via MCP, then discover events."""
    service = OnboardingService()
    result = await service.connect(req.user_id)
    try:
        detected = await service.discover_events(req.user_id)
        for ev in detected:
            store.upsert_event(ev)
        result["events_detected"] = len(detected)
    except Exception as e:  # pragma: no cover - stub resilience
        result["events_detected"] = 0
        result["discovery_error"] = str(e)
    return result


@router.get("/events")
async def list_events(user_id: str = DEMO_USER_ID):
    return [e.model_dump() for e in store.list_events(user_id)]


@router.get("/events/{event_id}")
async def get_event(event_id: str):
    event = store.get_event(event_id)
    if not event:
        return {"error": "not_found", "event_id": event_id}
    return event.model_dump()
