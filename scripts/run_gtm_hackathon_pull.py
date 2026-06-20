#!/usr/bin/env python3
"""GTM Hackathon pull — calendar attendees only + Tavily (LinkedIn / Google).

Does NOT merge the investor CSV. Uses only invitees on the GTM Hackathon
London calendar event, enriches each via Tavily, then runs pre-meet drafts.

Usage:
  make run-gmail-mcp
  PYTHONPATH=. warmth/.venv/bin/python warmth/scripts/run_gtm_hackathon_pull.py
"""
from __future__ import annotations

import asyncio
import json
import os
import re
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Optional

from dotenv import load_dotenv

REPO_ROOT = Path(__file__).resolve().parents[2]
WARMTH_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))
load_dotenv(WARMTH_ROOT / ".env")

from warmth.apps.api.integration_helpers import (  # noqa: E402
    gmail_client_optional,
    hubspot_client_optional,
    unify_client_optional,
    zero_client_optional,
    warmth_client_email,
    warmth_client_name,
)
from warmth.apps.lifecycle.contact_sync import ContactSyncPipeline  # noqa: E402
from warmth.apps.lifecycle.premeet import PreMeetPipeline  # noqa: E402
from warmth.packages.core.models.event import DetectedEvent, EventType, LifecycleStage  # noqa: E402
from warmth.packages.integrations.google_calendar.attendees import calendar_attendees_from_raw  # noqa: E402
from warmth.packages.integrations.google_calendar.client import GoogleCalendarClient  # noqa: E402
from warmth.packages.integrations.tavily.client import TavilyClient  # noqa: E402

sys.path.insert(0, str(WARMTH_ROOT / "scripts"))
from run_premeet_e2e import _render_briefing  # noqa: E402

GTM_HINTS = ("gtm", "hackathon")
TOP_N = 10


def _pick_gtm_event(events: list) -> tuple[Any, dict]:
    for ev in events:
        if any(h in (ev.title or "").lower() for h in GTM_HINTS):
            return ev, ev.raw or {}
    if not events:
        raise SystemExit("No calendar events found.")
    return events[0], events[0].raw or {}


def _linkedin_from_results(results: list[dict]) -> Optional[str]:
    for r in results:
        url = (r.get("url") or "").split("?")[0]
        if "linkedin.com/in/" in url.lower():
            return url
    return None


async def tavily_enrich(tavily: TavilyClient, att: dict[str, Any]) -> dict[str, Any]:
    name = att.get("name") or ""
    email = att.get("email") or ""
    company = att.get("company") or ""

    queries = [
        f'"{name}" site:linkedin.com/in',
        f'"{name}" {email.split("@")[0]} GTM hackathon London',
        f'"{name}" Google GTM conference intelligence',
    ]

    linkedin: Optional[str] = None
    snippets: list[str] = []
    interests: list[str] = []

    for q in queries:
        try:
            res = await tavily.search(q, search_depth="basic", max_results=5)
            for row in res.get("results", []):
                if not linkedin:
                    linkedin = _linkedin_from_results([row])
                text = f"{row.get('title', '')} {row.get('content', '')}".strip()
                if text and text not in snippets:
                    snippets.append(text[:280])
                for kw in ("gtm", "revops", "saas", "conference", "crm", "ai"):
                    if kw in text.lower() and kw not in interests:
                        interests.append(kw)
        except Exception as exc:
            print(f"      Tavily warn ({name}): {exc}")

    # Refine name from LinkedIn title if we got a hit
    if linkedin and snippets:
        m = re.search(r"([A-Z][a-z]+(?: [A-Z][a-z]+)+)", snippets[0])
        if m:
            name = m.group(1)

    notes = " | ".join(snippets[:2])
    if linkedin:
        notes = (notes + " | " if notes else "") + f"LinkedIn: {linkedin}"

    return {
        **att,
        "name": name,
        "linkedin": linkedin,
        "interests": interests[:5] or ["GTM", "hackathon"],
        "research_notes": notes or f"GTM Hackathon London invitee ({email})",
        "source": "calendar+tavily",
    }


async def run() -> dict[str, Any]:
    print("\n" + "=" * 60)
    print("  GTM HACKATHON PULL (calendar-only + Tavily)")
    print("=" * 60 + "\n")

    cal = GoogleCalendarClient()
    now = datetime.now(timezone.utc)
    events = await cal.list_events(
        time_min=now.replace(tzinfo=None),
        time_max=(now + timedelta(days=60)).replace(tzinfo=None),
    )
    cal_ev, raw = _pick_gtm_event(events)

    # Real invitees only — exclude Warmth bot inbox from attendee list
    warmth_inbox = warmth_client_email().lower()
    attendees = calendar_attendees_from_raw(
        raw,
        exclude_emails={warmth_inbox},
    )

    print(f"[1/5] Calendar: {cal_ev.title}")
    print(f"      Location: {cal_ev.location}")
    print(f"      Invitees ({len(attendees)}):")
    for a in attendees:
        print(f"        • {a['name']} <{a['email']}>")

    print("[2/5] Tavily enrichment (LinkedIn + Google)…")
    tavily = TavilyClient()
    enriched = await asyncio.gather(*[tavily_enrich(tavily, a) for a in attendees])
    for a in enriched:
        print(f"        → {a['name']}: {a.get('linkedin') or 'no LinkedIn'}")

    out_dir = WARMTH_ROOT / "data"
    out_dir.mkdir(exist_ok=True)
    out_path = out_dir / "gtm_hackathon_attendees.json"
    out_path.write_text(json.dumps(enriched, indent=2))
    print(f"      Saved → {out_path}")

    event = DetectedEvent(
        id="event_gtm_hackathon_london",
        user_id="demo-user",
        calendar_event_id=cal_ev.external_id,
        name=cal_ev.title,
        event_type=EventType.CONFERENCE,
        location=cal_ev.location,
        start_date=cal_ev.start_time,
        end_date=cal_ev.end_time,
        confidence=1.0,
        stage=LifecycleStage.BEFORE_MEET,
        attendee_count=len(enriched),
    )

    print("[3/5] Contact sync pipeline…")
    contact_sync = ContactSyncPipeline(
        hubspot_client=hubspot_client_optional(),
        unify_client=unify_client_optional(),
        zero_client=zero_client_optional(),
    )
    sync_result = await contact_sync.process_batch(
        attendees=enriched,
        event_id=event.id,
        conference_name=event.name,
    )
    synced_connections = sync_result["connections"]
    hubspot_result = sync_result.get("hubspot", {})
    print(
        f"      Contact sync: {len(synced_connections)} attendees | "
        f"HubSpot {hubspot_result.get('created', 0)} created, "
        f"{hubspot_result.get('updated', 0)} updated"
    )

    print("[4/5] Pre-meet pipeline…")
    pipeline = PreMeetPipeline(
        unify_client=unify_client_optional(),
        zero_client=zero_client_optional(),
        gmail_client=gmail_client_optional(),
    )
    top = await pipeline.run(event, manual_attendees=enriched, top_n=min(TOP_N, len(enriched)))

    print("[5/5] Briefing draft…")
    gmail = gmail_client_optional()
    briefing_id = None
    if gmail:
        subj, body = _render_briefing(event, top, client_name=warmth_client_name())
        body += "\n\nATTENDEES (from calendar — not CSV)\n"
        for a in enriched:
            body += f"  • {a['name']} <{a['email']}>\n"
            if a.get("linkedin"):
                body += f"    LinkedIn: {a['linkedin']}\n"
        draft = await gmail.create_email_draft(to=warmth_client_email(), subject=subj, body=body)
        briefing_id = draft.get("id")

    print("\n" + "=" * 60)
    print("  Done")
    print("=" * 60 + "\n")

    # Sync dashboard store for web UI
    from warmth.apps.api.store import store

    store.refresh_gtm_hackathon(
        enriched,
        premeet_results=top,
        sync_results=sync_result,
    )
    print("      Dashboard store updated")

    return {
        "event": event.name,
        "attendees": enriched,
        "top_leads": [c.model_dump() for c in top],
        "briefing_draft_id": briefing_id,
        "hubspot": hubspot_result,
        "file": str(out_path),
    }


def main() -> int:
    result = asyncio.run(run())
    print(json.dumps(
        {
            "event": result["event"],
            "attendee_count": len(result["attendees"]),
            "names": [a["name"] for a in result["attendees"]],
            "briefing_draft_id": result["briefing_draft_id"],
        },
        indent=2,
    ))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
