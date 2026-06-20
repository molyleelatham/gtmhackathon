# Warmth — Technical Architecture

> Two-tier, name-triggered event intelligence. The **phone is intentionally
> "dumb"**: it detects names on-device, captures the conversation locally, does a
> fast rule-based extraction + pre-score, and fires the signal at the backend.
> The **compute host is "smart"**: persistent graph ML, enrichment, and the CRM /
> follow-up thresholds.

## 1. System overview (two tiers)

```
┌─────────────────────────────────────────────────────────────────┐
│  iOS APP  (Swift, on-device only)                               │
│                                                                 │
│  AVAudioEngine → Soniqo WakeWord → SFSpeechRecognizer          │
│       ↓                                                         │
│  SocialGraphEngine (LIGHTWEIGHT — Swift only)                   │
│  ├── NLTagger NER          → names, orgs                       │
│  ├── Regex RE              → (subject, predicate, object)      │
│  ├── ICP keyword proximity → fast rule-based pre-score         │
│  └── PersonNode dict       → in-memory only, session-scoped    │
│       ↓                                                         │
│  Package signal as JSON payload                                 │
│  URLSession POST (async, fire-and-forget)                       │
└──────────────────────┬──────────────────────────────────────────┘
                       │  HTTPS  ·  POST /api/signals
                       ▼
┌─────────────────────────────────────────────────────────────────┐
│  COMPUTE HOST  (Python, Modal / cloud server)   ← backend agent │
│                                                                 │
│  FastAPI receives signal payload                                │
│       ↓                                                         │
│  KnowledgeGraphBuilder (NetworkX) — persistent across sessions │
│  TGN memory update → temporal signal decay                     │
│  Spectral GCN → P(ICP fit)                                     │
│  Social path scorer → warm intro path                          │
│  Eigenvector centrality                                         │
│       ↓                                                         │
│  Enrichment: UnifyGTM + Zero CRM contact lookup                │
│       ↓                                                         │
│  Score ≥ 70  → Zero CRM push                                   │
│  Score ≥ 80  → Faxxing sequence trigger                        │
│  Score ≥ 80  → Lightfern GTM workflow                          │
│       ↓                                                         │
│  WebSocket push → Dashboard UI (live updates)                  │
└─────────────────────────────────────────────────────────────────┘
```

Tier 1 (this codebase: `iOS/`) is detailed below. Tier 2 (the compute host) is
owned by the backend agent; §10–11 define the contract between them.

Orchestration on the phone lives in `EventListeningEngine`.

## 2. Components

| Component | File | Responsibility |
|-----------|------|----------------|
| `MicrophoneStream` | `Warmth/Services/MicrophoneStream.swift` | One shared `AVAudioEngine` input tap; fans each buffer out as raw `AVAudioPCMBuffer` (for ASR) and downsampled 16 kHz mono `[Float]` (for wake word) via `AVAudioConverter`. |
| `WakeWordEngine` | `Warmth/Services/WakeWordEngine.swift` | Wraps Soniqo `SpeechWakeWord`. Builds `KeywordSpec`s from the watchlist; `push(audio:)` returns `[WakeWordDetection]`; maps matched phrase → contact name. |
| `CaptureWindow` | `Warmth/Services/CaptureWindow.swift` | 30 s on-device `SFSpeechRecognizer` session biased by `SFCustomLanguageModelData` (ICP vocab). Emits partial + final transcript. |
| `ICPVocabulary` | `Warmth/Models/ICPVocabulary.swift` | Weighted ICP keywords; mirrors backend `packages/core/models/icp.py`. Used for LM bias and scoring. |
| `SocialGraphEngine` | `Warmth/Services/SocialGraphEngine.swift` | `NLTagger` NER (people/orgs), relationship-cue detection, proximity-based ICP scoring, `PersonNode` graph accumulation. |
| `Signal` / `PersonNode` | `Warmth/Models/Signal.swift` | Output model; `CodingKeys` map to the backend signal schema (snake_case). |
| `SignalAPIClient` | `Warmth/Services/SignalAPIClient.swift` | `POST /api/signals` (snake_case keys, ISO-8601 dates). Base URL from `WARMTH_API_BASE_URL`. |
| `EventListeningEngine` | `Warmth/Services/EventListeningEngine.swift` | State machine wiring all of the above; publishes `state`, `liveTranscript`, `lastSignal`. |
| `WatchConnectivityService` | `Warmth/Services/…` + `WarmthWatch/Services/…` | Sends `wakeWord` / `leadDetected` messages; watch plays haptic + shows lead. |
| `AudioSessionManager` | `Warmth/Services/AudioSessionManager.swift` | `AVAudioSession` config (`.playAndRecord`, `.measurement`). |
| `WatchlistProvider` | `Warmth/Services/WatchlistProvider.swift` | Names the wake word listens for; seeded sample, hydrate from CRM contacts. |

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

## 6. Backend contract

`POST /api/signals` with `Signal` JSON:

```json
{
  "id": "uuid",
  "person": { "name": "Anna Lee", "company": "Acme", "icp_keywords_hit": ["RevOps"], … },
  "company": { "name": "Acme", "icp_keywords_hit": ["Series B"] },
  "relationships": [ { "subject": "Anna Lee", "kind": "works_at", "object": "Acme" } ],
  "icp_pre_score": 65,
  "raw_text": "…transcript…",
  "source": "event_audio",
  "detected_at": "2026-06-20T17:00:00Z"
}
```

Field names align with `packages/core/models/signal.py` via `Signal.CodingKeys`.

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

**Endpoint:** `POST {WARMTH_API_BASE_URL}/api/signals`
**Headers:** `Content-Type: application/json`
**Semantics:** fire-and-forget; iOS sends **every** signal (no client-side
gating). Backend must be idempotent on `id` (UUID) and tolerant of partial data
(many fields optional). Return `2xx` quickly; do heavy work async.

**Encoding:** `JSONEncoder` with `keyEncodingStrategy = .convertToSnakeCase` and
`dateEncodingStrategy = .iso8601`.

```jsonc
{
  "id": "0f4e…",                       // UUID, idempotency key
  "person": {
    "name": "Anna Lee",
    "company": "Acme",                 // nullable
    "title": null,
    "related_names": ["James Ford"],   // array (from a Set)
    "icp_keywords_hit": ["RevOps"],
    "first_seen": "2026-06-20T17:00:00Z",
    "last_seen":  "2026-06-20T17:00:30Z",
    "mention_count": 2
  },
  "company": {                         // nullable
    "name": "Acme",
    "icp_keywords_hit": ["Series B"]
  },
  "relationships": [
    { "subject": "Anna Lee", "kind": "works_at", "object": "Acme" }
  ],
  "icp_pre_score": 65,                 // 0–100, ADVISORY pre-score
  "raw_text": "…full transcript…",
  "source": "event_audio",
  "detected_at": "2026-06-20T17:00:30Z"
}
```

`relationship.kind` enum: `works_with` · `works_at` · `reports_to` · `knows` ·
`introduced_by`.

> **Backend-agent action items to stay aligned:**
> 1. FastAPI route `POST /api/signals` accepting the schema above (snake_case).
>    It maps cleanly onto `packages/core/models/signal.py` — keep them in sync.
> 2. Treat `icp_pre_score` as a hint; compute the authoritative score in the
>    graph layer. Apply 70 / 80 thresholds backend-side only.
> 3. Idempotency on `id`; tolerate null `company` / `title` and empty arrays.
> 4. (Future) expose a push/WebSocket channel so confirmed leads can buzz the
>    phone/watch authoritatively; today the watch buzzes on the local pre-score.

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

Reproduce end-to-end (from the repo root): `python warmth/scripts/demo_person_context.py`.

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
