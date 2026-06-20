# Warmth — Product Overview

> **Conference Intelligence Platform · GTM Hackathon · June 2026**
> Stack: Python (Backend) + iOS/watchOS (Mobile) + React (Web) · FastAPI · Zero CRM · UnifyGTM · Google MCP · Lightfern

---

## What is Warmth?

**Warmth** is a conference intelligence platform that turns chaotic networking into a structured, scored, and actionable personal CRM.

At a conference you might meet 50+ people. Most tools only help *after* the fact. Warmth is designed to:

1. **Prepare** — know who's worth meeting before you walk the floor
2. **Capture** — record and extract intelligence *during* the conversation, hands-free
3. **Route** — decide whether a connection is a hot lead, a warm intro, or better shared with someone in your network
4. **Follow up** — send context-rich emails grounded in both pre-meet research and what you actually talked about

---

## Three Surfaces, One Backend

| Surface | Role | When you use it |
|---------|------|-----------------|
| **iOS + Apple Watch** | **Capture** — phrase trigger, manual recording, on-device NLP | On the conference floor |
| **Web Dashboard** | **Review & manage** — events, leads, warmth scores, follow-ups | Before/after the event, at your desk |
| **Python Backend** | **Intelligence pipeline** — ML scoring, CRM, email, enrichment | Always running server-side |

**Surface split:** capture happens on **mobile**; review/management happens on the **web dashboard**. Both clients talk to the same FastAPI backend + data layer.

---

## The Warmth Lifecycle

Every conference connection moves through four stages:

```
Onboarding ──> Before meet ──────────> Meet ───────────────> Post meet
(connect      (research, enrich,       (phrase trigger,       (Lightfern
 calendar +    warmth-score, draft      capture signals,       follow-up with
 email via     outreach, book          ML pipeline routes      full pipeline
 Google MCP)   meetings)               by warmth uplift)       context)
```

### Stage 1 — Onboarding

- Connect **Google Calendar + Gmail** via Google MCP
- Scan upcoming events and **detect conferences** (e.g. "SaaStr Annual 2026")
- Seeds the lifecycle for each detected event

**Code:** `apps/lifecycle/onboarding.py`, `packages/integrations/google_calendar/`

### Stage 2 — Before Meet

- Build an **attendee dataset** from calendar invites, conference directory scraping, and manual input
- **Enrich** firmographics via **UnifyGTM** (company size, industry, funding stage)
- Pull **ICP profile + ICP fit** from **Zero CRM** (Warmth does not own ICP — Zero does)
- Run the **WarmthModel** to predict pre-meet warmth and produce a **prioritization score**
- Surface top leads on the web dashboard; draft personalized outreach via **Lightfern + Gmail**

**Code:** `apps/lifecycle/premeet.py`

### Stage 3 — Meet (the mobile moment)

1. You say **"hey it's nice to meet you"** (wake phrase) or tap to record manually
2. On-device speech recognition transcribes the conversation
3. **SocialGraphEngine** extracts structured signals locally:
   - Names & organizations (Apple NaturalLanguage NER)
   - Relations ("works at", "founded", "interested in")
   - ICP keyword proximity score
4. A `CapturedSignal` is POSTed to the backend
5. Backend runs the **MeetIntelligencePipeline** and returns a **routing decision**

**Code:** `apps/lifecycle/meet.py`, `packages/ml/pipeline.py`

### Stage 4 — Post Meet

- **Lightfern** generates a follow-up email using:
  - Pre-meet research ("parasocial" context)
  - Live conversation signals (interests, takeaways, topic time)
- Optionally sends via **Google MCP (Gmail)**

**Code:** `apps/lifecycle/postmeet.py`

---

## The "Warmth" Concept

Warmth separates two dimensions and combines them:

| Dimension | Source | Meaning |
|-----------|--------|---------|
| **ICP Score** | Zero CRM | How well does this person/company match your ideal customer profile? |
| **Warmth Score** | Warmth ML model | How warm is the *relationship* — intent, engagement, rapport, topic relevance? |

**Data ownership is explicit:**
- **ICP fit** → Zero CRM
- **Enrichment** → UnifyGTM
- **Warmth scoring** → Warmth's own ML models (built on top of the above)

### Routing logic

After a meeting, Warmth compares **post-meet actual score** vs. **pre-meet predicted score**:

| Outcome | Action |
|---------|--------|
| **Warmth went UP** (uplift) | Push to **Zero CRM + Lightfern outreach** |
| **Warmth flat or down** | Route to **founder community** (nearest friend/founder match) |

A perfect ICP fit can still be cold. A non-ICP person can be extremely warm. Warmth captures both.

---

## System Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│  iOS/watchOS App (Mobile Layer)                                    │
│                                                                     │
│  ┌──────────────────────┐    ┌──────────────────────┐             │
│  │   iPhone App         │    │   Apple Watch        │             │
│  │ - Phrase Trigger      │◄──►│ - Widget Complications│             │
│  │ - Manual Recording    │    │ - Remote Control      │             │
│  │ - On-device NLP       │    │ - WatchConnectivity   │             │
│  └──────────────────────┘    └──────────────────────┘             │
│              │ REST API + WebSocket                               │
└─────────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────────┐
│  Python Backend (Server Layer)                                     │
│                                                                     │
│  FastAPI → Lifecycle Pipelines → ML Pipeline → Integrations        │
│                                                                     │
│  Integrations: Zero CRM · UnifyGTM · Google MCP · Lightfern      │
│                Deepgram · Tavily · Firebase Firestore               │
└─────────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────────┐
│  Web Dashboard (React + Vite + Tailwind)                           │
│  Dashboard · Events · Pre-Meet Pipeline · Connections · Follow-ups  │
└─────────────────────────────────────────────────────────────────────┘
```

---

## iOS Capture Pipeline

| Component | Responsibility |
|-----------|----------------|
| `AppModel` | Root composition — owns all services, injected via SwiftUI environment |
| `SpeechService` | AVAudioEngine → wake word → on-device `SFSpeechRecognizer` |
| `SocialGraphEngine` | 100% on-device NLP extraction (NER, regex relations, ICP keywords) |
| `SessionCaptureLog` | In-memory session log; merges duplicate names |
| `SignalClient` | Fire-and-forget POST to backend with offline retry queue |
| `FirebaseAuthService` | Auth + ID tokens for signal payloads |

**App shell:** Onboarding → three-tab Liquid Glass UI (**Capture · Connections · Settings**)

### Capture flow

1. User says wake phrase or taps record
2. `SpeechService` transcribes on-device
3. `SocialGraphEngine` extracts `PersonNode` from transcript
4. `AppModel.capturePerson()` logs locally + sends `CapturedSignal` to backend
5. `SignalClient` POSTs to `{baseURL}/api/signals` (fire-and-forget with retry queue)

---

## Backend API Surface

| Endpoint | Stage |
|----------|-------|
| `POST /api/v1/connect`, `GET /api/v1/events` | Onboarding |
| `POST /api/v1/events/{id}/premeet`, `GET /api/v1/events/{id}/leads` | Before meet |
| `POST /api/v1/meet/signals` | Meet (returns routing decision) |
| `POST /api/v1/connections/{id}/followup` | Post meet |
| `GET /api/v1/dashboard`, `/leads`, `/connections` | Web dashboard reads |

The backend ships with an in-memory demo store (`apps/api/store.py`) seeded with a sample conference so the API and dashboard are demoable without external credentials.

---

## ML Pipeline (`packages/ml/`)

| Model | Purpose |
|-------|---------|
| `WarmthModel` | Builds warmth on top of Zero ICP fit + Unify enrichment; pre-meet prediction + post-meet actual + uplift |
| `LeadScorer` | Intent scoring + fallback ICP fit heuristic (when Zero unavailable) |
| `LeadClusterer` | Clustering + nearest-neighbor for community matching |
| `MeetIntelligencePipeline` | Orchestrates clustering → scoring → routing decision |

---

## Web Dashboard

| Route | Purpose |
|-------|---------|
| `/` | Dashboard — stats, upcoming events, top leads |
| `/events` | Detected conferences |
| `/events/:id` | Before-meet pipeline + ranked leads |
| `/connections` | All connections sorted by warmth |
| `/connections/:id` | Detail view — scores, routing, follow-up actions |

---

## External Integrations

| Integration | Role |
|-------------|------|
| **Zero CRM** | ICP profile + fit + lead storage |
| **UnifyGTM** | Firmographic enrichment |
| **Google MCP** | Calendar · Gmail · Docs |
| **Lightfern** | Personalized email drafts |
| **Deepgram Nova-3** | ASR transcription |
| **Tavily** | Signal search (listener service) |
| **Firebase Firestore** | Persistent storage |
| **GCP Cloud Run / Pub/Sub** | Deployment |

---

## End-to-End User Journey

### Before the event
- Connect calendar via onboarding
- Review ranked leads on web dashboard
- Send pre-meet outreach drafts

### On the floor
- Meet someone new
- Say wake phrase — conversation captured automatically
- See live transcript on phone

### After the conversation
- Warmth scores & routes the connection
- Hot lead → CRM + outreach draft
- Lukewarm → intro to founder friend in your network

### Back at hotel
- Review connections on web dashboard
- Approve & send follow-ups

---

## Implementation Status

| Area | Status |
|------|--------|
| iOS capture pipeline (`SpeechService`, `SocialGraphEngine`, `SignalClient`) | Implemented |
| iOS UI views (`CaptureView`, `ConnectionsView`, etc.) | Referenced, in progress |
| Wake word detection | Stub provider (manual trigger works) |
| Backend lifecycle pipelines | Orchestration wired; external calls stubbed |
| ML models | Stub scoring logic with stable contracts |
| Web dashboard | Implemented with demo data |
| Demo store | Seeded in-memory store for offline demo |

---

## Repo Links

| Doc | Path |
|-----|------|
| Main README | `README.md` |
| Integrated architecture | `warmth-integrated-architecture.md` |
| iOS README | `iOS/Warmth-iOS/README.md` |
| Web README | `web/README.md` |

---

## Summary

**Warmth = Conference capture + warmth scoring + intelligent routing + automated follow-up.**

- **Mobile** captures the moment (phrase trigger, speech, on-device NLP)
- **Backend** enriches, scores, and decides where each connection goes
- **Web** lets you review, prioritize, and act on your growing personal CRM
- **Warmth uplift** (did the real conversation exceed the pre-meet prediction?) is the key routing signal
