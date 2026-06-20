"""Rate limiting for POST /api/signals — reduces abuse of the public ingest path."""

from __future__ import annotations

import hashlib
import os
import time
from collections import defaultdict, deque
from typing import Deque

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse


def _env_int(name: str, default: int) -> int:
    raw = os.getenv(name, "").strip()
    if not raw:
        return default
    try:
        return max(1, int(raw))
    except ValueError:
        return default


def signal_rate_limit_enabled() -> bool:
    raw = os.getenv("SIGNAL_RATE_LIMIT_ENABLED", "true").lower()
    return raw not in ("0", "false", "no", "off")


def signal_rate_limit_ip_per_minute() -> int:
    return _env_int("SIGNAL_RATE_LIMIT_IP_PER_MINUTE", 30)


def signal_rate_limit_token_per_minute() -> int:
    return _env_int("SIGNAL_RATE_LIMIT_TOKEN_PER_MINUTE", 60)


class SlidingWindowRateLimiter:
    """In-memory sliding window limiter (per Cloud Run instance)."""

    def __init__(self, max_requests: int, window_seconds: int = 60) -> None:
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self._hits: dict[str, Deque[float]] = defaultdict(deque)

    def check(self, key: str) -> tuple[bool, int]:
        """Return (allowed, retry_after_seconds)."""
        now = time.monotonic()
        window_start = now - self.window_seconds
        bucket = self._hits[key]
        while bucket and bucket[0] <= window_start:
            bucket.popleft()
        if len(bucket) >= self.max_requests:
            retry_after = max(1, int(self.window_seconds - (now - bucket[0])) + 1)
            return False, retry_after
        bucket.append(now)
        return True, 0

    def reset(self) -> None:
        self._hits.clear()


_ip_limiter = SlidingWindowRateLimiter(signal_rate_limit_ip_per_minute())
_token_limiter = SlidingWindowRateLimiter(signal_rate_limit_token_per_minute())


def reset_signal_rate_limiters() -> None:
    """Test helper — clear in-memory counters."""
    _ip_limiter.reset()
    _token_limiter.reset()


def client_ip(request: Request) -> str:
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    if request.client and request.client.host:
        return request.client.host
    return "unknown"


def token_bucket_key(request: Request) -> str | None:
    header = request.headers.get("Authorization", "")
    if not header.startswith("Bearer "):
        return None
    token = header[7:].strip()
    if not token:
        return None
    digest = hashlib.sha256(token.encode("utf-8")).hexdigest()[:16]
    return f"tok:{digest}"


class SignalRateLimitMiddleware(BaseHTTPMiddleware):
    """429 when POST /api/signals exceeds per-IP or per-token quotas."""

    _SIGNAL_PATH = "/api/signals"

    async def dispatch(self, request: Request, call_next):
        if (
            not signal_rate_limit_enabled()
            or request.method != "POST"
            or request.url.path != self._SIGNAL_PATH
        ):
            return await call_next(request)

        ip_key = f"ip:{client_ip(request)}"
        allowed, retry_after = _ip_limiter.check(ip_key)
        if not allowed:
            return _too_many(retry_after, scope="ip")

        token_key = token_bucket_key(request)
        if token_key:
            allowed, retry_after = _token_limiter.check(token_key)
            if not allowed:
                return _too_many(retry_after, scope="token")

        return await call_next(request)


def _too_many(retry_after: int, *, scope: str) -> JSONResponse:
    return JSONResponse(
        status_code=429,
        headers={"Retry-After": str(retry_after)},
        content={
            "status": "error",
            "reason": "rate_limit_exceeded",
            "scope": scope,
            "retry_after_seconds": retry_after,
            "detail": "Too many signal uploads. Please wait before trying again.",
        },
    )
