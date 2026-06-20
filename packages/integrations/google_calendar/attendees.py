"""Parse Google Calendar event attendees into pre-meet contact dicts."""
from __future__ import annotations

import re
from typing import Any, Optional

CONSUMER_DOMAINS = {
    "gmail.com",
    "googlemail.com",
    "hotmail.com",
    "yahoo.com",
    "outlook.com",
    "icloud.com",
    "me.com",
}


def _email_local_part(email: str) -> str:
    return email.split("@")[0] if "@" in email else email


def _email_domain(email: str) -> Optional[str]:
    return email.split("@")[-1].lower() if "@" in email else None


def email_to_display_name(email: str, display_name: Optional[str] = None) -> str:
    """Best-effort human name from calendar displayName or email local part."""
    if display_name and display_name.strip():
        return display_name.strip()

    local = re.sub(r"\d+", "", _email_local_part(email))
    parts = re.split(r"[._\-+]+", local)
    parts = [p for p in parts if p and not p.isdigit()]
    if len(parts) >= 2:
        return " ".join(p.capitalize() for p in parts)

    # e.g. nicholasyswong → keep title-cased local; Tavily can refine
    spaced = re.sub(r"([a-z])([A-Z])", r"\1 \2", local)
    spaced = re.sub(r"([a-z])([A-Z])", r"\1 \2", spaced.title())
    return spaced.title() if spaced else email


def company_from_email(email: str) -> tuple[Optional[str], Optional[str]]:
    """Return (company_name, company_domain) — skip consumer inboxes."""
    domain = _email_domain(email)
    if not domain or domain in CONSUMER_DOMAINS:
        return None, None
    slug = domain.split(".")[0]
    return slug.replace("-", " ").title(), domain


def calendar_attendees_from_raw(
    event_raw: dict,
    *,
    exclude_self: bool = True,
    exclude_emails: Optional[set[str]] = None,
) -> list[dict[str, Any]]:
    """Map Google Calendar API attendee objects to pre-meet attendee dicts."""
    skip = {e.lower() for e in (exclude_emails or set())}
    attendees: list[dict[str, Any]] = []

    for att in event_raw.get("attendees", []):
        email = (att.get("email") or "").strip()
        if not email:
            continue
        if exclude_self and att.get("self"):
            continue
        if email.lower() in skip:
            continue

        name = email_to_display_name(email, att.get("displayName"))
        company, company_domain = company_from_email(email)

        attendees.append(
            {
                "name": name,
                "email": email,
                "title": "Organizer" if att.get("organizer") else None,
                "company": company,
                "company_domain": company_domain,
                "response_status": att.get("responseStatus"),
                "source": "calendar",
            }
        )

    return attendees
