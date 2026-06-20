"""Post-meet stage.

Lightfern sends a follow-up email grounded in the full data pipeline: the
pre-meet research ("parasocial" context) plus everything captured during the
conversation. Optionally logs the interaction to the CRM.
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
    ) -> dict:
        """Generate + (optionally) send a personalized follow-up email."""
        context = {
            "interests": signal.interests,
            "most_interesting": signal.most_interesting,
            "what_you_learned": signal.what_you_learned,
            "topics": conversation.topics if conversation else [],
            "follow_up_actions": conversation.follow_up_actions if conversation else [],
        }

        personalized = await self.lightfern_client.personalize_outreach(
            recipient={"name": signal.name, "company": signal.company},
            context=context,
            purpose="post_meet_followup",
        )

        result = {"status": "drafted", **personalized}

        if self.gmail_client and lead.contact_email:
            try:
                sent = await self.gmail_client.send_email(
                    to=lead.contact_email,
                    subject=personalized.get("subject", ""),
                    body=personalized.get("body", ""),
                )
                result = {"status": "sent", "message_id": sent.get("id"), **personalized}
            except Exception as e:  # pragma: no cover - stub resilience
                print(f"PostMeet send_followup stub fallback: {e}")

        return result
