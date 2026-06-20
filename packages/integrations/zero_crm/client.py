import httpx
from typing import Optional, dict, Any
import os
from ..core.schemas.zero_crm_schema import ZeroCRMPayload


class ZeroCRMClient:
    """Client for Zero.inc CRM API"""
    
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