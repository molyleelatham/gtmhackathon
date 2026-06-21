"""Pydantic model round-trip tests."""

from datetime import datetime

import pytest

from packages.core.models.lead import Lead
from packages.core.models.meeting_signal import MeetingSignal
from packages.core.models.pre_connection import PreMeetConnection, PreMeetStatus
from packages.core.models.signal import Signal, SignalType
from packages.core.models.user_profile import UserProfile
from packages.core.models.warmth import WarmthBand, WarmthScore


@pytest.mark.unit
def test_lead_round_trip():
    lead = Lead(
        company_name="Acme",
        contact_name="Jane",
        icp_score=72,
        tags=["revops"],
    )
    data = lead.model_dump()
    restored = Lead.model_validate(data)
    assert restored.company_name == "Acme"
    assert restored.icp_score == 72


@pytest.mark.unit
def test_pre_connection_round_trip():
    conn = PreMeetConnection(
        id="conn_1",
        event_id="evt_1",
        user_id="user-1",
        name="Maya",
        status=PreMeetStatus.SCORED,
        predicted_warmth=80.0,
        interests=["RevOps", "HubSpot"],
    )
    restored = PreMeetConnection.model_validate(conn.model_dump())
    assert restored.name == "Maya"
    assert restored.interests == ["RevOps", "HubSpot"]


@pytest.mark.unit
def test_meeting_signal_round_trip():
    signal = MeetingSignal(
        name="Alex",
        company="NorthWind",
        interests=["attribution"],
        what_you_learned=["Q3 budget"],
    )
    restored = MeetingSignal.model_validate(signal.model_dump())
    assert restored.company == "NorthWind"


@pytest.mark.unit
def test_warmth_score_round_trip():
    score = WarmthScore(
        connection_id="conn_1",
        icp_score=85,
        warmth_score=78.0,
        band=WarmthBand.HOT,
    )
    restored = WarmthScore.model_validate(score.model_dump())
    assert restored.band == WarmthBand.HOT


@pytest.mark.unit
def test_user_profile_round_trip():
    now = datetime.utcnow()
    profile = UserProfile(
        uid="uid-1",
        email="user@test.com",
        display_name="User",
        created_at=now,
        updated_at=now,
    )
    restored = UserProfile.model_validate(profile.model_dump(mode="json"))
    assert restored.uid == "uid-1"


@pytest.mark.unit
def test_signal_enum_round_trip():
    signal = Signal(
        company_name="Acme",
        signal_type=SignalType.HIRING,
        raw_text="Hiring RevOps",
        source="tavily_search",
    )
    restored = Signal.model_validate(signal.model_dump())
    assert restored.signal_type == SignalType.HIRING
