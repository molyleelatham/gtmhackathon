from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class WarmthBand(str, Enum):
    COLD = "cold"
    WARM = "warm"
    HOT = "hot"


class WarmthScore(BaseModel):
    """Warmth score for a connection.

    `icp_score` and `warmth_score` are tracked independently and correlated by
    the ML pipeline (see packages/ml). High ICP fit + high warmth = top priority.

    Pre-meet, `predicted` is set from research/enrichment. Post-meet, `actual`
    is computed from captured conversation signals. The delta drives routing:
    if actual > predicted (uplift), push to CRM + outreach; otherwise consider
    routing the connection to the founder community.
    """
    id: str = Field(default_factory=lambda: f"warmth_{datetime.now().timestamp()}")
    connection_id: Optional[str] = None
    lead_id: Optional[str] = None

    icp_score: float = 0.0  # 0-100 ICP fit
    warmth_score: float = 0.0  # 0-100 relational/intent warmth

    predicted_score: Optional[float] = None  # pre-meet combined prediction
    actual_score: Optional[float] = None  # post-meet combined actual
    band: WarmthBand = WarmthBand.COLD

    # component breakdown for explainability / ML features
    components: dict = Field(default_factory=dict)
    model_version: str = "stub-v0"
    scored_at: datetime = Field(default_factory=datetime.utcnow)

    @property
    def uplift(self) -> Optional[float]:
        """Post-meet uplift vs. pre-meet prediction (None until both exist)."""
        if self.predicted_score is None or self.actual_score is None:
            return None
        return self.actual_score - self.predicted_score

    class Config:
        json_encoders = {datetime: lambda v: v.isoformat()}
