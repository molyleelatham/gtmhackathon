"""Client-safe error messages for production API responses."""

from __future__ import annotations

import os


def expose_internal_errors() -> bool:
    return os.getenv("EXPOSE_INTERNAL_ERRORS", "").lower() in ("1", "true", "yes")


def client_safe_message(exc: BaseException, *, fallback: str = "An internal error occurred.") -> str:
    """Return a generic message in deployed environments unless explicitly opted in."""
    if expose_internal_errors() or not os.getenv("GCP_PROJECT_ID"):
        return str(exc)
    return fallback
