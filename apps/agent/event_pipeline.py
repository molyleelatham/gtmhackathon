"""Event Intelligence Pipeline — full autonomous agent.

This is the top-level orchestrator for the *before-meet* event flow.
Given an event URL (or a pre-populated attendee list), it:

  1. **Scrape** — Uses Playwright to extract attendees from the event
     directory page.
  2. **Research** — For each attendee/company, run a Tavily search to surface
     buying signals, recent funding news, tech stack, and talking points.
  3. **Score ICP** — Calls Zero CRM (via MCP bridge) to score each company's
     ICP fit.  Falls back to the local ``LeadScorer`` heuristic.
  4. **Rank warmth** — The ``WarmthModel`` produces a predicted warmth score
     layered over (ICP fit + intent signals from Tavily).
  5. **Draft outreach** — Generates a personalised email draft via the Google
     MCP Gmail service and stores the draft ID.
  6. **Book calendar** — For the top N leads, optionally creates a calendar
     event invite via Google Calendar MCP.
  7. **Push to Zero CRM** — Upserts contacts + companies into Zero via the
     ``ZeroMCPBridge``, attaches a note with scores, adds them to the
     "{conference} — Hot Leads" list.
  8. **Sync to HubSpot** — Mirrors hot leads to HubSpot contacts and a
     matching static list for SDR follow-up.

Usage (standalone / CLI demo)::

    import asyncio
    from warmth.apps.agent.event_pipeline import EventPipeline

    pipeline = EventPipeline()
    results = asyncio.run(pipeline.run(
        event_name="SaaStr Annual 2026",
        directory_url="https://www.saastrannual2026.com/speakers",
        top_n=20,
    ))
    print(results["summary"])

Usage (inside Cursor SDK agent loop with live MCP tools)::

    from warmth.apps.agent.event_pipeline import EventPipeline

    # mcp_caller must be async (tool_name, args) -> dict
    pipeline = EventPipeline(mcp_caller=agent.call_mcp_tool)
    results = await pipeline.run(
        event_name="SaaStr Annual 2026",
        directory_url="https://www.saastrannual2026.com/speakers",
        top_n=20,
    )
"""

from __future__ import annotations

import asyncio
from datetime import datetime, timedelta
from typing import Any, Awaitable, Callable, Optional

from ...packages.core.models.event import DetectedEvent, EventType, LifecycleStage
from ...packages.core.models.icp import ICPConfig
from ...packages.integrations.google_calendar.client import GoogleCalendarClient
from ...packages.integrations.google_mcp.client import GoogleMCPClient
from ...packages.integrations.hubspot.client import HubSpotClient
from ...packages.integrations.lightfern.workflow import LightfernClient
from ...packages.integrations.tavily.client import TavilyClient
from ...packages.integrations.unify_gtm.client import UnifyGTMClient
from ...packages.integrations.zero_crm.client import ZeroCRMClient
from ...packages.integrations.zero_crm.mcp_bridge import ZeroMCPBridge
from ...packages.ml.lead_scorer import LeadScorer
from ...packages.ml.warmth_model import WarmthModel
from ..lifecycle.premeet import PreMeetPipeline
from ..scraper.sources.playwright_scraper import EventDirectoryScraper

MCPCaller = Callable[[str, dict], Awaitable[dict]]


# ---------------------------------------------------------------------------
# Tavily research helper
# ---------------------------------------------------------------------------

class _TavilyResearcher:
    """Enrich attendee records with Tavily signal extraction."""

    def __init__(self, tavily: TavilyClient):
        self._tavily = tavily

    async def research_person(
        self,
        name: str,
        company: Optional[str],
        title: Optional[str],
    ) -> dict[str, Any]:
        """Return a research summary dict for one attendee."""
        queries = []
        if company:
            queries.append(f'"{company}" funding OR product launch OR hiring 2025 2026')
        if name and company:
            queries.append(f'"{name}" "{company}" site:linkedin.com OR site:twitter.com')

        snippets: list[str] = []
        interests: list[str] = []
        funding_stage: Optional[str] = None
        tech_stack: list[str] = []

        for q in queries:
            try:
                result = await self._tavily.search(q, search_depth="basic", max_results=5)
                for r in result.get("results", []):
                    content = f"{r.get('title', '')} {r.get('content', '')}"
                    snippets.append(content[:300])
                    # Simple signal extraction from snippet text
                    cl = content.lower()
                    if any(w in cl for w in ["series a", "seed round", "raised"]):
                        if not funding_stage:
                            funding_stage = "Series A" if "series a" in cl else "Seed"
                    for tech in ["aws", "snowflake", "salesforce", "hubspot", "segment", "stripe",
                                 "databricks", "dbt", "fivetran", "hightouch", "amplitude"]:
                        if tech in cl and tech.title() not in tech_stack:
                            tech_stack.append(tech.title())
                    for kw in ["revops", "pipeline", "attribution", "revenue operations",
                               "go-to-market", "gtm", "sales operations"]:
                        if kw in cl and kw not in interests:
                            interests.append(kw)
            except Exception as exc:
                print(f"Tavily research error for {name}: {exc}")

        return {
            "research_notes": " | ".join(snippets[:3]),
            "interests": interests[:5],
            "funding_stage": funding_stage,
            "technographics": tech_stack[:6],
        }


# ---------------------------------------------------------------------------
# Main pipeline
# ---------------------------------------------------------------------------

class EventPipeline:
    """Autonomous event intelligence agent.

    Args:
        mcp_caller:      Optional async MCP tool caller — needed to use the live
                         Zero CRM MCP bridge.  If None the REST-based ZeroCRMClient
                         is used instead (requires ZERO_CRM_API_KEY env var).
        icp_config:      ICP scoring configuration (defaults to ICPConfig()).
        unify_client:    UnifyGTM enrichment client (optional; skipped if None).
        zero_rest:       Zero CRM REST client (optional; used when mcp_caller is None).
        gmail_client:    Google MCP Gmail client (optional; skips email drafting if None).
        calendar_client: Google Calendar MCP client (optional; skips booking if None).
        hubspot_client:  HubSpot client (optional; skips HubSpot sync if None).
        tavily_client:   Tavily search client (optional; skips research if None).
        headless:        Run Playwright browser headlessly (default True).
    """

    def __init__(
        self,
        mcp_caller: Optional[MCPCaller] = None,
        icp_config: Optional[ICPConfig] = None,
        unify_client: Optional[UnifyGTMClient] = None,
        zero_rest: Optional[ZeroCRMClient] = None,
        gmail_client: Optional[GoogleMCPClient] = None,
        calendar_client: Optional[GoogleCalendarClient] = None,
        hubspot_client: Optional[HubSpotClient] = None,
        tavily_client: Optional[TavilyClient] = None,
        lightfern_client: Optional[LightfernClient] = None,
        headless: bool = True,
    ):
        self.icp_config = icp_config or ICPConfig()
        self.lead_scorer = LeadScorer(self.icp_config)
        self.warmth_model = WarmthModel()

        # MCP bridge takes priority over REST client for Zero
        self.zero_bridge: Optional[ZeroMCPBridge] = (
            ZeroMCPBridge(mcp_caller) if mcp_caller else None
        )
        self.zero_rest = zero_rest
        self.unify_client = unify_client
        self.gmail_client = gmail_client
        self.calendar_client = calendar_client
        self.hubspot_client = hubspot_client
        self.tavily_researcher = (
            _TavilyResearcher(tavily_client) if tavily_client else None
        )
        self.lightfern_client = lightfern_client or LightfernClient()
        self.headless = headless

    # ------------------------------------------------------------------
    # Public entry point
    # ------------------------------------------------------------------

    async def run(
        self,
        event_name: str,
        directory_url: Optional[str] = None,
        manual_attendees: Optional[list[dict[str, Any]]] = None,
        top_n: int = 20,
        book_meetings: bool = False,
        meeting_start_time: Optional[datetime] = None,
        meeting_duration_minutes: int = 30,
    ) -> dict[str, Any]:
        """Run the full event pipeline end-to-end.

        Args:
            event_name:          Human-readable name of the event.
            directory_url:            URL of the attendee/speaker directory page
                                      to scrape.  Provide either this or
                                      ``manual_attendees``.
            manual_attendees:         Pre-populated list of attendee dicts
                                      (overrides scraping when provided).
            top_n:                    Number of top leads to process for outreach
                                      and CRM sync.
            book_meetings:            If True, create calendar invites for top
                                      leads (requires ``calendar_client``).
            meeting_start_time:       When to schedule the first meeting
                                      (defaults to event start + 1 day).
            meeting_duration_minutes: Duration of each meeting slot in minutes.

        Returns:
            Summary dict with ranked leads, Zero/HubSpot sync results, and
            email draft IDs.
        """
        print(f"\n{'='*60}")
        print(f"  CONFERENCE PIPELINE: {event_name}")
        print(f"{'='*60}\n")

        # Build a synthetic DetectedEvent for the lifecycle pipeline
        now = datetime.utcnow()
        event = DetectedEvent(
            id=f"conf_{int(now.timestamp())}",
            user_id="demo-user",
            name=event_name,
            event_type=EventType.EVENT,
            directory_url=directory_url,
            start_date=now + timedelta(days=3),
            end_date=now + timedelta(days=5),
            confidence=1.0,
            stage=LifecycleStage.BEFORE_MEET,
        )

        # ---------------------------------------------------------------
        # Step 1: Scrape directory
        # ---------------------------------------------------------------
        raw_attendees = await self._scrape(directory_url, manual_attendees)
        print(f"[1/7] Scraped {len(raw_attendees)} attendees")

        # ---------------------------------------------------------------
        # Step 2: Tavily research
        # ---------------------------------------------------------------
        if self.tavily_researcher:
            raw_attendees = await self._research(raw_attendees)
            print("[2/7] Tavily research complete")
        else:
            print("[2/7] Tavily not configured — skipping research")

        # ---------------------------------------------------------------
        # Step 3-5: Enrich → Score ICP → Rank warmth (PreMeetPipeline)
        # ---------------------------------------------------------------
        premeet = PreMeetPipeline(
            icp_config=self.icp_config,
            unify_client=self.unify_client,
            zero_client=self.zero_rest,
            gmail_client=self.gmail_client,
            lightfern_client=self.lightfern_client,
            lead_scorer=self.lead_scorer,
            warmth_model=self.warmth_model,
        )
        top_leads = await premeet.run(
            event, manual_attendees=raw_attendees, top_n=top_n
        )
        leads_dicts = [c.model_dump() for c in top_leads]
        print(f"[3-5/7] Pre-meet pipeline: {len(top_leads)} ranked leads")

        # ---------------------------------------------------------------
        # Step 6: Book calendar meetings (optional)
        # ---------------------------------------------------------------
        meeting_results: list[dict] = []
        if book_meetings and self.calendar_client:
            start = meeting_start_time or (event.start_date or now + timedelta(days=3))
            meeting_results = await self._book_meetings(
                top_leads, start, meeting_duration_minutes
            )
            print(f"[6/7] Booked {len(meeting_results)} calendar meetings")
        else:
            print("[6/7] Meeting booking skipped")

        # ---------------------------------------------------------------
        # Step 7a: Push to Zero CRM via MCP bridge
        # ---------------------------------------------------------------
        zero_result: dict[str, Any] = {}
        if self.zero_bridge:
            zero_contact_ids = await self.zero_bridge.push_hot_leads(
                leads_dicts, event_name=event_name
            )
            zero_result = {
                "contact_ids": zero_contact_ids,
                "count": len(zero_contact_ids),
            }
            print(f"[7a/7] Zero CRM: {len(zero_contact_ids)} contacts upserted")
        else:
            print("[7a/7] Zero MCP bridge not configured — skipping Zero sync")

        # ---------------------------------------------------------------
        # Step 7b: Sync to HubSpot
        # ---------------------------------------------------------------
        hubspot_result: dict[str, Any] = {}
        if self.hubspot_client:
            hubspot_result = await self.hubspot_client.sync_hot_leads(
                leads_dicts, event_name=event_name
            )
            print(
                f"[7b/7] HubSpot: {hubspot_result.get('created', 0)} created, "
                f"{hubspot_result.get('updated', 0)} updated → list '{hubspot_result.get('list_name')}'"
            )
        else:
            print("[7b/7] HubSpot not configured — skipping HubSpot sync")

        # ---------------------------------------------------------------
        # Summary
        # ---------------------------------------------------------------
        summary = {
            "event": event_name,
            "attendees_scraped": len(raw_attendees),
            "top_leads": len(top_leads),
            "leads": leads_dicts,
            "email_drafts": [
                {"name": c.name, "draft_id": c.gmail_draft_id}
                for c in top_leads
                if c.gmail_draft_id
            ],
            "meetings_booked": meeting_results,
            "zero_crm": zero_result,
            "hubspot": hubspot_result,
        }
        print(f"\n{'='*60}")
        print(f"  DONE — {len(top_leads)} hot leads processed")
        print(f"{'='*60}\n")
        return summary

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    async def _scrape(
        self,
        directory_url: Optional[str],
        manual_attendees: Optional[list[dict]],
    ) -> list[dict[str, Any]]:
        if manual_attendees:
            return manual_attendees
        if not directory_url:
            return []
        try:
            scraper = EventDirectoryScraper(headless=self.headless)
            return await scraper.scrape(directory_url)
        except Exception as exc:
            print(f"Scraper error: {exc}")
            return []

    async def _research(
        self, attendees: list[dict[str, Any]]
    ) -> list[dict[str, Any]]:
        """Run Tavily research in parallel (max concurrency = 5)."""
        sem = asyncio.Semaphore(5)

        async def _research_one(att: dict) -> dict:
            async with sem:
                intel = await self.tavily_researcher.research_person(
                    name=att.get("name"),
                    company=att.get("company"),
                    title=att.get("title"),
                )
                return {
                    **att,
                    "interests": att.get("interests", []) + intel.get("interests", []),
                    "funding_stage": intel.get("funding_stage") or att.get("funding_stage"),
                    "technographics": intel.get("technographics", []),
                    "research_notes": intel.get("research_notes"),
                }

        return await asyncio.gather(*[_research_one(a) for a in attendees])

    async def _book_meetings(
        self,
        leads: list,
        base_start: datetime,
        duration_minutes: int,
    ) -> list[dict[str, Any]]:
        """Create calendar invites for each lead with an email address."""
        results = []
        slot = base_start
        for lead in leads:
            if not lead.email:
                continue
            end = slot + timedelta(minutes=duration_minutes)
            try:
                result = await self.calendar_client.create_event(
                    title=f"Warmth intro: {lead.name or lead.company_name}",
                    start_time=slot,
                    end_time=end,
                    attendees_emails=[lead.email],
                    description=(
                        f"Pre-event intro meeting arranged by Warmth.\n\n"
                        f"ICP Score: {lead.icp_score:.0f}/100\n"
                        f"Warmth Score: {lead.predicted_warmth:.0f}/100"
                    ),
                )
                results.append({"name": lead.name, "result": result})
                lead.status = "meeting_set"
            except Exception as exc:
                print(f"Calendar booking error for {lead.name}: {exc}")
            # Stagger slots
            slot = end + timedelta(minutes=15)
        return results


# ---------------------------------------------------------------------------
# CLI runner
# ---------------------------------------------------------------------------

async def _demo() -> None:
    """Run the pipeline with the first 10 rows of the event CSV mock data."""
    import sys

    from ..scraper.sources.csv_loader import load_csv_attendees

    csv_path = (
        sys.argv[1]
        if len(sys.argv) > 1
        else "/Users/molyleelatham/Downloads/data.csv"
    )

    # Load first 10 attendees from the CSV
    attendees = load_csv_attendees(csv_path, max_rows=10)
    print(f"Loaded {len(attendees)} attendees from {csv_path}")

    # Try to initialise real clients where env vars are present
    tavily = None
    try:
        tavily = TavilyClient()
        print("Tavily: connected")
    except Exception:
        print("Tavily: not configured (skipping research)")

    unify = None
    try:
        unify = UnifyGTMClient()
        print("Unify: connected")
    except Exception:
        print("Unify: not configured (skipping enrichment)")

    hubspot = None
    try:
        hubspot = HubSpotClient()
        print("HubSpot: connected")
    except Exception:
        print("HubSpot: not configured (skipping sync)")

    pipeline = EventPipeline(
        tavily_client=tavily,
        unify_client=unify,
        hubspot_client=hubspot,
        headless=True,
    )

    results = await pipeline.run(
        event_name="Tech Event 2026",
        manual_attendees=attendees,
        top_n=5,
        book_meetings=False,
    )

    print("\n--- TOP LEADS ---")
    for i, lead in enumerate(results["leads"], 1):
        print(
            f"  #{i} {lead.get('name')} | {lead.get('company_name')} | "
            f"ICP: {lead.get('icp_score', 0):.0f} | "
            f"Warmth: {lead.get('predicted_warmth', 0):.0f} | "
            f"Status: {lead.get('status')}"
        )

    if results.get("zero_crm"):
        print(f"\nZero CRM: {results['zero_crm'].get('count', 0)} contacts upserted")
    if results.get("hubspot"):
        hs = results["hubspot"]
        print(
            f"HubSpot: {hs.get('created', 0)} created, {hs.get('updated', 0)} updated"
            f" → list '{hs.get('list_name')}'"
        )
    if results.get("email_drafts"):
        print(f"Email drafts: {len(results['email_drafts'])} created")


if __name__ == "__main__":
    asyncio.run(_demo())
