"""Per-person knowledge-graph models for the MEET stage.

Data flow this supports:

    transcript utterance
        -> SpeakerID mapped to a PersonNode
        -> PersonContextBuilder.update()
        -> PersonalContext appended to the PersonNode (accumulates over 30s windows)
        -> SignalPayload carries personal_context per person
        -> backend KG: PersonNode.context evolves over the session
        -> Zero CRM push includes the personal-context narrative
        -> Faxxing personalises the outreach sequence to communication_style + values

A `PersonalContext` is the *incremental* read of a single ~30s window. A
`PersonNode` is the *evolving* aggregate for one speaker across the whole
session. `PersonKnowledgeGraph` maps diarization speaker ids -> PersonNodes.
"""
from __future__ import annotations

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class PainPoint(BaseModel):
    """A pain the person expressed, with an accumulated intensity (0..1)."""
    topic: str
    intensity: float = 0.0  # 0..1, grows the more / more strongly it's raised

    @property
    def level(self) -> str:
        if self.intensity >= 0.66:
            return "high"
        if self.intensity >= 0.33:
            return "moderate"
        return "low"


class PersonalContext(BaseModel):
    """The signal extracted from one ~30s transcript window for one speaker.

    These are *deltas*; the PersonNode accumulates them across the session.
    """
    window_start: datetime = Field(default_factory=datetime.utcnow)
    window_end: Optional[datetime] = None

    communication_style: list[str] = Field(default_factory=list)  # e.g. analytical, data-driven
    values: list[str] = Field(default_factory=list)               # e.g. accuracy, transparency
    topic_weights: dict[str, float] = Field(default_factory=dict)  # topic -> share of attention
    learnings: list[str] = Field(default_factory=list)            # net-new things they revealed
    pain_points: list[PainPoint] = Field(default_factory=list)

    transcript_excerpt: Optional[str] = None

    class Config:
        json_encoders = {datetime: lambda v: v.isoformat()}


class PersonNode(BaseModel):
    """The evolving aggregate context for a single person over a session.

    `update()` folds a window-level PersonalContext into the node so the
    knowledge graph reflects the whole conversation, not just the last window.
    """
    speaker_id: int
    is_self: bool = False  # your own voice -> never enriched / pushed
    person_id: str = Field(default_factory=lambda: f"person_{datetime.now().timestamp()}")

    name: Optional[str] = None
    company: Optional[str] = None
    role: Optional[str] = None

    communication_style: list[str] = Field(default_factory=list)
    values: list[str] = Field(default_factory=list)
    topic_weights: dict[str, float] = Field(default_factory=dict)  # normalised topic -> weight
    learnings: list[str] = Field(default_factory=list)
    pain_points: list[PainPoint] = Field(default_factory=list)

    contexts: list[PersonalContext] = Field(default_factory=list)  # window history
    first_seen: datetime = Field(default_factory=datetime.utcnow)
    last_updated: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        json_encoders = {datetime: lambda v: v.isoformat()}

    # -- accumulation -----------------------------------------------------

    def update(self, context: PersonalContext) -> "PersonNode":
        """Fold a 30s-window PersonalContext into the evolving node context."""
        self.contexts.append(context)

        self.communication_style = _merge_ranked(self.communication_style, context.communication_style)
        self.values = _merge_ranked(self.values, context.values)
        self.learnings = _merge_unique(self.learnings, context.learnings)
        self.topic_weights = _accumulate_topics(self.topic_weights, context.topic_weights)
        self.pain_points = _accumulate_pains(self.pain_points, context.pain_points)

        self.last_updated = context.window_end or datetime.utcnow()
        return self

    # -- derived views ----------------------------------------------------

    @property
    def dominant_topic(self) -> Optional[tuple[str, float]]:
        if not self.topic_weights:
            return None
        topic, weight = max(self.topic_weights.items(), key=lambda kv: kv[1])
        return topic, round(weight, 2)

    @property
    def top_pain(self) -> Optional[PainPoint]:
        if not self.pain_points:
            return None
        return max(self.pain_points, key=lambda p: p.intensity)

    def to_narrative(self) -> str:
        """Human-readable context summary, e.g. what gets pushed to Zero CRM:

        "Anna is analytical, data-driven, cares about accuracy. Dominant topic:
        pipeline visibility (0.8 weight). Recently learned HubSpot has AI
        forecasting. High pain intensity around manual data entry."
        """
        who = self.name or f"Speaker {self.speaker_id}"
        parts: list[str] = []

        descriptors = list(self.communication_style)
        sentence = who
        if descriptors:
            sentence += " is " + _join(descriptors)
        if self.values:
            sentence += (", " if descriptors else " ") + "cares about " + _join(self.values)
        if descriptors or self.values:
            parts.append(sentence.rstrip(".") + ".")

        dom = self.dominant_topic
        if dom:
            parts.append(f"Dominant topic: {dom[0]} ({dom[1]} weight).")

        if self.learnings:
            parts.append("Recently learned " + _join(self.learnings) + ".")

        pain = self.top_pain
        if pain:
            parts.append(f"{pain.level.capitalize()} pain intensity around {pain.topic}.")

        return " ".join(parts).strip()


class PersonKnowledgeGraph(BaseModel):
    """In-session knowledge graph: diarization speaker id -> PersonNode.

    Lives for the duration of a meeting/session. The backend persists the
    evolved PersonNodes (e.g. to Firestore) at the end of the session.
    """
    session_id: str = Field(default_factory=lambda: f"kg_{datetime.now().timestamp()}")
    self_speaker_id: Optional[int] = None
    nodes: dict[int, PersonNode] = Field(default_factory=dict)

    class Config:
        json_encoders = {datetime: lambda v: v.isoformat()}

    def get_or_create(self, speaker_id: int, **attrs) -> PersonNode:
        node = self.nodes.get(speaker_id)
        if node is None:
            node = PersonNode(
                speaker_id=speaker_id,
                is_self=(speaker_id == self.self_speaker_id),
                **attrs,
            )
            self.nodes[speaker_id] = node
        else:
            for key, value in attrs.items():
                if value is not None and getattr(node, key, None) in (None, [], {}):
                    setattr(node, key, value)
        return node

    def people(self, exclude_self: bool = True) -> list[PersonNode]:
        return [n for n in self.nodes.values() if not (exclude_self and n.is_self)]


# --------------------------------------------------------------------------
# accumulation helpers
# --------------------------------------------------------------------------


def _join(items: list[str]) -> str:
    items = [i for i in items if i]
    if not items:
        return ""
    if len(items) == 1:
        return items[0]
    if len(items) == 2:
        return f"{items[0]} and {items[1]}"
    return ", ".join(items[:-1]) + f", and {items[-1]}"


def _merge_unique(existing: list[str], incoming: list[str]) -> list[str]:
    out = list(existing)
    for item in incoming:
        if item and item not in out:
            out.append(item)
    return out


def _merge_ranked(existing: list[str], incoming: list[str], limit: int = 5) -> list[str]:
    """Merge preserving first-seen order, capped so the strongest traits stay."""
    return _merge_unique(existing, incoming)[:limit]


def _accumulate_topics(existing: dict[str, float], incoming: dict[str, float]) -> dict[str, float]:
    """Sum raw topic attention then renormalise to weights that sum to ~1."""
    totals: dict[str, float] = dict(existing)
    # de-normalise existing weights back to counts is lossy; instead keep a
    # running sum by treating prior weights as accumulated mass.
    for topic, weight in incoming.items():
        totals[topic] = totals.get(topic, 0.0) + weight
    total = sum(totals.values())
    if total <= 0:
        return totals
    return {t: round(w / total, 4) for t, w in totals.items()}


def _accumulate_pains(existing: list[PainPoint], incoming: list[PainPoint]) -> list[PainPoint]:
    by_topic = {p.topic: p for p in existing}
    for pain in incoming:
        if pain.topic in by_topic:
            current = by_topic[pain.topic]
            current.intensity = min(1.0, current.intensity + pain.intensity)
        else:
            by_topic[pain.topic] = PainPoint(topic=pain.topic, intensity=min(1.0, pain.intensity))
    return list(by_topic.values())
