import httpx
from typing import Optional, dict, Any
import os
from ..core.models.lead import Lead


class LightfernClient:
    """Client for Lightfern GTM workflow triggers"""
    
    def __init__(self, webhook_url: Optional[str] = None):
        self.webhook_url = webhook_url or os.getenv("LIGHTFERN_WEBHOOK_URL")
        
        if not self.webhook_url:
            print("Warning: LIGHTFERN_WEBHOOK_URL not set, workflow triggers disabled")
    
    async def trigger_workflow(
        self,
        lead: Lead,
        workflow_type: str = "gtm_outreach"
    ) -> dict[str, Any]:
        """
        Trigger a Lightfern GTM workflow for a lead
        
        Args:
            lead: Lead to trigger workflow for
            workflow_type: Type of workflow to trigger
        
        Returns:
            Workflow trigger response
        """
        if not self.webhook_url:
            print("Lightfern webhook URL not configured, skipping workflow trigger")
            return {"status": "skipped", "reason": "no_webhook_url"}
        
        payload = {
            "workflow_type": workflow_type,
            "lead": {
                "id": lead.id,
                "company_name": lead.company_name,
                "company_domain": lead.company_domain,
                "contact_name": lead.contact_name,
                "contact_email": lead.contact_email,
                "icp_score": lead.icp_score,
                "signal_source": lead.signal_source,
                "tags": lead.tags,
                "buying_signals": lead.buying_signals
            },
            "signals": [
                {
                    "type": signal.signal_type.value,
                    "raw_text": signal.raw_text,
                    "source": signal.source,
                    "keywords_hit": signal.keywords_hit,
                    "detected_at": signal.detected_at.isoformat()
                }
                for signal in lead.signals
            ]
        }
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    self.webhook_url,
                    json=payload
                )
                response.raise_for_status()
                return response.json()
        except Exception as e:
            print(f"Error triggering Lightfern workflow: {e}")
            return {
                "status": "error",
                "reason": str(e)
            }
    
    async def trigger_enrichment_workflow(
        self,
        lead_id: str,
        enrichment_data: dict[str, Any]
    ) -> dict[str, Any]:
        """
        Trigger enrichment workflow in Lightfern
        
        Args:
            lead_id: Internal lead ID
            enrichment_data: Enrichment data to process
        
        Returns:
            Workflow trigger response
        """
        if not self.webhook_url:
            return {"status": "skipped", "reason": "no_webhook_url"}
        
        payload = {
            "workflow_type": "enrichment",
            "lead_id": lead_id,
            "enrichment_data": enrichment_data
        }
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    self.webhook_url,
                    json=payload
                )
                response.raise_for_status()
                return response.json()
        except Exception as e:
            print(f"Error triggering enrichment workflow: {e}")
            return {
                "status": "error",
                "reason": str(e)
            }