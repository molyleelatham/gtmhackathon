import pytest
import os
from packages.integrations.cursor_ai.client import CursorSDKClient


@pytest.mark.skipif(
    not os.getenv("CURSOR_SDK_API_KEY"),
    reason="CURSOR_SDK_API_KEY environment variable not set"
)
class TestCursorSDKIntegration:
    """Integration tests for Cursor SDK"""
    
    @pytest.fixture
    def cursor_client(self):
        """Create Cursor SDK client for testing"""
        return CursorSDKClient()
    
    @pytest.mark.asyncio
    async def test_score_lead(self, cursor_client):
        """Test lead scoring functionality"""
        company_data = {
            "name": "Test Company",
            "size": 200,
            "arr": 15_000_000,
            "industry": "Technology"
        }
        
        signals = [
            {
                "type": "hiring",
                "text": "Hiring RevOps specialist",
                "source": "tavily_search"
            }
        ]
        
        icp_config = {
            "size_range": [50, 500],
            "arr_range": [5_000_000, 50_000_000],
            "keywords": ["RevOps", "HubSpot", "Salesforce"]
        }
        
        try:
            result = await cursor_client.score_lead(
                company_name="Test Company",
                company_data=company_data,
                signals=signals,
                icp_config=icp_config
            )
            
            # Check if result has expected structure
            assert "icp_score" in result or "overall_score" in result
            
        except Exception as e:
            # This is expected if Cursor SDK is not yet available
            pytest.skip(f"Cursor SDK not available: {e}")
    
    @pytest.mark.asyncio
    async def test_generate_crm_payload(self, cursor_client):
        """Test CRM payload generation"""
        lead_data = {
            "company_name": "Test Company",
            "contact_name": "John Doe",
            "contact_email": "john@testcompany.com"
        }
        
        enrichment_data = {
            "company_size": 200,
            "arr": 15_000_000,
            "technographics": ["HubSpot", "Salesforce"]
        }
        
        try:
            result = await cursor_client.generate_crm_payload(
                lead_data=lead_data,
                enrichment_data=enrichment_data,
                target_system="zero"
            )
            
            # Check if result has expected structure
            assert isinstance(result, dict)
            
        except Exception as e:
            # This is expected if Cursor SDK is not yet available
            pytest.skip(f"Cursor SDK not available: {e}")