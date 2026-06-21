"""Rate limit tests for POST /api/signals."""

import pytest
from httpx import ASGITransport, AsyncClient
from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.routing import Route
from warmth.apps.api.middleware.signal_rate_limit import (
    SignalRateLimitMiddleware,
    SlidingWindowRateLimiter,
    reset_signal_rate_limiters,
)


async def _echo(_: Request) -> JSONResponse:
    return JSONResponse({"ok": True})


def _test_app() -> Starlette:
    app = Starlette(routes=[Route("/api/signals", _echo, methods=["POST"])])
    app.add_middleware(SignalRateLimitMiddleware)
    return app


@pytest.fixture(autouse=True)
def _reset_limiters(monkeypatch):
    reset_signal_rate_limiters()
    monkeypatch.setenv("SIGNAL_RATE_LIMIT_ENABLED", "true")
    monkeypatch.setenv("SIGNAL_RATE_LIMIT_IP_PER_MINUTE", "3")
    monkeypatch.setenv("SIGNAL_RATE_LIMIT_TOKEN_PER_MINUTE", "5")
    import warmth.apps.api.middleware.signal_rate_limit as rl

    rl._ip_limiter = SlidingWindowRateLimiter(3, 60)
    rl._token_limiter = SlidingWindowRateLimiter(5, 60)
    yield
    reset_signal_rate_limiters()


@pytest.mark.asyncio
async def test_signals_rate_limited_by_ip():
    transport = ASGITransport(app=_test_app())
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        for _ in range(3):
            res = await client.post("/api/signals", json={"session_id": "x"})
            assert res.status_code == 200

        blocked = await client.post("/api/signals", json={"session_id": "y"})
    assert blocked.status_code == 429
    body = blocked.json()
    assert body["reason"] == "rate_limit_exceeded"
    assert body["scope"] == "ip"
    assert blocked.headers.get("Retry-After")


def test_sliding_window_limiter():
    limiter = SlidingWindowRateLimiter(max_requests=2, window_seconds=60)
    assert limiter.check("k")[0] is True
    assert limiter.check("k")[0] is True
    allowed, retry = limiter.check("k")
    assert allowed is False
    assert retry >= 1
