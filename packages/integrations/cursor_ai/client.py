import os
from typing import Any, Optional

import httpx


class CursorSDKClient:
    """Client for Cursor SDK operations - AI-powered lead scoring and enrichment"""

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("CURSOR_SDK_API_KEY")
        self.base_url = "https://api.cursor.ai/v1"  # Placeholder URL
        if not self.api_key:
            raise ValueError("CURSOR_SDK_API_KEY environment variable must be set")

    async def score_lead(
        self,
        company_name: str,
        company_data: dict[str, Any],
        signals: list[dict[str, Any]],
        icp_config: dict[str, Any]
    ) -> dict[str, Any]:
        """
        Score a lead using Cursor SDK's AI capabilities

        Args:
            company_name: Name of the company
            company_data: Firmographic data about the company
            signals: List of buying signals detected
            icp_config: ICP configuration for scoring context

        Returns:
            Dictionary with score and breakdown
        """
        url = f"{self.base_url}/score"

        payload = {
            "company_name": company_name,
            "company_data": company_data,
            "signals": signals,
            "icp_config": icp_config
        }

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(url, json=payload, headers=headers)
            response.raise_for_status()
            return response.json()

    async def generate_crm_payload(
        self,
        lead_data: dict[str, Any],
        enrichment_data: dict[str, Any],
        target_system: str = "zero"
    ) -> dict[str, Any]:
        """
        Generate CRM payload using Cursor SDK's AI capabilities

        Args:
            lead_data: Basic lead information
            enrichment_data: Enriched data about the lead
            target_system: Target CRM system (zero, salesforce, etc.)

        Returns:
            Formatted CRM payload
        """
        url = f"{self.base_url}/generate-crm-payload"

        payload = {
            "lead_data": lead_data,
            "enrichment_data": enrichment_data,
            "target_system": target_system
        }

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(url, json=payload, headers=headers)
            response.raise_for_status()
            return response.json()

    async def analyze_signals(
        self,
        signals: list[dict[str, Any]],
        context: Optional[dict[str, Any]] = None
    ) -> dict[str, Any]:
        """
        Analyze signals using Cursor SDK to extract insights

        Args:
            signals: List of signals to analyze
            context: Additional context for analysis

        Returns:
            Analysis results with insights and recommendations
        """
        url = f"{self.base_url}/analyze-signals"

        payload = {
            "signals": signals,
            "context": context or {}
        }

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(url, json=payload, headers=headers)
            response.raise_for_status()
            return response.json()
