"""Tests for Zero CRM mapper."""

import pytest

from packages.core.models.lead import Lead
from packages.core.models.person import PersonNode
from packages.integrations.zero_crm.mapper import ZeroCRMMapper


@pytest.mark.unit
def test_lead_to_zero_payload():
    lead = Lead(
        company_name="Acme",
        contact_name="Jane",
        contact_email="jane@acme.com",
        icp_score=80,
        tags=["revops"],
    )
    payload = ZeroCRMMapper.lead_to_zero_payload(lead)
    assert payload.company_name == "Acme"
    assert payload.contact_email == "jane@acme.com"
    assert payload.icp_score == 80


@pytest.mark.unit
def test_lead_to_zero_payload_with_person_context():
    lead = Lead(company_name="Acme", icp_score=70)
    person = PersonNode(speaker_id=1, name="Anna")
    person.topic_weights["pipeline"] = 0.8
    person.communication_style.append("analytical")
    payload = ZeroCRMMapper.lead_to_zero_payload_with_context(lead, person)
    assert payload.contact_name == "Anna"
    assert payload.dominant_topic == "pipeline"
    assert payload.personal_context
