"""Meet stage.

Starts when the phrase trigger ("hey it's nice to meet you") fires on the phone.
Captured conversation signals are turned into a MeetingSignal, run through the
ML pipeline, and routed:

  - warmth went UP vs. pre-meet expectation -> push to Zero CRM + Lightfern outreach
  - otherwise -> route to the founder community (nearest friend/founder)
"""
from typing import Optional

from ...packages.core.models.meeting_signal import MeetingSignal
from ...packages.core.models.warmth import WarmthScore
from ...packages.core.models.lead import Lead
from ...packages.ml.pipeline import MeetIntelligencePipeline, RoutingDecision, RoutingTarget
from ...packages.integrations.zero_crm.client import ZeroCRMClient
from ...packages.integrations.zero_crm.mapper import ZeroCRMMapper
from ...packages.integrations.lightfern.workflow import LightfernClient
from ...packages.integrations.faxxing.client import FaxxingClient
from .community_matcher import CommunityMatcher


class MeetPipeline:
    def __init__(
        self,
        ml_pipeline: Optional[MeetIntelligencePipeline] = None,
        zero_client: Optional[ZeroCRMClient] = None,
        lightfern_client: Optional[LightfernClient] = None,
        faxxing_client: Optional[FaxxingClient] = None,
        community_matcher: Optional[CommunityMatcher] = None,
    ):
        self.ml_pipeline = ml_pipeline or MeetIntelligencePipeline()
        self.zero_client = zero_client
        self.lightfern_client = lightfern_client
        self.faxxing_client = faxxing_client or FaxxingClient()
        self.community_matcher = community_matcher or CommunityMatcher()

    async def process(
        self,
        signal: MeetingSignal,
        prior_warmth: Optional[WarmthScore] = None,
        lead: Optional[Lead] = None,
        community_members: Optional[list[dict]] = None,
    ) -> RoutingDecision:
        """Run the ML pipeline and act on the routing decision."""
        decision = self.ml_pipeline.run(
            signal,
            prior_warmth=prior_warmth,
            community_candidates=community_members or [],
        )

        if decision.target == RoutingTarget.CRM_AND_OUTREACH:
            await self._push_to_crm_and_outreach(lead, signal, decision)
        else:
            # Already matched inside the pipeline; surface via the matcher too.
            decision.matched_candidates = self.community_matcher.find_match(
                signal, community_members or [], top_k=2
            )

        return decision

    async def _push_to_crm_and_outreach(
        self,
        lead: Optional[Lead],
        signal: MeetingSignal,
        decision: RoutingDecision,
    ) -> None:
        person = signal.personal_context

        if lead and self.zero_client:
            try:
                # Push the lead enriched with the evolved per-person context
                # (communication style, values, dominant topic, pains) so the
                # CRM record carries the narrative, not just firmographics.
                payload = ZeroCRMMapper.lead_to_zero_payload_with_context(lead, person)
                await self.zero_client.create_lead(payload)
            except Exception as e:  # pragma: no cover - stub resilience
                print(f"Meet push-to-CRM stub fallback: {e}")

        # Faxxing tailors the outreach sequence to the person's communication
        # style + values captured during the meet.
        if person is not None:
            try:
                decision.outreach_sequence = await self.faxxing_client.personalize_sequence(person)
            except Exception as e:  # pragma: no cover - stub resilience
                print(f"Meet Faxxing stub fallback: {e}")

        if lead and self.lightfern_client:
            try:
                await self.lightfern_client.send_followup_email(
                    lead,
                    context={
                        "personal_context": person,
                        "interests": signal.interests,
                        "most_interesting": signal.most_interesting,
                        "what_you_learned": signal.what_you_learned,
                        "uplift": decision.uplift,
                    },
                )
            except Exception as e:  # pragma: no cover - stub resilience
                print(f"Meet outreach stub fallback: {e}")
