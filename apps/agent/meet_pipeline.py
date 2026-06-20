"""Meet Stage Agent — autonomous orchestrator for the *meet* flow.

Primary output: a Gmail draft carrying scoring, lead data, and person context
so Lightfern can populate/polish inside Gmail. The human completes and sends;
that closes the loop.
"""
from __future__ import annotations

import asyncio
from typing import Any, Optional

from ...packages.core.models.lead import Lead
from ...packages.core.models.warmth import WarmthScore
from ...packages.integrations.zero_crm.client import ZeroCRMClient
from ...packages.integrations.zero_crm.mapper import ZeroCRMMapper
from ...packages.integrations.faxxing.client import FaxxingClient
from ...packages.integrations.lightfern.workflow import LightfernClient
from ...packages.integrations.google_mcp.client import GoogleMCPClient
from ...packages.integrations.hubspot.client import HubSpotClient
from ...packages.ml.pipeline import RoutingTarget
from ..lifecycle.meet import MeetPipeline
from ..listener.intelligence.meet_encoder import MeetEncoder
from ..api.integration_helpers import (
    gmail_client_optional,
    hubspot_client_optional,
    warmth_client_email,
    warmth_client_name,
    wrap_self_draft,
)


class MeetStageAgent:
    def __init__(
        self,
        use_agent: bool = False,
        encoder: Optional[MeetEncoder] = None,
        meet_pipeline: Optional[MeetPipeline] = None,
        zero_client: Optional[ZeroCRMClient] = None,
        faxxing_client: Optional[FaxxingClient] = None,
        lightfern_client: Optional[LightfernClient] = None,
        gmail_client: Optional[GoogleMCPClient] = None,
        hubspot_client: Optional[HubSpotClient] = None,
    ):
        self.encoder = encoder or MeetEncoder(use_agent=use_agent)
        self.faxxing_client = faxxing_client or FaxxingClient()
        self.lightfern_client = lightfern_client or LightfernClient()
        self.gmail_client = gmail_client or gmail_client_optional()
        self.hubspot_client = hubspot_client or hubspot_client_optional()
        self.meet_pipeline = meet_pipeline or MeetPipeline(
            zero_client=zero_client,
            faxxing_client=self.faxxing_client,
            lightfern_client=None,  # Gmail handoff handled here (single path)
        )

    async def run(
        self,
        turns: list[dict[str, Any]],
        speaker_attrs: Optional[dict[int, dict]] = None,
        self_speaker_id: int = 0,
        lead: Optional[Lead] = None,
        prior_warmth: Optional[WarmthScore] = None,
        connection_id: Optional[str] = None,
        community_members: Optional[list[dict]] = None,
    ) -> dict[str, Any]:
        signal, kg = await asyncio.to_thread(
            self.encoder.encode,
            turns,
            self_speaker_id,
            speaker_attrs or {},
            None,
            connection_id,
        )
        person = signal.personal_context

        if lead is None:
            lead = Lead(
                company_name=signal.company or "Unknown Company",
                contact_name=signal.name,
                signal_source="event_audio",
            )

        decision = await self.meet_pipeline.process(
            signal,
            prior_warmth=prior_warmth,
            lead=lead,
            community_members=community_members or [],
        )

        warmth = decision.warmth
        scores = {
            "icp_score": warmth.icp_score if warmth else lead.icp_score,
            "warmth_score": warmth.warmth_score if warmth else None,
            "predicted_score": warmth.predicted_score if warmth else None,
            "actual_score": warmth.actual_score if warmth else None,
            "band": warmth.band.value if warmth else None,
            "uplift": decision.uplift,
            "routing": decision.target.value,
            "reason": decision.reason,
        }

        # Primary handoff: Gmail draft with scoring + lead + person for Lightfern.
        gmail_context = {
            "personal_context": person,
            "scores": scores,
            "lead": lead.model_dump(),
            "interests": signal.interests,
            "what_you_learned": signal.what_you_learned,
            "most_interesting": signal.most_interesting,
            "decision": decision.model_dump(),
            "client_email": warmth_client_email(),
            "client_name": warmth_client_name(),
        }
        gmail_draft = await self.lightfern_client.send_followup_email(lead, context=gmail_context)

        if self.gmail_client:
            try:
                subject, body = wrap_self_draft(
                    gmail_draft.get("subject", ""),
                    gmail_draft.get("body", ""),
                    stage="post_meet",
                    recipient_name=lead.contact_name or signal.name,
                    recipient_email=lead.contact_email,
                )
                created = await self.gmail_client.create_email_draft(
                    to=warmth_client_email(),
                    subject=subject,
                    body=body,
                )
                gmail_draft["subject"] = subject
                gmail_draft["body"] = body
                gmail_draft["to"] = warmth_client_email()
                gmail_draft["gmail_draft_id"] = created.get("id")
            except Exception as e:
                print(f"Gmail MCP draft fallback: {e}")

        zero_payload = ZeroCRMMapper.lead_to_zero_payload_with_context(lead, person)

        # HubSpot is the source of record: write the same merged payload here and
        # let the native Zero/Unify integrations propagate it (avoids dup writes).
        hubspot_contact_id = None
        if self.hubspot_client and decision.target == RoutingTarget.CRM_AND_OUTREACH:
            try:
                hubspot_contact_id = await self.hubspot_client.upsert_from_zero_payload(
                    zero_payload
                )
            except Exception as e:
                print(f"HubSpot upsert failed: {e}")

        outreach_sequence = None
        if decision.target == RoutingTarget.CRM_AND_OUTREACH and person is not None:
            outreach_sequence = await self.faxxing_client.personalize_sequence(person)
            decision.outreach_sequence = outreach_sequence

        return {
            "routed_to": decision.target.value,
            "narrative": person.to_narrative() if person else None,
            "signal": signal.model_dump(),
            "people": [p.model_dump() for p in kg.people()],
            "decision": decision.model_dump(),
            "scores": scores,
            "zero_crm_payload": zero_payload.model_dump(),
            "hubspot_contact_id": hubspot_contact_id,
            "gmail_draft": gmail_draft,
            "outreach_sequence": outreach_sequence,
            "pushed_to_crm": decision.target == RoutingTarget.CRM_AND_OUTREACH,
            "handoff": "gmail_lightfern",
        }
