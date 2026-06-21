"""Firebase authentication middleware for the Warmth API."""

from __future__ import annotations

from fastapi import HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

from ....packages.core.auth import auth_required, bearer_token_from_request, verify_firebase_id_token
from ..store import DEMO_USER_ID
from ..user_context import current_user_id


class FirebaseAuthMiddleware(BaseHTTPMiddleware):
    """Verify Firebase ID tokens and scope requests to the caller's uid."""

    _PUBLIC_PATHS = frozenset({"/health"})

    async def dispatch(self, request: Request, call_next):
        if request.method == "OPTIONS" or request.url.path in self._PUBLIC_PATHS:
            if request.url.path in self._PUBLIC_PATHS:
                current_user_id.set(DEMO_USER_ID)
                request.state.firebase_user = None
            return await call_next(request)

        token = bearer_token_from_request(request)
        if token:
            try:
                claims = verify_firebase_id_token(token)
            except HTTPException as exc:
                return JSONResponse(
                    status_code=exc.status_code,
                    content={"detail": exc.detail},
                )
            uid = str(claims.get("uid") or claims.get("sub") or "")
            if not uid:
                return JSONResponse(
                    status_code=401,
                    content={"detail": "Invalid Firebase token (missing uid)"},
                )
            current_user_id.set(uid)
            request.state.firebase_user = claims
            return await call_next(request)

        if auth_required():
            return JSONResponse(
                status_code=401,
                content={"detail": "Authorization required"},
            )

        current_user_id.set(DEMO_USER_ID)
        request.state.firebase_user = None
        return await call_next(request)
