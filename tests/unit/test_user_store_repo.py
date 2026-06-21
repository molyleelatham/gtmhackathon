"""Unit tests for Firestore user store repository (mocked client)."""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import MagicMock

from warmth.infra.firebase import user_store_repo as repo_module
from warmth.infra.firebase.user_store_repo import UserStoreRepository

from packages.core.models.event import DetectedEvent, EventType, LifecycleStage
from packages.core.models.lead import Lead
from packages.core.models.pre_connection import PreMeetConnection, PreMeetStatus
from packages.core.models.warmth import WarmthBand, WarmthScore


def _mock_db():
    db = MagicMock()
    db.collection.return_value = db
    db.document.return_value = db
    db.stream.return_value = iter([])
    doc = MagicMock()
    doc.id = "x"
    doc.reference = db
    db.stream.return_value = iter([])
    db.get.return_value = MagicMock(exists=False, to_dict=lambda: {})
    db.batch.return_value = db
    db.set = MagicMock()
    db.delete = MagicMock()
    db.commit = MagicMock()
    return db


def test_save_event_writes_document():
    db = _mock_db()
    repo = UserStoreRepository(db)
    event = DetectedEvent(
        id="event_test",
        user_id="uid1",
        name="GTM Hackathon",
        event_type=EventType.EVENT,
        stage=LifecycleStage.BEFORE_MEET,
    )
    repo.save_event("uid1", event)
    db.collection.assert_called()


def test_load_into_empty_store():
    db = _mock_db()
    repo = UserStoreRepository(db)
    store = SimpleNamespace(
        events={},
        pre_connections={},
        warmth={},
        meet_results={},
        leads={},
        signal_index={},
        gtm_sync_results={},
        community_members=[],
    )
    repo.load_into(store, "uid1")
    assert store.events == {}
    assert store.pre_connections == {}


def test_persist_snapshot_commits_batch():
    db = _mock_db()
    repo = UserStoreRepository(db)
    event = DetectedEvent(
        id="event_gtm",
        user_id="uid1",
        name="GTM",
        event_type=EventType.EVENT,
        stage=LifecycleStage.BEFORE_MEET,
    )
    conn = PreMeetConnection(
        id="premeet_a",
        event_id="event_gtm",
        user_id="uid1",
        name="Alice",
        email="a@test.com",
        status=PreMeetStatus.SCORED,
    )
    warmth = WarmthScore(
        connection_id=conn.id,
        icp_score=80,
        warmth_score=75,
        band=WarmthBand.HOT,
    )
    store = SimpleNamespace(
        events={event.id: event},
        pre_connections={conn.id: conn},
        warmth={conn.id: warmth},
        meet_results={},
        leads={},
        signal_index={},
        gtm_sync_results={},
        community_members=[{"user_id": "a", "name": "Amir"}],
        list_events=lambda uid: [event],
        list_connections=lambda uid: [conn],
        list_leads=lambda: [],
        warmth_for_connection=lambda cid: warmth if cid == conn.id else None,
        meet_result_for=lambda cid: None,
        knowledge_graph_for=lambda cid: None,
    )
    repo.persist_snapshot("uid1", store)
    db.commit.assert_called()


def test_persist_snapshot_writes_leads_and_signal_index():
    db = _mock_db()
    repo = UserStoreRepository(db)
    event = DetectedEvent(
        id="event_gtm",
        user_id="uid1",
        name="GTM",
        event_type=EventType.EVENT,
        stage=LifecycleStage.BEFORE_MEET,
    )
    lead = Lead(
        id="lead_1",
        company_name="Acme",
        contact_name="Bob",
        contact_email="bob@test.com",
    )
    store = SimpleNamespace(
        events={event.id: event},
        pre_connections={},
        warmth={},
        meet_results={},
        leads={lead.id: lead},
        signal_index={"sig-abc": "premeet_a"},
        gtm_sync_results={},
        community_members=[],
        list_events=lambda uid: [event],
        list_connections=lambda uid: [],
        list_leads=lambda: [lead],
        warmth_for_connection=lambda cid: None,
        meet_result_for=lambda cid: None,
        knowledge_graph_for=lambda cid: None,
    )
    repo.persist_snapshot("uid1", store)
    assert db.set.call_count >= 3
    db.commit.assert_called()


def test_persist_snapshot_chunks_large_batches(monkeypatch):
    monkeypatch.setattr(repo_module, "_BATCH_LIMIT", 2)
    db = _mock_db()
    repo = UserStoreRepository(db)
    events = [
        DetectedEvent(
            id=f"event_{i}",
            user_id="uid1",
            name=f"Event {i}",
            event_type=EventType.EVENT,
            stage=LifecycleStage.BEFORE_MEET,
        )
        for i in range(5)
    ]
    store = SimpleNamespace(
        events={e.id: e for e in events},
        pre_connections={},
        warmth={},
        meet_results={},
        leads={},
        signal_index={},
        gtm_sync_results={},
        community_members=[],
        list_events=lambda uid: events,
        list_connections=lambda uid: [],
        list_leads=lambda: [],
        warmth_for_connection=lambda cid: None,
        meet_result_for=lambda cid: None,
        knowledge_graph_for=lambda cid: None,
    )
    repo.persist_snapshot("uid1", store)
    assert db.commit.call_count >= 2
