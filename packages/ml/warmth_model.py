from typing import Optional

from pydantic import BaseModel, Field

from ..core.models.meeting_signal import MeetingSignal
from ..core.models.pre_connection import PreMeetConnection
from ..core.models.warmth import WarmthBand, WarmthScore


class WarmthFeatures(BaseModel):
    """Feature vector consumed by the warmth model.

    Data-source ownership: `icp_fit` is sourced from **Zero CRM** (the ICP owner),
    firmographic/technographic inputs come from **UnifyGTM** enrichment, and
    **warmth is built on top** by this model. ICP fit and warmth are kept as
    separate inputs intentionally: a connection can be a perfect ICP fit but cold,
    or off-ICP but extremely warm. The model correlates them to produce a single
    prioritization score.
    """
    icp_fit: float = 0.0          # 0-100, firmographic/persona fit
    intent: float = 0.0           # 0-100, buying intent signals
    engagement: float = 0.0       # 0-100, conversational engagement (post-meet)
    topic_relevance: float = 0.0  # 0-100, overlap of topics with our offering
    relationship: float = 0.0     # 0-100, rapport / network proximity
    extra: dict = Field(default_factory=dict)


class WarmthModel:
    """Combined ICP + warmth prioritization model.

    Warmth is built ON TOP of upstream signals owned by other systems: ICP fit
    comes from **Zero CRM**, enrichment from **UnifyGTM**, and this model layers
    warmth (intent/engagement/relationship) over them, then correlates ICP fit
    with warmth into a single prioritization score.

    STUB: replace `_score` with a trained model. The contract is stable:
    given features, return icp_score, warmth_score and a combined band.
    """

    def __init__(self, model_version: str = "stub-v0"):
        self.model_version = model_version

    # ------------------------------------------------------------------ #
    # Public API
    # ------------------------------------------------------------------ #
    def predict_pre_meet(self, connection: PreMeetConnection) -> WarmthScore:
        """Predict warmth for a connection BEFORE the meeting using research."""
        features = self._features_from_pre_connection(connection)
        icp, warmth = self._score(features)
        combined = self._combine(icp, warmth)
        return WarmthScore(
            connection_id=connection.id,
            icp_score=icp,
            warmth_score=warmth,
            predicted_score=combined,
            band=self._band(combined),
            components=features.model_dump(),
            model_version=self.model_version,
        )

    def score_post_meet(
        self,
        signal: MeetingSignal,
        prior: Optional[WarmthScore] = None,
    ) -> WarmthScore:
        """Score warmth AFTER a meeting using captured conversation signals.

        If `prior` (the pre-meet prediction) is provided, its predicted_score is
        carried over so the lifecycle can compute uplift.
        """
        features = self._features_from_meeting_signal(signal, prior)
        icp, warmth = self._score(features)
        combined = self._combine(icp, warmth)
        return WarmthScore(
            connection_id=signal.connection_id,
            conversation_id=signal.conversation_id,
            icp_score=icp,
            warmth_score=warmth,
            predicted_score=prior.predicted_score if prior else None,
            actual_score=combined,
            band=self._band(combined),
            components=features.model_dump(),
            model_version=self.model_version,
        )

    # ------------------------------------------------------------------ #
    # Stub scoring internals  (TODO: replace with trained model)
    # ------------------------------------------------------------------ #
    def _score(self, f: WarmthFeatures) -> tuple[float, float]:
        """Return (icp_score, warmth_score). Placeholder heuristic."""
        icp = min(100.0, 0.7 * f.icp_fit + 0.3 * f.topic_relevance)
        warmth = min(
            100.0,
            0.4 * f.intent + 0.35 * f.engagement + 0.25 * f.relationship,
        )
        return round(icp, 2), round(warmth, 2)

    def _combine(self, icp: float, warmth: float) -> float:
        """Combine ICP fit and warmth into a single prioritization score.

        Both must be reasonably high to score at the top; this multiplicative
        blend penalizes connections that are strong on only one axis.
        """
        norm = (icp / 100.0) * (warmth / 100.0)
        blended = 0.5 * ((icp + warmth) / 2.0) + 0.5 * (norm * 100.0)
        return round(min(100.0, blended), 2)

    @staticmethod
    def _band(score: float) -> WarmthBand:
        if score >= 70:
            return WarmthBand.HOT
        if score >= 40:
            return WarmthBand.WARM
        return WarmthBand.COLD

    # ------------------------------------------------------------------ #
    # Feature extraction (placeholder mappings)
    # ------------------------------------------------------------------ #
    def _features_from_pre_connection(self, c: PreMeetConnection) -> WarmthFeatures:
        # c.icp_score is sourced from Zero CRM (with a local fallback) upstream
        # in PreMeetPipeline.score(); warmth is layered on top of it here.
        return WarmthFeatures(
            icp_fit=c.icp_score,
            intent=c.intent_score,
            engagement=0.0,  # unknown pre-meet
            topic_relevance=float(min(100, len(c.interests) * 20)),
            relationship=0.0,
            extra={"source": c.source},
        )

    def _features_from_meeting_signal(
        self, s: MeetingSignal, prior: Optional[WarmthScore]
    ) -> WarmthFeatures:
        total_topic_time = sum(t.seconds for t in s.topic_time) or 1.0
        engagement = min(100.0, total_topic_time / 60.0 * 10.0)  # ~10pts/min
        return WarmthFeatures(
            icp_fit=prior.icp_score if prior else 50.0,
            intent=float(min(100, len(s.what_you_learned) * 15)),
            engagement=engagement,
            topic_relevance=float(min(100, len(s.interests) * 20)),
            relationship=80.0 if s.most_interesting else 40.0,
            extra={"most_time_topic": s.most_time_topic},
        )
