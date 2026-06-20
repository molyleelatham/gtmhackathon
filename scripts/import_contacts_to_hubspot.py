#!/usr/bin/env python3
"""Import event contacts from a CSV into HubSpot.

Creates (idempotently) a set of custom contact properties to hold the enrichment
context from the CSV, then bulk-creates the contacts populated with those
properties plus the standard name/title/company fields.

Auth: HubSpot private-app token via HUBSPOT_API_KEY (or HUBSPOT_PRIVATE_APP_TOKEN).

Usage:
    python scripts/import_contacts_to_hubspot.py [/path/to/data.csv] [--dry-run]
"""

from __future__ import annotations

import csv
import os
import re
import sys
import time

import httpx

# Canonical schema is the single source of truth (shared with the agent pipeline).
_REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)
from warmth.packages.integrations.hubspot.schema import (  # noqa: E402
    CSV_COLUMN_MAP as ENRICHMENT_MAP,
    CUSTOM_PROPERTIES,
    PROPERTY_GROUP,
    PROPERTY_GROUP_LABEL,
)

BASE_URL = "https://api.hubapi.com"
DEFAULT_CSV = os.path.expanduser("~/Downloads/data.csv")

_FOOTNOTE = re.compile(r"【[^】]*】")


def _token() -> str:
    tok = os.getenv("HUBSPOT_API_KEY") or os.getenv("HUBSPOT_PRIVATE_APP_TOKEN")
    if not tok:
        sys.exit("ERROR: set HUBSPOT_API_KEY (private-app token) in the environment.")
    return tok


def _headers(tok: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {tok}", "Content-Type": "application/json"}


def _clean(s: str | None) -> str:
    return _FOOTNOTE.sub("", (s or "")).strip()


def ensure_property_group(client: httpx.Client, tok: str) -> None:
    r = client.post(
        f"{BASE_URL}/crm/v3/properties/contacts/groups",
        headers=_headers(tok),
        json={"name": PROPERTY_GROUP, "label": PROPERTY_GROUP_LABEL, "displayOrder": -1},
    )
    if r.status_code in (200, 201):
        print(f"  + property group '{PROPERTY_GROUP}' created")
    elif r.status_code == 409:
        print(f"  = property group '{PROPERTY_GROUP}' already exists")
    else:
        print(f"  ! group create returned {r.status_code}: {r.text[:200]}")


def ensure_properties(client: httpx.Client, tok: str) -> None:
    for prop in CUSTOM_PROPERTIES:
        body = {**prop, "groupName": PROPERTY_GROUP}
        r = client.post(
            f"{BASE_URL}/crm/v3/properties/contacts", headers=_headers(tok), json=body
        )
        if r.status_code in (200, 201):
            print(f"  + property '{prop['name']}' created")
        elif r.status_code == 409:
            print(f"  = property '{prop['name']}' already exists")
        else:
            print(f"  ! property '{prop['name']}' returned {r.status_code}: {r.text[:200]}")


def parse_csv(path: str) -> list[dict[str, str]]:
    contacts: list[dict[str, str]] = []
    with open(path, encoding="utf-8-sig") as f:
        for row in csv.DictReader(f):
            name = _clean(row.get("Name"))
            if not name:
                continue
            parts = name.split()
            props = {
                "firstname": parts[0],
                "lastname": " ".join(parts[1:]) if len(parts) > 1 else "",
                "jobtitle": _clean(row.get("Title")),
                "company": _clean(row.get("Fund")),
            }
            for csv_col, prop_name in ENRICHMENT_MAP.items():
                val = _clean(row.get(csv_col))
                if val:
                    props[prop_name] = val
            contacts.append({k: v for k, v in props.items() if v})
    return contacts


def batch_create(client: httpx.Client, tok: str, contacts: list[dict[str, str]]) -> None:
    created = 0
    for i in range(0, len(contacts), 100):  # HubSpot batch cap = 100
        chunk = contacts[i : i + 100]
        r = client.post(
            f"{BASE_URL}/crm/v3/objects/contacts/batch/create",
            headers=_headers(tok),
            json={"inputs": [{"properties": c} for c in chunk]},
        )
        if r.status_code in (200, 201):
            results = r.json().get("results", [])
            created += len(results)
            print(f"  + batch {i // 100 + 1}: created {len(results)} contacts")
        else:
            print(f"  ! batch {i // 100 + 1} failed {r.status_code}: {r.text[:300]}")
        time.sleep(0.2)
    print(f"\nDone. Created {created}/{len(contacts)} contacts.")


def main() -> None:
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    dry = "--dry-run" in sys.argv
    csv_path = args[0] if args else DEFAULT_CSV
    if not os.path.exists(csv_path):
        sys.exit(f"ERROR: CSV not found: {csv_path}")

    props_only = "--properties-only" in sys.argv

    contacts = parse_csv(csv_path)
    print(f"Parsed {len(contacts)} contacts from {csv_path}")
    if dry:
        import json

        print(json.dumps(contacts[:3], indent=2, ensure_ascii=False))
        print("(dry run — nothing sent)")
        return

    tok = _token()
    with httpx.Client(timeout=30) as client:
        print("Ensuring custom properties (merged HubSpot ↔ Zero schema)...")
        ensure_property_group(client, tok)
        ensure_properties(client, tok)
        if props_only:
            print("(--properties-only — skipping contact import)")
            return
        print("Creating contacts...")
        batch_create(client, tok, contacts)


if __name__ == "__main__":
    main()
