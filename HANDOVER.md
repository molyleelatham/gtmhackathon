# Warmth — Handover

_Last updated: 2026-06-20_

Quick-start context for whoever picks this up next. Covers what's built, what's
wired, what's blocked, and the exact next steps.

## TL;DR

Warmth is an event-intelligence platform with two capture surfaces and one
**Gmail-first handoff**:

```
Capture (iPhone) → encode + score → Gmail draft (SCORES / LEAD / PERSON context)
  → open getwarmth@gmail.com in Gmail → Lightfern polishes → human sends
```

- **Tier 1 — iOS (`iOS/Warmth-iOS/`)**: Xcode app (`Warmth.xcodeproj`) with
  on-device speech, social-graph extraction, and `SignalClient` →
  `POST /api/signals` (`CapturedSignal` schema).
- **Tier 2 — Python backend (`warmth/`)**: meet pipeline, warmth scoring,
  optional Zero CRM + Faxxing, **primary output = Gmail draft** for Lightfern.
- **Gmail client inbox**: `getwarmth@gmail.com` (`WARMTH_CLIENT_EMAIL`).

Full design: **`warmth-ios-technical-architecture.md`** · Gmail MCP:
**`docs/GMAIL_MCP.md`**

---

## What's built (iOS)

Xcode project: **`iOS/Warmth-iOS/Warmth.xcodeproj`** (XcodeGen, PR #3 on `main`).

| Area | Location |
|------|----------|
| App shell + tabs (Capture / Connections / Settings) | `Warmth-iOS/Warmth/App/`, `Features/` |
| Wire model → backend | `Warmth/Models/CapturedSignal.swift` |
| Upload + retry queue | `Warmth/Services/Signal/SignalClient.swift` |
| Social graph | `Warmth/Services/SocialGraph/SocialGraphEngine.swift` |
| Speech + wake phrase | `Warmth/Services/Speech/SpeechService.swift` |
| Watch bridge (embedded companion) | `WarmthWatch/`, `WATCH_INTEGRATION.md` |
| Backend URL (Settings) | default production `https://warmth-api-30164818817.us-central1.run.app`; local dev `http://127.0.0.1:8000` |

Legacy wake-word pipeline sources still exist under
`Warmth-iOS/Warmth-iOS/Warmth/Services/` (`EventListeningEngine`, etc.) but
are **not** in the Xcode target — the shipped app uses `CapturedSignal`.

Setup: `iOS/Warmth-iOS/README.md` · open `Warmth.xcodeproj` · physical device
recommended.

---

## What's built (Backend)

### E2E ingress + meet pipeline

| Endpoint | Purpose |
|----------|---------|
| `POST /api/signals` | iOS `CapturedSignal` (+ legacy `EventAudioSignal`) → `MeetStageAgent` → store + Gmail draft |
| `POST /api/v1/meet/encode` | Diarized transcript → `MeetingSignal` + KG |
| `POST /api/v1/meet/process` | Encode + score + Gmail handoff |
| `POST /api/v1/meet/signals` | Structured `MeetingSignal` → route + draft |
| `GET /api/v1/dashboard` | Web CRM dashboard |

Key files:

| Area | File |
|------|------|
| iOS ingress router | `apps/api/routers/signals.py` |
| Ingest + persist | `apps/lifecycle/signal_ingest.py` |
| Meet orchestrator (single Lightfern path) | `apps/agent/meet_pipeline.py` |
| Demo store | `apps/api/store.py` |
| iOS schema | `packages/core/schemas/captured_signal.py` |
| Legacy iOS schema | `packages/core/schemas/event_audio_signal.py` |

Run API from repo root (`gtmhackathon/`):

```bash
cd warmth && make run-api
```

Smoke test:

```bash
PYTHONPATH=. warmth/.venv/bin/python warmth/scripts/e2e_smoke.py
```

### Per-person context pipeline

```
transcript → SpeakerID → PersonNode → PersonContextBuilder → SignalPayload
  → KG → Zero CRM narrative → Faxxing (secondary) → Gmail draft (primary)
```

| Area | File |
|------|------|
| Person models | `packages/core/models/person.py` |
| Context builder + Cursor agent extractor | `apps/listener/intelligence/person_context_builder.py`, `agent_extractor.py` |
| Meet encoder | `apps/listener/intelligence/meet_encoder.py` |
| Zero CRM mapper | `packages/integrations/zero_crm/mapper.py` |
| Faxxing stub | `packages/integrations/faxxing/client.py` |
| Local meet test server | `scripts/serve_meet_local.py` |

---

## Outreach drafting (Lightfern → Gmail)

Lightfern is a **Gmail draft assistant, not a send API**. We draft → save locally
→ hand the user a Gmail compose link → Lightfern polishes in Gmail. We never
auto-send.

- `LightfernClient` returns `draft_ready` with `gmail_compose_url`, `client_email`,
  and a context brief (`SCORES`, `LEAD`, `PERSON`, `CLIENT`) under
  `--- CONTEXT FOR LIGHTFERN ---` (`packages/integrations/lightfern/workflow.py`).
- **Client inbox**: `getwarmth@gmail.com` — set via `WARMTH_CLIENT_EMAIL` /
  `WARMTH_CLIENT_NAME=Warmth`.
- Web dashboard: `ConnectionDetail.tsx` → "Open in Gmail · Lightfern polishes there".

---

## Gmail MCP (getwarmth@gmail.com)

The MCP **bridge server** creates real drafts in the Warmth Gmail inbox.

> **Do not** point `GOOGLE_MCP_CREDENTIALS` at `gcp-credentials.json` (service
> account). Personal Gmail requires **OAuth**.

### Setup (one time)

1. Google Cloud Console → enable **Gmail API** → OAuth Desktop client → save
   `google-oauth-client.json`
2. `make install-gmail && make setup-gmail-mcp` (sign in as **getwarmth@gmail.com**)
3. Set in `.env`:

```bash
GOOGLE_MCP_CREDENTIALS=google-gmail-oauth.json
GOOGLE_MCP_SERVER_URL=http://localhost:3000
WARMTH_CLIENT_EMAIL=getwarmth@gmail.com
WARMTH_CLIENT_NAME=Warmth
```

### Run (two terminals)

```bash
make run-gmail-mcp   # port 3000
make run-api         # port 8000
```

Full guide: **`docs/GMAIL_MCP.md`**

| Component | Path |
|-----------|------|
| MCP bridge server | `services/google_mcp_server/main.py` |
| OAuth setup script | `scripts/setup_gmail_oauth.py` |
| HTTP client | `packages/integrations/google_mcp/client.py` |

---

## Web dashboard

```bash
cd web && npm run build && npm run dev
```

`web/src/lib/{api,auth,useAsync}` talk to `/api/v1`. Demo auth user:
`getwarmth@gmail.com`.

---

## Credentials & infra status

- **Zero CRM**: API key + workspace id in `.env` (gitignored).
- **UnifyGTM**: `UNIFY_GTM_API_KEY` in `.env`.
- **Tavily**: key in `.env`.
- **GCP**: project `warmth-gtm-hackathon`; service account at `gcp-credentials.json`
  (Firestore/Secret Manager — **not** for Gmail).
- **Gmail MCP**: OAuth token at `google-gmail-oauth.json` (gitignored; run setup script).
- **Secret Manager**: `scripts/secrets_sync.py` push/pull; `load_secrets_into_env()` at API boot.

> Rotate any keys that were pasted in plaintext before a public demo.

---

## Suggested next steps

1. **Gmail MCP**: run `make setup-gmail-mcp` as getwarmth@gmail.com; start bridge + API; confirm drafts appear in Gmail.
2. **iOS device test**: set backend URL to Mac LAN IP; capture a person → verify `POST /api/signals` → draft link on dashboard.
3. **Watch**: re-enable `WarmthWatch` target per `WATCH_INTEGRATION.md`.
4. **Production**: deploy API + MCP bridge; point iOS Settings base URL at deployed host.

---

## Agent / local dev notes

- Package imports: run from **`gtmhackathon/`** with `PYTHONPATH=.` or `make run-api`.
- Cursor agent extraction: `WARMTH_USE_AGENT=1` or `"use_agent": true` on meet endpoints (~15–25 s/window).
- `FaxxingClient` is a stub unless `FAXXING_API_URL` is set.
- Skills: `.cursor/skills/warmth-meet-pipeline/`, `warmth-person-context/`.
