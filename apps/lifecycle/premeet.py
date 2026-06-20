"""Before-meet stage.

Builds the pre-meet attendee dataset for a detected conference, enriches it via
UnifyGTM, predicts warmth, surfaces the highest-intent leads, drafts personalized
outreach (Lightfern + Gmail via MCP), and books meetings on the calendar.

Data-source ownership (per product decision):
- **ICP profile + ICP fit = Zero CRM.** Zero owns the ICP definition and scores a
  company's fit (`ZeroCRMClient.score_icp_fit`). The local `LeadScorer` heuristic
  is only a fallback for when Zero isn't configured/reachable.
- **Enrichment = UnifyGTM.** Firmographics/technographics are populated in
  `enrich()` from UnifyGTM.
- **Warmth = built on top.** `WarmthModel` layers warmth over (Zero ICP fit +
  Unify enrichment + intent/engagement).

Attendee ingestion supports both calendar-derived attendees and conference
directory scraping (per product decision). Manual user input is also accepted.

This module is intentionally a thin orchestrator over stubbed integrations.
"""
from datetime import datetime
from typing import Optional

from ...packages.core.models.event import DetectedEvent
from ...packages.core.models.pre_connection import PreMeetConnection, PreMeetStatus
from ...packages.core.models.icp import ICPConfig
from ...packages.ml.lead_scorer import LeadScorer
from ...packages.ml.warmth_model import WarmthModel
from ...packages.integrations.unify_gtm.client import UnifyGTMClient
from ...packages.integrations.zero_crm.client import ZeroCRMClient
from ...packages.integrations.google_mcp.client import GoogleMCPClient
from ...packages.integrations.lightfern.workflow import LightfernClient


class PreMeetPipeline:
    def __init__(
        self,
        icp_config: Optional[ICPConfig] = None,
        unify_client: Optional[UnifyGTMClient] = None,
        zero_client: Optional[ZeroCRMClient] = None,
        gmail_client: Optional[GoogleMCPClient] = None,
        lightfern_client: Optional[LightfernClient] = None,
        lead_scorer: Optional[LeadScorer] = None,
        warmth_model: Optional[WarmthModel] = None,
    ):
        self.icp_config = icp_config or ICPConfig()
        self.unify_client = unify_client
        # Zero CRM owns ICP fit scoring. Optional (default None) so the offline
        # demo still runs via the local LeadScorer fallback in `score()`.
        self.zero_client = zero_client
        self.gmail_client = gmail_client
        self.lightfern_client = lightfern_client or LightfernClient()
        self.lead_scorer = lead_scorer or LeadScorer(self.icp_config)
        self.warmth_model = warmth_model or WarmthModel()

    # ------------------------------------------------------------------ #
    # 1. Build attendee dataset
    # ------------------------------------------------------------------ #
    async def build_attendee_dataset(
        self,
        event: DetectedEvent,
        manual_attendees: Optional[list[dict]] = None,
    ) -> list[PreMeetConnection]:
        """Assemble pre-meet connections from manual input + directory scrape.

        If ``event.directory_url`` is set the Playwright scraper is used to
        extract attendees from the conference directory page. Manual attendees
        (if provided) are merged in and take priority (deduped by name).
        """
        scraped: list[dict] = []
        if event.directory_url:
            try:
                from ..scraper.sources.playwright_scraper import ConferenceDirectoryScraper
                scraper = ConferenceDirectoryScraper(headless=True)
                scraped = await scraper.scrape(event.directory_url)
            except Exception as exc:
                print(f"PreMeetPipeline scraper fallback: {exc}")

        # Merge: manual attendees override scraped ones (dedup by name)
        seen_names: set[str] = set()
        raw: list[dict] = []
        for att in (manual_attendees or []):
            key = (att.get("name") or "").lower().strip()
            if key:
                seen_names.add(key)
            raw.append(att)
        for att in scraped:
            key = (att.get("name") or "").lower().strip()
            if key and key not in seen_names:
                seen_names.add(key)
                raw.append(att)

        connections: list[PreMeetConnection] = []
        for att in raw:
            connections.append(
                PreMeetConnection(
                    event_id=event.id,
                    user_id=event.user_id,
                    name=att.get("name"),
                    email=att.get("email"),
                    title=att.get("title"),
                    company_name=att.get("company") or att.get("company_name"),
                    company_domain=att.get("company_domain"),
                    interests=att.get("interests", []),
                    source=att.get("source", "manual"),
                )
            )
        return connections

    # ------------------------------------------------------------------ #
    # 2. Enrich via UnifyGTM
    # ------------------------------------------------------------------ #
    async def enrich(self, connection: PreMeetConnection) -> PreMeetConnection:
        if not self.unify_client or not connection.company_name:
            return connection
        try:
            data = await self.unify_client.enrich_company(
                connection.company_name, connection.company_domain
            )
        except Exception as e:  # pragma: no cover - stub resilience
            print(f"PreMeet enrich stub fallback: {e}")
            return connection

        firmo = data.get("firmographics", data)
        connection.company_size = firmo.get("employee_count") or connection.company_size
        connection.industry = firmo.get("industry") or connection.industry
        connection.funding_stage = firmo.get("funding_stage") or connection.funding_stage
        connection.arr_usd = firmo.get("arr_usd") or connection.arr_usd
        connection.technographics = data.get("technographics", connection.technographics)
        connection.status = PreMeetStatus.ENRICHED
        connection.updated_at = datetime.utcnow()
        return connection

    # ------------------------------------------------------------------ #
    # 3. Score (Zero ICP fit + intent -> warmth built on top)
    # ------------------------------------------------------------------ #
    async def score(self, connection: PreMeetConnection) -> PreMeetConnection:
        """Score a connection.

        ICP fit is sourced from Zero CRM (the ICP owner) via
        `ZeroCRMClient.score_icp_fit`, using the firmographics UnifyGTM populated
        during `enrich()`. We fall back to the local `LeadScorer` heuristic only
        when Zero isn't configured/reachable. `WarmthModel` then builds warmth on
        top of (Zero ICP fit + Unify enrichment + intent).
        """
        connection.icp_score = await self._score_icp_fit(connection)
        connection.intent_score = self.lead_scorer.score_intent(connection)
        warmth = self.warmth_model.predict_pre_meet(connection)
        connection.predicted_warmth = warmth.predicted_score or 0.0
        connection.status = PreMeetStatus.SCORED
        connection.updated_at = datetime.utcnow()
        return connection

    async def _score_icp_fit(self, connection: PreMeetConnection) -> float:
        """Resolve ICP fit from Zero CRM, falling back to the local heuristic.

        Zero CRM owns ICP fit; `LeadScorer.score_icp_fit` is only the offline
        fallback for when Zero isn't available.
        """
        if self.zero_client:
            try:
                company_data = {
                    "company_name": connection.company_name,
                    "company_domain": connection.company_domain,
                    "employee_count": connection.company_size,
                    "industry": connection.industry,
                    "funding_stage": connection.funding_stage,
                    "arr_usd": connection.arr_usd,
                    "technographics": connection.technographics,
                }
                result = await self.zero_client.score_icp_fit(company_data)
                return float(result.get("icp_score", 0.0))
            except Exception as e:  # pragma: no cover - stub resilience
                print(f"PreMeet Zero ICP scoring fallback to LeadScorer: {e}")
        # Fallback: local heuristic ICP fit (used when Zero isn't configured).
        return self.lead_scorer.score_icp_fit(connection)

    def rank_highest_intent(
        self,
        connections: list[PreMeetConnection],
        top_n: int = 10,
    ) -> list[PreMeetConnection]:
        """Surface the highest-intent leads for this conference."""
        return sorted(
            connections,
            key=lambda c: (c.predicted_warmth, c.icp_score, c.intent_score),
            reverse=True,
        )[:top_n]

    # ------------------------------------------------------------------ #
    # 4. Draft personalized outreach + create Gmail draft
    # ------------------------------------------------------------------ #
    async def draft_outreach(self, connection: PreMeetConnection) -> PreMeetConnection:
        from ..api.integration_helpers import (
            warmth_client_email,
            warmth_client_name,
            wrap_self_draft,
        )

        personalized = await self.lightfern_client.personalize_outreach(
            recipient={"name": connection.name, "company": connection.company_name, "email": connection.email},
            context={
                "interests": connection.interests,
                "notes": connection.research_notes,
                "client_email": warmth_client_email(),
                "client_name": warmth_client_name(),
                "lead": {
                    "contact_name": connection.name,
                    "company_name": connection.company_name,
                    "contact_email": connection.email,
                    "icp_score": int(connection.icp_score),
                },
                "scores": {
                    "icp_score": connection.icp_score,
                    "warmth_score": connection.predicted_warmth,
                    "predicted_score": connection.predicted_warmth,
                },
            },
            purpose="pre_meet_intro",
        )
        subject, body = wrap_self_draft(
            personalized.get("subject") or "",
            personalized.get("body") or "",
            stage="pre_meet",
            recipient_name=connection.name,
            recipient_email=connection.email,
        )
        connection.draft_subject = subject
        connection.draft_body = body

        if self.gmail_client:
            try:
                draft = await self.gmail_client.create_email_draft(
                    to=warmth_client_email(),
                    subject=subject,
                    body=body,
                )
                connection.gmail_draft_id = draft.get("draft_id") or draft.get("id")
            except Exception as e:  # pragma: no cover - stub resilience
                print(f"PreMeet draft_outreach stub fallback: {e}")

        connection.status = PreMeetStatus.OUTREACH_DRAFTED
        connection.updated_at = datetime.utcnow()
        return connection

    # ------------------------------------------------------------------ #
    # Orchestration
    # ------------------------------------------------------------------ #
    async def run(
        self,
        event: DetectedEvent,
        manual_attendees: Optional[list[dict]] = None,
        top_n: int = 10,
    ) -> list[PreMeetConnection]:
        """Run the full before-meet pipeline and return ranked, drafted leads."""
        connections = await self.build_attendee_dataset(event, manual_attendees)
        for c in connections:
            await self.enrich(c)
            await self.score(c)
        top = self.rank_highest_intent(connections, top_n=top_n)
        for c in top:
            await self.draft_outreach(c)
        event.premeet_completed = True
        return top
