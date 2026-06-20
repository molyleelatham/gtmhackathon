"""Post-meet stage.

Generates a follow-up email draft grounded in the full data pipeline: the
pre-meet research ("parasocial" context) plus everything captured during the
conversation. We draft + save it and hand the user a Gmail compose link; the
user opens it in Gmail where Lightfern completes/polishes the final email. If
Google MCP is configured we also create the draft directly in Gmail (never
auto-send).
"""
from typing import Optional

from ...packages.core.models.lead import Lead
from ...packages.core.models.meeting_signal import MeetingSignal
from ...packages.core.models.conversation import ConversationIntelligence
from ...packages.integrations.lightfern.workflow import LightfernClient
from ...packages.integrations.google_mcp.client import GoogleMCPClient


class PostMeetPipeline:
    def __init__(
        self,
        lightfern_client: Optional[LightfernClient] = None,
        gmail_client: Optional[GoogleMCPClient] = None,
    ):
        self.lightfern_client = lightfern_client or LightfernClient()
        self.gmail_client = gmail_client

    async def send_followup(
        self,
        lead: Lead,
        signal: MeetingSignal,
        conversation: Optional[ConversationIntelligence] = None,
        extra_context: Optional[dict] = None,
    ) -> dict:
        """Generate + (optionally) send a personalized follow-up email."""
        context = {
            # Per-person evolved context (PersonNode) — the richest signal for
            # Lightfern. Dumped into the Gmail draft so Lightfern can personalize.
            "personal_context": signal.personal_context,
            "interests": signal.interests,
            "most_interesting": signal.most_interesting,
            "what_you_learned": signal.what_you_learned,
            "most_time_topic": signal.most_time_topic,
            "role": signal.role,
            "origin": signal.origin,
            "background": signal.background,
            "topics": conversation.topics if conversation else [],
            "pain_points": conversation.pain_points if conversation else [],
            "goals": conversation.goals if conversation else [],
            "follow_up_actions": conversation.follow_up_actions if conversation else [],
        }
        if extra_context:
            context.update(extra_context)

        draft = await self.lightfern_client.personalize_outreach(
            recipient={
                "name": signal.name,
                "company": signal.company,
                "email": lead.contact_email,
            },
            context=context,
            purpose="post_meet_followup",
        )

        # Optionally materialize the draft inside Gmail via Google MCP so the
        # user finds it ready to polish. We create a DRAFT, never send.
        if self.gmail_client and lead.contact_email:
            try:
                gmail_draft = await self.gmail_client.create_email_draft(
                    to=lead.contact_email,
                    subject=draft.get("subject", ""),
                    body=draft.get("body", ""),
                )
                draft["gmail_draft_id"] = gmail_draft.get("id")
            except Exception as e:  # pragma: no cover - stub resilience
                print(f"PostMeet create-Gmail-draft stub fallback: {e}")

        return draft
