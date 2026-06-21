"""Event intelligence pipeline endpoints.

POST /api/v1/event-runs/run
    Runs the full autonomous event pipeline:
      scrape directory → Tavily research → ICP score (Zero) →
      rank warmth → draft Gmail outreach → push to Zero CRM → sync to HubSpot

GET  /api/v1/event-runs/{run_id}
    Retrieve results from a previous pipeline run.

The pipeline auto-wires available integrations based on env vars:
  TAVILY_API_KEY, UNIFY_GTM_API_KEY, ZERO_CRM_API_KEY,
  HUBSPOT_API_KEY, GOOGLE_MCP_CREDENTIALS.

When the Cursor SDK / MCP caller is present in the request context, the Zero
MCP bridge is preferred over the REST fallback.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any, Optional

from fastapi import APIRouter, BackgroundTasks
from pydantic import AliasChoices, BaseModel, Field

from ....packages.core.errors import client_safe_message
from ....packages.core.url_safety import UnsafeUrlError, validate_scrape_url
from ...agent.event_pipeline import EventPipeline

router = APIRouter(prefix="/api/v1/event-runs", tags=["event-runs"])

# In-memory run cache (replace with Firestore in prod)
_run_cache: dict[str, dict[str, Any]] = {}


# ---------------------------------------------------------------------------
# Request / response models
# ---------------------------------------------------------------------------

class AttendeeInput(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    title: Optional[str] = None
    company: Optional[str] = None
    company_domain: Optional[str] = None
    linkedin: Optional[str] = None
    interests: list[str] = []
    source: str = "manual"


class EventRunRequest(BaseModel):
    """Body for POST /api/v1/event-runs/run."""
    event_name: str
    directory_url: Optional[str] = None
    manual_attendees: list[AttendeeInput] = []
    top_n: int = 20
    book_meetings: bool = False
    meeting_start_iso: Optional[str] = None   # ISO datetime for first meeting slot
    meeting_duration_minutes: int = 30
    # Feature flags
    skip_scraping: bool = False               # use manual_attendees only
    skip_research: bool = False               # skip Tavily enrichment
    skip_email_drafts: bool = False           # skip Gmail drafting
    skip_zero_sync: bool = False              # skip Zero CRM push
    skip_hubspot_sync: bool = False           # skip HubSpot sync


class EventRunResponse(BaseModel):
    run_id: str
    status: str                               # "running" | "complete" | "error"
    event: str = Field(validation_alias=AliasChoices("event", "event"))
    started_at: str
    completed_at: Optional[str] = None
    summary: Optional[dict[str, Any]] = None
    error: Optional[str] = None

    model_config = {"populate_by_name": True}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _build_pipeline(req: EventRunRequest) -> EventPipeline:
    """Instantiate a EventPipeline wiring only available integrations."""
    from ....packages.integrations.google_calendar.client import GoogleCalendarClient
    from ....packages.integrations.google_mcp.client import GoogleMCPClient
    from ....packages.integrations.hubspot.client import HubSpotClient
    from ....packages.integrations.lightfern.workflow import LightfernClient
    from ....packages.integrations.tavily.client import TavilyClient
    from ....packages.integrations.unify_gtm.client import UnifyGTMClient
    from ....packages.integrations.zero_crm.client import ZeroCRMClient

    tavily = None
    if not req.skip_research:
        try:
            tavily = TavilyClient()
        except Exception as e:
            print(f"[event-runs] Tavily not available: {e}")

    unify = None
    try:
        unify = UnifyGTMClient()
    except Exception as e:
        print(f"[event-runs] Unify not available: {e}")

    gmail = None
    if not req.skip_email_drafts:
        try:
            gmail = GoogleMCPClient()
        except Exception as e:
            print(f"[event-runs] Google MCP not available: {e}")

    calendar = None
    if req.book_meetings:
        try:
            calendar = GoogleCalendarClient()
        except Exception as e:
            print(f"[event-runs] Google Calendar not available: {e}")

    hubspot = None
    if not req.skip_hubspot_sync:
        try:
            hubspot = HubSpotClient()
        except Exception as e:
            print(f"[event-runs] HubSpot not available: {e}")

    lightfern = LightfernClient()

    zero_rest = None
    if not req.skip_zero_sync:
        try:
            zero_rest = ZeroCRMClient()
        except Exception as e:
            print(f"[event-runs] Zero CRM not available: {e}")

    return EventPipeline(
        mcp_caller=None,       # NOTE: inject via agent context when using Cursor SDK
        unify_client=unify,
        zero_rest=zero_rest,
        gmail_client=gmail,
        calendar_client=calendar,
        hubspot_client=hubspot,
        tavily_client=tavily,
        lightfern_client=lightfern,
        headless=True,
    )


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@router.post("/run", response_model=EventRunResponse)
async def run_event_pipeline(
    req: EventRunRequest,
    background_tasks: BackgroundTasks,
):
    """Kick off the autonomous event intelligence pipeline.

    The pipeline runs asynchronously. Check ``GET /conferences/{run_id}`` for
    results.  For small attendee lists (< 30 people) the response is returned
    inline; larger lists run in the background.
    """
    run_id = str(uuid.uuid4())
    started_at = datetime.utcnow().isoformat()

    # Store initial state
    _run_cache[run_id] = {
        "run_id": run_id,
        "status": "running",
        "event": req.event_name,
        "started_at": started_at,
        "completed_at": None,
        "summary": None,
        "error": None,
    }

    attendees_raw = [a.model_dump() for a in req.manual_attendees]
    directory_url: Optional[str] = None
    if not req.skip_scraping and req.directory_url:
        try:
            directory_url = validate_scrape_url(req.directory_url)
        except UnsafeUrlError as exc:
            _run_cache[run_id].update({
                "status": "error",
                "completed_at": datetime.utcnow().isoformat(),
                "error": str(exc),
            })
            return EventRunResponse(**_run_cache[run_id])

    meeting_start = None
    if req.meeting_start_iso:
        try:
            meeting_start = datetime.fromisoformat(req.meeting_start_iso)
        except ValueError:
            pass

    async def _execute() -> None:
        try:
            pipeline = _build_pipeline(req)
            summary = await pipeline.run(
                event_name=req.event_name,
                directory_url=directory_url,
                manual_attendees=attendees_raw or None,
                top_n=req.top_n,
                book_meetings=req.book_meetings,
                meeting_start_time=meeting_start,
                meeting_duration_minutes=req.meeting_duration_minutes,
            )
            _run_cache[run_id].update({
                "status": "complete",
                "completed_at": datetime.utcnow().isoformat(),
                "summary": summary,
            })
        except Exception as exc:
            _run_cache[run_id].update({
                "status": "error",
                "completed_at": datetime.utcnow().isoformat(),
                "error": client_safe_message(
                    exc, fallback="Event pipeline failed. Please try again later."
                ),
            })

    # Small lists: run inline and return immediately
    if len(attendees_raw) <= 30 and req.skip_scraping:
        await _execute()
    else:
        background_tasks.add_task(_execute)

    return EventRunResponse(**_run_cache[run_id])


@router.get("/{run_id}", response_model=EventRunResponse)
async def get_event_run(run_id: str):
    """Retrieve the status and results of a event pipeline run."""
    run = _run_cache.get(run_id)
    if not run:
        return EventRunResponse(
            run_id=run_id,
            status="not_found",
            event="",
            started_at="",
            error=f"No run found with id {run_id}",
        )
    return EventRunResponse(**run)


@router.get("/")
async def list_event_runs():
    """List all event pipeline runs (most recent first)."""
    runs = sorted(
        _run_cache.values(),
        key=lambda r: r.get("started_at", ""),
        reverse=True,
    )
    return [EventRunResponse(**r) for r in runs]
