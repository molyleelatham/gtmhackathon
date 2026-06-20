#!/usr/bin/env python3
"""GTM Hackathon demo — pre-meet + post-meet Gmail drafts to our inbox.

Creates:
  1. Pre-meet briefing draft (all ranked contacts)
  2. Pre-meet outreach drafts (one per top contact, addressed to ourselves)
  3. Post-meet follow-up draft (after chatting with the #1 lead at the hackathon)

Usage:
  make run-gmail-mcp   # terminal 1
  PYTHONPATH=. warmth/.venv/bin/python warmth/scripts/run_gtm_hackathon_demo.py
"""
from __future__ import annotations

import asyncio
import json
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path

from dotenv import load_dotenv

REPO_ROOT = Path(__file__).resolve().parents[2]
WARMTH_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))
load_dotenv(WARMTH_ROOT / ".env")

from warmth.apps.api.integration_helpers import (
    gmail_client_optional,
    unify_client_optional,
    zero_client_optional,
    warmth_client_email,
    warmth_client_name,
)
from warmth.apps.lifecycle.premeet import PreMeetPipeline
from warmth.apps.lifecycle.postmeet import PostMeetPipeline
from warmth.apps.scraper.sources.csv_loader import load_csv_attendees
from warmth.packages.core.models.event import DetectedEvent, EventType, LifecycleStage
from warmth.packages.core.models.lead import Lead
from warmth.packages.core.models.meeting_signal import MeetingSignal

sys.path.insert(0, str(WARMTH_ROOT / "scripts"))
from run_premeet_e2e import DEFAULT_CSV, _render_briefing  # noqa: E402

GTM_HACKATHON = DetectedEvent(
    id="event_gtm_hackathon_2026",
    user_id="demo-user",
    name="GTM Hackathon",
    event_type=EventType.EVENT,
    location="London, UK",
    start_date=datetime(2026, 6, 20, 9, 0),
    end_date=datetime(2026, 6, 20, 18, 0),
    confidence=1.0,
    stage=LifecycleStage.BEFORE_MEET,
    attendee_count=0,
)


async def run_demo(
    *,
    csv_path: str = DEFAULT_CSV,
    top_n: int = 3,
) -> dict:
    client_email = warmth_client_email()
    client_name = warmth_client_name()

    print("\n" + "=" * 60)
    print("  GTM HACKATHON DEMO — pre-meet + post-meet drafts")
    print("=" * 60 + "\n")

    # --- Pre-meet ---
    print("[Pre-meet] Loading contacts from CSV…")
    attendees = load_csv_attendees(csv_path, max_rows=10) if os.path.exists(csv_path) else []
    if not attendees:
        attendees = [
            {
                "name": "Federico Ruosi",
                "title": "Investor",
                "company": "Atomico",
                "interests": ["deep tech", "SaaS"],
                "research_notes": "European growth fund; strong GTM hackathon fit.",
                "source": "manual",
            }
        ]

    event = GTM_HACKATHON.model_copy()
    event.attendee_count = len(attendees)

    print(f"[Pre-meet] Running pipeline for {event.name} ({len(attendees)} contacts)…")
    premeet = PreMeetPipeline(
        unify_client=unify_client_optional(),
        zero_client=zero_client_optional(),
        gmail_client=gmail_client_optional(),
    )
    top_leads = await premeet.run(event, manual_attendees=attendees, top_n=top_n)

    gmail = gmail_client_optional()
    briefing_draft = None
    if gmail:
        subject, body = _render_briefing(event, top_leads, client_name=client_name)
        briefing_draft = await gmail.create_email_draft(
            to=client_email, subject=subject, body=body
        )
        print(f"  ✓ Briefing draft → {client_email} (id {briefing_draft.get('id')})")

    pre_drafts = [
        {"name": c.name, "draft_id": c.gmail_draft_id}
        for c in top_leads
        if c.gmail_draft_id
    ]
    print(f"  ✓ {len(pre_drafts)} pre-meet outreach drafts → {client_email}")
    for d in pre_drafts:
        print(f"      • {d['name']} (id {d['draft_id']})")

    # --- Post-meet (simulate conversation with top lead at GTM Hackathon) ---
    top = top_leads[0]
    print(f"\n[Post-meet] Drafting follow-up after meeting {top.name} @ {event.name}…")

    lead = Lead(
        company_name=top.company_name or "Unknown Company",
        contact_name=top.name,
        contact_email=top.email,
        icp_score=int(top.icp_score),
        signal_source="gtm_hackathon",
    )
    signal = MeetingSignal(
        connection_id=top.id,
        name=top.name,
        company=top.company_name,
        interests=top.interests or ["GTM", "event intelligence"],
        most_interesting="Building warmth scoring on top of Zero CRM ICP fit",
        what_you_learned=[
            "They invest in B2B SaaS with strong GTM motion",
            "Interested in Lightfern + Warmth handoff at the hackathon demo",
            "Wants to see post-meet follow-up grounded in captured context",
        ],
        role=top.title,
    )

    postmeet = PostMeetPipeline(gmail_client=gmail)
    post_draft = await postmeet.send_followup(
        lead,
        signal,
        extra_context={
            "scores": {
                "icp_score": top.icp_score,
                "warmth_score": top.predicted_warmth,
                "predicted_score": top.predicted_warmth,
                "actual_score": min(top.predicted_warmth + 12, 100),
                "band": "hot",
            },
            "lead": lead.model_dump(),
            "client_email": client_email,
            "client_name": client_name,
            "event": event.name,
        },
    )
    print(f"  ✓ Post-meet draft → {client_email} (id {post_draft.get('gmail_draft_id')})")
    print(f"      Subject: {post_draft.get('subject')}")

    print("\n" + "=" * 60)
    print("  Done — check Gmail Drafts on getwarmth@gmail.com")
    print("=" * 60 + "\n")

    return {
        "event": event.name,
        "briefing_draft": briefing_draft,
        "pre_meet_drafts": pre_drafts,
        "post_meet_draft": {
            "subject": post_draft.get("subject"),
            "gmail_draft_id": post_draft.get("gmail_draft_id"),
            "to": post_draft.get("to"),
        },
    }


def main() -> int:
    result = asyncio.run(run_demo())
    print(json.dumps(result, indent=2, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
