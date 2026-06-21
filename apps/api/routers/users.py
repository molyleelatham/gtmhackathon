"""User profile endpoints — bootstrap on sign-in and fetch persisted profile."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, status

from ...lifecycle.user_bootstrap import UserBootstrapService
from ..deps import get_firestore_client
from ..user_context import get_user_id

router = APIRouter(prefix="/api/v1/users", tags=["users"])


def _service() -> UserBootstrapService:
    return UserBootstrapService(get_firestore_client())


@router.get("/me")
async def get_me():
    """Return the authenticated user's Firestore profile."""
    uid = get_user_id()
    profile = await _service().get_profile(uid)
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Profile not found — call POST /bootstrap after sign-in",
        )
    return profile.model_dump(mode="json")


@router.post("/bootstrap")
async def bootstrap_profile():
    """Upsert profile from Firebase Auth and seed demo dashboard data."""
    uid = get_user_id()
    profile = await _service().bootstrap(uid)
    return profile.model_dump(mode="json")
