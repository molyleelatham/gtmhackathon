"""Register warmth namespace and shared pytest fixtures."""

from __future__ import annotations

import importlib.util
import os
import sys
from pathlib import Path
from typing import AsyncIterator
from unittest.mock import patch

import pytest
from httpx import ASGITransport, AsyncClient

from packages.core.models.icp import ICPConfig

_REPO_ROOT = Path(__file__).resolve().parents[1]

# Stable test env for CI and local runs
os.environ.setdefault("REQUIRE_FIREBASE_AUTH", "false")
os.environ.setdefault("SEED_DEMO_DATA", "true")
os.environ.setdefault("USE_FIRESTORE_STORE", "false")


def _ensure_warmth_namespace() -> None:
    if "warmth" in sys.modules:
        return
    init = _REPO_ROOT / "__init__.py"
    spec = importlib.util.spec_from_file_location(
        "warmth",
        init,
        submodule_search_locations=[str(_REPO_ROOT)],
    )
    if spec is None or spec.loader is None:
        return
    module = importlib.util.module_from_spec(spec)
    sys.modules["warmth"] = module
    spec.loader.exec_module(module)


_ensure_warmth_namespace()


@pytest.fixture
def icp_config() -> ICPConfig:
    return ICPConfig()


@pytest.fixture
def demo_user_id() -> str:
    return "demo-user"


@pytest.fixture
def test_user_id() -> str:
    return "test-user"


@pytest.fixture
def auth_headers() -> dict[str, str]:
    return {"Authorization": "Bearer test-firebase-token"}


@pytest.fixture
def mock_firebase_verify(test_user_id: str):
    """Patch Firebase token verification to return a stable test user."""

    def _verify(token: str) -> dict:
        if token == "invalid":
            from fastapi import HTTPException, status

            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired Firebase ID token",
            )
        return {
            "uid": test_user_id,
            "email": "test@warmth.test",
            "sub": test_user_id,
        }

    with patch(
        "warmth.apps.api.middleware.auth_middleware.verify_firebase_id_token",
        side_effect=_verify,
    ):
        yield _verify


@pytest.fixture
def isolated_store(demo_user_id: str):
    """Fresh in-memory store per test; clears user store cache."""
    from warmth.apps.api.store import DemoStore, _user_stores
    from warmth.apps.api.user_context import current_user_id

    _user_stores.clear()
    current_user_id.set(demo_user_id)
    store = DemoStore(seed=True)
    _user_stores[demo_user_id] = store
    yield store
    _user_stores.clear()
    current_user_id.set(demo_user_id)


@pytest.fixture
async def api_client(isolated_store, demo_user_id: str) -> AsyncIterator[AsyncClient]:
    """httpx client against the full FastAPI app."""
    from warmth.apps.api.main import app
    from warmth.apps.api.user_context import current_user_id

    current_user_id.set(demo_user_id)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client


@pytest.fixture
def anyio_backend():
    return "asyncio"
