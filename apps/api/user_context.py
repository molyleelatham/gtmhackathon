"""Request-scoped authenticated user id for API handlers."""

from __future__ import annotations

from contextvars import ContextVar

from .store import DEMO_USER_ID

current_user_id: ContextVar[str] = ContextVar("current_user_id", default=DEMO_USER_ID)


def get_user_id() -> str:
    return current_user_id.get()
