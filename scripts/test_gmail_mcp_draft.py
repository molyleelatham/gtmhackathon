#!/usr/bin/env python3
"""Send a test Gmail draft to the Warmth client inbox via the MCP bridge."""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import httpx

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT.parent))

CLIENT = os.getenv("WARMTH_CLIENT_EMAIL", "getwarmth@gmail.com")
MCP = os.getenv("GOOGLE_MCP_SERVER_URL", "http://localhost:3000").rstrip("/")


def main() -> int:
    health = httpx.get(f"{MCP}/health", timeout=5)
    print("health:", health.status_code, health.json())

    payload = {
        "to": CLIENT,
        "subject": "Warmth Gmail MCP test",
        "body": (
            "This is a test draft from the Warmth Gmail MCP bridge.\n\n"
            "If you see this in Drafts for getwarmth@gmail.com, MCP is working.\n"
            "Lightfern would polish follow-ups here; you send manually."
        ),
    }
    res = httpx.post(f"{MCP}/gmail/drafts", json=payload, timeout=30)
    print("draft:", res.status_code)
    try:
        print(json.dumps(res.json(), indent=2))
    except Exception:
        print(res.text)
    return 0 if res.status_code == 200 else 1


if __name__ == "__main__":
    raise SystemExit(main())
