"""Shared API dependencies (Firestore client set at startup)."""

from __future__ import annotations

from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from ....infra.firebase.firestore import FirestoreClient

_firestore_client: Optional["FirestoreClient"] = None


def set_firestore_client(client: Optional["FirestoreClient"]) -> None:
    global _firestore_client
    _firestore_client = client


def get_firestore_client() -> Optional["FirestoreClient"]:
    return _firestore_client
