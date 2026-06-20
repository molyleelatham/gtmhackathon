from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field

from ..core.models.meeting_signal import MeetingSignal
from ..core.models.warmth import WarmthScore
from .warmth_model import WarmthModel
from .clustering import LeadClusterer
from .lead_scorer import LeadScorer


class RoutingTarget(str, Enum):
    """Where a connection goes after the meet stage."""
    CRM_AND_OUTREACH = "crm_and_outreach"   # warmth went up -> push to Zero + Lightfern
    FOUNDER_COMMUNITY = "founder_community"  # warmth flat/down -> match to a friend/founder


class RoutingDecision(BaseModel):
    target: RoutingTarget
    reason: str
    uplift: Optional[float] = None
    cluster_id: Optional[int] = None
    warmth: Optional[WarmthScore] = None
    matched_candidates: list[dict] = Field(default_factory=list)
    outreach_sequence: Optional[dict] = None  # Faxxing-personalised sequence


class MeetIntelligencePipeline:
    """End-to-end ML pipeline for the MEET stage.

    Given a captured MeetingSignal (and the optional pre-meet warmth prediction):
      1. cluster the connection
      2. compute lead + warmth scores
      3. decide routing based on warmth uplift vs. the pre-meet expectation

    STUB orchestration — the individual models are placeholders.
    """

    def __init__(
        self,
        warmth_model: Optional[WarmthModel] = None,
        clusterer: Optional[LeadClusterer] = None,
        lead_scorer: Optional[LeadScorer] = None,
        uplift_threshold: float = 0.0,
    ):
        self.warmth_model = warmth_model or WarmthModel()
        self.clusterer = clusterer or LeadClusterer()
        self.lead_scorer = lead_scorer or LeadScorer()
        self.uplift_threshold = uplift_threshold

    def run(
        self,
        signal: MeetingSignal,
        prior_warmth: Optional[WarmthScore] = None,
        community_candidates: Optional[list[dict]] = None,
    ) -> RoutingDecision:
        cluster_id = self.clusterer.assign_cluster(signal)
        warmth = self.warmth_model.score_post_meet(signal, prior=prior_warmth)

        uplift = warmth.uplift
        # If we have no pre-meet baseline, treat a hot post-meet score as uplift.
        if uplift is None:
            improved = (warmth.actual_score or 0.0) >= 70.0
        else:
            improved = uplift > self.uplift_threshold

        if improved:
            return RoutingDecision(
                target=RoutingTarget.CRM_AND_OUTREACH,
                reason="Post-meet warmth exceeded pre-meet expectation."
                if uplift is not None
                else "Strong post-meet warmth with no prior baseline.",
                uplift=uplift,
                cluster_id=cluster_id,
                warmth=warmth,
            )

        matches = self.clusterer.nearest(signal, community_candidates or [], top_k=2)
        return RoutingDecision(
            target=RoutingTarget.FOUNDER_COMMUNITY,
            reason="Warmth did not increase; routing to the nearest founder/friend.",
            uplift=uplift,
            cluster_id=cluster_id,
            warmth=warmth,
            matched_candidates=matches,
        )
