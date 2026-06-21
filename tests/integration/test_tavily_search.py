import os

import pytest

from packages.integrations.tavily.client import TavilyClient


@pytest.mark.external
@pytest.mark.skipif(
    not os.getenv("TAVILY_API_KEY"),
    reason="TAVILY_API_KEY environment variable not set"
)
class TestTavilyIntegration:
    """Integration tests for Tavily API"""

    @pytest.fixture
    def tavily_client(self):
        """Create Tavily client for testing"""
        return TavilyClient()

    @pytest.mark.asyncio
    async def test_basic_search(self, tavily_client):
        """Test basic search functionality"""
        results = await tavily_client.search(
            query="RevOps hiring",
            max_results=3
        )

        assert "results" in results
        assert len(results["results"]) <= 3

        if results["results"]:
            first_result = results["results"][0]
            assert "title" in first_result
            assert "url" in first_result

    @pytest.mark.asyncio
    async def test_gtm_signals_search(self, tavily_client):
        """Test GTM signals search"""
        keywords = ["RevOps", "HubSpot", "Salesforce"]
        signals = await tavily_client.search_gtm_signals(keywords)

        assert isinstance(signals, list)

        for signal in signals:
            assert "title" in signal
            assert "url" in signal
            assert "content" in signal

    @pytest.mark.asyncio
    async def test_search_with_domains(self, tavily_client):
        """Test search with domain filtering"""
        results = await tavily_client.search(
            query="CRM software",
            include_domains=["hubspot.com", "salesforce.com"],
            max_results=5
        )

        assert "results" in results

        # Check if results are from specified domains
        for result in results["results"]:
            url = result.get("url", "")
            assert any(domain in url for domain in ["hubspot.com", "salesforce.com"])
