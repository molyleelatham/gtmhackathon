"""Initialize the Firebase Admin SDK (Auth + Firestore)."""

from __future__ import annotations

import json
import os
from typing import Optional

import firebase_admin
from firebase_admin import credentials

from ...packages.core.secrets import resolve_project_id


def _certificate_from_key(key: str):
    """Parse a service account from a file path or JSON string; None if unusable."""
    trimmed = key.strip()
    if not trimmed:
        return None
    if os.path.exists(trimmed):
        return credentials.Certificate(trimmed)
    if trimmed.startswith("{"):
        try:
            return credentials.Certificate(json.loads(trimmed))
        except json.JSONDecodeError:
            return None
    return None


def ensure_firebase_initialized(service_account_key: Optional[str] = None) -> None:
    """Initialize Firebase Admin once per process.

    Resolution order:
    1. Explicit service account key (path or JSON string)
    2. ``FIREBASE_SERVICE_ACCOUNT_KEY`` env (path or JSON)
    3. Application Default Credentials on GCP (Cloud Run, GCE, local gcloud ADC)
    """
    if firebase_admin._apps:
        return

    key = service_account_key or os.getenv("FIREBASE_SERVICE_ACCOUNT_KEY")
    if key:
        cred = _certificate_from_key(key)
        if cred is not None:
            firebase_admin.initialize_app(cred)
            return

    project_id = resolve_project_id() or os.getenv("FIREBASE_PROJECT_ID")
    if project_id:
        firebase_admin.initialize_app(
            credentials.ApplicationDefault(),
            {"projectId": project_id},
        )
        return

    raise ValueError(
        "Firebase credentials not configured. Set FIREBASE_SERVICE_ACCOUNT_KEY "
        "or run on GCP with ADC (GCP_PROJECT_ID / GOOGLE_CLOUD_PROJECT)."
    )
