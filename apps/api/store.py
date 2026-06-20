"""In-memory demo store.

A lightweight, process-local data store seeded with sample data so the web
dashboard and API are demoable without Firebase or external credentials.

TODO: replace with FirestoreClient-backed repositories. The shape here mirrors
the domain models in packages/core/models.
"""
from datetime import datetime, timedelta
from typing import Any, Optional

from ...packages.core.models.event import DetectedEvent, EventType, LifecycleStage
from ...packages.core.models.pre_connection import PreMeetConnection, PreMeetStatus
from ...packages.core.models.lead import Lead
from ...packages.core.models.warmth import WarmthScore, WarmthBand


DEMO_USER_ID = "demo-user"


class DemoStore:
    def __init__(self):
        self.events: dict[str, DetectedEvent] = {}
        self.pre_connections: dict[str, PreMeetConnection] = {}
        self.leads: dict[str, Lead] = {}
        self.warmth: dict[str, WarmthScore] = {}
        self.community_members: list[dict] = []
        self.meet_results: dict[str, dict[str, Any]] = {}  # connection_id -> last meet result
        self.signal_index: dict[str, str] = {}  # ios signal uuid -> connection_id
        self._seed()

    # ------------------------------------------------------------------ #
    def _seed(self) -> None:
        now = datetime.utcnow()
        event = DetectedEvent(
            id="event_demo_saastr",
            user_id=DEMO_USER_ID,
            name="SaaStr Annual 2026",
            event_type=EventType.CONFERENCE,
            location="San Francisco, CA",
            start_date=now + timedelta(days=7),
            end_date=now + timedelta(days=9),
            confidence=0.9,
            stage=LifecycleStage.BEFORE_MEET,
            attendee_count=3,
        )
        self.events[event.id] = event

        seed_attendees = [
            {
                "name": "Maya Chen", "title": "VP RevOps", "company_name": "NorthWind Labs",
                "company_size": 220, "industry": "B2B SaaS", "funding_stage": "Series B",
                "interests": ["RevOps", "pipeline visibility", "attribution"],
                "icp": 88, "intent": 70, "warmth": 81, "band": WarmthBand.HOT,
            },
            {
                "name": "Diego Alvarez", "title": "Founder & CEO", "company_name": "Loophole",
                "company_size": 35, "industry": "DevTools", "funding_stage": "Series A",
                "interests": ["growth", "developer experience"],
                "icp": 64, "intent": 55, "warmth": 58, "band": WarmthBand.WARM,
            },
            {
                "name": "Priya Nair", "title": "Head of Sales Engineering", "company_name": "Quanta",
                "company_size": 480, "industry": "Fintech", "funding_stage": "Series C",
                "interests": ["Salesforce", "automation"],
                "icp": 76, "intent": 40, "warmth": 49, "band": WarmthBand.WARM,
            },
        ]
        for a in seed_attendees:
            conn = PreMeetConnection(
                event_id=event.id,
                user_id=DEMO_USER_ID,
                name=a["name"],
                title=a["title"],
                company_name=a["company_name"],
                company_size=a["company_size"],
                industry=a["industry"],
                funding_stage=a["funding_stage"],
                interests=a["interests"],
                icp_score=a["icp"],
                intent_score=a["intent"],
                predicted_warmth=a["warmth"],
                status=PreMeetStatus.SCORED,
                source="calendar",
            )
            self.pre_connections[conn.id] = conn
            self.warmth[conn.id] = WarmthScore(
                connection_id=conn.id,
                icp_score=a["icp"],
                warmth_score=a["warmth"],
                predicted_score=a["warmth"],
                band=a["band"],
            )

        self.community_members = [
            {"user_id": "founder_amir", "name": "Amir", "interests": ["RevOps", "AI", "GTM"]},
            {"user_id": "friend_sara", "name": "Sara", "interests": ["fintech", "automation"]},
            {"user_id": "founder_lena", "name": "Lena", "interests": ["developer experience", "growth"]},
        ]

    # ------------------------------------------------------------------ #
    def list_events(self, user_id: Optional[str] = None) -> list[DetectedEvent]:
        items = list(self.events.values())
        if user_id:
            items = [e for e in items if e.user_id == user_id]
        return items

    def get_event(self, event_id: str) -> Optional[DetectedEvent]:
        return self.events.get(event_id)

    def upsert_event(self, event: DetectedEvent) -> DetectedEvent:
        self.events[event.id] = event
        return event

    def connections_for_event(self, event_id: str) -> list[PreMeetConnection]:
        return [c for c in self.pre_connections.values() if c.event_id == event_id]

    def upsert_connection(self, conn: PreMeetConnection) -> PreMeetConnection:
        self.pre_connections[conn.id] = conn
        return conn

    def list_leads(self) -> list[Lead]:
        return list(self.leads.values())

    def upsert_lead(self, lead: Lead) -> Lead:
        self.leads[lead.id] = lead
        return lead

    def warmth_for_connection(self, connection_id: str) -> Optional[WarmthScore]:
        return self.warmth.get(connection_id)

    def upsert_warmth(self, score: WarmthScore) -> WarmthScore:
        key = score.connection_id or score.id
        self.warmth[key] = score
        return score

    def get_connection(self, connection_id: str) -> Optional[PreMeetConnection]:
        return self.pre_connections.get(connection_id)

    def record_meet_result(
        self,
        connection_id: str,
        signal_id: str,
        routed_to: str,
        narrative: Optional[str] = None,
        gmail_draft: Optional[dict] = None,
        outreach_sequence: Optional[dict] = None,
    ) -> None:
        self.meet_results[connection_id] = {
            "signal_id": signal_id,
            "routed_to": routed_to,
            "narrative": narrative,
            "gmail_draft": gmail_draft,
            "outreach_sequence": outreach_sequence,
            "recorded_at": datetime.utcnow().isoformat(),
        }
        self.signal_index[signal_id] = connection_id

    def meet_result_for(self, connection_id: str) -> Optional[dict[str, Any]]:
        return self.meet_results.get(connection_id)

    def upsert_lead_from_signal(
        self,
        payload: Any,
        connection_id: str,
        summary: dict[str, Any],
    ) -> Lead:
        lead = Lead(
            company_name=(
                payload.company.name if getattr(payload, "company", None)
                else payload.person.company or "Unknown Company"
            ),
            contact_name=payload.person.name,
            icp_score=int(payload.icp_pre_score),
            signal_source="conference_audio",
            tags=list(payload.person.icp_keywords_hit),
        )
        self.leads[lead.id] = lead
        return lead


# Process-local singleton for the demo.
store = DemoStore()
