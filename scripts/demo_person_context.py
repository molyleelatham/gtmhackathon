"""End-to-end demo of the per-person context pipeline.

    transcript utterance -> SpeakerID -> PersonNode -> PersonContextBuilder.update()
    -> PersonalContext accumulates over 30s windows -> SignalPayload (personal_context)
    -> Zero CRM push narrative -> Faxxing personalised outreach sequence

Run from the repo root (the directory that contains `warmth/`):

    python warmth/scripts/demo_person_context.py
"""
import asyncio
import json
import os
import sys
from datetime import datetime, timedelta

# Make `warmth` importable as a package regardless of where this is run from.
_REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

from warmth.apps.listener.intelligence.person_context_builder import PersonContextBuilder
from warmth.packages.core.models.lead import Lead
from warmth.packages.core.models.meeting_signal import MeetingSignal
from warmth.packages.core.models.person import PersonKnowledgeGraph
from warmth.packages.integrations.faxxing.client import FaxxingClient
from warmth.packages.integrations.zero_crm.mapper import ZeroCRMMapper

# Diarized transcript: speaker 0 is you (self), speaker 1 is Anna. Each entry is
# one ~30s window the listener would emit.
TRANSCRIPT_WINDOWS = [
    (0, "Hey, it's nice to meet you. What are you working on?"),
    (
        1,
        "I'm Anna, I run RevOps. I care a lot about accuracy in our numbers, so I "
        "look at the data and pipeline metrics constantly. Specifically pipeline "
        "visibility is what I obsess over.",
    ),
    (
        1,
        "Pipeline visibility is really the thing. I spend most of my time in "
        "dashboards measuring attribution and pipeline, the numbers have to be exact.",
    ),
    (
        1,
        "We just learned HubSpot has AI forecasting now. But honestly I'm so "
        "frustrated by manual data entry, it's a constant problem, I really hate "
        "the manual data entry across the team.",
    ),
]


async def main() -> None:
    builder = PersonContextBuilder()
    kg = PersonKnowledgeGraph(self_speaker_id=0)

    base = datetime.utcnow()
    for i, (speaker_id, text) in enumerate(TRANSCRIPT_WINDOWS):
        start = base + timedelta(seconds=30 * i)
        builder.update(
            kg,
            speaker_id=speaker_id,
            transcript_window=text,
            name="Anna" if speaker_id == 1 else None,
            company="Acme RevOps" if speaker_id == 1 else None,
            role="Head of RevOps" if speaker_id == 1 else None,
            window_start=start,
            window_end=start + timedelta(seconds=30),
        )

    anna = kg.people(exclude_self=True)[0]

    print("=" * 72)
    print("PersonNode (evolved over session)")
    print("=" * 72)
    print(f"  name:                 {anna.name}")
    print(f"  communication_style:  {anna.communication_style}")
    print(f"  values:               {anna.values}")
    print(f"  topic_weights:        {anna.topic_weights}")
    print(f"  dominant_topic:       {anna.dominant_topic}")
    print(f"  learnings:            {anna.learnings}")
    print(f"  pain_points:          {[(p.topic, p.level, round(p.intensity, 2)) for p in anna.pain_points]}")

    print("\n" + "=" * 72)
    print("Narrative pushed to Zero CRM")
    print("=" * 72)
    print("  " + anna.to_narrative())

    # SignalPayload carries personal_context per person.
    signal = MeetingSignal(name=anna.name, company=anna.company, personal_context=anna)
    lead = Lead(
        company_name=anna.company or "Acme RevOps",
        contact_name=anna.name,
        icp_score=78,
        signal_source="event_audio",
    )

    payload = ZeroCRMMapper.lead_to_zero_payload_with_context(lead, signal.personal_context)
    print("\n" + "=" * 72)
    print("ZeroCRMPayload")
    print("=" * 72)
    print(json.dumps(payload.model_dump(), indent=2))

    print("\n" + "=" * 72)
    print("Faxxing personalised outreach sequence")
    print("=" * 72)
    sequence = await FaxxingClient().personalize_sequence(anna)
    print(json.dumps(sequence, indent=2))


if __name__ == "__main__":
    asyncio.run(main())
