"""Deprecated route alias for legacy `/api/v1/conferences/*` clients."""
from fastapi import APIRouter

from . import event_runs

legacy_router = APIRouter(prefix="/api/v1/events", tags=["event-runs-legacy"])

legacy_router.add_api_route(
    "/run",
    event_runs.run_event_pipeline,
    methods=["POST"],
    response_model=event_runs.EventRunResponse,
)
legacy_router.add_api_route(
    "/{run_id}",
    event_runs.get_event_run,
    methods=["GET"],
    response_model=event_runs.EventRunResponse,
)
legacy_router.add_api_route(
    "/",
    event_runs.list_event_runs,
    methods=["GET"],
)

__all__ = ["legacy_router"]
