"""PersonContextBuilder — turns a ~30s transcript window into a PersonalContext
and folds it into the per-speaker PersonNode in the knowledge graph.

It reuses the existing topic/interest analysers and layers on communication
style + pain-intensity inference so the evolving PersonNode.context can drive
the Zero CRM push and Faxxing personalisation.
"""
import re
from datetime import datetime
from typing import Optional

from .topic_extractor import TopicExtractor
from .interest_analyzer import InterestAnalyzer
from ....packages.core.models.person import (
    PersonalContext,
    PersonNode,
    PersonKnowledgeGraph,
    PainPoint,
)


# Lexical cues for communication style. Kept simple/heuristic for the hackathon;
# swap for an LLM classifier behind the same interface later.
_STYLE_CUES: dict[str, list[str]] = {
    "analytical": ["data", "metric", "number", "measure", "analy", "benchmark", "roi", "specifically"],
    "data-driven": ["data", "dashboard", "report", "attribution", "forecast", "pipeline", "kpi"],
    "visionary": ["vision", "future", "transform", "long-term", "mission", "big picture"],
    "relational": ["team", "people", "culture", "relationship", "trust", "we ", "together"],
    "pragmatic": ["practical", "quick", "simple", "just need", "get it done", "right now"],
    "skeptical": ["not sure", "skeptic", "concern", "doubt", "prove", "really work"],
    "enthusiastic": ["love", "excited", "amazing", "awesome", "can't wait", "thrilled"],
}

# Words that intensify a stated pain.
_INTENSIFIERS = ["really", "very", "extremely", "constantly", "always", "huge", "massive", "so much", "hate"]


class PersonContextBuilder:
    def __init__(
        self,
        topic_extractor: Optional[TopicExtractor] = None,
        interest_analyzer: Optional[InterestAnalyzer] = None,
    ):
        self.topic_extractor = topic_extractor or TopicExtractor()
        self.interest_analyzer = interest_analyzer or InterestAnalyzer()

    def build_window(
        self,
        transcript_window: str,
        window_start: Optional[datetime] = None,
        window_end: Optional[datetime] = None,
    ) -> PersonalContext:
        """Extract a PersonalContext delta from a single ~30s window."""
        analysis = self.interest_analyzer.analyze_interests(transcript_window)
        topics = self.topic_extractor.extract_topics(transcript_window, top_n=5)

        return PersonalContext(
            window_start=window_start or datetime.utcnow(),
            window_end=window_end,
            communication_style=self._infer_style(transcript_window),
            values=analysis.get("values", []),
            topic_weights=self._topic_weights(transcript_window, topics),
            learnings=self._extract_learnings(transcript_window),
            pain_points=self._extract_pains(transcript_window, analysis.get("pain_points", [])),
            transcript_excerpt=transcript_window.strip()[:500] or None,
        )

    def update(
        self,
        kg: PersonKnowledgeGraph,
        speaker_id: int,
        transcript_window: str,
        *,
        name: Optional[str] = None,
        company: Optional[str] = None,
        role: Optional[str] = None,
        window_start: Optional[datetime] = None,
        window_end: Optional[datetime] = None,
    ) -> PersonNode:
        """Map a speaker's window onto a PersonNode and fold in the new context.

        This is the `PersonContextBuilder.update()` node in the data flow:
        SpeakerID -> PersonNode -> accumulate PersonalContext across windows.
        """
        node = kg.get_or_create(speaker_id, name=name, company=company, role=role)
        if node.is_self:
            return node  # never enrich your own voice

        context = self.build_window(transcript_window, window_start, window_end)
        node.update(context)
        return node

    # -- inference helpers ------------------------------------------------

    def _infer_style(self, text: str) -> list[str]:
        lowered = text.lower()
        scored: list[tuple[str, int]] = []
        for style, cues in _STYLE_CUES.items():
            hits = sum(1 for cue in cues if cue in lowered)
            if hits:
                scored.append((style, hits))
        scored.sort(key=lambda kv: kv[1], reverse=True)
        return [style for style, _ in scored[:3]]

    def _topic_weights(self, text: str, topics: list[str]) -> dict[str, float]:
        """Weight topics by share of attention in this window.

        Specific multi-word phrases the person actually repeats (e.g.
        "pipeline visibility") are preferred over the coarse taxonomy buckets
        (e.g. "sales"), since they carry far more signal for personalisation.
        """
        lowered = text.lower()
        raw: dict[str, float] = {}

        # Coarse taxonomy topics.
        for topic in topics:
            keywords = self.topic_extractor.topic_keywords.get(topic, [topic])
            count = sum(lowered.count(kw) for kw in keywords)
            if count:
                raw[topic] = float(count)

        # Salient specific phrases get a boost so they dominate generic buckets.
        for phrase, count in self._salient_phrases(lowered).items():
            raw[phrase] = raw.get(phrase, 0.0) + count * 3.0

        total = sum(raw.values())
        if total <= 0:
            return {}
        return {t: round(c / total, 4) for t, c in raw.items()}

    @staticmethod
    def _salient_phrases(lowered: str, min_count: int = 1) -> dict[str, float]:
        """Find content-bearing 2-word phrases (bigrams) in the window.

        Drops stopword-led phrases so we keep things like "pipeline visibility"
        and "manual data" rather than "of the" / "in our".
        """
        stop = {
            "the", "a", "an", "of", "to", "in", "on", "for", "and", "or", "but",
            "is", "are", "was", "were", "i", "we", "you", "they", "it", "so",
            "my", "our", "your", "their", "that", "this", "with", "at", "as",
            "have", "has", "had", "do", "does", "be", "what", "lot", "really",
            "im", "me", "about", "what", "look", "spend", "time", "thing", "honestly",
        }
        words = re.findall(r"[a-z]+", lowered)
        counts: dict[str, int] = {}
        for w1, w2 in zip(words, words[1:]):
            if w1 in stop or w2 in stop:
                continue
            phrase = f"{w1} {w2}"
            counts[phrase] = counts.get(phrase, 0) + 1
        return {p: float(c) for p, c in counts.items() if c >= min_count}

    def _extract_learnings(self, text: str) -> list[str]:
        """Net-new facts the person revealed (e.g. tools they just adopted)."""
        patterns = [
            r"(?:just|recently|we) (?:learned|found out|discovered) (?:that )?(.+?)(?:\.|,| and|$)",
            r"(?:turns out|apparently) (.+?)(?:\.|,| and|$)",
            r"(?:we|they|i) (?:started using|adopted|switched to|moved to) (.+?)(?:\.|,| and|$)",
            r"(?:HubSpot|Salesforce|the platform|the tool) (?:has|now has|added|supports) (.+?)(?:\.|,| and|$)",
        ]
        learnings: list[str] = []
        for pattern in patterns:
            for match in re.findall(pattern, text, flags=re.IGNORECASE):
                phrase = match.strip()
                if len(phrase) > 3:
                    learnings.append(phrase)
        # De-dup, dropping phrases that are substrings of a longer learning
        # (e.g. drop "AI forecasting" when "HubSpot has AI forecasting" exists).
        unique: list[str] = []
        for item in sorted(learnings, key=len, reverse=True):
            lowered = item.lower()
            if any(lowered in kept.lower() for kept in unique):
                continue
            unique.append(item)
        # Restore original (longest-first) order by length for stable output.
        return unique

    def _extract_pains(self, text: str, base_pain_points: list[str]) -> list[PainPoint]:
        lowered = text.lower()
        pains: list[PainPoint] = []
        for topic in base_pain_points:
            intensity = 0.4  # a stated pain starts moderate
            window = self._context_around(lowered, topic.lower())
            intensity += 0.2 * sum(1 for word in _INTENSIFIERS if word in window)
            pains.append(PainPoint(topic=topic, intensity=min(1.0, round(intensity, 2))))
        return pains

    @staticmethod
    def _context_around(text: str, phrase: str, radius: int = 40) -> str:
        idx = text.find(phrase)
        if idx == -1:
            return text
        return text[max(0, idx - radius): idx + len(phrase) + radius]
