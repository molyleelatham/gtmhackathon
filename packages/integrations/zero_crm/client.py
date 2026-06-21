import os
from typing import Any, Optional

import httpx

from ...core.schemas.zero_crm_schema import ZeroCRMPayload


class ZeroCRMClient:
    """Client for Zero.inc CRM API.

    Zero CRM owns the ICP definition and ICP fit scoring: the ICP profile and a
    company's ICP fit score are sourced FROM Zero (see ``get_icp_profile`` /
    ``score_icp_fit``). Zero is also the push destination for qualified leads
    (``create_lead`` / ``update_lead``). Enrichment (firmographics/technographics)
    comes from UnifyGTM, and warmth is built on top of Zero ICP fit + Unify
    enrichment by Warmth's own model (``packages/ml/warmth_model.py``).
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None
    ):
        self.api_key = api_key or os.getenv("ZERO_CRM_API_KEY")
        self.base_url = base_url or os.getenv("ZERO_CRM_BASE_URL", "https://api.zero.inc/v1")

        if not self.api_key:
            raise ValueError("ZERO_CRM_API_KEY environment variable must be set")

    async def create_lead(self, payload: ZeroCRMPayload) -> dict[str, Any]:
        """
        Create a new lead in Zero CRM

        Args:
            payload: Lead data in Zero CRM format

        Returns:
            Created lead response with CRM lead ID
        """
        url = f"{self.base_url}/leads"

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                url,
                json=payload.model_dump(),
                headers=headers
            )
            response.raise_for_status()
            return response.json()

    async def update_lead(
        self,
        lead_id: str,
        payload: dict[str, Any]
    ) -> dict[str, Any]:
        """
        Update an existing lead in Zero CRM

        Args:
            lead_id: Zero CRM lead ID
            payload: Updated lead data

        Returns:
            Updated lead response
        """
        url = f"{self.base_url}/leads/{lead_id}"

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.patch(
                url,
                json=payload,
                headers=headers
            )
            response.raise_for_status()
            return response.json()

    async def get_icp_profile(self) -> dict[str, Any]:
        """Fetch the ICP definition that Zero CRM owns.

        Zero is the source of truth for *what* a good-fit account looks like
        (firmographic ranges, target industries, personas, tech stack, etc.).
        Warmth consumes this profile rather than defining ICP locally.

        STUB: hits a plausible Zero endpoint with a graceful fallback so the
        pipeline still works offline. TODO: map the real Zero ICP schema.
        """
        url = f"{self.base_url}/icp/profile"

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(url, headers=headers)
                response.raise_for_status()
                return response.json()
        except Exception as e:  # pragma: no cover - stub resilience
            print(f"ZeroCRMClient.get_icp_profile stub fallback: {e}")
            # Placeholder ICP definition mirroring Zero's expected shape.
            return {
                "name": "Default ICP (stub)",
                "employee_count_range": [50, 1000],
                "arr_usd_range": [1_000_000, 100_000_000],
                "target_industries": ["SaaS", "Fintech", "Developer Tools"],
                "funding_stages": ["Series A", "Series B", "Series C"],
                "tech_stack": ["AWS", "Snowflake", "Segment"],
                "source": "stub",
            }

    async def score_icp_fit(self, company_data: dict[str, Any]) -> dict[str, Any]:
        """Score a company's ICP fit using Zero CRM's ICP model.

        Zero owns ICP fit scoring; Warmth passes the enriched company data
        (firmographics from UnifyGTM) to Zero and receives back a fit score.

        Args:
            company_data: Firmographic/technographic data for the company,
                typically populated by UnifyGTM enrichment.

        Returns:
            ``{"icp_score": float (0-100), "components": {...}}``.

        STUB: hits a plausible Zero endpoint with a graceful fallback. When Zero
        is unreachable, a heuristic placeholder score is returned so the offline
        demo still produces a usable signal. TODO: wire the real Zero scoring
        request/response schema.
        """
        url = f"{self.base_url}/icp/score"

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(url, json=company_data, headers=headers)
                response.raise_for_status()
                return response.json()
        except Exception as e:  # pragma: no cover - stub resilience
            print(f"ZeroCRMClient.score_icp_fit stub fallback: {e}")
            return self._heuristic_icp_fit(company_data)

    @staticmethod
    def _heuristic_icp_fit(company_data: dict[str, Any]) -> dict[str, Any]:
        """Offline placeholder for Zero's ICP fit score.

        Mirrors the rough shape of Zero's response so the pipeline keeps working
        without network access. NOT a substitute for Zero's real scoring model.
        """
        components: dict[str, float] = {}

        size = company_data.get("employee_count") or company_data.get("company_size")
        if isinstance(size, (int, float)):
            components["company_size"] = 40.0 if 50 <= size <= 1000 else 15.0

        arr = company_data.get("arr_usd")
        if isinstance(arr, (int, float)):
            components["arr"] = 30.0 if 1_000_000 <= arr <= 100_000_000 else 10.0

        if company_data.get("funding_stage") in {"Series A", "Series B", "Series C"}:
            components["funding_stage"] = 20.0

        tech = {str(t).lower() for t in company_data.get("technographics", [])}
        if tech & {"aws", "snowflake", "segment"}:
            components["tech_stack"] = 10.0

        score = min(100.0, sum(components.values()))
        return {"icp_score": round(score, 2), "components": components, "source": "stub"}

    async def lookup_contact(self, email: str) -> Optional[dict[str, Any]]:
        """
        Look up a contact by email in Zero CRM

        Args:
            email: Contact email address

        Returns:
            Contact data if found, None otherwise
        """
        url = f"{self.base_url}/contacts/lookup"

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        params = {"email": email}

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                url,
                params=params,
                headers=headers
            )

            if response.status_code == 404:
                return None

            response.raise_for_status()
            return response.json()

    async def create_contact(self, contact_data: dict[str, Any]) -> dict[str, Any]:
        """
        Create a new contact in Zero CRM

        Args:
            contact_data: Contact information

        Returns:
            Created contact response
        """
        url = f"{self.base_url}/contacts"

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                url,
                json=contact_data,
                headers=headers
            )
            response.raise_for_status()
            return response.json()

    async def update_contact(
        self, contact_id: str, contact_data: dict[str, Any]
    ) -> dict[str, Any]:
        """Update an existing contact in Zero CRM."""
        url = f"{self.base_url}/contacts/{contact_id}"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.patch(url, json=contact_data, headers=headers)
                response.raise_for_status()
                return response.json()
        except Exception as exc:
            print(f"ZeroCRMClient.update_contact fallback: {exc}")
            return {"id": contact_id, "status": "stubbed", **contact_data}
