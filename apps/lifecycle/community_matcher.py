"""Founder-community matcher.

When a meeting does not raise warmth above expectation, the connection may still
be valuable to someone in your network. This finds the nearest founder/friend
who would benefit from the connection.
"""
from typing import Optional

from ...packages.core.models.meeting_signal import MeetingSignal
from ...packages.ml.clustering import LeadClusterer


class CommunityMatcher:
    def __init__(self, clusterer: Optional[LeadClusterer] = None):
        self.clusterer = clusterer or LeadClusterer()

    def find_match(
        self,
        signal: MeetingSignal,
        community_members: list[dict],
        top_k: int = 1,
    ) -> list[dict]:
        """Return the closest community member(s) for this connection.

        `community_members` are dicts like:
            {"user_id": ..., "name": ..., "interests": [...]}

        STUB: interest-overlap ranking via the clusterer.
        """
        return self.clusterer.nearest(signal, community_members, top_k=top_k)
