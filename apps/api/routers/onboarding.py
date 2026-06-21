"""Onboarding + event discovery endpoints."""
from fastapi import APIRouter, HTTPException, status

from ....packages.core.errors import client_safe_message
from ...lifecycle.onboarding import OnboardingService
from ..store import get_store
from ..user_context import get_user_id

router = APIRouter(prefix="/api/v1", tags=["onboarding"])


@router.post("/connect")
async def connect():
    """Connect the user's email + Google Calendar via MCP, then discover events."""
    user_id = get_user_id()
    service = OnboardingService()
    result = await service.connect(user_id)
    try:
        detected = await service.discover_events(user_id)
        for ev in detected:
            get_store().upsert_event(ev)
        result["events_detected"] = len(detected)
    except Exception as e:  # pragma: no cover - stub resilience
        result["events_detected"] = 0
        result["discovery_error"] = client_safe_message(
            e, fallback="Event discovery failed. Try again later."
        )
    return result


@router.get("/events")
async def list_events():
    user_id = get_user_id()
    return [e.model_dump() for e in get_store().list_events(user_id)]


@router.get("/events/{event_id}")
async def get_event(event_id: str):
    user_id = get_user_id()
    event = get_store().get_event(event_id)
    if not event or event.user_id != user_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Event not found")
    return event.model_dump()
