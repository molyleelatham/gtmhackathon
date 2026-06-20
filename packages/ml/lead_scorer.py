from typing import Optional
from ..core.models.meeting_signal import MeetingSignal
from ..core.models.pre_connection import PreMeetConnection
from ..core.models.icp import ICPConfig


class LeadScorer:
    """Lead scoring stub used both pre-meet (intent estimation) and post-meet.

    Data-source ownership: **ICP profile + ICP fit are owned by Zero CRM**
    (`ZeroCRMClient.score_icp_fit`), enrichment by UnifyGTM, and warmth is built
    on top by `WarmthModel`. The `score_icp_fit` method here is only a *fallback*
    for when Zero isn't configured/reachable. Intent scoring remains Warmth's own.

    STUB: replace heuristics with a trained classifier/regressor. Kept separate
    from WarmthModel so ICP scoring and warmth scoring can evolve independently
    and then be correlated downstream.
    """

    def __init__(self, icp_config: Optional[ICPConfig] = None):
        self.icp_config = icp_config or ICPConfig()

    def score_icp_fit(self, connection: PreMeetConnection) -> float:
        """Estimate ICP fit (0-100) from firmographics.

        FALLBACK ONLY: ICP fit is owned by Zero CRM (`ZeroCRMClient.score_icp_fit`).
        This local heuristic is used only when Zero isn't available. Placeholder.
        """
        score = 0.0
        if connection.company_size:
            lo, hi = self.icp_config.size_range
            if lo <= connection.company_size <= hi:
                score += 40
            else:
                score += 15
        if connection.arr_usd:
            lo, hi = self.icp_config.arr_range
            if lo <= connection.arr_usd <= hi:
                score += 30
        if connection.funding_stage in {"Series A", "Series B"}:
            score += 20
        tech = {t.lower() for t in connection.technographics}
        if tech & {t.lower() for t in self.icp_config.tech_stack}:
            score += 10
        return min(100.0, score)

    def score_intent(self, connection: PreMeetConnection) -> float:
        """Estimate buying intent (0-100) from research signals. Placeholder."""
        return min(100.0, len(connection.research_notes) * 20.0 + len(connection.interests) * 10.0)

    def score_meeting(self, signal: MeetingSignal) -> float:
        """Estimate post-meet lead quality (0-100) from captured signals."""
        score = 0.0
        score += min(40.0, len(signal.what_you_learned) * 10.0)
        score += min(30.0, len(signal.interests) * 10.0)
        if signal.most_interesting:
            score += 15.0
        if signal.company:
            score += 15.0
        return min(100.0, score)
