# Warmth — GTM Hackathon Submission

> **Conference Intelligence Platform**
> GTM Hackathon · June 20, 2026

---

## What We Built

Warmth turns chaotic conference networking into structured, scored, and actionable GTM intelligence — in real time.

Most tools help you _after_ the fact. Warmth is live during the conversation. You walk the floor at SaaStr, say a phrase, and Warmth silently captures the conversation, scores the person against your ICP, builds a per-speaker personality model, and drops a ready-to-send follow-up email in your Gmail before you've reached the next booth.

The result: a warm, scored lead with a narrative CRM record and a personalized outreach draft — automatically — from a 60-second hallway conversation.

---

## The Problem

Conference networking produces almost zero structured GTM data. You leave with a stack of business cards or a pocketful of vague memories. Even if you diligently log everything that evening, you've lost the nuance: what did they actually care about, what pain were they expressing, how did they communicate?

Warmth solves this at the moment of capture — not in retrospect.

---

## Three Surfaces, One Backend

| Surface | Role | When |
|---------|------|------|
| **iOS + Apple Watch** | Capture — phrase trigger, live transcription, on-device NLP | On the conference floor |
| **Web Dashboard** | Review — events, warmth scores, leads, follow-ups | Before/after the event |
| **Python Backend** | Intelligence pipeline — ML scoring, CRM routing, email generation | Always-on server |

---

## The Lifecycle

Every conference connection moves through four stages:

```
Onboarding ──> Before Meet ──────> Meet ──────────────> Post Meet
(calendar +    (enrich via          (phrase trigger,      (Gmail draft →
 Gmail via      UnifyGTM, score      on-device NLP,        Lightfern polishes →
 Google MCP)    via Zero CRM,        ML pipeline,          human sends)
                draft outreach)      warmth routing)
```

### Stage 1 — Onboarding

Connect Google Calendar + Gmail via Google MCP. Warmth scans upcoming events, detects conferences automatically, and seeds the lifecycle for each one. No manual setup.

### Stage 2 — Before Meet

- **Attendee dataset**: built from calendar invites + conference directory scraping (Playwright)
- **Enrichment**: firmographics, funding stage, technographics via **UnifyGTM**
- **ICP fit**: scored by **Zero CRM** (Warmth explicitly does not own ICP — Zero does)
- **Pre-meet warmth prediction**: `WarmthModel` runs before you've met anyone, producing a prioritization score for the web dashboard
- **Outreach drafts**: personalized via **Lightfern + Gmail MCP** before you walk in

### Stage 3 — Meet (the live moment)

1. Say **"hey it's nice to meet you"** (phrase trigger) or tap to record manually
2. `SpeechService` transcribes on-device via `SFSpeechRecognizer`
3. `SocialGraphEngine` extracts structured data from the transcript: names, organizations, ICP keyword matches, relations
4. A `CapturedSignal` is POSTed to the backend (fire-and-forget with offline retry queue)
5. Backend runs `MeetStageAgent` → `MeetIntelligencePipeline` → routing decision
6. Gmail draft lands in `getwarmth@gmail.com` for Lightfern to polish

### Stage 4 — Post Meet

**Lightfern** receives a Gmail draft containing three layers of context:

- ICP score + warmth score + uplift delta
- Lead data (company, contact, signal source)
- Per-person narrative (communication style, values, dominant topic, pain points)

Lightfern polishes the draft. The human reviews and sends. Loop closed.

---

## The Technical Core

### Warmth Scoring — Two Independent Dimensions

Warmth separates two things that most tools collapse together:

| Dimension | Source | Meaning |
|-----------|--------|---------|
| **ICP Score** | Zero CRM | How well does this person/company match your ideal customer profile? |
| **Warmth Score** | Warmth ML | How warm is the _relationship_ — intent, engagement, rapport, topic relevance? |

A perfect ICP fit can be completely cold. A non-ICP person can be extremely warm. Warmth captures both, then computes **uplift**: post-meet actual score vs. pre-meet predicted score. Uplift drives routing.

```
uplift > threshold  → Zero CRM push + Faxxing outreach + Lightfern Gmail draft
uplift flat/down    → route to founder community (nearest-neighbor match)
```

### ML Pipeline

```
diarized transcript ([{speaker, text}], self_speaker_id)
    → MeetEncoder             per-person context + MeetingSignal
    → MeetIntelligencePipeline  warmth/lead/cluster → RoutingDecision
    → warmth uplift?  yes → Zero CRM + Faxxing + Gmail draft
                      no  → founder community
```

**`MeetEncoder`** turns a raw diarized transcript into a structured `MeetingSignal`: name, company, interests, per-topic time allocation, what you learned, most interesting moment, and the evolved `PersonNode` for the primary speaker.

**`MeetIntelligencePipeline`** runs three models:

- `WarmthModel` — builds warmth on top of Zero ICP fit + Unify enrichment; computes pre-meet prediction, post-meet actual, and uplift delta
- `LeadScorer` — intent scoring + ICP fit heuristic fallback
- `LeadClusterer` — nearest-neighbor for community routing when warmth is flat

### Per-Person Context Model

The most technically interesting piece. Every ~30-second transcript window produces a `PersonalContext` delta that accumulates into an evolving `PersonNode`:

```python
class PersonalContext(BaseModel):
    communication_style: list[str]   # ["analytical", "data-driven"]
    values:              list[str]   # ["accuracy", "team autonomy"]
    topic_weights:       dict[str, float]  # {"pipeline visibility": 0.38, ...}
    learnings:           list[str]   # ["just adopted HubSpot AI forecasting"]
    pain_points:         list[PainPoint]  # [PainPoint(topic="manual data entry", intensity=0.8)]
    transcript_excerpt:  str | None
```

`PersonNode.update(context)` folds each window in: merges style traits, sums + renormalizes topic weights, escalates pain intensity. At the end of the conversation, `to_narrative()` produces the Zero CRM record:

> Anna is analytical, data-driven, cares about accuracy. Dominant topic: pipeline visibility. Recently learned HubSpot has AI forecasting. High pain intensity around manual data entry.

This narrative is what Lightfern receives and what the CRM stores — not a bag of keywords, but a person model.

**Two extraction modes:**

1. **Heuristic (default)** — lexical style cues, `InterestAnalyzer`, `TopicExtractor` topic buckets, salient repeated bigrams, regex learning patterns, intensifier-scored pain points. Zero latency, no API key required.
2. **AI agent (Cursor SDK)** — `AgentContextExtractor` runs a one-shot agent prompt against the window. Heuristics fill any gaps. ~15-25s per window, runs off the event loop via `asyncio.to_thread`. `MeetEncoder(use_agent=True)` wires it automatically.

### iOS App — Liquid Glass on the Conference Floor

Built in SwiftUI with iOS 26 "Liquid Glass" APIs throughout.

**`AppModel`** is the root composition object — owns all services and is injected via SwiftUI's `@Environment`. Protocol-based services (`SpeechServicing`, `SocialGraphProcessing`, `SignalSending`) mean every screen uses mocks in previews.

**`RecordOrb`** is the hero of the Capture screen: an ember-gradient orb that breathes when idle, emits pulsing rings while listening for the wake phrase, and morphs into a live waveform during recording. Audio level drives the orb scale in real time.

**`SocialGraphEngine`** runs entirely on-device:

- Apple NaturalLanguage NER for names + organizations
- Regex-based relation extraction ("works at", "founded", "interested in")
- ICP keyword proximity scoring
- Session deduplication (merges repeated mentions of the same person)

**`SignalClient`** POSTs to the backend with an offline retry queue — if you're in a basement with no cell signal, signals queue and flush when connectivity returns.

**Apple Watch integration**: `WatchSessionService` bridges iPhone ↔ Watch via `WCSession`. Watch complications give one-tap start/stop from the wrist. `watch.onStartRequested` / `watch.onStopRequested` hooks wire directly into `AppModel.capturePerson()`.

### Backend API

FastAPI backend with a clean lifecycle router structure:

| Endpoint | Stage |
|----------|-------|
| `POST /api/signals` | iOS ingress → `MeetStageAgent` → Gmail draft |
| `POST /api/v1/meet/encode` | Diarized transcript → `MeetingSignal` + KG |
| `POST /api/v1/meet/process` | Encode + score + Gmail handoff in one call |
| `GET /api/v1/dashboard` | Web dashboard reads |
| `POST /api/v1/events/{id}/premeet` | Before-meet pipeline trigger |

The signals endpoint accepts both payload schemas (current `CapturedSignal` from Xcode + legacy `ConferenceAudioSignal` from the Porcupine wake-word pipeline) and routes transparently.

Demo store (`apps/api/store.py`) seeds a sample conference so the API and web dashboard are fully demoable with no external credentials.

### Web Dashboard

React + Vite + Tailwind with the same warm glassmorphism design language as iOS — frosted translucent cards over warm white backgrounds, Space Grotesk font, ember/orange/red ICP heat ramp.

Routes: Dashboard → Events → Before-Meet Pipeline → Connections → Follow-ups.

The interest knowledge graph (`graph_builder.py`) builds a per-person node graph connecting individuals to their interests, topics, values, and pain points — visualized on the connection detail view.

### Infrastructure

- **Firebase Firestore** — signal storage + dedup
- **Google Secret Manager** — secrets loaded at startup via `load_secrets_into_env()`; local `.env` overrides for dev
- **Google MCP** — calendar read + Gmail draft creation
- **GCP credentials** — service account for Firestore + Secret Manager
- **Docker + Makefile** — one-command local stack (`make run-api`)

---

## Integration Map

| Integration | What Warmth uses it for |
|-------------|------------------------|
| **Zero CRM** | ICP ownership + fit scoring + contact lookup + lead push |
| **UnifyGTM** | Firmographics, funding stage, technographics enrichment |
| **Google MCP** | Calendar event scan + Gmail draft creation |
| **Lightfern** | Outreach sequencing + Gmail draft polish |
| **Faxxing** | Outreach sequence personalization per communication style |
| **HubSpot MCP** | Source-of-record upsert on high-warmth CRM paths |
| **Deepgram Nova-3** | Real-time conference ASR (WebSocket stream, diarization) |
| **Tavily** | Signal detection for passive background listener |
| **Porcupine** | On-device wake word detection ("Hey Anna") |
| **Cursor SDK** | AI-agent context extraction (`AgentContextExtractor`) |
| **Firebase** | Signal storage, dedup, auth |

---

## What Makes It Different

**The person model, not the lead record.** Most conference tools create a contact with a job title and company. Warmth builds a behavioral model: how this person communicates, what they actually care about, where their pain intensity is highest. That model drives the CRM record _and_ the outreach — so follow-up emails feel like they came from someone who was paying attention.

**Warmth as a distinct dimension.** Separating ICP fit (Zero's data) from relationship warmth (Warmth's model) means the system can correctly route a warm non-ICP person to the founder community and a cold perfect-ICP person to a lower-priority follow-up queue. Most tools conflate these.

**Capture happens on the phone, not in the cloud.** On-device NLP via Apple NaturalLanguage means the social graph extracts even when you have no signal. The retry queue handles the network gap. Privacy-sensitive audio never has to leave the device for the initial extraction pass.

**The handoff is Gmail, not a proprietary inbox.** By dropping a structured draft into Gmail, Warmth integrates with whatever email workflow already exists — Lightfern, a human editor, or just direct send. No new tool to log into.

---

## Team

Built in one day at the GTM Hackathon, June 20, 2026.
