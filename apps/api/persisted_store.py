"""DemoStore with Firestore write-through persistence."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Optional

from infra.firebase.user_store_repo import UserStoreRepository
from apps.api.store import DemoStore
from packages.core.models.event import DetectedEvent
from packages.core.models.lead import Lead
from packages.core.models.pre_connection import PreMeetConnection
from packages.core.models.warmth import WarmthScore


class FirestoreBackedStore(DemoStore):
    """In-memory store that hydrates from and persists to Firestore."""

    def __init__(self, user_id: str, repo: UserStoreRepository, *, seed: bool = False) -> None:
        super().__init__(seed=False)
        self._owner_uid = user_id
        self._repo = repo
        try:
            self._repo.load_into(self, user_id)
        except Exception:
            pass
        if seed and not self.list_events(user_id):
            self._seed()

    def _persist_snapshot(self) -> None:
        self._repo.persist_snapshot(self._owner_uid, self)

    def refresh_gtm_hackathon(self, *args, **kwargs) -> DetectedEvent:
        event = super().refresh_gtm_hackathon(*args, **kwargs)
        self._persist_snapshot()
        return event

    def ensure_user_seed(self, user_id: str) -> None:
        if self.list_events(user_id):
            return
        super().ensure_user_seed(user_id)
        self._persist_snapshot()

    def upsert_event(self, event: DetectedEvent) -> DetectedEvent:
        out = super().upsert_event(event)
        self._repo.save_event(self._owner_uid, out)
        return out

    def upsert_connection(self, conn: PreMeetConnection) -> PreMeetConnection:
        out = super().upsert_connection(conn)
        self._repo.save_connection(
            self._owner_uid, out, warmth=self.warmth.get(conn.id)
        )
        return out

    def upsert_warmth(self, score: WarmthScore) -> WarmthScore:
        out = super().upsert_warmth(score)
        conn_id = score.connection_id or score.id
        conn = self.get_connection(conn_id)
        if conn:
            self._repo.save_connection(self._owner_uid, conn, warmth=out)
        return out

    def upsert_lead(self, lead: Lead) -> Lead:
        out = super().upsert_lead(lead)
        self._repo.save_lead(self._owner_uid, out)
        return out

    def record_meet_result(
        self,
        connection_id: str,
        signal_id: str,
        routed_to: str,
        narrative: Optional[str] = None,
        gmail_draft: Optional[dict] = None,
        outreach_sequence: Optional[dict] = None,
        *,
        interests: Optional[list[str]] = None,
        relations: Optional[list[dict]] = None,
        knowledge_graph: Optional[list[dict]] = None,
        matched_candidates: Optional[list[dict]] = None,
    ) -> None:
        super().record_meet_result(
            connection_id,
            signal_id,
            routed_to,
            narrative=narrative,
            gmail_draft=gmail_draft,
            outreach_sequence=outreach_sequence,
            interests=interests,
            relations=relations,
            knowledge_graph=knowledge_graph,
            matched_candidates=matched_candidates,
        )
        payload = self.meet_results.get(connection_id) or {}
        self._repo.save_meet_result(self._owner_uid, connection_id, payload)
        self._repo.save_signal_index(self._owner_uid, signal_id, connection_id)
        conn = self.get_connection(connection_id)
        if conn:
            self._repo.save_connection(
                self._owner_uid, conn, warmth=self.warmth.get(connection_id)
            )

    def record_knowledge_graph(
        self,
        connection_id: str,
        *,
        people: list[dict[str, Any]] | None = None,
        person: dict[str, Any] | None = None,
        narrative: str | None = None,
        signal: dict[str, Any] | None = None,
    ) -> None:
        super().record_knowledge_graph(
            connection_id,
            people=people,
            person=person,
            narrative=narrative,
            signal=signal,
        )
        kg = self.knowledge_graphs.get(connection_id)
        if kg:
            meet = dict(self.meet_results.get(connection_id) or {})
            meet["knowledge_graph"] = kg.get("people") or []
            if meet:
                self.meet_results[connection_id] = meet
                self._repo.save_meet_result(self._owner_uid, connection_id, meet)

    def upsert_lead_from_signal(
        self,
        payload: Any,
        connection_id: str,
        summary: dict[str, Any],
    ) -> Lead:
        lead = super().upsert_lead_from_signal(payload, connection_id, summary)
        self._repo.save_lead(self._owner_uid, lead)
        return lead
