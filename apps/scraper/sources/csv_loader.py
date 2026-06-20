"""CSV event attendee loader.

Maps a CSV export (e.g. from a pre-event research spreadsheet) into the
normalised attendee dict format used by the pre-meet pipeline.

Supported CSV schemas:

  Schema A — Warmth investor/event export (data.csv):
    Columns: Name, Title, Fund, Fund Description, Fund Size (Approx.),
             Typical Stage, Sector Focus, Classification, Notes

  Schema B — Generic attendee CSV:
    Columns: name/Name, email/Email, title/Title, company/Company,
             domain/Domain, linkedin/LinkedIn, bio/Bio

The loader auto-detects the schema from the column headers.
"""

from __future__ import annotations

import csv
import re
from pathlib import Path
from typing import Any, Optional


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _clean(val: Optional[str]) -> Optional[str]:
    """Strip whitespace/non-breaking spaces; return None if empty."""
    if not val:
        return None
    v = val.replace("\u202f", " ").replace("\u2011", "-").strip()
    return v or None


def _parse_interests(sector_focus: Optional[str], classification: Optional[str]) -> list[str]:
    """Turn sector / classification columns into an interests list."""
    interests: list[str] = []
    if sector_focus:
        for part in re.split(r"[,&]+", sector_focus):
            p = part.strip().strip("‑-").strip()
            if p and p.lower() not in ("varied", "n/a", ""):
                interests.append(p)
    if classification:
        cl = classification.strip()
        if cl not in ("", "N/A"):
            interests.append(cl)
    return interests[:6]


def _derive_domain(company_name: Optional[str]) -> Optional[str]:
    """Best-effort company domain from name (no network call)."""
    if not company_name:
        return None
    slug = company_name.lower()
    slug = re.sub(r"[^a-z0-9]+", "", slug)
    return f"{slug}.com" if slug else None


# ---------------------------------------------------------------------------
# Schema A: Warmth investor/event export
# ---------------------------------------------------------------------------

_SCHEMA_A_REQUIRED = {"Name", "Title", "Fund"}


def _is_schema_a(fieldnames: list[str]) -> bool:
    return _SCHEMA_A_REQUIRED.issubset(set(fieldnames))


def _map_schema_a(row: dict[str, str]) -> dict[str, Any]:
    name = _clean(row.get("Name"))
    title = _clean(row.get("Title"))
    company = _clean(row.get("Fund"))
    fund_desc = _clean(row.get("Fund Description"))
    fund_size = _clean(row.get("Fund Size (Approx.)"))
    stage = _clean(row.get("Typical Stage"))
    sector = _clean(row.get("Sector Focus"))
    classification = _clean(row.get("Classification"))
    notes = _clean(row.get("Notes"))

    interests = _parse_interests(sector, classification)
    if stage and stage not in ("N/A",):
        interests.append(f"Stage: {stage}")

    # Build a research note from the fund description + notes columns
    research_parts: list[str] = []
    if fund_desc:
        research_parts.append(fund_desc)
    if fund_size and fund_size != "N/A":
        research_parts.append(f"Fund size: {fund_size}")
    if notes:
        research_parts.append(notes)

    return {
        "name": name,
        "email": None,                          # not in this CSV schema
        "title": title,
        "company": company,
        "company_domain": _derive_domain(company),
        "linkedin": None,
        "bio": fund_desc,
        "interests": interests,
        "funding_stage": stage if stage not in (None, "N/A") else None,
        "research_notes": " | ".join(research_parts) if research_parts else None,
        "classification": classification,       # extra field for ICP scoring
        "sector_focus": sector,
        "source": "csv",
    }


# ---------------------------------------------------------------------------
# Schema B: Generic attendee CSV
# ---------------------------------------------------------------------------

_SCHEMA_B_NAME_KEYS = ("name", "Name", "full_name", "Full Name")
_SCHEMA_B_EMAIL_KEYS = ("email", "Email", "email_address")
_SCHEMA_B_COMPANY_KEYS = ("company", "Company", "organization", "Organization")


def _map_schema_b(row: dict[str, str]) -> dict[str, Any]:
    def _get(*keys: str) -> Optional[str]:
        for k in keys:
            if row.get(k):
                return _clean(row[k])
        return None

    name = _get(*_SCHEMA_B_NAME_KEYS)
    email = _get(*_SCHEMA_B_EMAIL_KEYS)
    company = _get(*_SCHEMA_B_COMPANY_KEYS)

    return {
        "name": name,
        "email": email,
        "title": _get("title", "Title", "job_title"),
        "company": company,
        "company_domain": _get("domain", "Domain") or _derive_domain(company),
        "linkedin": _get("linkedin", "LinkedIn", "linkedin_url"),
        "bio": _get("bio", "Bio", "description"),
        "interests": [],
        "funding_stage": _get("funding_stage", "stage"),
        "research_notes": _get("notes", "Notes"),
        "source": "csv",
    }


# ---------------------------------------------------------------------------
# Public loader
# ---------------------------------------------------------------------------

def load_csv_attendees(
    path: str,
    *,
    max_rows: int = 10,
    skip_classifications: Optional[list[str]] = None,
) -> list[dict[str, Any]]:
    """Load attendees from a CSV file.

    Args:
        path:                  Path to the CSV file.
        max_rows:              Maximum number of rows to return (default 10).
        skip_classifications:  Schema-A classification values to exclude, e.g.
                               ``["Potential Customer"]`` to keep only investors.

    Returns:
        List of normalised attendee dicts.
    """
    skip = {s.lower() for s in (skip_classifications or [])}

    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"CSV file not found: {path}")

    attendees: list[dict[str, Any]] = []

    with open(p, newline="", encoding="utf-8-sig") as fh:
        reader = csv.DictReader(fh)
        fieldnames = list(reader.fieldnames or [])
        use_schema_a = _is_schema_a(fieldnames)

        for row in reader:
            if len(attendees) >= max_rows:
                break

            if use_schema_a:
                att = _map_schema_a(row)
                # Skip unwanted classifications
                if skip and (att.get("classification") or "").lower() in skip:
                    continue
            else:
                att = _map_schema_b(row)

            if att.get("name"):
                attendees.append(att)

    return attendees
