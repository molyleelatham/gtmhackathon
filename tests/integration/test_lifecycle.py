"""Lifecycle pipeline integration tests with mocked external I/O."""

from unittest.mock import AsyncMock, patch

import pytest
from warmth.apps.lifecycle.postmeet import PostMeetPipeline
from warmth.apps.lifecycle.premeet import PreMeetPipeline
from warmth.packages.core.models.event import DetectedEvent, EventType, LifecycleStage
from warmth.packages.core.models.lead import Lead
from warmth.packages.core.models.meeting_signal import MeetingSignal
from warmth.packages.core.models.pre_connection import PreMeetConnection, PreMeetStatus


@pytest.mark.integration
@pytest.mark.asyncio
async def test_premeet_pipeline_ranks_connections(isolated_store, demo_user_id):
    event = DetectedEvent(
        id="evt_premeet",
        user_id=demo_user_id,
        name="Test Event",
        event_type=EventType.EVENT,
        stage=LifecycleStage.BEFORE_MEET,
    )
    isolated_store.upsert_event(event)
    conn = PreMeetConnection(
        id="conn_pm",
        event_id=event.id,
        user_id=demo_user_id,
        name="Lead A",
        status=PreMeetStatus.SCORED,
        predicted_warmth=90,
        icp_score=85,
    )
    with patch.object(PreMeetPipeline, "run", new_callable=AsyncMock) as mock_run:
        mock_run.return_value = [conn]
        pipeline = PreMeetPipeline()
        ranked = await pipeline.run(event, manual_attendees=[], top_n=5)
    assert ranked[0].predicted_warmth == 90


@pytest.mark.integration
@pytest.mark.asyncio
async def test_postmeet_pipeline_draft_ready():
    lead = Lead(company_name="Acme", contact_name="Jane")
    signal = MeetingSignal(
        name="Jane",
        company="Acme",
        interests=["RevOps"],
        what_you_learned=["budget"],
    )
    pipeline = PostMeetPipeline(gmail_client=None)
    draft = await pipeline.send_followup(lead, signal)
    assert draft["status"] == "draft_ready"
    assert "gmail_compose_url" in draft
