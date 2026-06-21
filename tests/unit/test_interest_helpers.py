"""Tests for interest helper utilities."""

import pytest
from warmth.apps.api.interest_helpers import (
    interests_from_knowledge_graph,
    interests_from_meet_summary,
    merge_interests,
)


@pytest.mark.unit
def test_merge_interests_dedupes_case_insensitive():
    merged = merge_interests(["RevOps", "hubspot"], ["HubSpot", "RevOps"])
    assert merged == ["RevOps", "hubspot"]


@pytest.mark.unit
def test_interests_from_knowledge_graph():
    people = [
        {
            "topic_weights": {"pipeline": 0.8, "attribution": 0.5},
            "values": ["accuracy"],
            "communication_style": ["analytical"],
            "learnings": ["uses HubSpot"],
        }
    ]
    interests = interests_from_knowledge_graph(people)
    assert "pipeline" in interests
    assert "accuracy" in interests


@pytest.mark.unit
def test_interests_from_meet_summary():
    summary = {
        "signal": {"interests": ["RevOps"]},
        "people": [{"topic_weights": {"GTM": 0.9}, "values": [], "communication_style": []}],
    }
    merged = interests_from_meet_summary(summary, ["HubSpot"])
    assert "RevOps" in merged
    assert "HubSpot" in merged
    assert "GTM" in merged
