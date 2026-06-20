import os
import json
from typing import Optional, dict, Any
import httpx


class GoogleMCPClient:
    """Google MCP client for Gmail and Google Docs integration"""
    
    def __init__(self, credentials: Optional[str] = None):
        """
        Initialize Google MCP client
        
        Args:
            credentials: Google credentials JSON string or path to credentials file
        """
        self.credentials = credentials or os.getenv("GOOGLE_MCP_CREDENTIALS")
        
        if not self.credentials:
            raise ValueError("Google MCP credentials must be provided")
        
        # Load credentials
        if os.path.exists(self.credentials):
            with open(self.credentials, 'r') as f:
                self.creds_dict = json.load(f)
        else:
            self.creds_dict = json.loads(self.credentials)
        
        # MCP server configuration
        self.mcp_server_url = os.getenv("GOOGLE_MCP_SERVER_URL", "http://localhost:3000")
    
    async def create_email_draft(
        self,
        to: str,
        subject: str,
        body: str,
        cc: Optional[list[str]] = None,
        bcc: Optional[list[str]] = None
    ) -> dict[str, Any]:
        """
        Create an email draft in Gmail
        
        Args:
            to: Recipient email address
            subject: Email subject
            body: Email body (can be HTML)
            cc: Optional CC recipients
            bcc: Optional BCC recipients
        
        Returns:
            Draft information including draft ID
        """
        url = f"{self.mcp_server_url}/gmail/drafts"
        
        payload = {
            "to": to,
            "subject": subject,
            "body": body,
            "credentials": self.creds_dict
        }
        
        if cc:
            payload["cc"] = cc
        if bcc:
            payload["bcc"] = bcc
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(url, json=payload)
            response.raise_for_status()
            return response.json()
    
    async def send_email(
        self,
        to: str,
        subject: str,
        body: str,
        cc: Optional[list[str]] = None,
        bcc: Optional[list[str]] = None
    ) -> dict[str, Any]:
        """
        Send an email directly via Gmail
        
        Args:
            to: Recipient email address
            subject: Email subject
            body: Email body (can be HTML)
            cc: Optional CC recipients
            bcc: Optional BCC recipients
        
        Returns:
            Sent message information
        """
        url = f"{self.mcp_server_url}/gmail/send"
        
        payload = {
            "to": to,
            "subject": subject,
            "body": body,
            "credentials": self.creds_dict
        }
        
        if cc:
            payload["cc"] = cc
        if bcc:
            payload["bcc"] = bcc
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(url, json=payload)
            response.raise_for_status()
            return response.json()
    
    async def create_document(
        self,
        title: str,
        content: str,
        folder_id: Optional[str] = None
    ) -> dict[str, Any]:
        """
        Create a Google Doc
        
        Args:
            title: Document title
            content: Document content
            folder_id: Optional Google Drive folder ID
        
        Returns:
            Document information including document ID
        """
        url = f"{self.mcp_server_url}/docs/create"
        
        payload = {
            "title": title,
            "content": content,
            "credentials": self.creds_dict
        }
        
        if folder_id:
            payload["folder_id"] = folder_id
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(url, json=payload)
            response.raise_for_status()
            return response.json()
    
    async def append_to_document(
        self,
        document_id: str,
        content: str
    ) -> dict[str, Any]:
        """
        Append content to an existing Google Doc
        
        Args:
            document_id: Google Document ID
            content: Content to append
        
        Returns:
            Updated document information
        """
        url = f"{self.mcp_server_url}/docs/append"
        
        payload = {
            "document_id": document_id,
            "content": content,
            "credentials": self.creds_dict
        }
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(url, json=payload)
            response.raise_for_status()
            return response.json()