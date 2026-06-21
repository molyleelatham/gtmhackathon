"""Tests for attendee matching (pure scoring)."""

import pytest
from warmth.apps.listener.intelligence.attendee_matcher import (
    AttendeeMatcher,
    Candidate,
    score_name,
)

from packages.core.models.meeting_signal import MeetingSignal


@pytest.mark.unit
def test_score_name_exact_match():
    score, matched = score_name("Maya Chen", "Maya Chen")
    assert score == 1.0
    assert "full_name" in matched


@pytest.mark.unit
def test_score_name_first_name_match():
    score, matched = score_name("Maya", "Maya Chen")
    assert score >= 0.6
    assert matched


@pytest.mark.unit
def test_attendee_matcher_pipeline_candidate():
    matcher = AttendeeMatcher()
    signal = MeetingSignal(name="Nicholas Wong", company="CLARK")
    candidates = [
        Candidate(
            name="Nicholas Wong",
            company="CLARK",
            source="pipeline",
            external_id="premeet_nicholas_wong",
        ),
        Candidate(name="Other Person", company="Other Co", source="pipeline"),
    ]
    result = matcher.match(signal, candidates)
    assert result is not None
    assert result.score >= 0.62
    assert result.candidate.external_id == "premeet_nicholas_wong"
