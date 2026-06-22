"""Unit tests for Tavily LinkedIn enrichment helpers."""
from packages.integrations.tavily.linkedin_enricher import (
    industry_from_text,
    interests_from_text,
    linkedin_url_from_results,
    parse_linkedin_headline,
)


def test_linkedin_url_from_results():
    rows = [
        {"url": "https://www.linkedin.com/in/jane-doe?trk=foo"},
        {"url": "https://example.com/jane"},
    ]
    assert linkedin_url_from_results(rows) == "https://www.linkedin.com/in/jane-doe"


def test_parse_linkedin_headline():
    parsed = parse_linkedin_headline(
        "Jane Doe - VP RevOps at Acme Corp | LinkedIn",
        "RevOps leader focused on GTM pipeline and HubSpot.",
    )
    assert parsed["name"] == "Jane Doe"
    assert parsed["title"] == "VP RevOps"
    assert parsed["company"] == "Acme Corp"
    assert parsed["industry"] in ("B2B SaaS", "GTM / SaaS")
    assert "Revops" in parsed["interests"] or "Gtm" in parsed["interests"]


def test_industry_from_text_fintech():
    assert industry_from_text("Payments and fintech platform for SMBs") == "Fintech"


def test_interests_merge_dedupes():
    merged = interests_from_text("saas revops", ["GTM", "RevOps"])
    assert len(merged) >= 2
    assert merged[0] == "GTM"
