"""Canonical HubSpot contact schema — the merge point between Warmth's internal
models, the Zero CRM schema, and HubSpot custom properties.

This module is the single source of truth for:

  * the ``warmth_*`` custom contact properties (provisioned in HubSpot), and
  * how a ``ZeroCRMPayload`` / ``Lead`` maps onto those properties,

so a single lead syncs *identically* to both Zero CRM and HubSpot. The CSV
importer and the agent pipeline's HubSpot sync both consume this module instead
of redefining property names locally.

Field parity with ``ZeroCRMPayload`` (packages/core/schemas/zero_crm_schema.py):

    ZeroCRMPayload field   -> HubSpot property
    --------------------------------------------------
    contact_name           -> firstname / lastname   (standard)
    contact_email          -> email                   (standard)
    company_name           -> company                 (standard)
    company_size           -> warmth_company_size
    arr_usd                -> warmth_arr_usd
    funding_stage          -> warmth_funding_stage
    icp_score              -> warmth_icp_score
    buying_signals         -> warmth_buying_signals   (JSON)
    signal_source          -> warmth_signal_source
    tags                   -> warmth_tags             ("; " joined)
    personal_context       -> warmth_personal_context
    communication_style    -> warmth_communication_style ("; " joined)
    values                 -> warmth_values           ("; " joined)
    dominant_topic         -> warmth_dominant_topic
    pain_points            -> warmth_pain_points       ("; " joined)

Plus conference-CSV enrichment fields (warmth_fund, warmth_sector_focus, …).
"""

from __future__ import annotations

import json
from typing import TYPE_CHECKING, Any, Optional

if TYPE_CHECKING:  # avoid import cycle at runtime
    from ...core.models.lead import Lead
    from ...core.models.person import PersonNode
    from ...core.schemas.zero_crm_schema import ZeroCRMPayload

PROPERTY_GROUP = "warmth_enrichment"
PROPERTY_GROUP_LABEL = "Warmth Enrichment"

# Single source of truth for the custom contact properties. Order = display order.
CUSTOM_PROPERTIES: list[dict[str, Any]] = [
    # --- Conference / CSV enrichment ---------------------------------------
    {"name": "warmth_fund", "label": "Fund", "type": "string", "fieldType": "text"},
    {"name": "warmth_fund_description", "label": "Fund Description", "type": "string", "fieldType": "textarea"},
    {"name": "warmth_fund_size", "label": "Fund Size (Approx.)", "type": "string", "fieldType": "text"},
    {"name": "warmth_sector_focus", "label": "Sector Focus", "type": "string", "fieldType": "text"},
    {"name": "warmth_stage", "label": "Typical Stage", "type": "string", "fieldType": "text"},
    {
        "name": "warmth_classification",
        "label": "Warmth Classification",
        "type": "enumeration",
        "fieldType": "select",
        "options": [
            {"label": "Good Connection", "value": "Good Connection"},
            {"label": "Potential Investor", "value": "Potential Investor"},
            {"label": "Potential Customer", "value": "Potential Customer"},
            {"label": "Irrelevant", "value": "Irrelevant"},
        ],
    },
    {"name": "warmth_notes", "label": "Warmth Notes", "type": "string", "fieldType": "textarea"},
    # --- Parity with ZeroCRMPayload ----------------------------------------
    {"name": "warmth_company_size", "label": "Company Size", "type": "number", "fieldType": "number"},
    {"name": "warmth_arr_usd", "label": "ARR (USD)", "type": "number", "fieldType": "number"},
    {"name": "warmth_funding_stage", "label": "Funding Stage", "type": "string", "fieldType": "text"},
    {"name": "warmth_icp_score", "label": "ICP Score", "type": "number", "fieldType": "number"},
    {"name": "warmth_warmth_score", "label": "Warmth Score", "type": "number", "fieldType": "number"},
    {"name": "warmth_signal_source", "label": "Signal Source", "type": "string", "fieldType": "text"},
    {"name": "warmth_buying_signals", "label": "Buying Signals", "type": "string", "fieldType": "textarea"},
    {"name": "warmth_tags", "label": "Tags", "type": "string", "fieldType": "text"},
    # --- Per-person context (meet stage) -----------------------------------
    {"name": "warmth_personal_context", "label": "Personal Context", "type": "string", "fieldType": "textarea"},
    {"name": "warmth_communication_style", "label": "Communication Style", "type": "string", "fieldType": "text"},
    {"name": "warmth_values", "label": "Values", "type": "string", "fieldType": "text"},
    {"name": "warmth_dominant_topic", "label": "Dominant Topic", "type": "string", "fieldType": "text"},
    {"name": "warmth_pain_points", "label": "Pain Points", "type": "string", "fieldType": "textarea"},
]

# CSV column -> HubSpot property, for the conference importer.
CSV_COLUMN_MAP: dict[str, str] = {
    "Fund": "warmth_fund",
    "Fund Description": "warmth_fund_description",
    "Fund Size (Approx.)": "warmth_fund_size",
    "Sector Focus": "warmth_sector_focus",
    "Typical Stage": "warmth_stage",
    "Classification": "warmth_classification",
    "Notes": "warmth_notes",
}


def _join(values: Any) -> Optional[str]:
    if not values:
        return None
    if isinstance(values, (list, tuple, set)):
        return "; ".join(str(v) for v in values if v) or None
    return str(values)


def _num(value: Any) -> Optional[str]:
    # HubSpot property values are strings; numbers are sent as numeric strings.
    return None if value is None else str(value)


def split_name(full_name: Optional[str]) -> tuple[Optional[str], Optional[str]]:
    """Split a display name into (firstname, lastname) the way both CRMs expect."""
    if not full_name:
        return None, None
    parts = full_name.strip().split(" ", 1)
    return parts[0] or None, (parts[1] if len(parts) > 1 else None)


def zero_payload_to_hubspot_properties(payload: "ZeroCRMPayload") -> dict[str, str]:
    """Map a ``ZeroCRMPayload`` onto HubSpot contact properties.

    This is the schema merge: the exact same payload that goes to Zero CRM is
    projected onto HubSpot's standard + ``warmth_*`` properties, guaranteeing the
    two CRMs stay field-for-field consistent. Empty/None values are dropped.
    """
    firstname, lastname = split_name(payload.contact_name)
    candidate: dict[str, Optional[str]] = {
        "firstname": firstname,
        "lastname": lastname,
        "email": payload.contact_email,
        "company": payload.company_name,
        "warmth_company_size": _num(payload.company_size),
        "warmth_arr_usd": _num(payload.arr_usd),
        "warmth_funding_stage": payload.funding_stage,
        "warmth_icp_score": _num(payload.icp_score),
        "warmth_signal_source": payload.signal_source,
        "warmth_buying_signals": json.dumps(payload.buying_signals) if payload.buying_signals else None,
        "warmth_tags": _join(payload.tags),
        "warmth_personal_context": payload.personal_context,
        "warmth_communication_style": _join(payload.communication_style),
        "warmth_values": _join(payload.values),
        "warmth_dominant_topic": payload.dominant_topic,
        "warmth_pain_points": _join(payload.pain_points),
    }
    return {k: v for k, v in candidate.items() if v not in (None, "")}


class HubSpotMapper:
    """Map internal models to HubSpot contact properties.

    Parallel to ``ZeroCRMMapper`` so the agent pipeline can fan a single lead out
    to both CRMs through symmetric mappers.
    """

    @staticmethod
    def lead_to_contact_properties(
        lead: "Lead",
        person: "Optional[PersonNode]" = None,
        *,
        predicted_warmth: Optional[float] = None,
        conference_name: Optional[str] = None,
    ) -> dict[str, str]:
        """Convert a ``Lead`` (+ optional evolved person context) to HubSpot props.

        Routes through ``ZeroCRMMapper`` so HubSpot and Zero receive an identical
        field set, then layers on HubSpot-only extras (warmth score, conference).
        """
        from ...core.schemas.zero_crm_schema import ZeroCRMPayload  # noqa: F401
        from ..zero_crm.mapper import ZeroCRMMapper

        if person is not None:
            payload = ZeroCRMMapper.lead_to_zero_payload_with_context(lead, person)
        else:
            payload = ZeroCRMMapper.lead_to_zero_payload(lead)

        props = zero_payload_to_hubspot_properties(payload)
        if predicted_warmth is not None:
            props["warmth_warmth_score"] = _num(predicted_warmth)
        if conference_name:
            props["warmth_notes"] = f"Conference: {conference_name}"
        return props

    @staticmethod
    def lead_dict_to_contact_properties(lead: dict[str, Any]) -> dict[str, str]:
        """Map a PreMeetConnection-style dict (as used by ``sync_hot_leads``)."""
        firstname, lastname = split_name(lead.get("name"))
        candidate: dict[str, Optional[str]] = {
            "firstname": firstname,
            "lastname": lastname,
            "email": lead.get("email"),
            "jobtitle": lead.get("title"),
            "company": lead.get("company_name"),
            "warmth_funding_stage": lead.get("funding_stage"),
            "warmth_icp_score": _num(lead.get("icp_score")),
            "warmth_warmth_score": _num(lead.get("predicted_warmth")),
            "warmth_signal_source": lead.get("signal_source"),
            "warmth_buying_signals": (
                json.dumps(lead["buying_signals"]) if lead.get("buying_signals") else None
            ),
            "warmth_tags": _join(lead.get("tags")),
        }
        return {k: v for k, v in candidate.items() if v not in (None, "")}
