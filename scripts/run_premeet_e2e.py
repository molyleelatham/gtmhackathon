#!/usr/bin/env python3
"""End-to-end pre-meet workflow: calendar event → score contacts → briefing draft.

Steps:
  1. Pull upcoming events from Google Calendar (via MCP bridge)
  2. Pick the best event/meeting event (or next event with attendees)
  3. Merge calendar attendees with CSV research contacts
  4. Run PreMeetPipeline (enrich → ICP/warmth score → outreach drafts)
  5. Create a briefing Gmail draft summarizing all ranked contacts

Usage:
  cd warmth && make setup-gmail-mcp   # once, includes Calendar scopes
  make run-gmail-mcp                 # terminal 1
  PYTHONPATH=. warmth/.venv/bin/python warmth/scripts/run_premeet_e2e.py
"""
from __future__ import annotations

import asyncio
import json
import os
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Optional

from dotenv import load_dotenv

REPO_ROOT = Path(__file__).resolve().parents[2]
WARMTH_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))
load_dotenv(WARMTH_ROOT / ".env")

from warmth.apps.lifecycle.onboarding import OnboardingService
from warmth.apps.lifecycle.premeet import PreMeetPipeline
from warmth.apps.scraper.sources.csv_loader import load_csv_attendees
from warmth.apps.api.integration_helpers import (
    gmail_client_optional,
    unify_client_optional,
    zero_client_optional,
    warmth_client_email,
    warmth_client_name,
)
from warmth.packages.core.models.event import DetectedEvent, EventType, LifecycleStage
from warmth.packages.core.models.pre_connection import PreMeetConnection
from warmth.packages.integrations.google_calendar.client import GoogleCalendarClient
from warmth.packages.integrations.google_calendar.attendees import calendar_attendees_from_raw


DEFAULT_CSV = os.path.expanduser("~/Downloads/data.csv")
DEMO_USER = "demo-user"


def _naive_utc(dt: Optional[datetime]) -> Optional[datetime]:
    if dt is None:
        return None
    if dt.tzinfo is not None:
        return dt.astimezone(timezone.utc).replace(tzinfo=None)
    return dt


def _pick_calendar_event(
    calendar_events: list,
    detected: list,
) -> tuple[Optional[Any], Optional[dict]]:
    """Pick best event and its raw Google Calendar payload."""
    picked = _pick_event(detected)
    raw_match: dict = {}

    if calendar_events:
        # Prefer detected event linked to calendar
        if picked and picked.calendar_event_id:
            for ev in calendar_events:
                if ev.external_id == picked.calendar_event_id or ev.id == picked.calendar_event_id:
                    raw_match = ev.raw or {}
                    return picked, raw_match

        # Else pick next upcoming event with most attendees
        upcoming = sorted(
            calendar_events,
            key=lambda e: (
                len(e.attendees_emails),
                e.start_time or datetime.min,
            ),
            reverse=True,
        )
        best = upcoming[0]
        raw_match = best.raw or {}
        if not picked:
            picked = DetectedEvent(
                user_id=DEMO_USER,
                calendar_event_id=best.external_id or best.id,
                name=best.title,
                event_type=EventType.MEETING,
                location=best.location,
                start_date=best.start_time,
                end_date=best.end_time,
                confidence=0.5,
                stage=LifecycleStage.BEFORE_MEET,
                attendee_count=len(best.attendees_emails),
            )
        return picked, raw_match

    return picked, raw_match


def _pick_event(events: list) -> Optional[Any]:
    """Prefer event-like events; else next event with attendees."""
    if not events:
        return None
    hints = ["event", "summit", "expo", "meetup", "demo day", "hackathon", "gtm", "saas"]
    scored: list[tuple[float, Any]] = []
    for ev in events:
        text = f"{ev.name} {ev.location or ''}".lower()
        score = ev.confidence
        if any(h in text for h in hints):
            score += 0.5
        if ev.attendee_count >= 2:
            score += 0.2
        if ev.start_date:
            start = _naive_utc(ev.start_date)
            if start:
                days_out = (start - datetime.utcnow()).days
                if 0 <= days_out <= 14:
                    score += 0.3
        scored.append((score, ev))
    scored.sort(key=lambda x: x[0], reverse=True)
    return scored[0][1]


def _merge_attendees(
    calendar: list[dict[str, Any]],
    csv_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Merge CSV research contacts with calendar invitees (dedupe by name/email)."""
    seen: set[str] = set()
    merged: list[dict[str, Any]] = []

    for att in csv_rows:
        key = (att.get("email") or att.get("name") or "").lower().strip()
        if key:
            seen.add(key)
        merged.append(att)

    for att in calendar:
        key = (att.get("email") or att.get("name") or "").lower().strip()
        if key and key in seen:
            continue
        if key:
            seen.add(key)
        merged.append(att)

    return merged


def _render_briefing(
    event: DetectedEvent,
    leads: list[PreMeetConnection],
    *,
    client_name: str,
) -> tuple[str, str]:
    """Build subject + body for the pre-meet briefing draft."""
    when = ""
    if event.start_date:
        when = event.start_date.strftime("%a %b %d, %Y %H:%M UTC")

    subject = f"Pre-meet briefing: {event.name}"
    if when:
        subject += f" ({when.split(',')[0]})"

    lines = [
        f"Hi {client_name},",
        "",
        f"Warmth pre-meet intel for **{event.name}**.",
        "",
        "EVENT",
        f"  • Name: {event.name}",
    ]
    if when:
        lines.append(f"  • When: {when}")
    if event.location:
        lines.append(f"  • Where: {event.location}")
    lines.append(f"  • Contacts ranked: {len(leads)}")
    lines.append("")
    lines.append("TOP CONTACTS (by predicted warmth)")
    lines.append("")

    for i, c in enumerate(leads, 1):
        company = c.company_name or "—"
        title = c.title or "—"
        lines.append(f"{i}. {c.name or 'Unknown'} — {title} @ {company}")
        lines.append(
            f"   ICP: {c.icp_score:.0f} | Warmth: {c.predicted_warmth:.0f} | "
            f"Intent: {c.intent_score:.0f}"
        )
        if c.email:
            lines.append(f"   Email: {c.email}")
        if c.interests:
            lines.append(f"   Interests: {', '.join(c.interests[:5])}")
        if c.industry or c.funding_stage:
            lines.append(
                f"   Firmographics: {c.industry or '—'} | {c.funding_stage or '—'}"
            )
        if c.research_notes:
            raw_notes = c.research_notes
            if isinstance(raw_notes, list):
                raw_notes = " | ".join(str(n) for n in raw_notes if n)
            note = str(raw_notes)[:180] + ("…" if len(str(raw_notes)) > 180 else "")
            lines.append(f"   Notes: {note}")
        if c.gmail_draft_id:
            lines.append(f"   Outreach draft: created (id {c.gmail_draft_id})")
        lines.append("")

    lines.extend(
        [
            "Next steps:",
            "  1. Review outreach drafts in Gmail (Lightfern can polish before send)",
            "  2. Capture conversations on-site with the Warmth iOS app",
            "  3. Post-meet follow-ups will include meet context automatically",
            "",
            "— Warmth",
        ]
    )
    return subject, "\n".join(lines)


async def run_e2e(
    *,
    csv_path: str = DEFAULT_CSV,
    csv_max_rows: int = 10,
    top_n: int = 5,
) -> dict[str, Any]:
    print("\n" + "=" * 60)
    print("  WARMTH PRE-MEET E2E")
    print("=" * 60 + "\n")

    # --- Step 1: Calendar discovery ---
    print("[1/5] Fetching calendar events…")
    onboarding = OnboardingService()
    connect = await onboarding.connect(DEMO_USER)
    print(f"      Calendar connected: {connect.get('calendar_connected')}")

    detected = await onboarding.discover_events(DEMO_USER, lookahead_days=30)
    cal_client = GoogleCalendarClient()
    calendar_events: list = []
    try:
        now = datetime.now(timezone.utc)
        calendar_events = await cal_client.list_events(
            time_min=now.replace(tzinfo=None),
            time_max=(now + timedelta(days=30)).replace(tzinfo=None),
        )
    except Exception as exc:
        print(f"      Calendar list warning: {exc}")

    picked, raw_match = _pick_calendar_event(calendar_events, detected)

    if not picked:
        # Fallback synthetic event for demo
        now = datetime.utcnow()
        picked = DetectedEvent(
            id="event_gtm_hackathon_2026",
            user_id=DEMO_USER,
            name="GTM Hackathon",
            event_type=EventType.EVENT,
            location="London, UK",
            start_date=datetime(2026, 6, 20, 9, 0),
            end_date=datetime(2026, 6, 20, 18, 0),
            confidence=1.0,
            stage=LifecycleStage.BEFORE_MEET,
        )
        raw_match = {}
        print("      No calendar events found — using GTM Hackathon demo event")
    else:
        print(f"      Selected event: {picked.name} (confidence {picked.confidence})")
        print(f"      Calendar events fetched: {len(calendar_events)}")

    cal_attendees = calendar_attendees_from_raw(
        raw_match,
        exclude_emails={warmth_client_email().lower()},
    )
    print(f"      Calendar attendees: {len(cal_attendees)}")

    # --- Step 2: Load CSV research contacts ---
    print("[2/5] Loading contact research…")
    csv_attendees: list[dict] = []
    if os.path.exists(csv_path):
        csv_attendees = load_csv_attendees(csv_path, max_rows=csv_max_rows)
        print(f"      CSV contacts: {len(csv_attendees)} from {csv_path}")
    else:
        print(f"      CSV not found at {csv_path} — calendar attendees only")

    manual_attendees = _merge_attendees(cal_attendees, csv_attendees)
    if not manual_attendees:
        manual_attendees = [
            {
                "name": "Maya Chen",
                "title": "VP RevOps",
                "company": "NorthWind Labs",
                "interests": ["RevOps", "pipeline visibility"],
                "source": "fallback",
            }
        ]
        print("      Using fallback demo contact")
    print(f"      Total contacts to process: {len(manual_attendees)}")

    # --- Step 3: Pre-meet pipeline ---
    print("[3/5] Running pre-meet pipeline (enrich → score → draft outreach)…")
    pipeline = PreMeetPipeline(
        unify_client=unify_client_optional(),
        zero_client=zero_client_optional(),
        gmail_client=gmail_client_optional(),
    )
    event = picked
    event.attendee_count = len(manual_attendees)
    top_leads = await pipeline.run(event, manual_attendees=manual_attendees, top_n=top_n)
    print(f"      Ranked {len(top_leads)} top leads")

    for i, c in enumerate(top_leads, 1):
        print(
            f"        #{i} {c.name} | {c.company_name} | "
            f"ICP {c.icp_score:.0f} | Warmth {c.predicted_warmth:.0f}"
        )

    # --- Step 4: Briefing email draft ---
    print("[4/5] Creating briefing email draft…")
    client_email = warmth_client_email()
    client_name = warmth_client_name()
    subject, body = _render_briefing(event, top_leads, client_name=client_name)

    gmail = gmail_client_optional()
    briefing_result: dict[str, Any] = {}
    if gmail:
        briefing_result = await gmail.create_email_draft(
            to=client_email,
            subject=subject,
            body=body,
        )
        print(f"      Briefing draft created → {client_email}")
        print(f"      Draft id: {briefing_result.get('id') or briefing_result.get('draft_id')}")
    else:
        print("      Gmail MCP not configured — briefing saved locally only")
        drafts_dir = WARMTH_ROOT / "drafts"
        drafts_dir.mkdir(exist_ok=True)
        draft_id = f"briefing_{datetime.utcnow().strftime('%Y%m%dT%H%M%S')}"
        path = drafts_dir / f"{draft_id}.json"
        path.write_text(
            json.dumps(
                {"to": client_email, "subject": subject, "body": body, "purpose": "pre_meet_briefing"},
                indent=2,
            )
        )
        briefing_result = {"draft_id": draft_id, "path": str(path)}

    # --- Step 5: Summary ---
    print("[5/5] Done")
    print("=" * 60 + "\n")

    return {
        "event": event.model_dump(),
        "contacts_processed": len(manual_attendees),
        "top_leads": [c.model_dump() for c in top_leads],
        "outreach_drafts": [
            {"name": c.name, "draft_id": c.gmail_draft_id}
            for c in top_leads
            if c.gmail_draft_id
        ],
        "briefing_draft": briefing_result,
        "briefing_to": client_email,
    }


def main() -> int:
    csv_path = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_CSV
    result = asyncio.run(run_e2e(csv_path=csv_path))
    print(json.dumps(
        {
            "event": result["event"].get("name"),
            "contacts": result["contacts_processed"],
            "top_leads": len(result["top_leads"]),
            "outreach_drafts": len(result["outreach_drafts"]),
            "briefing_draft": result["briefing_draft"],
            "briefing_to": result["briefing_to"],
        },
        indent=2,
    ))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
