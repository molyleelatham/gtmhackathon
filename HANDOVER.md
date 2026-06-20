# Warmth — Handover

_Last updated: 2026-06-20_

Quick-start context for whoever picks this up next. Covers what's built, what's
wired, what's blocked, and the exact next steps.

## TL;DR

Warmth is a two-tier conference-intelligence app:

- **Tier 1 — iOS (this repo, `iOS/`)**: on-device, name-triggered listening.
  Detects contact names → 30 s on-device transcription → lightweight social-graph
  extraction + rule-based pre-score → fire-and-forget `POST /api/signals`.
- **Tier 2 — Compute host (Python, owned by the backend agent)**: persistent
  graph ML (NetworkX / TGN / Spectral GCN), enrichment (UnifyGTM, Zero CRM),
  thresholds (CRM ≥70, Faxxing + Lightfern ≥80), WebSocket dashboard.

Full design + the iOS↔backend contract: **`warmth-ios-technical-architecture.md`**
(see §10 division of responsibility, §11 wire contract).

## What's built (iOS, Tier 1)

All under `iOS/Warmth-iOS/Warmth-iOS/`. Every file passes `swiftc -parse`.

| Area | File |
|------|------|
| Mic (16 kHz Float32 + raw buffers) | `Warmth/Services/MicrophoneStream.swift` |
| Wake word (Soniqo `SpeechWakeWord`) | `Warmth/Services/WakeWordEngine.swift` |
| 30 s capture + ICP custom LM | `Warmth/Services/CaptureWindow.swift` |
| Social graph (NLTagger + regex + score) | `Warmth/Services/SocialGraphEngine.swift` |
| Output model | `Warmth/Models/Signal.swift` |
| ICP vocab (mirrors backend) | `Warmth/Models/ICPVocabulary.swift` |
| Backend client (`POST /api/signals`) | `Warmth/Services/SignalAPIClient.swift` |
| Orchestrator (state machine) | `Warmth/Services/ConferenceListeningEngine.swift` |
| Audio session | `Warmth/Services/AudioSessionManager.swift` |
| Watchlist (names to listen for) | `Warmth/Services/WatchlistProvider.swift` |
| Root UI | `Warmth/Views/ListeningView.swift`, `Warmth/App/WarmthApp.swift` |
| Watch haptic + lead banner | `WarmthWatch/Services/WatchConnectivityService.swift`, `WarmthWatch/Views/RecordingStateView.swift` |

Removed: Deepgram (transcription is on-device via `SFSpeechRecognizer`). The old
phrase-trigger ("hey it's nice to meet you") is superseded by name wake words;
`PhraseTriggerEngine.swift` is unused.

## What's built (Backend, Tier 2): per-person context pipeline

A per-speaker context pipeline that accumulates who each person is across a
session and feeds the Zero CRM push + Faxxing outreach. Flow:

```
transcript utterance → SpeakerID → PersonNode → PersonContextBuilder.update()
  → PersonalContext accumulates over 30s windows → SignalPayload.personal_context
  → KG: PersonNode.context evolves → Zero CRM narrative → Faxxing sequence
```

| Area | File |
|------|------|
| `PersonalContext` / `PersonNode` / `PersonKnowledgeGraph` / `PainPoint` | `packages/core/models/person.py` |
| `PersonContextBuilder` (30 s window → context, folds into node) | `apps/listener/intelligence/person_context_builder.py` |
| `personal_context` on the meet signal | `packages/core/models/meeting_signal.py`, `apps/api/routers/meet.py` |
| Zero CRM narrative + structured fields | `packages/integrations/zero_crm/mapper.py` (`lead_to_zero_payload_with_context`), `packages/core/schemas/zero_crm_schema.py` |
| Faxxing outreach personalisation (style + values) | `packages/integrations/faxxing/client.py` |
| Wired into the MEET stage (CRM push + Faxxing) | `apps/lifecycle/meet.py` (`RoutingDecision.outreach_sequence`) |
| Runnable end-to-end demo | `scripts/demo_person_context.py` |

`PersonNode.to_narrative()` produces the CRM prose, e.g. _"Anna is analytical,
data-driven, cares about accuracy. Dominant topic: pipeline visibility. Recently
learned HubSpot has AI forecasting. High pain intensity around manual data
entry."_ Faxxing then tailors the outreach tone/hook to `communication_style` +
`values`.

Run the demo from the repo root (the dir containing `warmth/`):

```bash
python warmth/scripts/demo_person_context.py
```

### Outreach drafting (Lightfern → Gmail)

Lightfern is a **Gmail draft assistant, not a send API**. We draft → save locally
→ hand the user a Gmail compose link → Lightfern polishes in Gmail. We never
auto-send.

- `LightfernClient.personalize_outreach()` / `send_followup_email()` return a
  `draft_ready` draft with `to`, `subject`, `body`, `gmail_compose_url`,
  `draft_id` (`packages/integrations/lightfern/workflow.py`). Drafts save under
  `WARMTH_DRAFTS_DIR` (default `drafts/`, gitignored).
- `PostMeetPipeline` additionally calls `GoogleMCPClient.create_email_draft()`
  (a Gmail **draft**, not send) when MCP is configured.
- Web `ConnectionDetail.tsx` shows an "Open in Gmail" handoff link. See
  `warmth-ios-technical-architecture.md` §13.

Notes / follow-ups:
- Extraction is **heuristic** (lexical cues + regex + bigram salience), built to
  run without API keys. Swap `PersonContextBuilder._infer_style` /
  `_extract_learnings` and the topic weighting for an LLM classifier behind the
  same interface when ready.
- `FaxxingClient` is a stub that drafts locally; set `FAXXING_API_URL` /
  `FAXXING_API_KEY` to call the real API (no spec was available at build time).
- Speaker→identity mapping currently takes name/company from caller-supplied
  attrs; hydrate from diarization + the iOS `PersonNode`/watchlist when wired.
- Package runs as `warmth.*` from the repo root (relative imports assume a parent
  `warmth` package); run `uvicorn` / `pytest` from above `warmth/`.

## ⚠️ Build blockers (must do before it compiles)

1. **No Xcode project is checked in** — there is no `.xcodeproj` / `Package.swift`.
   The Swift files exist but aren't in a buildable target. SourceKit shows
   "Failed to build module Foundation/SwiftUI" on every file purely because of
   this (not real code bugs). **Create the Xcode project** (targets: `Warmth`,
   `WarmthWatch`, widget) and add these sources.
2. **Add the SPM dependency**: `https://github.com/soniqo/speech-swift`
   (product `SpeechWakeWord`) to the **Warmth** target.
3. **Info.plist** keys: `NSMicrophoneUsageDescription`,
   `NSSpeechRecognitionUsageDescription`, and `WARMTH_API_BASE_URL`.
4. **One API assumption to verify**: `ConferenceListeningEngine.matchedName(from:)`
   reads `WakeWordDetection.keyword`. If the SDK names it `phrase`/`label`, fix
   that one line.

See `iOS/Warmth-iOS/README.md` for full setup steps.

## What the backend agent needs to align (Tier 2)

From `warmth-ios-technical-architecture.md` §11:

1. `POST /api/signals` accepting the snake_case payload (maps to
   `packages/core/models/signal.py`).
2. Treat `icp_pre_score` as advisory; compute the authoritative score in the
   graph layer; apply 70/80 thresholds **backend-side only**.
3. Idempotent on `id` (UUID); tolerate null `company`/`title` and empty arrays.
4. (Future) push/WebSocket channel to authoritatively buzz phone/watch.

## Credentials & infra status

- **Zero CRM**: API key + workspace id are in `.env` (gitignored). Workspace id
  `6e938aa3-df49-4fa8-8c03-77d2a485c455`. Zero MCP is connected.
- **UnifyGTM**: API key in `.env` as `UNIFY_API_KEY` / `UNIFY_GTM_API_KEY`. The
  official SDK (`import unify`) authenticates with an `x-api-key` header and uses
  base path `api.unifygtm.com/data/v1` (objects/records/attributes).
- **Tavily**: key in `.env`.
- **GCP**: project `warmth-gtm-hackathon`; service-account JSON at
  `gcp-credentials.json` (gitignored), referenced via `GOOGLE_APPLICATION_CREDENTIALS`.
  Service account `warmth-backend@…` authenticates successfully and has
  `datastore.user`, `firebase.admin`, `pubsub.publisher`, **`secretmanager.admin`**.
- **Google Secret Manager (team secrets)**: ✅ **connected and seeded.** API
  enabled; the `secretmanager.admin` role is granted to the service account.
  Tooling: `packages/core/secrets.py` (runtime loader) + `scripts/secrets_sync.py`
  (`push` / `pull` / `list`). **11 secrets pushed** from `.env` and verified by
  read-back (e.g. `ZERO_WORKSPACE_ID` round-trips):
  `CURSOR_SDK_API_KEY, DEEPGRAM_API_KEY, FIREBASE_PROJECT_ID,
  FIREBASE_SERVICE_ACCOUNT_KEY, GCP_SERVICE_ACCOUNT_KEY,
  GOOGLE_APPLICATION_CREDENTIALS, TAVILY_API_KEY, UNIFY_API_KEY, UNIFY_GTM_API_KEY,
  ZERO_CRM_API_KEY, ZERO_WORKSPACE_ID`.
  - Team workflow: a teammate sets `GCP_PROJECT_ID` + ADC
    (`gcloud auth application-default login`) and runs
    `python scripts/secrets_sync.py pull` to populate their `.env`; at runtime
    `load_secrets_into_env()` fills any gaps from Secret Manager.
  - **Cleanup needed**: `DEEPGRAM_API_KEY` is obsolete (Deepgram removed — on-device
    ASR now); and `GOOGLE_APPLICATION_CREDENTIALS` / `GCP_SERVICE_ACCOUNT_KEY` /
    `FIREBASE_SERVICE_ACCOUNT_KEY` were pushed as **local file paths**, not secret
    values — either store the JSON contents instead or add them to the skip list in
    `scripts/secrets_sync.py`.

> Several API keys were pasted in plaintext during setup — rotate them before any
> public demo.

## Suggested next steps

1. **iOS**: create the Xcode project, add the SPM package + Info.plist, build on a
   physical device, verify the "hey Anna" → capture → POST flow end-to-end.
2. **Backend**: stand up `POST /api/signals` per the contract; confirm a real
   payload from the phone round-trips into the graph layer.
3. **Watchlist**: hydrate `WatchlistProvider` from Zero CRM contacts.
4. **Auth/transport**: add an auth header to `SignalAPIClient` if the host
   requires it; set `WARMTH_API_BASE_URL` to the deployed URL.
