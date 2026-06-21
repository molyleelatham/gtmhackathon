"""Unit tests for DemoStore."""

import pytest
from warmth.apps.api.store import DEMO_USER_ID, GTM_EVENT_ID, DemoStore
from warmth.packages.core.models.event import DetectedEvent, EventType, LifecycleStage
from warmth.packages.core.models.pre_connection import PreMeetConnection, PreMeetStatus
from warmth.packages.core.models.warmth import WarmthBand, WarmthScore


@pytest.mark.unit
def test_demo_store_seeds_gtm_event(isolated_store):
    events = isolated_store.list_events(DEMO_USER_ID)
    assert len(events) >= 1
    assert events[0].id == GTM_EVENT_ID


@pytest.mark.unit
def test_list_connections_scoped_by_user(isolated_store):
    all_conns = isolated_store.list_connections()
    demo_conns = isolated_store.list_connections(DEMO_USER_ID)
    assert len(demo_conns) == len(all_conns)
    assert len(demo_conns) >= 1

    other = DemoStore(seed=False)
    other.upsert_connection(
        PreMeetConnection(
            id="other_conn",
            event_id="evt_other",
            user_id="other-user",
            name="Other",
            status=PreMeetStatus.SCORED,
        )
    )
    assert len(other.list_connections(DEMO_USER_ID)) == 0


@pytest.mark.unit
def test_upsert_event_and_connection(isolated_store):
    event = DetectedEvent(
        id="evt_test",
        user_id=DEMO_USER_ID,
        name="Test Conf",
        event_type=EventType.EVENT,
        stage=LifecycleStage.BEFORE_MEET,
    )
    isolated_store.upsert_event(event)
    assert isolated_store.get_event("evt_test") is not None

    conn = PreMeetConnection(
        id="conn_test",
        event_id="evt_test",
        user_id=DEMO_USER_ID,
        name="Jane",
        status=PreMeetStatus.SCORED,
        predicted_warmth=75.0,
    )
    isolated_store.upsert_connection(conn)
    assert isolated_store.get_connection("conn_test") is not None
    assert len(isolated_store.connections_for_event("evt_test")) == 1


@pytest.mark.unit
def test_record_meet_result(isolated_store):
    conn_id = isolated_store.list_connections()[0].id
    isolated_store.record_meet_result(
        conn_id,
        signal_id="sig-1",
        routed_to="gmail",
        narrative="Great chat",
        interests=["RevOps"],
    )
    meet = isolated_store.meet_result_for(conn_id)
    assert meet is not None
    assert meet["routed_to"] == "gmail"
    assert "RevOps" in meet["interests"]


@pytest.mark.unit
def test_warmth_upsert(isolated_store):
    conn_id = isolated_store.list_connections()[0].id
    score = WarmthScore(
        connection_id=conn_id,
        icp_score=80,
        warmth_score=72.0,
        band=WarmthBand.HOT,
    )
    isolated_store.upsert_warmth(score)
    loaded = isolated_store.warmth_for_connection(conn_id)
    assert loaded is not None
    assert loaded.icp_score == 80
