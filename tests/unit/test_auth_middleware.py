"""Tests for Firebase auth middleware."""

from unittest.mock import patch

import pytest


@pytest.mark.unit
@pytest.mark.asyncio
async def test_health_is_public(api_client):
    res = await api_client.get("/health")
    assert res.status_code == 200
    assert res.json()["status"] == "healthy"


@pytest.mark.unit
@pytest.mark.asyncio
async def test_options_bypasses_auth(api_client):
    res = await api_client.options("/api/v1/dashboard")
    assert res.status_code in (200, 204, 405)


@pytest.mark.unit
@pytest.mark.asyncio
async def test_require_auth_missing_token_returns_401(api_client, monkeypatch):
    monkeypatch.setenv("REQUIRE_FIREBASE_AUTH", "true")
    res = await api_client.get("/api/v1/leads")
    assert res.status_code == 401
    assert "Authorization required" in res.json()["detail"]


@pytest.mark.unit
@pytest.mark.asyncio
async def test_require_auth_invalid_token_returns_401(api_client, monkeypatch):
    monkeypatch.setenv("REQUIRE_FIREBASE_AUTH", "true")

    def _bad_verify(token: str):
        from fastapi import HTTPException, status

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired Firebase ID token",
        )

    with patch(
        "warmth.apps.api.middleware.auth_middleware.verify_firebase_id_token",
        side_effect=_bad_verify,
    ):
        res = await api_client.get(
            "/api/v1/leads",
            headers={"Authorization": "Bearer bad-token"},
        )
    assert res.status_code == 401


@pytest.mark.unit
@pytest.mark.asyncio
async def test_valid_token_sets_user_and_allows_request(
    api_client, auth_headers, mock_firebase_verify, monkeypatch, test_user_id
):
    monkeypatch.setenv("REQUIRE_FIREBASE_AUTH", "true")
    from warmth.apps.api.store import DemoStore, _user_stores
    from warmth.apps.api.user_context import current_user_id

    _user_stores.clear()
    _user_stores[test_user_id] = DemoStore(seed=False)
    current_user_id.set(test_user_id)

    res = await api_client.get("/api/v1/leads", headers=auth_headers)
    assert res.status_code == 200
    assert isinstance(res.json(), list)
