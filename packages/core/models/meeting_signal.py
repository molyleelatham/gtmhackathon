from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field

from .person import PersonNode


class TopicTime(BaseModel):
    """How long was spent talking about a given topic during a meeting."""
    topic: str
    seconds: float = 0.0


class MeetingSignal(BaseModel):
    """Signals captured live during a meeting, starting when the phrase
    trigger ("hey it's nice to meet you") fires.

    These are the raw conversational signals that feed the ML pipeline:
    name, interests, origin, background, time-per-topic, and takeaways.
    """
    id: str = Field(default_factory=lambda: f"msig_{datetime.now().timestamp()}")
    event_id: Optional[str] = None
    connection_id: Optional[str] = None
    conversation_id: Optional[str] = None

    # who you met
    name: Optional[str] = None
    company: Optional[str] = None
    role: Optional[str] = None
    origin: Optional[str] = None  # where they're from

    # what you learned
    interests: list[str] = Field(default_factory=list)
    background: Optional[str] = None
    topic_time: list[TopicTime] = Field(default_factory=list)  # time per topic
    most_time_topic: Optional[str] = None
    what_you_learned: list[str] = Field(default_factory=list)
    most_interesting: Optional[str] = None

    # evolving per-person context accumulated by the PersonContextBuilder across
    # 30s windows (communication style, values, dominant topics, pains, learnings)
    personal_context: Optional[PersonNode] = None

    # raw + provenance
    transcript_excerpt: Optional[str] = None
    captured_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        json_encoders = {datetime: lambda v: v.isoformat()}
