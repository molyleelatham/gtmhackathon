#!/usr/bin/env python3
"""Seed GTM Hackathon demo data into Firestore for a user (by email).

Usage:
  uv run python scripts/migrate_user_demo_to_firestore.py dzakwan1844@gmail.com
"""
from __future__ import annotations

import json
import os
import re
import sys
from datetime import datetime
from pathlib import Path
from types import SimpleNamespace

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from dotenv import load_dotenv

load_dotenv()

from packages.core.secrets import load_secrets_into_env  # noqa: E402

load_secrets_into_env()

os.environ.setdefault("GCP_PROJECT_ID", "warmth-gtm-hackathon")

from firebase_admin import auth as firebase_auth  # noqa: E402
from firebase_admin import firestore as firebase_firestore  # noqa: E402

from infra.firebase.admin import ensure_firebase_initialized  # noqa: E402
from infra.firebase.user_store_repo import UserStoreRepository  # noqa: E402
from packages.core.models.event import DetectedEvent, EventType, LifecycleStage  # noqa: E402
from packages.core.models.pre_connection import PreMeetConnection, PreMeetStatus  # noqa: E402
from packages.core.models.warmth import WarmthScore, WarmthBand  # noqa: E402
from packages.core.models.user_profile import UserProfile  # noqa: E402

OWNER_DEMO_EMAIL = "dzakwan1844@gmail.com"
GTM_EVENT_ID = "event_gtm_hackathon_london"
GTM_DATA_FILE = Path(ROOT) / "data" / "gtm_hackathon_attendees.json"
GTM_ATTENDEE_IDS = {
    "molyleelatham@gmail.com": "premeet_moly_leelatham",
    "dzakwan1844@gmail.com": "premeet_dzakwan_nabil",
    "nicholasyswong@googlemail.com": "premeet_nicholas_wong",
}
GTM_SCORES = {
    "molyleelatham@gmail.com": {"icp": 88, "warmth": 82, "intent": 75},
    "dzakwan1844@gmail.com": {"icp": 71, "warmth": 58, "intent": 52},
    "nicholasyswong@googlemail.com": {"icp": 76, "warmth": 68, "intent": 60},
}


def _notes_list(raw) -> list[str]:
    if raw is None:
        return []
    if isinstance(raw, list):
        return [str(x) for x in raw if x]
    text = str(raw).strip()
    return [text] if text else []


def _build_demo_store(user_id: str) -> SimpleNamespace:
    attendees = json.loads(GTM_DATA_FILE.read_text()) if GTM_DATA_FILE.exists() else []
    event = DetectedEvent(
        id=GTM_EVENT_ID,
        user_id=user_id,
        name="GTM Hackathon London",
        event_type=EventType.EVENT,
        location="The Building Centre",
        start_date=datetime(2026, 6, 20, 8, 30),
        end_date=datetime(2026, 6, 20, 18, 0),
        confidence=1.0,
        stage=LifecycleStage.BEFORE_MEET,
        attendee_count=len(attendees),
    )
    events = {event.id: event}
    pre_connections = {}
    warmth = {}
    for att in attendees:
        email = (att.get("email") or "").lower()
        scores = GTM_SCORES.get(email, {"icp": 65, "warmth": 50, "intent": 45})
        conn_id = GTM_ATTENDEE_IDS.get(email, f"premeet_{email.replace('@', '_')}")
        conn = PreMeetConnection(
            id=conn_id,
            event_id=event.id,
            user_id=user_id,
            name=att.get("name"),
            email=att.get("email"),
            linkedin=att.get("linkedin"),
            industry="GTM / SaaS",
            interests=att.get("interests") or [],
            research_notes=_notes_list(att.get("research_notes")),
            icp_score=scores["icp"],
            predicted_warmth=scores["warmth"],
            intent_score=scores["intent"],
            status=PreMeetStatus.SCORED,
            source=att.get("source", "calendar+tavily"),
        )
        pre_connections[conn.id] = conn
        warmth[conn.id] = WarmthScore(
            connection_id=conn.id,
            icp_score=int(conn.icp_score),
            warmth_score=conn.predicted_warmth,
            predicted_score=conn.predicted_warmth,
            band=WarmthBand.HOT if conn.predicted_warmth >= 70 else WarmthBand.WARM,
        )
    community_members = [
        {"user_id": "founder_amir", "name": "Amir", "interests": ["RevOps", "AI", "GTM"]},
        {"user_id": "friend_sara", "name": "Sara", "interests": ["fintech", "automation"]},
        {"user_id": "founder_lena", "name": "Lena", "interests": ["developer experience", "growth"]},
    ]
    return SimpleNamespace(
        events=events,
        pre_connections=pre_connections,
        warmth=warmth,
        meet_results={},
        leads={},
        signal_index={},
        gtm_sync_results={},
        community_members=community_members,
        list_events=lambda uid: [e for e in events.values() if e.user_id == uid],
        list_connections=lambda uid: [c for c in pre_connections.values() if c.user_id == uid],
        warmth_for_connection=lambda cid: warmth.get(cid),
        meet_result_for=lambda cid: None,
    )


def main() -> None:
    email = (sys.argv[1] if len(sys.argv) > 1 else OWNER_DEMO_EMAIL).lower()
    ensure_firebase_initialized()
    user = firebase_auth.get_user_by_email(email)
    uid = user.uid
    print(f"Migrating demo roster for {email} (uid={uid})...")

    store = _build_demo_store(uid)
    repo = UserStoreRepository(firebase_firestore.client())
    repo.persist_snapshot(uid, store)

    firebase_firestore.client().collection("users").document(uid).set(
        UserProfile(
            uid=uid,
            email=user.email,
            display_name=user.display_name,
            photo_url=user.photo_url,
            demo_seeded=True,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        ).model_dump(mode="json"),
        merge=True,
    )

    print(f"Done: {len(store.list_events(uid))} event(s), {len(store.list_connections(uid))} connection(s).")
    for c in store.list_connections(uid):
        print(f"  - {c.name} ({c.email}) warmth={c.predicted_warmth}")


if __name__ == "__main__":
    main()
