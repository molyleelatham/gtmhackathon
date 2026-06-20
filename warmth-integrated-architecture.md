# Warmth — Integrated System Architecture

> **iOS/watchOS App + Python Backend**
> Event Intelligence Platform · GTM Hackathon · June 2026

---

## System Overview

Warmth now consists of three main components:
1. **Native iOS/watchOS App** - Capture: phrase trigger, manual recording, Apple Watch, Siri shortcuts
2. **Python Backend** - Server-side processing, the warmth lifecycle pipeline, CRM/email integrations, and ML
3. **Web Dashboard** (`web/`) - Personal CRM to monitor and manage connections across the lifecycle

> **Surface split:** capture happens on **mobile**; review/management happens on the **web dashboard**. Both clients talk to the same FastAPI backend + data layer.

---

## The Warmth Lifecycle

Warmth runs every event connection through a three-stage lifecycle:

```
Onboarding ──> Before meet ──────────> Meet ───────────────> Post meet
(connect      (research, enrich,       (phrase trigger,       (Lightfern
 calendar +    warmth-score, draft      capture signals,       follow-up with
 email via     outreach, book          ML pipeline routes      full pipeline
 Google MCP)   meetings)               by warmth uplift)       context)
```

**Onboarding** — connect email + Google Calendar via Google MCP; detect which events are events.
`apps/lifecycle/onboarding.py`, `packages/integrations/google_calendar/`

**Before meet** — build the attendee dataset (calendar-derived + directory scrape + manual), enrich firmographics via **UnifyGTM**, source the **ICP profile + ICP fit from Zero CRM** (`ZeroCRMClient.get_icp_profile` / `score_icp_fit`; the local `LeadScorer` heuristic is only a fallback when Zero is unavailable), then **build warmth on top** with the ML model (`icp_score` from Zero + `warmth_score` correlated into a prioritization score), surface highest-intent leads, draft personalized outreach (Lightfern + Gmail via MCP), and book meetings.
`apps/lifecycle/premeet.py`

**Meet** — phrase trigger ("hey it's nice to meet you") starts recording. Captured signals (name, interests, origin, background, time-per-topic, takeaways) become a `MeetingSignal`, run through the ML pipeline (`packages/ml/`), and are routed:
- post-meet warmth **rose** vs. the pre-meet prediction → push to Zero CRM + Lightfern outreach
- otherwise → route to the **founder community** (nearest founder/friend match)
`apps/lifecycle/meet.py`, `apps/lifecycle/community_matcher.py`

**Post meet** — generate a follow-up email *draft* grounded in the full pipeline context (pre-meet research + captured conversation), save it locally, and hand the user a Gmail compose link. The user opens it in Gmail where **Lightfern** completes/polishes the final email (we draft; Lightfern polishes — we never auto-send). If Google MCP is configured we also create the draft directly in Gmail.
`apps/lifecycle/postmeet.py`

### ML pipeline (`packages/ml/`)

Data-source ownership: **ICP profile + ICP fit come from Zero CRM**, **enrichment comes from UnifyGTM**, and **warmth is built on top** by Warmth's own models.

Stub interfaces for the team's own models:
- `WarmthModel` — builds warmth on top of Zero ICP fit + Unify enrichment, combining ICP fit + warmth into a prioritization score (pre-meet prediction, post-meet actual, uplift)
- `LeadScorer` — intent scoring + a *fallback* ICP fit heuristic (used only when Zero CRM isn't available; Zero owns ICP fit)
- `LeadClusterer` — clustering + nearest-neighbor for community matching
- `MeetIntelligencePipeline` — orchestrates clustering → scoring → routing decision

### API surface (`apps/api/routers/`)

| Endpoint | Stage |
|----------|-------|
| `POST /api/v1/connect`, `GET /api/v1/events` | Onboarding |
| `POST /api/v1/events/{id}/premeet`, `GET /api/v1/events/{id}/leads` | Before meet |
| `POST /api/v1/meet/signals` | Meet (returns routing decision) |
| `POST /api/v1/connections/{id}/followup` | Post meet |
| `GET /api/v1/dashboard`, `/leads`, `/connections` | Web dashboard reads |

The backend ships with an in-memory demo store (`apps/api/store.py`) seeded with a sample event so the API and dashboard are demoable without external credentials.

---

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│  iOS/watchOS App (Mobile Layer)                                    │
│                                                                     │
│  ┌──────────────────────┐    ┌──────────────────────┐             │
│  │   iPhone App         │    │   Apple Watch        │             │
│  │                      │◄──►│                      │             │
│  │ - Phrase Trigger      │    │ - Widget Complications│             │
│  │ - Manual Recording    │    │ - Remote Control      │             │
│  │ - Audio Recording     │    │ - Status Display      │             │
│  │ - Real-time UI        │    │ - WatchConnectivity   │             │
│  │ - Local Storage       │    │ - Quick Actions       │             │
│  │ - Siri Shortcuts      │    │                       │             │
│  └──────────────────────┘    └──────────────────────┘             │
│              │                                                   │
│              │ REST API + WebSocket                               │
│              ▼                                                   │
└─────────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────────┐
│  Python Backend (Server Layer)                                     │
│                                                                     │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │ FastAPI Backend                                              │   │
│  │ - REST API endpoints                                        │   │
│  │ - WebSocket for real-time updates                           │   │
│  │ - Request handling & validation                            │   │
│  └──────────────────────────────────────────────────────────────┘   │
│                              │                                     │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │ Processing Services                                          │   │
│  │ - Deepgram Transcription                                    │   │
│  │ - Conversation Intelligence (Cursor SDK)                     │   │
│  │ - Lead Classification (me/team/founders/community)            │   │
│  │ - Event Directory Scraping                             │   │
│  └──────────────────────────────────────────────────────────────┘   │
│                              │                                     │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │ Integrations                                                 │   │
│  │ - Zero CRM                                                   │   │
│  │ - UnifyGTM                                                   │   │
│  │ - Google MCP (email automation)                             │   │
│  │ - Firebase Firestore (data storage)                         │   │
│  └──────────────────────────────────────────────────────────────┘   │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Directory Structure

```
gtmhackathon/
├── warmth/                          # Python Backend
│   ├── apps/                        # FastAPI applications
│   ├── packages/                    # Python packages
│   ├── infra/                       # Infrastructure (Firebase, GCP)
│   └── warmth-architecture-v2.md    # Backend architecture
│
└── iOS/                             # iOS/watchOS App (Sandboxed)
    └── Warmth-iOS/
        ├── Warmth-iOS/
        │   ├── Warmth/               # iOS App Target
        │   ├── WarmthWatch/          # watchOS App Target
        │   ├── WarmthWatchWidgetExtension/
        │   └── Shared/               # Shared code
        └── README.md                 # iOS-specific README
```

---

## iOS App → Backend Integration

### API Endpoints

**Upload Recording**
```
POST /api/recordings
Content-Type: multipart/form-data

{
  "audio_file": <audio_data>,
  "metadata": {
    "duration": 120.5,
    "device_info": "iPhone 15 Pro",
    "location": "Event Hall A"
  }
}

Response: {
  "recording_id": "rec_123",
  "status": "processing"
}
```

**Get Conversation Intelligence**
```
GET /api/conversations/{recording_id}

Response: {
  "recording_id": "rec_123",
  "transcript": "Full transcript...",
  "intelligence": {
    "topics": ["funding", "hiring"],
    "interests": ["growth", "efficiency"],
    "values": ["innovation", "collaboration"],
    "key_insights": ["Looking for Series A", "Expanding team"]
  }
}
```

**WebSocket Transcript Stream**
```
WS /ws/transcript/{recording_id}

Message: {
  "type": "transcript_chunk",
  "text": "We are looking for...",
  "timestamp": 1640995200.0,
  "confidence": 0.95
}
```

### Data Flow

1. **Recording Start**
   - User starts recording from the iPhone app or Apple Watch
   - iOS: Upload audio chunks to backend via WebSocket
   - Backend: Process with Deepgram → Store in Firebase

2. **Real-time Transcription**
   - Backend: Send transcript chunks to iOS via WebSocket
   - iOS: Display real-time transcription to user

3. **Intelligence Processing**
   - Backend: Analyze transcript with Cursor SDK
   - Backend: Extract topics, interests, values
   - Backend: Store conversation intelligence in Firebase

4. **CRM Integration**
   - Backend: Enrich data via UnifyGTM → Zero CRM
   - Backend: Draft emails via Google MCP
   - iOS: Display CRM sync status

---

## WatchConnectivity Protocol

### iPhone → Watch Messages

**Recording State Update**
```json
{
  "action": "recordingStateChanged",
  "isRecording": true,
  "timestamp": 1640995200.0
}
```

**Transcript Update**
```json
{
  "action": "transcriptUpdate",
  "transcript": "We are looking for Series A funding...",
  "timestamp": 1640995200.0
}
```

### Watch → iPhone Messages

**Toggle Recording**
```json
{
  "action": "toggleRecording",
  "timestamp": 1640995200.0
}
```

**Request Status**
```json
{
  "action": "requestStatus",
  "timestamp": 1640995200.0
}
```

---

## Configuration

### iOS App Configuration

**Environment Variables (iOS)**
```swift
// AppConstants.swift
struct AppConstants {
    static let backendAPIURL = "https://your-backend-api.com"
    static let webSocketURL = "wss://your-backend-api.com/ws/transcript"
}
```

### Backend Configuration

**Environment Variables (Python)**
```bash
# .env
BACKEND_API_URL=https://your-backend-api.com
IOS_ALLOWED_ORIGINS=https://your-frontend.com
DEEPGRAM_API_KEY=xxx
ZERO_CRM_API_KEY=xxx
UNIFY_GTM_API_KEY=xxx
GOOGLE_MCP_CREDENTIALS=xxx
FIREBASE_PROJECT_ID=xxx
```

---

## Deployment Strategy

### iOS App
- **Development**: TestFlight for beta testing
- **Production**: App Store
- **Backend URL**: Configurable via build settings

### Python Backend
- **Development**: Local development with Docker
- **Staging**: GCP Cloud Run (test environment)
- **Production**: GCP Cloud Run (production)

---

## Security Considerations

### iOS App Security
- API key storage in Keychain
- Certificate pinning for backend API
- End-to-end encryption for sensitive data
- Biometric authentication for app access

### Backend Security
- JWT authentication for API endpoints
- Rate limiting per device
- Input validation and sanitization
- CORS configuration for iOS origins

---

## Development Workflow

### iOS Development
```bash
cd iOS/Warmth-iOS
open Warmth-iOS.xcodeproj
# Develop in Xcode
```

### Backend Development
```bash
cd warmth
uv sync
uv run uvicorn apps.api.main:app --reload
```

### Integration Testing
1. Start backend locally
2. Configure iOS app to point to local backend
3. Test full recording → transcription → intelligence pipeline

---

## Benefits of This Architecture

1. **Sandboxed iOS Development**: iOS team can work independently
2. **Clear Separation**: Mobile logic separate from server logic
3. **Flexibility**: Can deploy backend updates without app store review
4. **Scalability**: Backend can scale independently of mobile clients
5. **Testing**: Easier to test components in isolation

---

This integrated architecture allows you to leverage both native iOS capabilities and powerful server-side processing while maintaining clean separation of concerns.
