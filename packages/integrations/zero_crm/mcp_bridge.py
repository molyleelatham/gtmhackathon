"""Zero CRM MCP Bridge.

This module wraps the Zero CRM MCP server tools (find_contacts, add_contact,
add_list, add_contacts_to_list, find_companies, add_company, add_note) into
async Python methods that the pre-meet pipeline can call directly.

Unlike the REST-based ``ZeroCRMClient``, this bridge is invoked by agent code
that has direct access to the MCP tool layer (e.g. the Cursor SDK agent loop or
a server-side agent runner).  The MCP tools are called through the agent
runtime's tool-calling mechanism rather than over HTTP.

Usage (inside an agent context that has MCP tools available)::

    bridge = ZeroMCPBridge(mcp_caller)
    contact_id = await bridge.upsert_contact(
        name="Maya Chen",
        email="maya@northwindlabs.com",
        title="VP RevOps",
        company_name="NorthWind Labs",
        icp_score=88,
        warmth_score=81,
        event_name="SaaStr 2026",
    )
    list_id = await bridge.get_or_create_hot_leads_list("SaaStr 2026 Hot Leads")
    await bridge.add_contacts_to_list(list_id, [contact_id])

The ``mcp_caller`` is any async callable with signature::

    async def mcp_caller(tool_name: str, arguments: dict) -> dict
"""

from __future__ import annotations

from typing import Any, Awaitable, Callable, Optional

MCPCaller = Callable[[str, dict], Awaitable[dict]]


class ZeroMCPBridge:
    """Thin async wrapper around Zero CRM MCP tools.

    Args:
        mcp_caller: Async function that calls a Zero MCP tool by name and
                    returns the parsed JSON response.  In the Cursor SDK agent
                    loop this is provided by the agent runtime.  In tests it
                    can be replaced with a mock.
        owner_id:   Zero CRM user UUID to assign as record owner.
                    Defaults to Moly's workspace user ID.
    """

    # Moly's Zero workspace user ID (from get_instructions metadata)
    DEFAULT_OWNER_ID = "789280d7-d436-4915-9c00-565127069c0e"

    # Pre-existing list IDs in the workspace
    LIST_QUALIFIED_LEADS = "41e23dbf-e82e-4c4d-b0f6-273b8c5b8c90"
    LIST_OUTREACH = "30870675-d18a-402f-b423-c8eeb8699d06"

    def __init__(
        self,
        mcp_caller: MCPCaller,
        owner_id: Optional[str] = None,
    ):
        self._call = mcp_caller
        self.owner_id = owner_id or self.DEFAULT_OWNER_ID

    # ------------------------------------------------------------------
    # Contacts
    # ------------------------------------------------------------------

    async def find_contact(self, email: str) -> Optional[dict[str, Any]]:
        """Look up a contact by email. Returns the first match or None."""
        result = await self._call("find_contacts", {"email": email, "limit": 1})
        rows = result.get("rows", [])
        return rows[0] if rows else None

    async def upsert_contact(
        self,
        name: str,
        *,
        email: Optional[str] = None,
        title: Optional[str] = None,
        linkedin: Optional[str] = None,
        company_name: Optional[str] = None,
        company_id: Optional[str] = None,
        icp_score: Optional[float] = None,
        warmth_score: Optional[float] = None,
        event_name: Optional[str] = None,
        list_ids: Optional[list[str]] = None,
    ) -> Optional[str]:
        """Create or find a contact in Zero CRM; return its UUID.

        If the contact already exists (matched by email) this is a no-op and
        returns the existing ID.  New contacts are added to the outreach list
        by default and to any extra ``list_ids`` provided.
        """
        # Try to find existing contact first
        if email:
            existing = await self.find_contact(email)
            if existing:
                return existing.get("id")

        # Build list memberships
        lists = list(list_ids or [])
        if self.LIST_OUTREACH not in lists:
            lists.append(self.LIST_OUTREACH)

        payload: dict[str, Any] = {
            "name": name,
            "ownerIds": [self.owner_id],
            "listIds": lists,
        }
        if email:
            payload["email"] = email
        if title:
            payload["title"] = title
        if linkedin:
            payload["linkedin"] = linkedin
        if company_id:
            payload["companyId"] = company_id

        result = await self._call("add_contact", payload)
        contact_id: Optional[str] = result.get("id") or (
            result.get("data", {}) or {}
        ).get("id")

        # Attach a note with scoring context
        if contact_id and (icp_score is not None or event_name):
            note_parts = []
            if event_name:
                note_parts.append(f"**Event:** {event_name}")
            if icp_score is not None:
                note_parts.append(f"**ICP Score:** {icp_score:.0f}/100")
            if warmth_score is not None:
                note_parts.append(f"**Warmth Score:** {warmth_score:.0f}/100")
            if note_parts:
                await self._call("add_note", {
                    "name": f"Pre-meet intel — {event_name or 'event'}",
                    "emoji": "🎯",
                    "content": "\n".join(note_parts),
                    "contactId": contact_id,
                })

        return contact_id

    # ------------------------------------------------------------------
    # Companies
    # ------------------------------------------------------------------

    async def find_company(
        self,
        name: Optional[str] = None,
        domain: Optional[str] = None,
    ) -> Optional[dict[str, Any]]:
        """Find a company by name or domain. Returns first match or None."""
        args: dict[str, Any] = {"limit": 1}
        if domain:
            args["domain"] = domain
        elif name:
            args["name"] = name
        else:
            return None
        result = await self._call("find_companies", args)
        rows = result.get("rows", [])
        return rows[0] if rows else None

    async def upsert_company(
        self,
        name: str,
        domain: Optional[str] = None,
        description: Optional[str] = None,
        list_ids: Optional[list[str]] = None,
    ) -> Optional[str]:
        """Find or create a company; return its UUID."""
        existing = await self.find_company(name=name, domain=domain)
        if existing:
            return existing.get("id")

        payload: dict[str, Any] = {
            "name": name,
            "ownerIds": [self.owner_id],
        }
        if domain:
            payload["domain"] = domain
        if description:
            payload["description"] = description
        if list_ids:
            payload["listIds"] = list_ids

        result = await self._call("add_company", payload)
        return result.get("id") or (result.get("data", {}) or {}).get("id")

    # ------------------------------------------------------------------
    # Lists
    # ------------------------------------------------------------------

    async def get_or_create_hot_leads_list(
        self,
        list_name: str,
        entity: str = "contacts",
    ) -> str:
        """Return an existing list UUID or create a new one."""
        # First check workspace lists already available
        meta = await self._call("get_workspace_metadata", {})
        for lst in (meta.get("lists") or {}).get(entity, []):
            if lst.get("name", "").lower() == list_name.lower():
                return lst["id"]

        # Create a new list
        result = await self._call("add_list", {
            "name": list_name,
            "entity": entity,
            "icon": "flame",
        })
        return result.get("id") or (result.get("data", {}) or {}).get("id")

    async def add_contacts_to_list(
        self,
        list_id: str,
        contact_ids: list[str],
    ) -> None:
        """Bulk-add contacts to a list."""
        if not contact_ids:
            return
        await self._call("add_contacts_to_list", {
            "listId": list_id,
            "contactIds": contact_ids,
        })

    # ------------------------------------------------------------------
    # Convenience: push a batch of scored leads
    # ------------------------------------------------------------------

    async def push_hot_leads(
        self,
        leads: list[dict[str, Any]],
        event_name: str,
        hot_leads_list_id: Optional[str] = None,
    ) -> list[str]:
        """Upsert a list of scored lead dicts into Zero CRM.

        Each lead dict should contain the keys produced by
        ``PreMeetPipeline.run()`` (i.e. PreMeetConnection.model_dump()).

        Returns the list of Zero contact UUIDs that were created/found.
        """
        if hot_leads_list_id is None:
            hot_leads_list_id = await self.get_or_create_hot_leads_list(
                f"{event_name} — Hot Leads"
            )

        contact_ids: list[str] = []
        for lead in leads:
            # Upsert company first so we can link the contact
            company_id: Optional[str] = None
            if lead.get("company_name"):
                company_id = await self.upsert_company(
                    name=lead["company_name"],
                    domain=lead.get("company_domain"),
                    list_ids=[self.LIST_QUALIFIED_LEADS],
                )

            contact_id = await self.upsert_contact(
                name=lead.get("name") or "Unknown",
                email=lead.get("email"),
                title=lead.get("title"),
                linkedin=lead.get("linkedin"),
                company_name=lead.get("company_name"),
                company_id=company_id,
                icp_score=lead.get("icp_score"),
                warmth_score=lead.get("predicted_warmth"),
                event_name=event_name,
                list_ids=[hot_leads_list_id],
            )
            if contact_id:
                contact_ids.append(contact_id)

        return contact_ids
