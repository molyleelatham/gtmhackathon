#!/usr/bin/env python3
"""Quick E2E smoke script — run with API already up or via in-process ASGI."""
from __future__ import annotations

import asyncio
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))


async def run_inprocess() -> int:
    from httpx import ASGITransport, AsyncClient
    from warmth.apps.api.main import app

    captured = {
        "user": {"uid": "demo-user", "id_token": "smoke"},
        "session_id": f"smoke-{datetime.now(timezone.utc).timestamp()}",
        "captured_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "person": {"name": "Sam Rivera", "org": "Glide", "role": "RevOps Lead"},
        "relations": [],
        "interests": ["RevOps", "attribution"],
        "icp_keyword_score": 72,
        "transcript_excerpt": "Sam is rebuilding RevOps after Series B.",
        "device": {"model": "iPhone", "os": "iOS 26.0"},
    }

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://smoke") as client:
        health = await client.get("/health")
        signal = await client.post("/api/signals", json=captured)
        dashboard = await client.get("/api/v1/dashboard")

    print("health:", health.status_code, health.json())
    print("signal:", signal.status_code)
    print(json.dumps(signal.json(), indent=2)[:1200])
    print("dashboard connections:", dashboard.json().get("connections"))
    return 0 if signal.status_code in (200, 202) else 1


if __name__ == "__main__":
    raise SystemExit(asyncio.run(run_inprocess()))
