"""HubSpot CRM client for Warmth's hot-leads list sync.

Pushes ranked conference leads to HubSpot as Contacts and creates/updates a
HubSpot Contact List so sales reps can pick them up immediately.

Auth: private-app token via HUBSPOT_API_KEY env var.
API base: https://api.hubapi.com

Endpoints used:
  POST /crm/v3/objects/contacts              – create contact
  POST /crm/v3/objects/contacts/search       – find existing by email
  PATCH /crm/v3/objects/contacts/{id}        – update contact
  POST /contacts/v1/lists                    – create static list
  POST /contacts/v1/lists/{listId}/add       – add contacts to list
  GET  /contacts/v1/lists/all/contacts/all   – find existing lists by name
"""

from __future__ import annotations

import os
from typing import Any, Optional
import httpx

from .schema import HubSpotMapper


class HubSpotClient:
    """HubSpot CRM integration for hot-leads sync.

    Args:
        api_key:  HubSpot private-app access token
                  (HUBSPOT_API_KEY env fallback).
    """

    BASE_URL = "https://api.hubapi.com"

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("HUBSPOT_API_KEY")
        if not self.api_key:
            raise ValueError("HUBSPOT_API_KEY environment variable must be set")

    def _headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

    # ------------------------------------------------------------------
    # Contacts
    # ------------------------------------------------------------------

    async def find_contact_by_email(self, email: str) -> Optional[dict[str, Any]]:
        """Return the first HubSpot contact matching *email*, or None."""
        url = f"{self.BASE_URL}/crm/v3/objects/contacts/search"
        payload = {
            "filterGroups": [{
                "filters": [{"propertyName": "email", "operator": "EQ", "value": email}]
            }],
            "properties": ["firstname", "lastname", "email", "jobtitle", "company", "hs_object_id"],
            "limit": 1,
        }
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                resp = await client.post(url, json=payload, headers=self._headers())
                resp.raise_for_status()
                results = resp.json().get("results", [])
                return results[0] if results else None
        except Exception as exc:
            print(f"HubSpotClient.find_contact_by_email error: {exc}")
            return None

    async def create_contact(
        self,
        *,
        firstname: Optional[str],
        lastname: Optional[str],
        email: Optional[str],
        jobtitle: Optional[str] = None,
        company: Optional[str] = None,
        website: Optional[str] = None,
        linkedin_bio: Optional[str] = None,
        icp_score: Optional[float] = None,
        warmth_score: Optional[float] = None,
        conference_name: Optional[str] = None,
        custom_properties: Optional[dict[str, Any]] = None,
    ) -> Optional[str]:
        """Create a HubSpot contact; return the HubSpot object ID.

        ``custom_properties`` carries the merged ``warmth_*`` schema properties
        (see ``packages/integrations/hubspot/schema.py``) so HubSpot contacts mirror
        the Zero CRM payload field-for-field.
        """
        props: dict[str, Any] = dict(custom_properties or {})
        if firstname:
            props["firstname"] = firstname
        if lastname:
            props["lastname"] = lastname
        if email:
            props["email"] = email
        if jobtitle:
            props["jobtitle"] = jobtitle
        if company:
            props["company"] = company
        if website:
            props["website"] = website
        if linkedin_bio:
            props["linkedin_bio"] = linkedin_bio
        # Store scores in standard HubSpot notes/description field
        notes_parts: list[str] = []
        if conference_name:
            notes_parts.append(f"Conference: {conference_name}")
        if icp_score is not None:
            notes_parts.append(f"ICP Score: {icp_score:.0f}/100")
        if warmth_score is not None:
            notes_parts.append(f"Warmth Score: {warmth_score:.0f}/100")
        if notes_parts:
            props["description"] = " | ".join(notes_parts)

        url = f"{self.BASE_URL}/crm/v3/objects/contacts"
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                resp = await client.post(
                    url, json={"properties": props}, headers=self._headers()
                )
                resp.raise_for_status()
                return resp.json().get("id")
        except httpx.HTTPStatusError as exc:
            if exc.response.status_code == 409:
                # Conflict: contact already exists — extract ID from error body
                err = exc.response.json()
                return err.get("message", "").split("Existing ID: ")[-1].strip() or None
            print(f"HubSpotClient.create_contact error: {exc}")
            return None
        except Exception as exc:
            print(f"HubSpotClient.create_contact error: {exc}")
            return None

    async def update_contact(
        self,
        contact_id: str,
        properties: dict[str, Any],
    ) -> bool:
        """Update an existing HubSpot contact by ID."""
        url = f"{self.BASE_URL}/crm/v3/objects/contacts/{contact_id}"
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                resp = await client.patch(
                    url, json={"properties": properties}, headers=self._headers()
                )
                resp.raise_for_status()
                return True
        except Exception as exc:
            print(f"HubSpotClient.update_contact error: {exc}")
            return False

    # ------------------------------------------------------------------
    # Lists
    # ------------------------------------------------------------------

    async def find_list_by_name(self, name: str) -> Optional[dict[str, Any]]:
        """Search static contact lists by name; return first match or None."""
        url = f"{self.BASE_URL}/contacts/v1/lists"
        params = {"count": 250}
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                resp = await client.get(url, params=params, headers=self._headers())
                resp.raise_for_status()
                lists = resp.json().get("lists", [])
                for lst in lists:
                    if lst.get("name", "").lower() == name.lower():
                        return lst
        except Exception as exc:
            print(f"HubSpotClient.find_list_by_name error: {exc}")
        return None

    async def create_static_list(self, name: str) -> Optional[str]:
        """Create a HubSpot static contact list; return its listId."""
        url = f"{self.BASE_URL}/contacts/v1/lists"
        payload = {"name": name, "dynamic": False, "portalId": None}
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                resp = await client.post(url, json=payload, headers=self._headers())
                resp.raise_for_status()
                return str(resp.json().get("listId"))
        except Exception as exc:
            print(f"HubSpotClient.create_static_list error: {exc}")
            return None

    async def get_or_create_list(self, name: str) -> Optional[str]:
        """Return an existing list ID or create a new static list."""
        existing = await self.find_list_by_name(name)
        if existing:
            return str(existing.get("listId"))
        return await self.create_static_list(name)

    async def add_contacts_to_list(
        self,
        list_id: str,
        hubspot_contact_ids: list[str],
    ) -> bool:
        """Add HubSpot contact IDs to a static list."""
        if not hubspot_contact_ids:
            return True
        url = f"{self.BASE_URL}/contacts/v1/lists/{list_id}/add"
        payload = {"vids": hubspot_contact_ids}
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                resp = await client.post(url, json=payload, headers=self._headers())
                resp.raise_for_status()
                return True
        except Exception as exc:
            print(f"HubSpotClient.add_contacts_to_list error: {exc}")
            return False

    # ------------------------------------------------------------------
    # High-level: sync a batch of scored leads
    # ------------------------------------------------------------------

    async def sync_hot_leads(
        self,
        leads: list[dict[str, Any]],
        conference_name: str,
        list_name: Optional[str] = None,
    ) -> dict[str, Any]:
        """Upsert all leads as HubSpot contacts and add to a dedicated list.

        Each lead dict should match the shape produced by
        ``PreMeetPipeline.run()`` (PreMeetConnection.model_dump()).

        Returns a summary dict with created/updated counts and the list ID.
        """
        list_name = list_name or f"{conference_name} — Hot Leads"
        list_id = await self.get_or_create_list(list_name)

        created = 0
        updated = 0
        failed = 0
        hs_ids: list[str] = []

        for lead in leads:
            # Merged schema: same field set HubSpot ↔ Zero CRM (see schema.py).
            props = HubSpotMapper.lead_dict_to_contact_properties(lead)
            if conference_name and "warmth_notes" not in props:
                props["warmth_notes"] = f"Conference: {conference_name}"
            if lead.get("company_domain"):
                props["website"] = f"https://{lead['company_domain']}"

            email = lead.get("email")
            existing = await self.find_contact_by_email(email) if email else None
            if existing:
                hs_id = existing.get("id") or existing.get("properties", {}).get("hs_object_id")
                if hs_id:
                    await self.update_contact(hs_id, props)
                    hs_ids.append(hs_id)
                    updated += 1
            else:
                hs_id = await self.create_contact(
                    firstname=props.pop("firstname", None),
                    lastname=props.pop("lastname", None),
                    email=email,
                    custom_properties=props,
                )
                if hs_id:
                    hs_ids.append(hs_id)
                    created += 1
                else:
                    failed += 1

        if list_id and hs_ids:
            await self.add_contacts_to_list(list_id, hs_ids)

        return {
            "list_id": list_id,
            "list_name": list_name,
            "created": created,
            "updated": updated,
            "failed": failed,
            "total": len(leads),
            "hubspot_ids": hs_ids,
        }
