"""Firebase ID token verification for API routes.

When REQUIRE_FIREBASE_AUTH=true, protected routes reject requests without a valid
Firebase ID token in the Authorization: Bearer header.

iOS already obtains tokens via FirebaseAuthService; web should wire Firebase Auth
before enabling this in production.
"""

from __future__ import annotations

import os
from typing import Optional

from fastapi import HTTPException, Request, status


def _auth_required() -> bool:
    return os.getenv("REQUIRE_FIREBASE_AUTH", "").lower() in ("1", "true", "yes")


def auth_required() -> bool:
    """Public helper for store seeding and route guards."""
    return _auth_required()


def verify_firebase_id_token(token: str) -> dict:
    """Verify a Firebase ID token; returns decoded claims."""
    import firebase_admin
    from firebase_admin import auth as firebase_auth

    if not firebase_admin._apps:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Firebase Auth not initialized",
        )
    try:
        return firebase_auth.verify_id_token(token)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired Firebase ID token",
        ) from exc


def bearer_token_from_request(request: Request) -> Optional[str]:
    header = request.headers.get("Authorization", "")
    if header.startswith("Bearer "):
        return header[7:].strip()
    return None


async def require_firebase_user(request: Request) -> dict:
    """FastAPI dependency: optional or required Firebase auth based on env."""
    token = bearer_token_from_request(request)
    if not token:
        if _auth_required():
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authorization required",
            )
        return {"uid": "demo-user", "auth": "anonymous"}
    return verify_firebase_id_token(token)


def authenticated_uid(user: dict) -> str:
    """Extract uid from verified Firebase claims or demo fallback."""
    return str(user.get("uid") or user.get("sub") or "demo-user")
