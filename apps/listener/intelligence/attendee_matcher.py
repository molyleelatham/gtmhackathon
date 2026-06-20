"""AttendeeMatcher — resolve a live MeetingSignal to a known person.

During the *listening* stage the encoder emits a ``MeetingSignal`` carrying the
person we just detected in conversation (e.g. ``name="Nick"`` from "hi Nick").
On its own that's an anonymous payload. This component matches it against the
people we already know about for the event, from three sources:

  * **Google** — the calendar event's attendee guest list (emails + names)
  * **CRM** — HubSpot contacts (the source of record)
  * **Pipeline** — the in-flight leads the pre-meet pipeline already ranked

so the meet pipeline can attach the right contact id / email instead of creating
a fresh "Unknown Company" lead. Returns the best match with a confidence score
and what it matched on, or ``None`` if nothing crosses the threshold.

Pure scoring (``score_name`` / ``match``) is I/O-free and unit-testable; the
async ``resolve`` does the HubSpot lookup to confirm + enrich the match.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from difflib import SequenceMatcher
from typing import Any, Optional

from ....packages.core.models.lead import Lead
from ....packages.core.models.meeting_signal import MeetingSignal

# Below this combined score we treat the signal as an unknown new person.
DEFAULT_THRESHOLD = 0.62


@dataclass
class Candidate:
    """One known person we could be talking to, from any source."""

    name: Optional[str] = None
    email: Optional[str] = None
    company: Optional[str] = None
    title: Optional[str] = None
    source: str = "unknown"  # "google_calendar" | "hubspot" | "pipeline"
    external_id: Optional[str] = None  # HubSpot contact id, calendar attendee, etc.
    raw: dict[str, Any] = field(default_factory=dict)


@dataclass
class MatchResult:
    candidate: Candidate
    score: float
    matched_on: list[str]  # e.g. ["email"] or ["first_name", "company"]

    @property
    def is_confident(self) -> bool:
        return self.score >= DEFAULT_THRESHOLD


def _norm(s: Optional[str]) -> str:
    return (s or "").strip().lower()


def _ratio(a: str, b: str) -> float:
    if not a or not b:
        return 0.0
    return SequenceMatcher(None, a, b).ratio()


def score_name(signal_name: Optional[str], candidate_name: Optional[str]) -> tuple[float, list[str]]:
    """Score a detected name against a candidate name. I/O-free.

    Handles the common live case where we only caught a first name ("Nick").
    """
    s, c = _norm(signal_name), _norm(candidate_name)
    if not s or not c:
        return 0.0, []
    if s == c:
        return 1.0, ["full_name"]

    s_parts, c_parts = s.split(), c.split()
    matched: list[str] = []
    score = _ratio(s, c)  # baseline whole-string similarity

    # First-name hit (we usually only hear a first name in conversation).
    if s_parts and c_parts and (s_parts[0] == c_parts[0] or _ratio(s_parts[0], c_parts[0]) > 0.85):
        score = max(score, 0.7)
        matched.append("first_name")

    # Detected token is a subset of the candidate's full name ("Nick" in "Nick Reed").
    if s in c or all(tok in c_parts for tok in s_parts):
        score = max(score, 0.66)
        if "first_name" not in matched:
            matched.append("name_subset")

    return score, matched


class AttendeeMatcher:
    """Resolve a MeetingSignal to a known attendee/CRM contact.

    Args:
        hubspot_client: optional HubSpotClient; when present, an email match is
            confirmed/enriched against HubSpot (the source of record).
        threshold: minimum combined score to count as a confident match.
    """

    def __init__(self, hubspot_client: Any = None, threshold: float = DEFAULT_THRESHOLD):
        self.hubspot_client = hubspot_client
        self.threshold = threshold

    # ------------------------------------------------------------------
    # Candidate gathering
    # ------------------------------------------------------------------

    @staticmethod
    def candidates_from_calendar(attendees: list[dict[str, Any]]) -> list[Candidate]:
        """Build candidates from Google Calendar event attendees.

        Accepts the shape returned by the calendar MCP / zero find_calendar_events:
        ``{"email": ..., "displayName"/"name": ...}``.
        """
        out: list[Candidate] = []
        for a in attendees or []:
            email = a.get("email")
            name = a.get("displayName") or a.get("name")
            if not email and not name:
                continue
            out.append(
                Candidate(
                    name=name or (email.split("@")[0] if email else None),
                    email=email,
                    company=a.get("company"),
                    source="google_calendar",
                    external_id=email,
                    raw=a,
                )
            )
        return out

    @staticmethod
    def candidates_from_pipeline(leads: list[dict[str, Any]]) -> list[Candidate]:
        """Build candidates from in-flight pipeline leads (PreMeetConnection dicts)."""
        out: list[Candidate] = []
        for lead in leads or []:
            out.append(
                Candidate(
                    name=lead.get("name") or lead.get("contact_name"),
                    email=lead.get("email") or lead.get("contact_email"),
                    company=lead.get("company_name"),
                    title=lead.get("title"),
                    source="pipeline",
                    external_id=lead.get("id"),
                    raw=lead,
                )
            )
        return out

    # ------------------------------------------------------------------
    # Matching
    # ------------------------------------------------------------------

    def match(self, signal: MeetingSignal, candidates: list[Candidate]) -> Optional[MatchResult]:
        """Pick the best candidate for the signal. I/O-free.

        Scoring: an exact email match short-circuits to 1.0; otherwise combine
        name similarity with a company-agreement bonus.
        """
        sig_email = _norm(signal.name and getattr(signal, "email", None))  # signals rarely carry email
        sig_company = _norm(signal.company)

        best: Optional[MatchResult] = None
        for cand in candidates:
            matched: list[str] = []

            # Email is the strongest signal when we have it.
            if sig_email and _norm(cand.email) == sig_email:
                return MatchResult(cand, 1.0, ["email"])

            name_score, name_matched = score_name(signal.name, cand.name)
            matched.extend(name_matched)
            score = name_score

            # Company agreement nudges an ambiguous first-name match over the line.
            if sig_company and cand.company and _ratio(sig_company, _norm(cand.company)) > 0.8:
                score = min(1.0, score + 0.2)
                matched.append("company")

            if score > 0 and (best is None or score > best.score):
                best = MatchResult(cand, round(score, 3), matched)

        if best and best.score >= self.threshold:
            return best
        return None

    # ------------------------------------------------------------------
    # Resolve (gather + match + CRM confirm) — the public entrypoint
    # ------------------------------------------------------------------

    async def resolve(
        self,
        signal: MeetingSignal,
        *,
        calendar_attendees: Optional[list[dict[str, Any]]] = None,
        pipeline_leads: Optional[list[dict[str, Any]]] = None,
    ) -> Optional[MatchResult]:
        """Resolve the signal against Google + pipeline candidates, then confirm
        the match against HubSpot (source of record) and enrich it.
        """
        candidates = self.candidates_from_calendar(calendar_attendees or [])
        candidates += self.candidates_from_pipeline(pipeline_leads or [])

        result = self.match(signal, candidates)
        if result is None:
            return None

        # Confirm / enrich against HubSpot when we have an email and a client.
        if self.hubspot_client and result.candidate.email:
            try:
                contact = await self.hubspot_client.find_contact_by_email(result.candidate.email)
            except Exception:
                contact = None
            if contact:
                props = contact.get("properties", {})
                result.candidate.external_id = (
                    contact.get("id") or props.get("hs_object_id") or result.candidate.external_id
                )
                result.candidate.source = "hubspot"
                result.candidate.company = result.candidate.company or props.get("company")
                result.candidate.title = result.candidate.title or props.get("jobtitle")
                if "crm" not in result.matched_on:
                    result.matched_on.append("crm")
        return result

    # ------------------------------------------------------------------
    # Pipeline hand-off
    # ------------------------------------------------------------------

    @staticmethod
    def to_lead(signal: MeetingSignal, match: Optional[MatchResult]) -> Lead:
        """Produce the Lead the meet pipeline should run with.

        A confident match carries the known email/company/id forward; otherwise we
        fall back to the raw signal (a new unknown person).
        """
        if match and match.is_confident:
            cand = match.candidate
            return Lead(
                company_name=cand.company or signal.company or "Unknown Company",
                contact_name=cand.name or signal.name,
                contact_email=cand.email,
                signal_source="conference_audio",
            )
        return Lead(
            company_name=signal.company or "Unknown Company",
            contact_name=signal.name,
            signal_source="conference_audio",
        )
