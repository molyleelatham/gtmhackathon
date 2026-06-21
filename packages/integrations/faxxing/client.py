"""Faxxing — outreach sequence personalisation.

Final node of the data flow: takes the evolved PersonNode context and tailors an
outreach sequence so the tone matches the person's `communication_style` and the
message leans on the `values` they expressed during the meet.

STUB: builds the sequence locally. Swap `_post` for the real Faxxing API when
`FAXXING_API_KEY` / `FAXXING_API_URL` are wired up.
"""
import os
from typing import Any, Optional

import httpx

from ...core.models.person import PersonNode

# How a communication style should shape the copy.
_STYLE_PLAYBOOK: dict[str, dict[str, str]] = {
    "analytical": {"tone": "precise, evidence-led", "hook": "a concrete metric / benchmark"},
    "data-driven": {"tone": "quantified, no fluff", "hook": "a data point or dashboard view"},
    "visionary": {"tone": "ambitious, big-picture", "hook": "where this goes long term"},
    "relational": {"tone": "warm, personal", "hook": "the shared connection from the chat"},
    "pragmatic": {"tone": "concise, action-first", "hook": "the fastest path to a quick win"},
    "skeptical": {"tone": "proof-first, low-hype", "hook": "a reference / guarantee that de-risks it"},
    "enthusiastic": {"tone": "high-energy, upbeat", "hook": "the exciting outcome"},
}

_DEFAULT_STYLE = {"tone": "friendly, clear", "hook": "what you discussed"}


class FaxxingClient:
    def __init__(
        self,
        api_url: Optional[str] = None,
        api_key: Optional[str] = None,
    ):
        self.api_url = api_url or os.getenv("FAXXING_API_URL")
        self.api_key = api_key or os.getenv("FAXXING_API_KEY")

    async def personalize_sequence(
        self,
        person: PersonNode,
        num_steps: int = 3,
        purpose: str = "post_meet_followup",
    ) -> dict[str, Any]:
        """Build an outreach sequence matched to the person's style + values."""
        primary_style = (person.communication_style or ["friendly"])[0]
        playbook = _STYLE_PLAYBOOK.get(primary_style, _DEFAULT_STYLE)
        sequence = self._draft_sequence(person, playbook, num_steps)

        body = {
            "purpose": purpose,
            "person_id": person.person_id,
            "recipient": person.name,
            "communication_style": person.communication_style,
            "values": person.values,
            "context_narrative": person.to_narrative(),
            "sequence": sequence,
        }

        remote = await self._post(body)
        if remote is not None:
            return remote

        return {"status": "stubbed", **body}

    # -- drafting ---------------------------------------------------------

    def _draft_sequence(
        self,
        person: PersonNode,
        playbook: dict[str, str],
        num_steps: int,
    ) -> list[dict[str, str]]:
        name = person.name or "there"
        tone, hook = playbook["tone"], playbook["hook"]
        values = ", ".join(person.values) or "what matters to you"
        dominant = person.dominant_topic
        topic = dominant[0] if dominant else "what we discussed"
        pain = person.top_pain

        steps: list[dict[str, str]] = []

        steps.append({
            "channel": "email",
            "delay": "same day",
            "subject": f"Following up on {topic}, {name}",
            "tone": tone,
            "body": (
                f"Hi {name}, great chat about {topic}. Opening on {hook} and "
                f"anchoring on {values}."
                + (f" Directly addresses the pain around {pain.topic}." if pain else "")
            ),
        })

        if num_steps >= 2:
            steps.append({
                "channel": "email",
                "delay": "+3 days",
                "subject": f"A {tone.split(',')[0]} idea for {topic}",
                "tone": tone,
                "body": (
                    f"Share proof framed for a {primary_descriptor(person)} reader: "
                    f"lead with {hook}, reinforce {values}."
                ),
            })

        if num_steps >= 3:
            steps.append({
                "channel": "linkedin",
                "delay": "+7 days",
                "subject": "",
                "tone": tone,
                "body": (
                    f"Light-touch nudge in a {tone} voice referencing {topic}; "
                    f"keep it aligned with {values}."
                ),
            })

        return steps[:num_steps]

    async def _post(self, body: dict[str, Any]) -> Optional[dict[str, Any]]:
        if not self.api_url:
            return None
        headers = {"Authorization": f"Bearer {self.api_key}"} if self.api_key else {}
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                resp = await client.post(self.api_url, json=body, headers=headers)
                resp.raise_for_status()
                return resp.json()
        except Exception as e:  # pragma: no cover - stub resilience
            print(f"Faxxing API stub fallback: {e}")
            return None


def primary_descriptor(person: PersonNode) -> str:
    return (person.communication_style or ["pragmatic"])[0]
