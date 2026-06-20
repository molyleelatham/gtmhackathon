# Warmth — Passive Social Listening × GTM Signal Intelligence

> **GTM Hackathon · June 2026**
> Stack: Python · FastAPI · Cursor SDK · Zero CRM · UnifyGTM · Lightfern · Firebase · GCP

## Overview

Warmth is a passive social listening system that detects GTM (Go-To-Market) signals from various sources including conference audio and Tavily search. It enriches leads using UnifyGTM, scores them with Cursor SDK, and routes them to Zero CRM and Lightfern workflows.

## Architecture

See [warmth-architecture.md](./warmth-architecture.md) for detailed technical architecture and repository structure.

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
- **Integrations**: `ZERO_CRM_API_KEY`, `UNIFY_GTM_API_KEY`, `LIGHTFERN_WEBHOOK_URL`, `CURSOR_SDK_API_KEY`
- **Signal Sources**: `TAVILY_API_KEY`
- **Firebase**: `FIREBASE_PROJECT_ID`, `FIREBASE_SERVICE_ACCOUNT_KEY`, `FIREBASE_DATABASE_URL`
- **GCP**: `GCP_PROJECT_ID`, `GCP_SERVICE_ACCOUNT_KEY`, `GCP_REGION`, `PUBSUB_TOPIC`

## Integrations

- **Signal Detection**: Deepgram Nova-3 (ASR), Tavily Search
- **Enrichment**: UnifyGTM (firmographics), Zero CRM (contacts)
- **Scoring**: Cursor SDK (AI-powered lead scoring)
- **Activation**: Zero CRM (lead management), Lightfern (GTM workflows)
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