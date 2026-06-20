from typing import Optional
from ..core.models.meeting_signal import MeetingSignal


class LeadClusterer:
    """Cluster connections/leads by interests, topics, and background.

    STUB: replace with a real clustering model (e.g. embeddings + KMeans/HDBSCAN).
    Used to (a) group similar connections and (b) help the community matcher
    find the nearest founder/friend for a given connection.
    """

    def __init__(self, n_clusters: int = 5, model_version: str = "stub-v0"):
        self.n_clusters = n_clusters
        self.model_version = model_version

    def embed(self, signal: MeetingSignal) -> list[float]:
        """Return a feature embedding for a meeting signal.

        TODO: replace bag-of-interests with a real text/embedding model.
        """
        # Placeholder: hash interests into a small fixed-size vector.
        vec = [0.0] * 16
        for token in (signal.interests or []) + ([signal.most_time_topic] if signal.most_time_topic else []):
            if token:
                vec[hash(token.lower()) % 16] += 1.0
        return vec

    def assign_cluster(self, signal: MeetingSignal) -> int:
        """Assign a connection to a cluster id. Placeholder modulo logic."""
        vec = self.embed(signal)
        dominant = max(range(len(vec)), key=lambda i: vec[i]) if any(vec) else 0
        return dominant % self.n_clusters

    def nearest(
        self,
        signal: MeetingSignal,
        candidates: list[dict],
        top_k: int = 1,
    ) -> list[dict]:
        """Find the nearest candidates (e.g. founders/friends) to a connection.

        `candidates` are arbitrary dicts with an `interests` list. STUB: scores
        by interest overlap. TODO: replace with cosine similarity over embeddings.
        """
        target = {i.lower() for i in (signal.interests or [])}
        scored: list[tuple[float, dict]] = []
        for cand in candidates:
            cand_interests = {i.lower() for i in cand.get("interests", [])}
            overlap = len(target & cand_interests)
            scored.append((float(overlap), cand))
        scored.sort(key=lambda x: x[0], reverse=True)
        return [c for _, c in scored[:top_k]]
