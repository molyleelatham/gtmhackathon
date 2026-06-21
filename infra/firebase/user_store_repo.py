"""Firestore persistence for per-user dashboard data (events, connections, meet results)."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Any, Optional

from google.cloud import firestore as gc_firestore

from ...packages.core.models.event import DetectedEvent
from ...packages.core.models.lead import Lead
from ...packages.core.models.pre_connection import PreMeetConnection
from ...packages.core.models.warmth import WarmthScore

if TYPE_CHECKING:
    from ...apps.api.store import DemoStore

COMMUNITY_DOC = "config/community_members"
MEET_DOC_ID = "latest"
_BATCH_LIMIT = 450


def _dump(model: Any) -> dict[str, Any]:
    if hasattr(model, "model_dump"):
        return model.model_dump(mode="json")
    return dict(model)


class _BatchWriter:
    """Accumulates Firestore batch writes and commits before the 500-op limit."""

    def __init__(self, db: gc_firestore.Client) -> None:
        self._db = db
        self._batch = db.batch()
        self._ops = 0
        self.commit_count = 0

    def set(self, ref: gc_firestore.DocumentReference, data: dict[str, Any], *, merge: bool = False) -> None:
        if merge:
            self._batch.set(ref, data, merge=True)
        else:
            self._batch.set(ref, data)
        self._flush_if_needed()

    def delete(self, ref: gc_firestore.DocumentReference) -> None:
        self._batch.delete(ref)
        self._flush_if_needed()

    def _flush_if_needed(self) -> None:
        self._ops += 1
        if self._ops >= _BATCH_LIMIT:
            self.commit()

    def commit(self) -> None:
        if self._ops == 0:
            return
        self._batch.commit()
        self.commit_count += 1
        self._batch = self._db.batch()
        self._ops = 0


class UserStoreRepository:
    """Low-level Firestore CRUD for a single user's dashboard slice."""

    def __init__(self, db: gc_firestore.Client) -> None:
        self.db = db

    def _user(self, uid: str) -> gc_firestore.DocumentReference:
        return self.db.collection("users").document(uid)

    def load_into(self, store: "DemoStore", uid: str) -> None:
        """Hydrate an in-memory DemoStore from Firestore."""
        user_ref = self._user(uid)

        for doc in user_ref.collection("events").stream():
            data = doc.to_dict() or {}
            event = DetectedEvent.model_validate(data)
            store.events[event.id] = event

        for doc in user_ref.collection("connections").stream():
            data = dict(doc.to_dict() or {})
            warmth_raw = data.pop("_warmth", None)
            conn = PreMeetConnection.model_validate(data)
            store.pre_connections[conn.id] = conn
            if warmth_raw:
                store.warmth[conn.id] = WarmthScore.model_validate(warmth_raw)
            meet_doc = doc.reference.collection("meet").document(MEET_DOC_ID).get()
            if meet_doc.exists:
                store.meet_results[conn.id] = meet_doc.to_dict() or {}

        for doc in user_ref.collection("leads").stream():
            lead = Lead.model_validate(doc.to_dict() or {})
            store.leads[lead.id] = lead

        for doc in user_ref.collection("signal_index").stream():
            payload = doc.to_dict() or {}
            conn_id = payload.get("connection_id")
            if conn_id:
                store.signal_index[doc.id] = conn_id

        meta = user_ref.collection("meta").document("dashboard").get()
        if meta.exists:
            payload = meta.to_dict() or {}
            store.gtm_sync_results = payload.get("gtm_sync_results") or {}

        store.community_members = self.load_community_members()

    def load_community_members(self) -> list[dict[str, Any]]:
        doc = self.db.document(COMMUNITY_DOC).get()
        if not doc.exists:
            return []
        payload = doc.to_dict() or {}
        members = payload.get("members")
        return list(members) if isinstance(members, list) else []

    def save_community_members(self, members: list[dict[str, Any]]) -> None:
        self.db.document(COMMUNITY_DOC).set({"members": members}, merge=True)

    def save_event(self, uid: str, event: DetectedEvent) -> None:
        self._user(uid).collection("events").document(event.id).set(_dump(event))

    def save_connection(
        self,
        uid: str,
        conn: PreMeetConnection,
        *,
        warmth: Optional[WarmthScore] = None,
    ) -> None:
        payload = _dump(conn)
        if warmth is not None:
            payload["_warmth"] = _dump(warmth)
        self._user(uid).collection("connections").document(conn.id).set(payload)

    def delete_connection(self, uid: str, connection_id: str) -> None:
        conn_ref = self._user(uid).collection("connections").document(connection_id)
        for meet in conn_ref.collection("meet").stream():
            meet.reference.delete()
        conn_ref.delete()

    def save_meet_result(self, uid: str, connection_id: str, payload: dict[str, Any]) -> None:
        (
            self._user(uid)
            .collection("connections")
            .document(connection_id)
            .collection("meet")
            .document(MEET_DOC_ID)
            .set(payload)
        )

    def save_signal_index(self, uid: str, signal_id: str, connection_id: str) -> None:
        self._user(uid).collection("signal_index").document(signal_id).set(
            {"connection_id": connection_id}
        )

    def signal_index_lookup(self, uid: str, signal_id: str) -> Optional[str]:
        doc = self._user(uid).collection("signal_index").document(signal_id).get()
        if not doc.exists:
            return None
        return (doc.to_dict() or {}).get("connection_id")

    def save_lead(self, uid: str, lead: Lead) -> None:
        self._user(uid).collection("leads").document(lead.id).set(_dump(lead))

    def save_dashboard_meta(self, uid: str, gtm_sync_results: dict[str, Any]) -> None:
        self._user(uid).collection("meta").document("dashboard").set(
            {
                "gtm_sync_results": gtm_sync_results,
                "updated_at": datetime.utcnow().isoformat(),
            },
            merge=True,
        )

    def persist_snapshot(self, uid: str, store: "DemoStore") -> None:
        """Write the full in-memory user slice (used after GTM roster refresh)."""
        writer = _BatchWriter(self.db)
        user_ref = self._user(uid)

        existing_events = {d.id for d in user_ref.collection("events").stream()}
        for event in store.list_events(uid):
            writer.set(user_ref.collection("events").document(event.id), _dump(event))
            existing_events.discard(event.id)
        for event_id in existing_events:
            writer.delete(user_ref.collection("events").document(event_id))

        existing_conns = {d.id for d in user_ref.collection("connections").stream()}
        for conn in store.list_connections(uid):
            payload = _dump(conn)
            warmth = store.warmth_for_connection(conn.id)
            if warmth is not None:
                payload["_warmth"] = _dump(warmth)
            writer.set(user_ref.collection("connections").document(conn.id), payload)
            existing_conns.discard(conn.id)
            meet = dict(store.meet_result_for(conn.id) or {})
            kg = store.knowledge_graph_for(conn.id) if hasattr(store, "knowledge_graph_for") else None
            if kg and not meet.get("knowledge_graph"):
                meet["knowledge_graph"] = kg.get("people") or []
            if meet:
                writer.set(
                    user_ref.collection("connections")
                    .document(conn.id)
                    .collection("meet")
                    .document(MEET_DOC_ID),
                    meet,
                )
        for conn_id in existing_conns:
            writer.delete(user_ref.collection("connections").document(conn_id))

        existing_leads = {d.id for d in user_ref.collection("leads").stream()}
        for lead in store.list_leads():
            writer.set(user_ref.collection("leads").document(lead.id), _dump(lead))
            existing_leads.discard(lead.id)
        for lead_id in existing_leads:
            writer.delete(user_ref.collection("leads").document(lead_id))

        existing_signals = {d.id for d in user_ref.collection("signal_index").stream()}
        for signal_id, connection_id in store.signal_index.items():
            writer.set(
                user_ref.collection("signal_index").document(signal_id),
                {"connection_id": connection_id},
            )
            existing_signals.discard(signal_id)
        for signal_id in existing_signals:
            writer.delete(user_ref.collection("signal_index").document(signal_id))

        if store.gtm_sync_results:
            writer.set(
                user_ref.collection("meta").document("dashboard"),
                {
                    "gtm_sync_results": store.gtm_sync_results,
                    "updated_at": datetime.utcnow().isoformat(),
                },
                merge=True,
            )

        writer.commit()
        if store.community_members:
            self.save_community_members(store.community_members)

    def user_has_events(self, uid: str) -> bool:
        docs = self._user(uid).collection("events").limit(1).stream()
        return any(True for _ in docs)
