"""Tests for ML scoring modules."""

import pytest

from packages.core.models.meeting_signal import MeetingSignal
from packages.core.models.pre_connection import PreMeetConnection, PreMeetStatus
from packages.ml.lead_scorer import LeadScorer
from packages.ml.warmth_model import WarmthModel


@pytest.mark.unit
def test_lead_scorer_icp_fit_in_range(icp_config):
    scorer = LeadScorer(icp_config)
    conn = PreMeetConnection(
        id="c1",
        event_id="e1",
        user_id="u1",
        name="Target Co",
        status=PreMeetStatus.SCORED,
        company_size=150,
        arr_usd=5_000_000,
        funding_stage="Series B",
        technographics=["HubSpot", "Salesforce"],
    )
    score = scorer.score_icp_fit(conn)
    assert 0 <= score <= 100
    assert score >= 50


@pytest.mark.unit
def test_lead_scorer_intent_from_research():
    scorer = LeadScorer()
    conn = PreMeetConnection(
        id="c2",
        event_id="e1",
        user_id="u1",
        status=PreMeetStatus.SCORED,
        research_notes=["Strong buying signals", "Budget confirmed"],
        interests=["RevOps"],
    )
    assert scorer.score_intent(conn) >= 40


@pytest.mark.unit
def test_lead_scorer_meeting_signal():
    scorer = LeadScorer()
    signal = MeetingSignal(
        name="Maya",
        company="NorthWind",
        interests=["attribution", "RevOps"],
        what_you_learned=["budget Q3"],
        most_interesting="tool consolidation",
    )
    score = scorer.score_meeting(signal)
    assert score >= 40


@pytest.mark.unit
def test_warmth_model_pre_meet():
    model = WarmthModel()
    conn = PreMeetConnection(
        id="c3",
        event_id="e1",
        user_id="u1",
        status=PreMeetStatus.SCORED,
        icp_score=80,
        predicted_warmth=65,
        intent_score=55,
        interests=["pipeline"],
        research_notes=["engaged"],
    )
    warmth = model.predict_pre_meet(conn)
    assert warmth.icp_score >= 0
    assert warmth.warmth_score >= 0
    assert warmth.band is not None


@pytest.mark.unit
def test_warmth_model_post_meet():
    model = WarmthModel()
    PreMeetConnection(
        id="c4",
        event_id="e1",
        user_id="u1",
        status=PreMeetStatus.SCORED,
        icp_score=70,
        predicted_warmth=60,
    )
    signal = MeetingSignal(
        name="Alex",
        company="Acme",
        interests=["RevOps"],
        what_you_learned=["timeline"],
        most_interesting="integration",
    )
    warmth = model.score_post_meet(signal, prior=None)
    assert warmth.actual_score is not None
    assert warmth.warmth_score >= 0
