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
from .community_matcher import CommunityMatcher


class MeetPipeline:
    def __init__(
        self,
        ml_pipeline: Optional[MeetIntelligencePipeline] = None,
        zero_client: Optional[ZeroCRMClient] = None,
        lightfern_client: Optional[LightfernClient] = None,
        community_matcher: Optional[CommunityMatcher] = None,
    ):
        self.ml_pipeline = ml_pipeline or MeetIntelligencePipeline()
        self.zero_client = zero_client
        self.lightfern_client = lightfern_client or LightfernClient()
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
        if lead and self.zero_client:
            try:
                payload = ZeroCRMMapper.lead_to_zero_payload(lead)
                await self.zero_client.create_lead(payload)
            except Exception as e:  # pragma: no cover - stub resilience
                print(f"Meet push-to-CRM stub fallback: {e}")

        if lead:
            try:
                await self.lightfern_client.send_followup_email(
                    lead,
                    context={
                        "interests": signal.interests,
                        "most_interesting": signal.most_interesting,
                        "what_you_learned": signal.what_you_learned,
                        "uplift": decision.uplift,
                    },
                )
            except Exception as e:  # pragma: no cover - stub resilience
                print(f"Meet outreach stub fallback: {e}")
