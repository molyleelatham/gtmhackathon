"""MeetEncoder — the missing link between raw capture and the models.

Turns a diarized transcript (the data coming off the phone / Deepgram) into the
structured inputs the MEET-stage models consume:

    diarized turns ([{speaker, text}], self_speaker_id)
        -> PersonContextBuilder over each non-self speaker (per-turn windows)
        -> PersonKnowledgeGraph (evolving PersonNode per speaker)
        -> a MeetingSignal for the primary counterpart (name, interests,
           topic_time, what_you_learned, most_time_topic, personal_context)

The MeetingSignal then feeds `MeetIntelligencePipeline` (warmth/lead/cluster
models) exactly as `POST /api/v1/meet/signals` expects.
"""
from datetime import datetime, timedelta
from typing import Optional

from .person_context_builder import PersonContextBuilder
from .interest_analyzer import InterestAnalyzer
from .topic_extractor import TopicExtractor
from ....packages.core.models.meeting_signal import MeetingSignal, TopicTime
from ....packages.core.models.person import PersonKnowledgeGraph, PersonNode


class MeetEncoder:
    def __init__(
        self,
        builder: Optional[PersonContextBuilder] = None,
        interest_analyzer: Optional[InterestAnalyzer] = None,
        topic_extractor: Optional[TopicExtractor] = None,
        use_agent: bool = False,
    ):
        if builder is None:
            extractor = None
            if use_agent:
                from .agent_extractor import AgentContextExtractor

                extractor = AgentContextExtractor()
            builder = PersonContextBuilder(extractor=extractor)
        self.builder = builder
        self.interest_analyzer = interest_analyzer or InterestAnalyzer()
        self.topic_extractor = topic_extractor or TopicExtractor()

    def encode(
        self,
        turns: list[dict],
        self_speaker_id: int = 0,
        speaker_attrs: Optional[dict[int, dict]] = None,
        event_id: Optional[str] = None,
        connection_id: Optional[str] = None,
        window_seconds: float = 30.0,
    ) -> tuple[MeetingSignal, PersonKnowledgeGraph]:
        """Encode diarized turns into a MeetingSignal + knowledge graph.

        `turns`: ordered list of {"speaker": int, "text": str}.
        `speaker_attrs`: optional {speaker_id: {"name", "company", "role"}}.
        """
        speaker_attrs = speaker_attrs or {}
        kg = PersonKnowledgeGraph(self_speaker_id=self_speaker_id)

        base = datetime.utcnow()
        for i, turn in enumerate(turns):
            speaker_id = int(turn.get("speaker", 0))
            text = (turn.get("text") or "").strip()
            if not text:
                continue
            attrs = speaker_attrs.get(speaker_id, {})
            start = base + timedelta(seconds=window_seconds * i)
            self.builder.update(
                kg,
                speaker_id=speaker_id,
                transcript_window=text,
                name=attrs.get("name"),
                company=attrs.get("company"),
                role=attrs.get("role"),
                window_start=start,
                window_end=start + timedelta(seconds=window_seconds),
            )

        primary = self._primary_counterpart(kg, turns, self_speaker_id)
        signal = self._signal_from_node(
            primary, turns, self_speaker_id, event_id, connection_id
        )
        return signal, kg

    # ------------------------------------------------------------------ #
    def _primary_counterpart(
        self,
        kg: PersonKnowledgeGraph,
        turns: list[dict],
        self_speaker_id: int,
    ) -> Optional[PersonNode]:
        """The non-self speaker who said the most (the person you met)."""
        words_by_speaker: dict[int, int] = {}
        for turn in turns:
            sid = int(turn.get("speaker", 0))
            if sid == self_speaker_id:
                continue
            words_by_speaker[sid] = words_by_speaker.get(sid, 0) + len(
                (turn.get("text") or "").split()
            )
        if not words_by_speaker:
            return None
        top_sid = max(words_by_speaker, key=words_by_speaker.get)
        return kg.nodes.get(top_sid)

    def _signal_from_node(
        self,
        node: Optional[PersonNode],
        turns: list[dict],
        self_speaker_id: int,
        event_id: Optional[str],
        connection_id: Optional[str],
    ) -> MeetingSignal:
        if node is None:
            return MeetingSignal(event_id=event_id, connection_id=connection_id)

        # Concatenate the counterpart's own utterances for analysis.
        their_text = " ".join(
            (t.get("text") or "")
            for t in turns
            if int(t.get("speaker", 0)) == node.speaker_id
        )
        analysis = self.interest_analyzer.analyze_interests(their_text)
        interests = analysis.get("interests", []) + analysis.get("values", [])

        # Per-topic seconds, accumulated per ~30s window: each window's weights
        # (which sum to ~1) are scaled by that window's duration, so the totals
        # reflect how long the counterpart actually spoke (drives engagement).
        secs_by_topic: dict[str, float] = {}
        for ctx in node.contexts:
            if ctx.window_end and ctx.window_start:
                dur = max(0.0, (ctx.window_end - ctx.window_start).total_seconds())
            else:
                dur = 30.0
            for topic, weight in ctx.topic_weights.items():
                secs_by_topic[topic] = secs_by_topic.get(topic, 0.0) + weight * dur
        topic_time = [
            TopicTime(topic=topic, seconds=round(secs, 1))
            for topic, secs in sorted(
                secs_by_topic.items(), key=lambda kv: kv[1], reverse=True
            )[:5]
        ]
        dom = node.dominant_topic

        what_you_learned = list(node.learnings)
        top_pain = node.top_pain
        if top_pain:
            what_you_learned.append(f"pain: {top_pain.topic} ({top_pain.level})")

        most_interesting = (
            node.learnings[0]
            if node.learnings
            else (dom[0] if dom else None)
        )

        return MeetingSignal(
            event_id=event_id,
            connection_id=connection_id,
            name=node.name,
            company=node.company,
            role=node.role,
            interests=interests,
            topic_time=topic_time,
            most_time_topic=dom[0] if dom else None,
            what_you_learned=what_you_learned,
            most_interesting=most_interesting,
            transcript_excerpt=their_text[:500] or None,
            personal_context=node,
        )
