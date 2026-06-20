# Warmth — Integrated Conference Intelligence Platform

> **GTM Hackathon · June 2026**
> Stack: Python (Backend) + iOS/watchOS (Mobile) · FastAPI · Cursor SDK · Deepgram · Zero CRM · UnifyGTM · Google MCP

## Overview

Warmth is an integrated conference intelligence platform combining:
- **Native iOS/watchOS App** - Mobile recording with phrase trigger ("Hi, I'm Zack"), manual controls, Apple Watch, and Siri shortcuts
- **Python Backend** - Server-side processing, CRM integration, and AI analysis

When you attend conferences, start recording from the iPhone app (phrase or manual), Apple Watch, or Siri; the backend processes transcriptions, extracts intelligence, and manages CRM integrations.

## Key Features

- **🎤 Phrase + Manual Recording**: Say **"Hi, I'm Zack"** on iPhone (foreground), or use manual controls, Apple Watch complications, and Siri shortcuts
- **👥 Lead Classification**: Automatically route leads to me/team/founders/community
- **📋 Directory Scraping**: Scrape conference directories for attendees by interests
- **🤝 First Connections**: Auto-enrich and draft emails via Google MCP
- **🧠 Conversation Intelligence**: Capture interests, topics, values, and insights
- **🔄 CRM Integration**: Send all intelligence to Zero CRM automatically
- **🤖 Auto Agents**: Create automated outbound strategies
- **👨‍👩‍👧‍👦 Community Sharing**: Share intelligence with closed groups

## Architecture

- **Backend**: [warmth-architecture-v2.md](./warmth-architecture-v2.md) - Python backend architecture
- **iOS**: [iOS/Warmth-iOS/README.md](./iOS/Warmth-iOS/README.md) - iOS/watchOS app documentation
- **Integration**: [warmth-integrated-architecture.md](./warmth-integrated-architecture.md) - Full system integration

## Directory Structure

```
warmth/
├── apps/                    # Python FastAPI backend
├── packages/                # Python packages and integrations
├── infra/                   # Infrastructure (Firebase, GCP)
├── iOS/                     # iOS/watchOS app (sandboxed)
│   └── Warmth-iOS/         # Native iOS project
├── tests/                   # Python tests
└── scripts/                 # Utility scripts
```

## Quick Start

```bash
# Install dependencies
cd warmth
uv sync

# Install audio dependencies (macOS)
brew install portaudio
pip install pyaudio rnnoise-python

# Install audio dependencies (Ubuntu)
sudo apt install portaudio19-dev && pip install pyaudio rnnoise-python

# Copy environment template
cp .env.example .env
# Edit .env with your API keys

# Run development server
uv run uvicorn apps.api.main:app --reload --port 8000

# Run listener service
uv run python apps/listener/main.py
```

## Environment Variables

Required environment variables (see `.env.example`):

- **ASR**: `DEEPGRAM_API_KEY`
- **Integrations**: `ZERO_CRM_API_KEY`, `UNIFY_GTM_API_KEY`, `CURSOR_SDK_API_KEY`
- **Google MCP**: `GOOGLE_MCP_CREDENTIALS`, `GOOGLE_MCP_SERVER_URL`
- **Signal Sources**: `TAVILY_API_KEY`
- **Firebase**: `FIREBASE_PROJECT_ID`, `FIREBASE_SERVICE_ACCOUNT_KEY`, `FIREBASE_DATABASE_URL`
- **GCP**: `GCP_PROJECT_ID`, `GCP_SERVICE_ACCOUNT_KEY`, `GCP_REGION`, `PUBSUB_TOPIC`
- **Community**: `COMMUNITY_GROUPS_ENABLED`, `COMMUNITY_PERMISSIONS`
- **User Config**: `USER_ROLE`, `TEAM_SIZE`, `COMPANY_STAGE`

## Integrations

- **Signal Detection**: Deepgram Nova-3 (ASR), Tavily Search
- **Lead Classification**: Custom routing logic (me/team/founders/community)
- **Directory Scraping**: BeautifulSoup (web), PyPDF (documents)
- **Enrichment**: UnifyGTM (firmographics), Zero CRM (contacts)
- **Conversation Intelligence**: Cursor SDK (AI-powered analysis)
- **Email Automation**: Google MCP (Gmail + Google Docs)
- **Auto Agents**: Cursor SDK (outbound strategy generation)
- **Community Sharing**: Firebase Firestore (permissions + sharing)
- **Infrastructure**: Firebase Firestore (database), GCP Cloud Functions (serverless)

## Development

```bash
# Run tests
uv run pytest

# Run specific test
uv run pytest tests/unit/test_keyword_engine.py

# Test microphone pipeline
uv run python scripts/test_mic_pipeline.py

# Test Tavily integration
uv run python scripts/test_tavily_pipeline.py
```

## Deployment

Warmth is designed for deployment on Google Cloud Platform:

- **API**: GCP Cloud Run
- **Workers**: GCP Cloud Functions
- **Database**: Firebase Firestore
- **Messaging**: GCP Pub/Sub
- **Scheduling**: GCP Cloud Scheduler

See `infra/terraform/` for infrastructure-as-code deployment configurations.

## License

MIT License — see LICENSE file for details
