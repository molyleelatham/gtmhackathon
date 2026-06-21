"""Start API for E2E tests (no reload — keeps warmth namespace in-process)."""

from __future__ import annotations

import os

os.environ.setdefault("REQUIRE_FIREBASE_AUTH", "false")
os.environ.setdefault("SEED_DEMO_DATA", "true")
os.environ.setdefault("USE_FIRESTORE_STORE", "false")

from scripts.run_dev_api import _ensure_warmth_namespace

if __name__ == "__main__":
    _ensure_warmth_namespace()
    import uvicorn

    uvicorn.run(
        "warmth.apps.api.main:app",
        host="127.0.0.1",
        port=8000,
        reload=False,
    )
