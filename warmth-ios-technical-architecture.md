# Warmth — Technical Architecture

> _Last updated: 2026-06-22_
>
> Two-tier, name-triggered event intelligence. The **phone is intentionally
> "dumb"**: it detects names on-device, captures the conversation locally, does a
> fast rule-based extraction + pre-score, and fires the signal at the backend.
> The **compute host is "smart"**: meet pipeline, enrichment, CRM routing, and
> Gmail draft handoff (Cloud Run).

## 1. System overview (two tiers)

```
┌─────────────────────────────────────────────────────────────────┐
│  iOS APP  (Swift, on-device only)                               │
│                                                                 │
│  AVAudioEngine → trigger phrase → SFSpeechRecognizer            │
│       ↓                                                         │
│  SocialGraphEngine (LIGHTWEIGHT — Swift only)                   │
│  ├── NLTagger NER          → names, orgs                       │
│  ├── Regex RE              → (subject, predicate, object)      │
│  ├── ICP keyword proximity → fast rule-based pre-score         │
│  └── PersonNode dict       → in-memory only, session-scoped    │
│       ↓                                                         │
│  Package CapturedSignal as JSON                                 │
│  SignalClient POST (async, fire-and-forget + retry queue)       │
└──────────────────────┬──────────────────────────────────────────┘
                       │  HTTPS  ·  POST /api/signals
                       ▼
┌─────────────────────────────────────────────────────────────────┐
│  COMPUTE HOST  (Python, GCP Cloud Run)                          │
│  https://warmth-api-30164818817.us-central1.run.app             │
│                                                                 │
│  FastAPI receives CapturedSignal                                │
│       ↓                                                         │
│  MeetStageAgent → warmth / lead / cluster models                 │
│  KnowledgeGraphBuilder (NetworkX)                               │
│  HubSpot + Zero CRM sync · UnifyGTM enrichment                  │
│       ↓                                                         │
│  Gmail draft (Lightfern handoff) · web dashboard update         │
└─────────────────────────────────────────────────────────────────┘
```

**Shipped iOS app** (`iOS/Warmth-iOS/Warmth.xcodeproj`): Capture / Connections /
Settings tabs, `CapturedSignal` + `SignalClient`. Legacy wake-word pipeline
sources (`ConferenceListeningEngine`, `SignalAPIClient`) remain on disk but are
**not** in the current Xcode target.

Orchestration on the phone lives in `EventListeningEngine` / Capture flow.
Tier 2 is the Python backend in this repo; §11–14 define the contract and deployment.

## 1.1 Repository layout

Git root is **`gtmhackathon/`** (not a nested `warmth/` subfolder). Python
imports use the `warmth.*` namespace; a `warmth/` directory at the repo root
holds symlinks to `apps/`, `packages/`, `infra/`, and `services/` so
`warmth.apps.api.main:app` resolves for uvicorn and Cloud Run.

```
gtmhackathon/
├── apps/              # FastAPI backend, listener, lifecycle, agent
├── packages/          # core models, integrations (Zero, HubSpot, Gmail MCP)
├── infra/             # Firebase Firestore client
├── services/          # Google MCP bridge (Gmail drafts)
├── web/               # React dashboard (Vite)
├── iOS/Warmth-iOS/    # Native iOS app
├── warmth/            # Python package namespace (symlinks → ../apps, etc.)
├── scripts/           # deploy, demo, e2e, Gmail OAuth
├── Dockerfile         # Cloud Run image
└── Makefile           # make run-api, run-web, run-gmail-mcp
```

## 2. Components (shipped iOS app)

| Component | File | Responsibility |
|-----------|------|----------------|
| `MicrophoneStream` | `Warmth/Services/MicrophoneStream.swift` | One shared `AVAudioEngine` input tap; fans each buffer out as raw `AVAudioPCMBuffer` (for ASR) and downsampled 16 kHz mono `[Float]` (for wake word) via `AVAudioConverter`. |
| `WakeWordEngine` | `Warmth/Services/WakeWordEngine.swift` | Wraps Soniqo `SpeechWakeWord`. Builds `KeywordSpec`s from the watchlist; `push(audio:)` returns `[WakeWordDetection]`; maps matched phrase → contact name. |
| `CaptureWindow` | `Warmth/Services/CaptureWindow.swift` | 30 s on-device `SFSpeechRecognizer` session biased by `SFCustomLanguageModelData` (ICP vocab). Emits partial + final transcript. |
| `ICPVocabulary` | `Warmth/Models/ICPVocabulary.swift` | Weighted ICP keywords; mirrors backend `packages/core/models/icp.py`. Used for LM bias and scoring. |
| `SocialGraphEngine` | `Warmth/Services/SocialGraphEngine.swift` | `NLTagger` NER (people/orgs), relationship-cue detection, proximity-based ICP scoring, `PersonNode` graph accumulation. |
| `CapturedSignal` | `Warmth/Models/CapturedSignal.swift` | Primary wire model POSTed to `/api/signals` (Firebase auth + snake_case). |
| `SignalClient` | `Warmth/Services/Signal/SignalClient.swift` | Fire-and-forget uploader + retry queue; roster fetch + attendee match. |
| `FirebaseAuthService` | `Warmth/Services/Auth/FirebaseAuthService.swift` | Firebase sign-in; `CapturedSignal.user` carries `uid` + `id_token`. |
| `Signal` / `PersonNode` | `Warmth/Models/Signal.swift` | Legacy output model; `CodingKeys` map to the backend signal schema (snake_case). |
| `SignalAPIClient` | `Warmth/Services/SignalAPIClient.swift` | Legacy `POST /api/signals` client. |
| `EventListeningEngine` | `Warmth/Services/EventListeningEngine.swift` | State machine wiring wake-word capture; publishes `state`, `liveTranscript`, `lastSignal`. |
| `WatchConnectivityService` | `Warmth/Services/…` + `WarmthWatch/Services/…` | Sends `wakeWord` / `leadDetected` messages; watch plays haptic + shows lead. |
| `AudioSessionManager` | `Warmth/Services/AudioSessionManager.swift` | `AVAudioSession` config (`.playAndRecord`, `.measurement`). |
| `WatchlistProvider` | `Warmth/Services/WatchlistProvider.swift` | Names the wake word listens for; seeded sample, hydrate from CRM contacts. |
| `SettingsStore` | `Warmth/Services/Settings/SettingsStore.swift` | UserDefaults-backed backend base URL (default `http://127.0.0.1:8010`). |

## 3. State machine

`EventListeningEngine.State`:

- `.idle` — engine stopped.
- `.listening` — mic running; every 16 kHz frame is pushed to the wake-word
  detector. A detection transitions to `.capturing`.
- `.capturing(name:)` — a 30 s `CaptureWindow` is open; mic buffers are appended
  to the recognizer and wake-word pushes are suppressed (prevents re-trigger).
  On window end → run `SocialGraphEngine.ingest` → build `Signal` → handle.

After a window, `WakeWordEngine.resetSession()` clears streaming state so trailing
audio doesn't immediately re-fire, and state returns to `.listening`.

## 4. Audio format contract

- Input: device-native format from `AVAudioEngine.inputNode`.
- Wake word: **16 kHz, mono, Float32** `[Float]` (converted per buffer).
- ASR: raw `AVAudioPCMBuffer` appended directly to
  `SFSpeechAudioBufferRecognitionRequest` (the recognizer handles format).

A single `AVAudioEngine` is shared — only one tap is installed, so there is no
device contention between wake-word and capture phases.

## 5. Scoring

`SocialGraphEngine.icpScore` (0–100, mirrors the backend pre-scorer):

- Sum of `ICPVocabulary` weights for keywords attached to the `PersonNode`.
- + 50% weight for ICP keywords found in proximity (~60 chars) to the company.
- + 5 event-audio source bonus.
- Capped at 100. `Signal.isLead` when `score >= 50`.

## 6. Backend contract (primary — CapturedSignal)

`POST /api/signals` with `CapturedSignal` JSON (schema:
`packages/core/schemas/captured_signal.py`):

```json
{
  "user": { "uid": "firebase-uid", "id_token": "…" },
  "session_id": "uuid",
  "captured_at": "2026-06-20T17:00:00Z",
  "person": { "name": "Anna Lee", "org": "Acme", "role": "VP RevOps" },
  "relations": [
    { "subject": "Anna Lee", "predicate": "works_at", "object": "Acme" }
  ],
  "interests": ["RevOps", "Series B"],
  "icp_keyword_score": 72,
  "transcript_excerpt": "…transcript…",
  "device": { "model": "iPhone", "os": "iOS 26.5" }
}
```

The backend also accepts the legacy **`ConferenceAudioSignal`** shape
(`icp_pre_score`, `raw_text`, `source: conference_audio`) for the wake-word
pipeline; the shipped app uses **`CapturedSignal`** only.

### Other iOS-facing endpoints

| Method | Path | Purpose |
|--------|------|---------|
| `POST` | `/api/v1/match/attendee` | Match spoken name → GTM Hackathon roster |
| `GET` | `/api/v1/connections` | Roster first names for wake-word hydration |

## 7. Privacy

- Wake-word detection and transcription run **entirely on-device**
  (`requiresOnDeviceRecognition = true`, CoreML wake word). No audio leaves the
  phone.
- Only the structured `Signal` (text transcript + extracted entities + pre-score)
  is sent to the backend. The POST is fire-and-forget; the phone never blocks on
  the backend verdict.

## 8. External dependencies

- **Soniqo `SpeechWakeWord`** — SPM `https://github.com/soniqo/speech-swift`
  (product `SpeechWakeWord`), added to the **Warmth** target.
- Apple frameworks: `AVFoundation`, `Speech`, `NaturalLanguage`,
  `WatchConnectivity`, `WatchKit`, `SwiftUI`.

## 9. Known assumptions / follow-ups

- `EventListeningEngine.matchedName(from:)` reads
  `WakeWordDetection.keyword`. Confirm the property name against the installed
  SDK version; adjust if it's `phrase`/`label`.
- `WatchlistProvider` is seeded with sample names — wire to Zero CRM contacts.
- Background listening: the current design assumes foreground/active. Background
  audio requires the audio background mode and additional session handling.
- `RecordingEngine` (manual file recording) remains for manual capture; it no
  longer streams to any cloud ASR.

## 10. Division of responsibility (who owns what)

| Concern | iOS (Tier 1) | Compute host (Tier 2) |
|---------|--------------|------------------------|
| Audio capture / wake word / ASR | ✅ on-device | — |
| Entity + relationship extraction | ✅ lightweight (NLTagger + regex) | may re-extract / enrich |
| Graph state | in-memory, **session-scoped**, discarded on stop | ✅ **persistent** (NetworkX), cross-session |
| Scoring | fast rule-based **pre-score** (hint only) | ✅ authoritative (TGN + Spectral GCN, centrality, path scorer) |
| Thresholds / actions | none | ✅ CRM push (≥70), Faxxing + Lightfern (≥80) |
| Enrichment (UnifyGTM, Zero lookup) | — | ✅ |
| Live dashboard | — | ✅ WebSocket push |
| Lead notification to phone/watch | instant local **hint** on pre-score | authoritative confirmation via push/WS (future) |

Rule of thumb: **the phone proposes, the backend decides.** The on-device
`icp_pre_score` is advisory; the backend recomputes the real score and owns all
side effects.

## 11. Wire contract (iOS → backend)

**Endpoint:** `POST {baseURL}/api/signals`
**Headers:** `Content-Type: application/json`
**Semantics:** fire-and-forget with client-side retry queue (`SignalClient`).
Backend is idempotent on `session_id` + person + timestamp. Returns `202`
(accepted) or `200` (duplicate).

**Base URL configuration:**

| Environment | URL |
|-------------|-----|
| iOS Simulator (local) | `http://127.0.0.1:8010` |
| Physical iPhone (local) | `http://<mac-lan-ip>:8010` (same Wi‑Fi) |
| **Production (Cloud Run)** | `https://warmth-api-30164818817.us-central1.run.app` |

Set in app: **Settings → Backend → Base URL** (`SettingsStore.defaultBaseURL`).
On a physical device, `localhost` refers to the phone — always use the Mac LAN
IP for local dev, or the Cloud Run HTTPS URL for production.

**Encoding:** `CapturedSignal.makeEncoder()` — ISO-8601 dates, snake_case keys.

```jsonc
{
  "user": { "uid": "…", "id_token": "…" },
  "session_id": "…",
  "captured_at": "2026-06-20T17:00:30Z",
  "person": { "name": "Anna Lee", "org": "Acme", "role": null },
  "relations": [
    { "subject": "Anna Lee", "predicate": "works_at", "object": "Acme" }
  ],
  "interests": ["RevOps"],
  "icp_keyword_score": 72,
  "transcript_excerpt": "…full transcript…",
  "device": { "model": "iPhone", "os": "iOS 26.5" }
}
```

> **Backend alignment:**
> 1. FastAPI route `POST /api/signals` in `apps/api/routers/signals.py`.
> 2. Ingest via `apps/lifecycle/signal_ingest.py` → meet pipeline → Gmail draft.
> 3. Secrets loaded from Google Secret Manager at boot (`packages/core/secrets.py`).

## 12. Per-person context pipeline (Tier 2, backend)

Where Tier 1's `PersonNode` is a session-scoped, in-memory dict on the phone
(§1), the compute host keeps an **evolving** per-person context that accumulates
across the conversation and drives the CRM push + Faxxing personalisation.

```
transcript utterance
  → SpeakerID  (diarization speaker id)
  → mapped to a PersonNode in the PersonKnowledgeGraph
  → PersonContextBuilder.update()         (one ~30s window)
  → PersonalContext appended to the node  (accumulates over windows)
  → SignalPayload carries personal_context per person
  → KG: PersonNode.context evolves over the session
  → Zero CRM push includes the context narrative
  → Faxxing personalises the outreach sequence to communication_style + values
```

### Models (`packages/core/models/person.py`)

| Type | Role |
|------|------|
| `PersonalContext` | The **delta** read from one ~30 s window: `communication_style`, `values`, `topic_weights`, `learnings`, `pain_points`, excerpt. |
| `PersonNode` | The **evolving aggregate** for one speaker: `update(context)` folds a window in (merges traits, sums + renormalises topic weights, escalates pain intensity). Exposes `dominant_topic`, `top_pain`, `to_narrative()`. |
| `PersonKnowledgeGraph` | Session KG mapping diarization `speaker_id → PersonNode` (`get_or_create`, `people(exclude_self=True)`). Skips your own voice via `self_speaker_id`. |
| `PainPoint` | `topic` + accumulated `intensity` (0–1) → `level` (low/moderate/high). |

### Builder (`apps/listener/intelligence/person_context_builder.py`)

`PersonContextBuilder.update(kg, speaker_id, transcript_window, …)` is the
`PersonContextBuilder.update()` node in the flow. It reuses `TopicExtractor` +
`InterestAnalyzer` and layers on:
- **communication style** — lexical cues (analytical, data-driven, visionary,
  relational, pragmatic, skeptical, enthusiastic).
- **topic weights** — coarse taxonomy buckets plus salient repeated bigrams
  (e.g. "pipeline visibility") which are boosted so specifics beat generic
  buckets.
- **learnings** — net-new facts revealed (regex; substring-deduped).
- **pain intensity** — stated pains, escalated by intensifier cues.

All heuristic and key-free by design; swap for an LLM classifier behind the same
interface later.

### Downstream

- **Zero CRM** — `ZeroCRMMapper.lead_to_zero_payload_with_context(lead, person)`
  attaches `personal_context` (the narrative) plus structured
  `communication_style` / `values` / `dominant_topic` / `pain_points`
  (`packages/core/schemas/zero_crm_schema.py`). Fires at the **≥70** threshold.
- **Faxxing** — `FaxxingClient.personalize_sequence(person)`
  (`packages/integrations/faxxing/client.py`) tailors a multi-step sequence's
  tone + hook to the person's style and anchors copy on their values. Fires at
  the **≥80** threshold; result surfaces on `RoutingDecision.outreach_sequence`.

Wired in the MEET stage at `apps/lifecycle/meet.py`; `MeetingSignal` carries
`personal_context: PersonNode` and the API accepts it on `POST /api/v1/meet/signals`.

### Example narrative (what lands on the CRM record)

> Anna is analytical, data-driven, cares about accuracy. Dominant topic:
> pipeline visibility. Recently learned HubSpot has AI forecasting. High pain
> intensity around manual data entry.

Reproduce end-to-end (from repo root): `uv run python scripts/demo_person_context.py`.

## 13. Outreach drafting (Lightfern → Gmail)

Lightfern is **not a send-side API** — it's a Gmail draft assistant. Our backend
owns drafting; Lightfern polishes inside Gmail. The flow:

```
generate draft (subject/body) in-app
  → save draft locally
  → hand user a Gmail compose link (open/copy into Gmail)
  → Lightfern completes/polishes the final email in Gmail   (we never auto-send)
```

- `LightfernClient.personalize_outreach()` / `send_followup_email()`
  (`packages/integrations/lightfern/workflow.py`) return a `draft_ready` draft:
  `{ to, subject, body, gmail_compose_url, draft_id, handoff: "gmail_lightfern" }`.
- `build_gmail_compose_url()` makes the `mail.google.com/mail/?view=cm…` deep
  link (prefilled `to`/`su`/`body`). Drafts are saved under `WARMTH_DRAFTS_DIR`
  (default `drafts/`, gitignored).
- If Google MCP is configured, `PostMeetPipeline` also calls
  `GoogleMCPClient.create_email_draft()` to materialize the draft in Gmail
  (a draft, never `send_email`); the id comes back as `gmail_draft_id`.
- Web: `ConnectionDetail.tsx` renders the draft with an **"Open in Gmail ·
  Lightfern polishes it there"** link. API: `POST /api/v1/connections/{id}/followup`.
- **Quick hack:** the full captured context (PersonNode narrative + style/values/
  dominant topic/pains/learnings, interests, what-you-learned, etc.) is dumped
  into the draft body under a `--- CONTEXT FOR LIGHTFERN ---` marker, so Lightfern
  reads it directly from the Gmail draft. See `_render_context_brief()`; strip
  below the marker before actually sending.

---

## 14. Local development

From repo root (`gtmhackathon/`):

```bash
uv sync                          # install deps
make run-api                     # FastAPI on http://0.0.0.0:8010
make run-gmail-mcp               # Gmail MCP bridge on :3000 (optional)
cd web && npm run dev            # dashboard on http://localhost:5173
```

| Service | Port | Notes |
|---------|------|-------|
| Warmth API | **8010** | Default (`API_PORT` in Makefile). Port 8000 is often taken by other local projects. |
| Web dashboard | **5173** | Vite; set `web/.env` → `VITE_API_BASE_URL=http://127.0.0.1:8010` |
| Gmail MCP | **3000** | Required for real Gmail drafts (`GOOGLE_MCP_SERVER_URL`) |

Run uvicorn as `warmth.apps.api.main:app` (the `warmth/` namespace symlinks are
required). Secrets resolve from local `.env` first, then Google Secret Manager.

---

## 15. Production deployment (GCP Cloud Run)

The FastAPI backend is deployed to **Google Cloud Run** in project
`warmth-gtm-hackathon` (same GCP project as Firebase).

| | |
|---|---|
| **Service** | `warmth-api` |
| **Region** | `us-central1` |
| **URL** | https://warmth-api-30164818817.us-central1.run.app |
| **Health** | `{URL}/health` |
| **Deploy script** | `scripts/deploy_cloud_run.sh` |

```bash
# Redeploy from repo root
bash scripts/deploy_cloud_run.sh

# Or directly:
gcloud run deploy warmth-api --source . --project warmth-gtm-hackathon \
  --region us-central1 --allow-unauthenticated --quiet
```

**How it works:**
- `Dockerfile` builds a Python 3.11 image; copies `apps/` under `warmth/` for imports.
- Cloud Run sets `PORT=8080`; container runs `uvicorn warmth.apps.api.main:app`.
- Env vars: `GCP_PROJECT_ID`, `FIREBASE_PROJECT_ID`, `WEB_ALLOWED_ORIGINS=*`.
- API keys load from **Secret Manager** at startup (no secrets baked into the image).
- Firebase Firestore + Auth remain on Firebase; Cloud Run is the compute layer.

**Not yet deployed:** Gmail MCP bridge (still local `:3000`). Deploy as a second
Cloud Run service when Gmail draft automation is needed in production.

---

## 16. Connecting clients

### iOS app

1. Open `iOS/Warmth-iOS/Warmth.xcodeproj` in Xcode.
2. Run on a **physical device** (mic/speech unreliable in Simulator).
3. **Settings → Backend → Base URL:**
   - Production: `https://warmth-api-30164818817.us-central1.run.app`
   - Local device: `http://<your-mac-ip>:8010` (find IP: `ipconfig getifaddr en0`)
4. Sign in with Firebase; capture a conversation → check delivery status in Settings.
5. For local HTTP on device, add `NSAllowsLocalNetworking` to `Info.plist` if ATS blocks cleartext.

### Web dashboard

```bash
# web/.env
VITE_API_BASE_URL=https://warmth-api-30164818817.us-central1.run.app
# local: http://127.0.0.1:8010
```

```bash
cd web && npm run dev    # http://localhost:5173
```

### Verify connectivity

```bash
curl https://warmth-api-30164818817.us-central1.run.app/health
curl https://warmth-api-30164818817.us-central1.run.app/api/v1/dashboard
```
