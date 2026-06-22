"""LinkedIn-oriented enrichment via Tavily search.

Uses Tavily to find LinkedIn profile snippets and extract:
  - profile URL
  - refined name / title / company (from headline)
  - industry (keyword taxonomy + headline cues)
  - interests (GTM + profile topic keywords)
  - research_notes (short snippets for CRM / dashboard)
"""
from __future__ import annotations

import re
from typing import Any, Optional

from ...core.models.pre_connection import PreMeetConnection
from .client import TavilyClient

# Map snippet keywords → normalized industry label (first match wins).
_INDUSTRY_KEYWORDS: list[tuple[str, tuple[str, ...]]] = [
    ("B2B SaaS", ("b2b saas", "saas", "software as a service", "enterprise software")),
    ("Fintech", ("fintech", "financial services", "payments", "banking")),
    ("DevTools", ("devtools", "developer tools", "developer platform", "api platform")),
    ("MarTech", ("martech", "marketing technology", "marketing automation")),
    ("Analytics", ("analytics", "business intelligence", "data platform")),
    ("AI / ML", (" artificial intelligence", " machine learning", " ai ", " llm")),
    ("Healthcare", ("healthcare", "health tech", "medtech", "life sciences")),
    ("E-commerce", ("e-commerce", "ecommerce", "retail tech")),
    ("Cybersecurity", ("cybersecurity", "infosec", "security software")),
    ("GTM / SaaS", ("go-to-market", "gtm", "revops", "revenue operations")),
]

# Interest tokens surfaced on profiles + conference context.
_INTEREST_KEYWORDS: tuple[str, ...] = (
    "gtm",
    "revops",
    "saas",
    "crm",
    "ai",
    "sales",
    "marketing",
    "pipeline",
    "attribution",
    "conference",
    "hubspot",
    "salesforce",
    "founder",
    "investor",
    "venture",
    "product-led",
    "demand gen",
    "outbound",
    "enablement",
    "forecasting",
)

def _looks_like_person_name(name: str) -> bool:
    """Reject article-style LinkedIn titles mistaken for names."""
    cleaned = (name or "").strip()
    if not cleaned or len(cleaned) > 45:
        return False
    lower = cleaned.lower()
    if any(
        phrase in lower
        for phrase in (
            " post",
            " ops",
            "what it takes",
            "linkedin",
            " | ",
            "automation work",
            "hackathon",
            "#",
        )
    ):
        return False
    parts = [p for p in cleaned.replace("-", " ").split() if p]
    if not parts or len(parts) > 4:
        return False
    for part in parts:
        if not part[0].isalpha() or not part[0].isupper():
            return False
    return True


_HEADLINE_RE = re.compile(
    r"^(.+?)\s[-–|]\s(.+?)(?:\s[-–|]\sLinkedIn)?$",
    re.IGNORECASE,
)
_TITLE_AT_RE = re.compile(
    r"^(?P<title>.+?)\s+(?:at|@)\s+(?P<company>.+?)(?:\s*\||$)",
    re.IGNORECASE,
)


def _norm_list(items: list[str], limit: int = 8) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for item in items:
        key = item.strip()
        if not key:
            continue
        norm = key.lower()
        if norm in seen:
            continue
        seen.add(norm)
        out.append(key if key[0].isupper() else key.title())
        if len(out) >= limit:
            break
    return out


def linkedin_url_from_results(results: list[dict[str, Any]]) -> Optional[str]:
    for row in results:
        url = (row.get("url") or "").split("?")[0].rstrip("/")
        if "linkedin.com/in/" in url.lower():
            return url
    return None


def interests_from_text(text: str, existing: Optional[list[str]] = None) -> list[str]:
    merged = list(existing or [])
    lower = text.lower()
    for kw in _INTEREST_KEYWORDS:
        if kw in lower and kw not in [x.lower() for x in merged]:
            merged.append(kw.title() if kw.islower() else kw)
    return _norm_list(merged, limit=8)


def industry_from_text(text: str, existing: Optional[str] = None) -> Optional[str]:
    if existing and existing.strip():
        return existing.strip()
    lower = f" {text.lower()} "
    for label, keys in _INDUSTRY_KEYWORDS:
        if any(k in lower for k in keys):
            return label
    return None


def parse_linkedin_headline(title: str, content: str) -> dict[str, Optional[str]]:
    """Best-effort parse of LinkedIn search result title/content."""
    headline = (title or "").strip()
    body = (content or "").strip()
    combined = f"{headline} {body}".strip()

    name: Optional[str] = None
    job_title: Optional[str] = None
    company: Optional[str] = None

    m = _HEADLINE_RE.match(headline)
    if m:
        name = m.group(1).strip()
        rest = m.group(2).strip()
        ta = _TITLE_AT_RE.match(rest)
        if ta:
            job_title = ta.group("title").strip()
            company = ta.group("company").strip()
        else:
            job_title = rest or None

    if not name:
        nm = re.search(r"([A-Z][a-z]+(?: [A-Z][a-z]+)+)", headline)
        if nm:
            name = nm.group(1)

    return {
        "name": name,
        "title": job_title,
        "company": company,
        "industry": industry_from_text(combined),
        "interests": interests_from_text(combined),
    }


class LinkedInEnricher:
    """Enrich people records using Tavily + LinkedIn search results."""

    def __init__(self, tavily: TavilyClient):
        self._tavily = tavily

    async def research_person(
        self,
        name: str,
        *,
        email: Optional[str] = None,
        company: Optional[str] = None,
        title: Optional[str] = None,
    ) -> dict[str, Any]:
        """Return enrichment dict for one person."""
        name = (name or "").strip()
        email = (email or "").strip()
        company = (company or "").strip() or None
        title = (title or "").strip() or None

        queries: list[str] = []
        if name:
            queries.append(f'"{name}" site:linkedin.com/in')
        if name and company:
            queries.append(f'"{name}" "{company}" site:linkedin.com/in')
        if name and email and "@" in email:
            local = email.split("@", 1)[0]
            queries.append(f'"{name}" {local} linkedin')
        if name and not company:
            queries.append(f'"{name}" GTM SaaS RevOps linkedin')

        linkedin: Optional[str] = None
        snippets: list[str] = []
        parsed_name = name
        parsed_title = title
        parsed_company = company
        interests: list[str] = []
        industry: Optional[str] = None

        for q in queries:
            try:
                res = await self._tavily.search(
                    q,
                    search_depth="basic",
                    max_results=5,
                    include_domains=["linkedin.com"],
                )
            except Exception:
                # Retry without domain filter (Tavily may not support on all plans)
                try:
                    res = await self._tavily.search(q, search_depth="basic", max_results=5)
                except Exception as exc:
                    print(f"LinkedInEnricher Tavily error ({name}): {exc}")
                    continue

            rows = res.get("results") or []
            if not linkedin:
                linkedin = linkedin_url_from_results(rows)

            for row in rows:
                row_title = row.get("title") or ""
                row_content = row.get("content") or ""
                text = f"{row_title} {row_content}".strip()
                if text and text not in snippets:
                    snippets.append(text[:320])

                parsed = parse_linkedin_headline(row_title, row_content)
                if parsed.get("name") and _looks_like_person_name(parsed["name"]):
                    parsed_name = parsed["name"]
                if parsed.get("title") and not parsed_title:
                    parsed_title = parsed["title"]
                if parsed.get("company") and not parsed_company:
                    parsed_company = parsed["company"]
                if parsed.get("industry") and not industry:
                    industry = parsed["industry"]
                interests = interests_from_text(text, interests)

            if linkedin and parsed_title and industry:
                break

        if not industry and snippets:
            industry = industry_from_text(" ".join(snippets))

        notes = " | ".join(snippets[:2])
        if linkedin:
            notes = (notes + " | " if notes else "") + f"LinkedIn: {linkedin}"

        return {
            "name": parsed_name or name,
            "title": parsed_title,
            "company": parsed_company,
            "company_name": parsed_company,
            "linkedin": linkedin,
            "industry": industry,
            "interests": _norm_list(interests or ["GTM"], limit=8),
            "research_notes": notes or f"LinkedIn/Tavily lookup for {name or email or 'attendee'}",
            "source": "calendar+tavily+linkedin",
        }

    async def enrich_attendee(self, attendee: dict[str, Any]) -> dict[str, Any]:
        """Merge Tavily LinkedIn enrichment into an attendee dict."""
        intel = await self.research_person(
            attendee.get("name") or "",
            email=attendee.get("email"),
            company=attendee.get("company") or attendee.get("company_name"),
            title=attendee.get("title"),
        )

        merged_interests = interests_from_text(
            " ".join(attendee.get("interests") or []),
            intel.get("interests") or [],
        )

        notes = attendee.get("research_notes")
        if isinstance(notes, list):
            note_list = [str(x) for x in notes if x]
        elif notes:
            note_list = [str(notes)]
        else:
            note_list = []
        if intel.get("research_notes"):
            note_list.append(str(intel["research_notes"]))

        incoming_name = (attendee.get("name") or "").strip()
        resolved_name = incoming_name
        if not _looks_like_person_name(incoming_name):
            intel_name = (intel.get("name") or "").strip()
            if _looks_like_person_name(intel_name):
                resolved_name = intel_name

        return {
            **attendee,
            "name": resolved_name,
            "title": intel.get("title") or attendee.get("title"),
            "company": intel.get("company") or attendee.get("company"),
            "company_name": intel.get("company_name") or attendee.get("company_name"),
            "linkedin": intel.get("linkedin") or attendee.get("linkedin"),
            "industry": intel.get("industry") or attendee.get("industry"),
            "interests": merged_interests,
            "research_notes": note_list[:3],
            "source": intel.get("source") or attendee.get("source", "tavily+linkedin"),
        }

    async def enrich_connection(self, connection: PreMeetConnection) -> PreMeetConnection:
        """Apply LinkedIn enrichment onto a PreMeetConnection in place."""
        intel = await self.research_person(
            connection.name or "",
            email=connection.email,
            company=connection.company_name,
            title=connection.title,
        )
        if intel.get("name"):
            connection.name = intel["name"]
        if intel.get("title"):
            connection.title = intel["title"]
        if intel.get("company"):
            connection.company_name = intel["company"]
        if intel.get("linkedin"):
            connection.linkedin = intel["linkedin"]
        if intel.get("industry"):
            connection.industry = intel["industry"]
        connection.interests = interests_from_text(
            " ".join(connection.interests),
            intel.get("interests") or [],
        )
        note = intel.get("research_notes")
        if note:
            connection.research_notes = (connection.research_notes or []) + [str(note)]
            connection.research_notes = connection.research_notes[:3]
        connection.source = intel.get("source") or connection.source
        return connection
