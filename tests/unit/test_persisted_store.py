"""Unit tests for FirestoreBackedStore with mocked repository."""

from unittest.mock import MagicMock

import pytest
from warmth.apps.api.persisted_store import FirestoreBackedStore
from warmth.packages.core.models.pre_connection import PreMeetConnection, PreMeetStatus


@pytest.mark.unit
def test_firestore_backed_upsert_connection_persists():
    repo = MagicMock()
    repo.load_into = MagicMock()
    store = FirestoreBackedStore("user-1", repo, seed=False)
    conn = PreMeetConnection(
        id="conn_persist",
        event_id="evt_1",
        user_id="user-1",
        name="Persist Test",
        status=PreMeetStatus.SCORED,
    )
    store.upsert_connection(conn)
    repo.save_connection.assert_called_once()
    assert store.get_connection("conn_persist") is not None


@pytest.mark.unit
def test_firestore_hydration_failure_without_data_continues():
    repo = MagicMock()
    repo.load_into.side_effect = RuntimeError("firestore down")
    store = FirestoreBackedStore("user-2", repo, seed=False)
    assert store.list_events("user-2") == []
