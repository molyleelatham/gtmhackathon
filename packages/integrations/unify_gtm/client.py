import httpx
from typing import Optional, dict, Any
import os


class UnifyGTMClient:
    """Client for UnifyGTM enrichment API"""
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None
    ):
        self.api_key = api_key or os.getenv("UNIFY_GTM_API_KEY")
        self.base_url = base_url or os.getenv("UNIFY_GTM_BASE_URL", "https://api.unifygtm.com/v1")
        
        if not self.api_key:
            raise ValueError("UNIFY_GTM_API_KEY environment variable must be set")
    
    async def enrich_company(
        self,
        company_name: str,
        company_domain: Optional[str] = None
    ) -> dict[str, Any]:
        """
        Enrich company data using UnifyGTM
        
        Args:
            company_name: Name of the company
            company_domain: Optional company domain for more accurate results
        
        Returns:
            Enriched company data including firmographics, technographics, funding
        """
        url = f"{self.base_url}/enrich"
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "company_name": company_name
        }
        
        if company_domain:
            payload["domain"] = company_domain
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                url,
                json=payload,
                headers=headers
            )
            response.raise_for_status()
            return response.json()
    
    async def find_contacts(
        self,
        company_name: str,
        company_domain: Optional[str] = None,
        titles: Optional[list[str]] = None
    ) -> list[dict[str, Any]]:
        """
        Find contacts at a company using UnifyGTM
        
        Args:
            company_name: Name of the company
            company_domain: Optional company domain
            titles: Optional list of job titles to filter by
        
        Returns:
            List of contacts with contact information
        """
        url = f"{self.base_url}/contacts"
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "company_name": company_name
        }
        
        if company_domain:
            payload["domain"] = company_domain
        
        if titles:
            payload["titles"] = titles
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                url,
                json=payload,
                headers=headers
            )
            response.raise_for_status()
            return response.json().get("contacts", [])
    
    async def get_company_funding(self, company_name: str) -> Optional[dict[str, Any]]:
        """
        Get funding information for a company
        
        Args:
            company_name: Name of the company
        
        Returns:
            Funding information if available
        """
        url = f"{self.base_url}/funding"
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "company_name": company_name
        }
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                url,
                json=payload,
                headers=headers
            )
            
            if response.status_code == 404:
                return None
            
            response.raise_for_status()
            return response.json()