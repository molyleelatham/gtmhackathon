# Warmth — Integrated System Architecture

> **iOS/watchOS App + Python Backend**
> Conference Intelligence Platform · GTM Hackathon · June 2026

---

## System Overview

Warmth now consists of two main components:
1. **Native iOS/watchOS App** - Mobile recording with phrase trigger, manual controls, Apple Watch, and Siri shortcuts
2. **Python Backend** - Server-side processing, CRM integration, and intelligence analysis

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
│  │ - Conference Directory Scraping                             │   │
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
    "location": "Conference Hall A"
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
