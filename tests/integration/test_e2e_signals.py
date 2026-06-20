"""E2E smoke tests for the meet → Gmail handoff loop."""
from datetime import datetime, timezone

import pytest
from httpx import ASGITransport, AsyncClient

from warmth.apps.api.main import app


@pytest.fixture
def anyio_backend():
    return "asyncio"


@pytest.mark.asyncio
async def test_health():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.get("/health")
    assert res.status_code == 200
    assert res.json()["status"] == "healthy"


@pytest.mark.asyncio
async def test_captured_signal_ingest():
    """Xcode app payload → scoring + Gmail draft handoff."""
    payload = {
        "user": {"uid": "demo-user", "id_token": "test-token"},
        "session_id": "session-smoke-1",
        "captured_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "person": {"name": "Maya Chen", "org": "NorthWind Labs", "role": "VP RevOps"},
        "relations": [
            {"subject": "Maya", "predicate": "works_at", "object": "NorthWind Labs"}
        ],
        "interests": ["RevOps", "attribution"],
        "icp_keyword_score": 88,
        "transcript_excerpt": "Maya leads RevOps at NorthWind Labs rebuilding attribution this quarter.",
        "device": {"model": "iPhone", "os": "iOS 26.0"},
    }
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.post("/api/signals", json=payload)
    assert res.status_code == 202
    body = res.json()
    assert body["status"] == "accepted"
    assert body["handoff"] == "gmail_lightfern"
    assert body["gmail_draft"]["status"] == "draft_ready"
    assert "gmail_compose_url" in body["gmail_draft"]
    assert body["gmail_draft"]["body"].find("SCORES:") != -1


@pytest.mark.asyncio
async def test_meet_signals_endpoint():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.post(
            "/api/v1/meet/signals",
            json={
                "name": "Alex",
                "company": "Acme",
                "interests": ["revops"],
                "what_you_learned": ["budget Q3"],
                "most_interesting": "consolidating tools",
            },
        )
    assert res.status_code == 200
    body = res.json()
    assert "gmail_draft" in body
    assert body.get("handoff") == "gmail_lightfern"


@pytest.mark.asyncio
async def test_dashboard():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.get("/api/v1/dashboard")
    assert res.status_code == 200
    data = res.json()
    assert "connections" in data
    assert "events" in data
