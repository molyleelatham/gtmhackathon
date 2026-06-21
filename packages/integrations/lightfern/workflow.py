import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Optional
from urllib.parse import urlencode

import httpx

from ...core.models.lead import Lead

_CONTEXT_MARKER = "--- CONTEXT FOR LIGHTFERN (remove before sending) ---"


def _csv(items: Any) -> str:
    if not items:
        return "—"
    if isinstance(items, (list, tuple, set)):
        return ", ".join(str(i) for i in items if i not in (None, ""))
    return str(items)


def _render_value(value: Any) -> str:
    if value in (None, "", [], {}):
        return ""
    if isinstance(value, (list, tuple, set)):
        return _csv(value)
    if isinstance(value, dict):
        return ", ".join(f"{k}={v}" for k, v in value.items())
    return str(value)


def build_gmail_compose_url(
    to: Optional[str],
    subject: str,
    body: str,
) -> str:
    """Build a Gmail compose deep link so the user can open the draft in Gmail.

    Gmail prefills `to` / `subject` / `body`; Lightfern then completes/polishes
    the final email inside Gmail.
    """
    params = {"view": "cm", "fs": "1", "su": subject, "body": body}
    if to:
        params["to"] = to
    return "https://mail.google.com/mail/?" + urlencode(params)


class LightfernClient:
    """Lightfern outreach assistant.

    Lightfern is NOT a send-side API. The flow is:
      1. generate the draft (subject/body) here,
      2. save the draft locally,
      3. hand the user a Gmail compose link to open/copy it into Gmail,
      4. Lightfern completes/polishes the final email inside Gmail.

    `webhook_url` is optional and only used for the legacy GTM workflow triggers
    (enrichment etc.); drafting works fully offline.
    """

    def __init__(
        self,
        webhook_url: Optional[str] = None,
        drafts_dir: Optional[str] = None,
    ):
        self.webhook_url = webhook_url or os.getenv("LIGHTFERN_WEBHOOK_URL")
        self.drafts_dir = Path(drafts_dir or os.getenv("WARMTH_DRAFTS_DIR", "drafts"))

    async def trigger_workflow(
        self,
        lead: Lead,
        workflow_type: str = "gtm_outreach"
    ) -> dict[str, Any]:
        """
        Trigger a Lightfern GTM workflow for a lead

        Args:
            lead: Lead to trigger workflow for
            workflow_type: Type of workflow to trigger

        Returns:
            Workflow trigger response
        """
        if not self.webhook_url:
            print("Lightfern webhook URL not configured, skipping workflow trigger")
            return {"status": "skipped", "reason": "no_webhook_url"}

        payload = {
            "workflow_type": workflow_type,
            "lead": {
                "id": lead.id,
                "company_name": lead.company_name,
                "company_domain": lead.company_domain,
                "contact_name": lead.contact_name,
                "contact_email": lead.contact_email,
                "icp_score": lead.icp_score,
                "signal_source": lead.signal_source,
                "tags": lead.tags,
                "buying_signals": lead.buying_signals
            },
            "signals": [
                {
                    "type": signal.signal_type.value,
                    "raw_text": signal.raw_text,
                    "source": signal.source,
                    "keywords_hit": signal.keywords_hit,
                    "detected_at": signal.detected_at.isoformat()
                }
                for signal in lead.signals
            ]
        }

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    self.webhook_url,
                    json=payload
                )
                response.raise_for_status()
                return response.json()
        except Exception as e:
            print(f"Error triggering Lightfern workflow: {e}")
            return {
                "status": "error",
                "reason": str(e)
            }

    async def personalize_outreach(
        self,
        recipient: dict[str, Any],
        context: dict[str, Any],
        purpose: str = "pre_meet_intro",
    ) -> dict[str, Any]:
        """Generate a Gmail-ready outreach draft (we draft; Lightfern polishes).

        Used pre-meet (intro to a high-intent attendee using the "parasocial"
        research context) and post-meet (follow-up grounded in the captured
        conversation signals). Returns the draft plus a `gmail_compose_url` for
        the user to open/copy it into Gmail, where Lightfern completes it. The
        draft is also saved locally.

        STUB body: templated copy. TODO: call the real Lightfern API to generate
        copy tuned to the sender's voice + recipient context.
        """
        name = recipient.get("name") or "there"
        company = recipient.get("company") or "your team"
        to = recipient.get("email") or recipient.get("to")
        interests = ", ".join(context.get("interests", [])) or "what you're building"

        if purpose == "post_meet_followup":
            subject = f"Great meeting you, {name}"
            body = (
                f"Hi {name},\n\n"
                f"Really enjoyed our chat about {interests}. "
                f"Following up with what we discussed and a couple of ideas for {company}.\n\n"
                f"[Lightfern will polish this in Gmail]\n"
            )
        else:
            subject = f"Excited to connect at the event, {name}"
            body = (
                f"Hi {name},\n\n"
                f"Saw you'll be at the event and noticed your work at {company}. "
                f"Would love to swap notes on {interests}.\n\n"
                f"[Lightfern will polish this in Gmail]\n"
            )

        # Quick hack: dump ALL the captured context into the draft so Lightfern
        # (which reads the draft inside Gmail) has full per-person context to
        # personalize from. Lives below a marker so it's easy to strip on send.
        brief = self._render_context_brief(context)
        if brief:
            body += f"\n\n{_CONTEXT_MARKER}\n{brief}\n"

        return self._as_draft(
            to=to,
            subject=subject,
            body=body,
            purpose=purpose,
            client_email=context.get("client_email"),
        )

    @staticmethod
    def _render_context_brief(context: dict[str, Any]) -> str:
        """Render every piece of captured context as a plain-text brief.

        Handles the per-person `PersonNode` specially (narrative + structured
        traits) and renders any other scalars/lists generically.
        """
        if not context:
            return ""

        lines: list[str] = [
            "Context for Lightfern (delete before sending):",
            "Warmth sends scoring + lead data here so Lightfern can populate the",
            "follow-up in Gmail. Human reviews/polishes in Gmail, then sends.",
        ]

        client_email = context.get("client_email") or os.getenv(
            "WARMTH_CLIENT_EMAIL", "getwarmth@gmail.com"
        )
        if client_email:
            lines.append("")
            lines.append("CLIENT:")
            lines.append(f"  sender_email: {client_email}")
            client_name = context.get("client_name") or os.getenv("WARMTH_CLIENT_NAME", "Warmth")
            if client_name:
                lines.append(f"  sender_name: {client_name}")

        scores = context.get("scores") or context.get("warmth")
        if scores:
            lines.append("")
            lines.append("SCORES:")
            if isinstance(scores, dict):
                for k in ("icp_score", "warmth_score", "predicted_score", "actual_score", "band", "uplift"):
                    if scores.get(k) is not None:
                        lines.append(f"  {k}: {scores[k]}")
                if scores.get("routing"):
                    lines.append(f"  routing: {scores['routing']}")
            else:
                lines.append(f"  {scores}")

        lead = context.get("lead")
        if lead is not None:
            lines.append("")
            lines.append("LEAD:")
            if isinstance(lead, dict):
                for k in ("contact_name", "company_name", "contact_email", "icp_score", "tags", "signal_source"):
                    if lead.get(k):
                        lines.append(f"  {k}: {_render_value(lead[k])}")
            else:
                lines.append(f"  contact_name: {getattr(lead, 'contact_name', '—')}")
                lines.append(f"  company_name: {getattr(lead, 'company_name', '—')}")
                lines.append(f"  icp_score: {getattr(lead, 'icp_score', '—')}")

        person = context.get("personal_context") or context.get("person")
        if person is not None:
            lines.append("")
            lines.append("PERSON:")
            # Duck-typed PersonNode (avoid a hard import / circular dep).
            narrative = getattr(person, "to_narrative", None)
            if callable(narrative):
                lines.append(f"  summary: {narrative()}")
                lines.append(f"  communication_style: {_csv(getattr(person, 'communication_style', []))}")
                lines.append(f"  values: {_csv(getattr(person, 'values', []))}")
                dom = getattr(person, "dominant_topic", None)
                if dom:
                    lines.append(f"  dominant_topic: {dom[0]} ({dom[1]})")
                lines.append(f"  learnings: {_csv(getattr(person, 'learnings', []))}")
                pains = getattr(person, "pain_points", []) or []
                if pains:
                    lines.append(
                        "  pain_points: "
                        + _csv([f"{p.topic} ({p.level})" for p in pains])
                    )
            elif isinstance(person, dict):
                for k, v in person.items():
                    lines.append(f"  {k}: {_render_value(v)}")

        # Everything else captured during the meet.
        skip = {"personal_context", "person", "scores", "warmth", "lead", "decision", "client_email", "client_name"}
        for key, value in context.items():
            if key in skip:
                continue
            rendered = _render_value(value)
            if rendered:
                lines.append(f"{key}: {rendered}")

        return "\n".join(lines)

    def _as_draft(
        self,
        to: Optional[str],
        subject: str,
        body: str,
        purpose: str,
        client_email: Optional[str] = None,
    ) -> dict[str, Any]:
        """Package + persist a draft and attach the Gmail handoff link."""
        sender = client_email or os.getenv("WARMTH_CLIENT_EMAIL", "getwarmth@gmail.com")
        draft = {
            "status": "draft_ready",
            "handoff": "gmail_lightfern",  # open in Gmail; Lightfern polishes there
            "purpose": purpose,
            "client_email": sender,
            "to": to,
            "subject": subject,
            "body": body,
            "gmail_compose_url": build_gmail_compose_url(to, subject, body),
        }
        draft["draft_id"] = self._save_draft_locally(draft)
        return draft

    def _save_draft_locally(self, draft: dict[str, Any]) -> Optional[str]:
        """Persist the draft to the local drafts store ("save draft in app")."""
        try:
            self.drafts_dir.mkdir(parents=True, exist_ok=True)
            draft_id = f"draft_{datetime.utcnow().strftime('%Y%m%dT%H%M%S%f')}"
            path = self.drafts_dir / f"{draft_id}.json"
            path.write_text(json.dumps({"id": draft_id, **draft}, indent=2))
            return draft_id
        except Exception as e:  # pragma: no cover - best-effort persistence
            print(f"Lightfern local draft save skipped: {e}")
            return None

    async def send_followup_email(
        self,
        lead: Lead,
        context: dict[str, Any],
    ) -> dict[str, Any]:
        """Draft a post-meet follow-up grounded in the full pipeline context.

        Despite the name, this does NOT send: it generates the draft, saves it
        locally, and returns a Gmail compose link for the user to open in Gmail,
        where Lightfern completes/polishes the final email.
        """
        return await self.personalize_outreach(
            recipient={
                "name": lead.contact_name,
                "company": lead.company_name,
                "email": lead.contact_email,
            },
            context=context,
            purpose="post_meet_followup",
        )

    async def trigger_enrichment_workflow(
        self,
        lead_id: str,
        enrichment_data: dict[str, Any]
    ) -> dict[str, Any]:
        """
        Trigger enrichment workflow in Lightfern

        Args:
            lead_id: Internal lead ID
            enrichment_data: Enrichment data to process

        Returns:
            Workflow trigger response
        """
        if not self.webhook_url:
            return {"status": "skipped", "reason": "no_webhook_url"}

        payload = {
            "workflow_type": "enrichment",
            "lead_id": lead_id,
            "enrichment_data": enrichment_data
        }

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    self.webhook_url,
                    json=payload
                )
                response.raise_for_status()
                return response.json()
        except Exception as e:
            print(f"Error triggering enrichment workflow: {e}")
            return {
                "status": "error",
                "reason": str(e)
            }
