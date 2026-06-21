"""Integration tests for /api/v1 routers."""

from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


@pytest.mark.integration
@pytest.mark.asyncio
async def test_list_events(api_client, isolated_store, demo_user_id):
    events = isolated_store.list_events(demo_user_id)
    assert len(events) >= 1
    res = await api_client.get("/api/v1/events")
    assert res.status_code == 200
    body = res.json()
    assert isinstance(body, list)
    assert len(body) >= 1


@pytest.mark.integration
@pytest.mark.asyncio
async def test_get_event(api_client, isolated_store):
    event_id = isolated_store.list_events()[0].id
    res = await api_client.get(f"/api/v1/events/{event_id}")
    assert res.status_code == 200
    assert res.json()["id"] == event_id


@pytest.mark.integration
@pytest.mark.asyncio
async def test_get_event_not_found(api_client):
    res = await api_client.get("/api/v1/events/nonexistent-event")
    assert res.status_code == 404


@pytest.mark.integration
@pytest.mark.asyncio
async def test_connect_onboarding(api_client):
    with patch("warmth.apps.api.routers.onboarding.OnboardingService") as mock_cls:
        service = MagicMock()
        service.connect = AsyncMock(return_value={"status": "connected"})
        service.discover_events = AsyncMock(return_value=[])
        mock_cls.return_value = service
        res = await api_client.post("/api/v1/connect")
    assert res.status_code == 200
    assert res.json()["status"] == "connected"


@pytest.mark.integration
@pytest.mark.asyncio
async def test_premeet_leads(api_client, isolated_store):
    event_id = isolated_store.list_events()[0].id
    res = await api_client.get(f"/api/v1/events/{event_id}/leads")
    assert res.status_code == 200
    leads = res.json()
    assert isinstance(leads, list)
    assert len(leads) >= 1


@pytest.mark.integration
@pytest.mark.asyncio
async def test_premeet_run(api_client, isolated_store):
    event_id = isolated_store.list_events()[0].id
    with patch("warmth.apps.lifecycle.premeet.PreMeetPipeline") as mock_cls:
        pipeline = MagicMock()
        conn = isolated_store.connections_for_event(event_id)[0]
        pipeline.run = AsyncMock(return_value=[conn])
        mock_cls.return_value = pipeline
        res = await api_client.post(
            f"/api/v1/events/{event_id}/premeet",
            json={"manual_attendees": [], "top_n": 5},
        )
    assert res.status_code == 200
    assert res.json()["event_id"] == event_id


@pytest.mark.integration
@pytest.mark.asyncio
async def test_meet_encode(api_client):
    res = await api_client.post(
        "/api/v1/meet/encode",
        json={
            "turns": [
                {"speaker": 0, "text": "Hi, I'm Amir."},
                {"speaker": 1, "text": "Nice to meet you, I'm Maya from NorthWind."},
            ],
            "self_speaker_id": 0,
            "speaker_attrs": {1: {"name": "Maya", "company": "NorthWind"}},
        },
    )
    assert res.status_code == 200
    body = res.json()
    assert "signal" in body
    assert "people" in body


@pytest.mark.integration
@pytest.mark.asyncio
async def test_meet_process(api_client, isolated_store):
    conns = isolated_store.list_connections()
    conn_id = conns[0].id
    res = await api_client.post(
        "/api/v1/meet/process",
        json={
            "turns": [{"speaker": 1, "text": "We are rebuilding attribution this quarter."}],
            "self_speaker_id": 0,
            "connection_id": conn_id,
            "speaker_attrs": {1: {"name": conns[0].name, "company": conns[0].company_name}},
        },
    )
    assert res.status_code == 200
    assert "gmail_draft" in res.json() or "routed_to" in res.json()


@pytest.mark.integration
@pytest.mark.asyncio
async def test_followup_draft(api_client, isolated_store):
    conn_id = isolated_store.list_connections()[0].id
    res = await api_client.post(
        f"/api/v1/connections/{conn_id}/followup",
        json={
            "name": "Maya",
            "company": "NorthWind",
            "interests": ["RevOps"],
            "what_you_learned": ["attribution rebuild"],
        },
    )
    assert res.status_code == 200
    body = res.json()
    assert body.get("status") == "draft_ready" or "gmail_compose_url" in body


@pytest.mark.integration
@pytest.mark.asyncio
async def test_dashboard_and_data_endpoints(api_client, isolated_store):
    res = await api_client.get("/api/v1/dashboard")
    assert res.status_code == 200
    dash = res.json()
    assert "connections" in dash

    res = await api_client.get("/api/v1/leads")
    assert res.status_code == 200

    res = await api_client.get("/api/v1/connections")
    assert res.status_code == 200
    connections = res.json()
    assert len(connections) >= 1

    conn_id = connections[0]["id"]
    res = await api_client.get(f"/api/v1/connections/{conn_id}")
    assert res.status_code == 200
    assert res.json()["connection"]["id"] == conn_id

    res = await api_client.get("/api/v1/community/members")
    assert res.status_code == 200

    res = await api_client.get("/api/v1/dashboard/roster")
    assert res.status_code == 200

    res = await api_client.get("/api/v1/integrations")
    assert res.status_code == 200
    assert isinstance(res.json(), list)

    res = await api_client.get("/api/v1/icp")
    assert res.status_code == 200


@pytest.mark.integration
@pytest.mark.asyncio
async def test_sync_gtm_hackathon(api_client):
    res = await api_client.post("/api/v1/dashboard/sync-gtm-hackathon")
    assert res.status_code == 200
    assert res.json()["status"] == "ok"


@pytest.mark.integration
@pytest.mark.asyncio
async def test_contacts_sync(api_client):
    with patch("warmth.apps.lifecycle.contact_sync.ContactSyncPipeline") as mock_cls:
        pipeline = MagicMock()
        pipeline.process_batch = AsyncMock(
            return_value={"connections": [], "hubspot": {}, "zero": {}}
        )
        mock_cls.return_value = pipeline
        res = await api_client.post("/api/v1/contacts/sync")
    assert res.status_code == 200
    assert res.json()["status"] == "ok"


@pytest.mark.integration
@pytest.mark.asyncio
async def test_match_attendee(api_client, isolated_store):
    conn = isolated_store.list_connections()[0]
    res = await api_client.post(
        "/api/v1/match/attendee",
        json={"name": conn.name or "Maya", "company": conn.company_name},
    )
    assert res.status_code == 200
    body = res.json()
    assert "matched" in body


@pytest.mark.integration
@pytest.mark.asyncio
async def test_users_bootstrap_and_me(
    api_client, auth_headers, mock_firebase_verify, test_user_id, monkeypatch
):
    from warmth.packages.core.models.user_profile import UserProfile

    profile = UserProfile(
        uid=test_user_id,
        email="test@warmth.test",
        display_name="Test User",
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )

    with patch(
        "warmth.apps.api.routers.users._service"
    ) as mock_service_factory:
        service = mock_service_factory.return_value
        service.bootstrap = AsyncMock(return_value=profile)
        service.get_profile = AsyncMock(return_value=profile)

        bootstrap = await api_client.post(
            "/api/v1/users/bootstrap", headers=auth_headers
        )
        assert bootstrap.status_code == 200
        assert bootstrap.json()["uid"] == test_user_id

        me = await api_client.get("/api/v1/users/me", headers=auth_headers)
        assert me.status_code == 200


@pytest.mark.integration
@pytest.mark.asyncio
async def test_users_me_not_found(api_client):
    with patch("warmth.apps.api.deps.get_firestore_client", return_value=None):
        res = await api_client.get("/api/v1/users/me")
    assert res.status_code == 404


@pytest.mark.integration
@pytest.mark.asyncio
async def test_event_runs(api_client):
    with patch("warmth.apps.agent.event_pipeline.EventPipeline") as mock_cls:
        pipeline = MagicMock()
        pipeline.run = AsyncMock(return_value={"ranked": [], "event": "Test Event"})
        mock_cls.return_value = pipeline
        res = await api_client.post(
            "/api/v1/event-runs/run",
            json={
                "event_name": "Test Event",
                "skip_scraping": True,
                "skip_research": True,
                "skip_email_drafts": True,
                "skip_zero_sync": True,
                "skip_hubspot_sync": True,
                "manual_attendees": [
                    {"name": "Alice", "email": "alice@test.com", "company": "Acme"}
                ],
            },
        )
    assert res.status_code == 200
    run_id = res.json()["run_id"]

    list_res = await api_client.get("/api/v1/event-runs/")
    assert list_res.status_code == 200

    get_res = await api_client.get(f"/api/v1/event-runs/{run_id}")
    assert get_res.status_code == 200


@pytest.mark.integration
@pytest.mark.asyncio
async def test_event_run_unsafe_url_rejected(api_client):
    res = await api_client.post(
        "/api/v1/event-runs/run",
        json={
            "event_name": "Bad URL Event",
            "directory_url": "file:///etc/passwd",
            "skip_scraping": False,
        },
    )
    assert res.status_code == 200
    body = res.json()
    assert body["status"] == "error"
