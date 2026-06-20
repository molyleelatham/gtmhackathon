"""Contact sync lifecycle stage."""
from __future__ import annotations

from datetime import datetime
from typing import Any, Optional

from ...packages.core.models.pre_connection import PreMeetConnection, PreMeetStatus
from ...packages.integrations.hubspot.client import HubSpotClient
from ...packages.integrations.unify_gtm.client import UnifyGTMClient
from ...packages.integrations.zero_crm.client import ZeroCRMClient
from ...packages.ml.lead_scorer import LeadScorer
from ...packages.ml.warmth_model import WarmthModel


class ContactSyncPipeline:
    """Sync enriched attendees to HubSpot and Zero CRM."""

    def __init__(
        self,
        *,
        hubspot_client: Optional[HubSpotClient] = None,
        unify_client: Optional[UnifyGTMClient] = None,
        zero_client: Optional[ZeroCRMClient] = None,
        lead_scorer: Optional[LeadScorer] = None,
        warmth_model: Optional[WarmthModel] = None,
    ) -> None:
        self.hubspot_client = hubspot_client
        self.unify_client = unify_client
        self.zero_client = zero_client
        self.lead_scorer = lead_scorer or LeadScorer()
        self.warmth_model = warmth_model or WarmthModel()

    @staticmethod
    def _notes_list(raw: Any) -> list[str]:
        if raw is None:
            return []
        if isinstance(raw, list):
            return [str(x) for x in raw if x]
        text = str(raw).strip()
        return [text] if text else []

    @staticmethod
    def _split_name(name: Optional[str]) -> tuple[Optional[str], Optional[str]]:
        if not name:
            return None, None
        parts = name.strip().split(" ", 1)
        return parts[0] or None, (parts[1] if len(parts) > 1 else None)

    async def _enrich_unify(self, connection: PreMeetConnection) -> None:
        if not self.unify_client or not connection.company_name:
            return
        try:
            data = await self.unify_client.enrich_company(
                connection.company_name,
                connection.company_domain,
            )
        except Exception as exc:
            print(f"ContactSyncPipeline Unify enrich fallback: {exc}")
            return

        firmo = data.get("firmographics", data)
        connection.company_size = firmo.get("employee_count") or connection.company_size
        connection.industry = firmo.get("industry") or connection.industry
        connection.funding_stage = firmo.get("funding_stage") or connection.funding_stage
        connection.arr_usd = firmo.get("arr_usd") or connection.arr_usd
        connection.technographics = data.get("technographics", connection.technographics)

    async def _score_zero_icp(self, connection: PreMeetConnection) -> float:
        if self.zero_client:
            company_data = {
                "company_name": connection.company_name,
                "company_domain": connection.company_domain,
                "employee_count": connection.company_size,
                "industry": connection.industry,
                "funding_stage": connection.funding_stage,
                "arr_usd": connection.arr_usd,
                "technographics": connection.technographics,
            }
            try:
                response = await self.zero_client.score_icp_fit(company_data)
                return float(response.get("icp_score", 0.0))
            except Exception as exc:
                print(f"ContactSyncPipeline Zero ICP fallback: {exc}")
        return self.lead_scorer.score_icp_fit(connection)

    async def _hubspot_upsert(self, connection: PreMeetConnection) -> Optional[str]:
        if not self.hubspot_client:
            return None
        firstname, lastname = self._split_name(connection.name)
        try:
            existing = (
                await self.hubspot_client.find_contact_by_email(connection.email)
                if connection.email
                else None
            )
            if existing:
                hs_id = existing.get("id") or existing.get("properties", {}).get("hs_object_id")
                if hs_id:
                    await self.hubspot_client.update_contact(
                        str(hs_id),
                        {
                            "firstname": firstname,
                            "lastname": lastname,
                            "jobtitle": connection.title,
                            "company": connection.company_name,
                        },
                    )
                    return str(hs_id)
            return await self.hubspot_client.create_contact(
                firstname=firstname,
                lastname=lastname,
                email=connection.email,
                jobtitle=connection.title,
                company=connection.company_name,
            )
        except Exception as exc:
            print(f"ContactSyncPipeline HubSpot upsert fallback: {exc}")
            return None

    async def _zero_push(self, connection: PreMeetConnection, event_name: str) -> Optional[str]:
        if not self.zero_client or not connection.email:
            return None
        payload = {
            "name": connection.name,
            "email": connection.email,
            "title": connection.title,
            "linkedin": connection.linkedin,
            "company": connection.company_name,
            "company_domain": connection.company_domain,
            "notes": " | ".join(connection.research_notes),
            "event_name": event_name,
            "scores": {
                "icp_score": round(connection.icp_score, 2),
                "warmth_score": round(connection.predicted_warmth, 2),
                "intent_score": round(connection.intent_score, 2),
            },
            "enriched_at": datetime.utcnow().isoformat(),
        }
        try:
            existing = await self.zero_client.lookup_contact(connection.email)
            if existing:
                zero_id = existing.get("id") or existing.get("contact_id")
                if zero_id:
                    await self.zero_client.update_contact(str(zero_id), payload)
                    return str(zero_id)
            created = await self.zero_client.create_contact(payload)
            created_id = created.get("id") or created.get("contact_id")
            return str(created_id) if created_id else None
        except Exception as exc:
            print(f"ContactSyncPipeline Zero push fallback: {exc}")
            return None

    async def _hubspot_writeback(
        self,
        hubspot_contact_id: Optional[str],
        connection: PreMeetConnection,
        event_name: str,
        zero_contact_id: Optional[str],
    ) -> bool:
        if not self.hubspot_client or not hubspot_contact_id:
            return False

        notes = [f"Event: {event_name}"]
        if zero_contact_id:
            notes.append(f"Zero Contact ID: {zero_contact_id}")
        if connection.research_notes:
            notes.append("Research: " + " | ".join(connection.research_notes[:2]))
        if connection.linkedin:
            notes.append(f"LinkedIn: {connection.linkedin}")

        properties = {
            "warmth_icp_score": str(round(connection.icp_score, 2)),
            "warmth_warmth_score": str(round(connection.predicted_warmth, 2)),
            "warmth_notes": " | ".join(notes),
        }

        try:
            return await self.hubspot_client.update_contact(hubspot_contact_id, properties)
        except Exception as exc:
            print(f"ContactSyncPipeline HubSpot writeback fallback: {exc}")
            return False

    def _attendee_to_connection(
        self,
        attendee: dict[str, Any],
        *,
        event_id: str,
        event_name: str,
    ) -> PreMeetConnection:
        return PreMeetConnection(
            event_id=event_id,
            user_id="demo-user",
            name=attendee.get("name"),
            email=attendee.get("email"),
            title=attendee.get("title"),
            linkedin=attendee.get("linkedin"),
            company_name=attendee.get("company") or attendee.get("company_name") or event_name,
            company_domain=attendee.get("company_domain"),
            interests=attendee.get("interests") or [],
            research_notes=self._notes_list(attendee.get("research_notes")),
            source=attendee.get("source", "calendar+tavily"),
        )

    async def process_batch(
        self,
        attendees: list[dict[str, Any]],
        event_id: str,
        event_name: str,
    ) -> dict[str, Any]:
        """Run contact sync order for each attendee and return summary results."""
        connections: list[PreMeetConnection] = []
        hubspot_summary = {
            "event_name": event_name,
            "created": 0,
            "updated": 0,
            "failed": 0,
            "total": len(attendees),
            "contacts": [],
        }
        zero_summary = {"pushed": 0, "failed": 0}

        for attendee in attendees:
            conn = self._attendee_to_connection(
                attendee,
                event_id=event_id,
                event_name=event_name,
            )

            # 1) Unify enrich
            await self._enrich_unify(conn)

            # 2) Zero ICP score
            conn.icp_score = await self._score_zero_icp(conn)

            # 3) Warmth score
            conn.intent_score = self.lead_scorer.score_intent(conn)
            warmth = self.warmth_model.predict_pre_meet(conn)
            conn.predicted_warmth = warmth.predicted_score or 0.0
            conn.status = PreMeetStatus.SCORED
            conn.updated_at = datetime.utcnow()

            # 4) HubSpot upsert
            hs_existing = (
                await self.hubspot_client.find_contact_by_email(conn.email)
                if self.hubspot_client and conn.email
                else None
            )
            hs_id = await self._hubspot_upsert(conn)
            if hs_id:
                if hs_existing:
                    hubspot_summary["updated"] += 1
                else:
                    hubspot_summary["created"] += 1
            elif self.hubspot_client:
                hubspot_summary["failed"] += 1

            # 5) Zero push
            zero_id = await self._zero_push(conn, event_name)
            if zero_id:
                zero_summary["pushed"] += 1
            elif self.zero_client:
                zero_summary["failed"] += 1

            # 6) HubSpot writeback with enriched scores/linkedin/notes
            writeback_ok = await self._hubspot_writeback(hs_id, conn, event_name, zero_id)

            hubspot_summary["contacts"].append(
                {
                    "email": conn.email,
                    "hubspot_contact_id": hs_id,
                    "zero_contact_id": zero_id,
                    "writeback": writeback_ok,
                }
            )
            connections.append(conn)

        return {
            "connections": connections,
            "hubspot": hubspot_summary,
            "zero": zero_summary,
        }
