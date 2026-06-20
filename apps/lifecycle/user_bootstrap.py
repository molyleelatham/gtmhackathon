"""Bootstrap Firestore user profiles and seed demo dashboard data on first sign-in."""

from __future__ import annotations

from datetime import datetime

from firebase_admin import auth as firebase_auth

from ...infra.firebase.firestore import FirestoreClient
from ...packages.core.models.user_profile import UserProfile
from ..api.store import get_store

# Demo dashboard roster (connections/events) is attached to this account only.
# Profile fields still come from Firebase Auth (Google name/photo/email).
OWNER_DEMO_EMAIL = "dzakwan1844@gmail.com"


class UserBootstrapService:
    """Upsert profile from Firebase Auth and ensure per-user demo roster."""

    def __init__(self, firestore: FirestoreClient | None) -> None:
        self.firestore = firestore

    async def bootstrap(self, uid: str) -> UserProfile:
        record = firebase_auth.get_user(uid)
        now = datetime.utcnow()
        existing = None
        if self.firestore:
            existing = await self.firestore.get_user_profile(uid)

        profile = UserProfile(
            uid=uid,
            email=record.email,
            display_name=record.display_name,
            photo_url=record.photo_url,
            demo_seeded=existing.demo_seeded if existing else False,
            created_at=existing.created_at if existing else now,
            updated_at=now,
        )

        # Profile always from Google Auth; demo roster only for the owner account.
        email = (record.email or "").lower()
        store = get_store(uid)
        if email == OWNER_DEMO_EMAIL.lower():
            store.ensure_user_seed(uid)
            profile.demo_seeded = True
        elif existing is None and not profile.demo_seeded:
            # Other Google accounts: empty dashboard until they add their own data.
            profile.demo_seeded = False

        if self.firestore:
            profile = await self.firestore.upsert_user_profile(profile)

        return profile

    async def get_profile(self, uid: str) -> UserProfile | None:
        if not self.firestore:
            return None
        return await self.firestore.get_user_profile(uid)
