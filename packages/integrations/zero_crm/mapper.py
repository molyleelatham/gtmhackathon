from typing import Any, Optional

from ...core.models.lead import Lead
from ...core.models.person import PersonNode
from ...core.schemas.zero_crm_schema import ZeroCRMPayload


class ZeroCRMMapper:
    """Map internal Lead model to Zero CRM format"""

    @staticmethod
    def lead_to_zero_payload(lead: Lead) -> ZeroCRMPayload:
        """
        Convert internal Lead to Zero CRM payload format

        Args:
            lead: Internal lead model

        Returns:
            Zero CRM formatted payload
        """
        return ZeroCRMPayload(
            contact_name=lead.contact_name,
            contact_email=lead.contact_email,
            company_name=lead.company_name,
            company_size=lead.company_size,
            arr_usd=lead.arr_usd,
            funding_stage=lead.funding_stage,
            icp_score=lead.icp_score,
            buying_signals=lead.buying_signals,
            signal_source=lead.signal_source,
            tags=lead.tags
        )

    @staticmethod
    def lead_to_zero_payload_with_context(
        lead: Lead,
        person: Optional[PersonNode],
    ) -> ZeroCRMPayload:
        """Zero CRM payload enriched with the evolved per-person context.

        This is the Zero CRM push that carries:
          "Anna is analytical, data-driven, cares about accuracy. Dominant
           topic: pipeline visibility (0.8 weight). Recently learned HubSpot
           has AI forecasting. High pain intensity around manual data entry."
        """
        payload = ZeroCRMMapper.lead_to_zero_payload(lead)
        if person is None:
            return payload

        dominant = person.dominant_topic
        payload.personal_context = person.to_narrative()
        payload.communication_style = list(person.communication_style)
        payload.values = list(person.values)
        payload.dominant_topic = dominant[0] if dominant else None
        payload.pain_points = [f"{p.topic} ({p.level})" for p in person.pain_points]
        if person.name and not payload.contact_name:
            payload.contact_name = person.name
        return payload

    @staticmethod
    def enrich_lead_to_contact(enrichment_data: dict[str, Any]) -> dict[str, Any]:
        """
        Convert enrichment data to Zero CRM contact format

        Args:
            enrichment_data: Enriched lead data from UnifyGTM

        Returns:
            Zero CRM contact format
        """
        contacts = enrichment_data.get("contacts", [])
        if not contacts:
            return {}

        # Take the first contact as primary
        primary_contact = contacts[0]

        return {
            "name": primary_contact.get("name", ""),
            "email": primary_contact.get("email", ""),
            "title": primary_contact.get("title", ""),
            "linkedin": primary_contact.get("linkedin", ""),
            "phone": primary_contact.get("phone", ""),
            "company": enrichment_data.get("company_name", ""),
            "company_domain": enrichment_data.get("company_domain", "")
        }

    @staticmethod
    def lead_to_deal(lead: Lead, enrichment_data: dict[str, Any]) -> dict[str, Any]:
        """
        Convert lead to Zero CRM deal format

        Args:
            lead: Internal lead model
            enrichment_data: Enriched company data

        Returns:
            Zero CRM deal format
        """
        return {
            "deal_name": f"{lead.company_name} - GTM Opportunity",
            "company_name": lead.company_name,
            "value": lead.arr_usd or 0,
            "stage": "prospecting" if lead.icp_score < 70 else "qualification",
            "probability": min(lead.icp_score, 100),
            "close_date": None,  # Would be calculated based on sales cycle
            "description": f"ICP Score: {lead.icp_score}\nSignals: {len(lead.signals)}",
            "custom_fields": {
                "signal_source": lead.signal_source,
                "funding_stage": lead.funding_stage,
                "technographics": enrichment_data.get("technographics", []),
                "buying_signals": lead.buying_signals
            }
        }
