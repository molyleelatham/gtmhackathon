# Warmth — Integrated Event Intelligence Platform

> **GTM Hackathon · June 2026**
> Stack: Python (Backend) + iOS/watchOS (Mobile) · FastAPI · Cursor SDK · Apple Speech (on-device ASR) · Zero CRM · UnifyGTM · Google MCP

## Overview

Warmth is an integrated event intelligence platform combining:
- **Native iOS/watchOS App** - Passive name-triggered listening: the phone detects contact names (wake words), captures the conversation on-device, builds a social graph, and scores leads against your ICP
- **Python Backend** - Server-side processing, CRM integration, and AI analysis

When you attend events, the iPhone listens for contact names; hearing one opens a 30-second on-device capture window that extracts people, companies, relationships, and ICP signals. Qualified leads buzz your Apple Watch and flow to the backend → Zero CRM → follow-up sequence.

## Key Features

- **🎤 Name-Triggered Passive Listening**: The phone wakes on contact names ("hey Anna", a first name) via a CoreML wake-word detector, then transcribes on-device with ICP-biased speech recognition
- **👥 Lead Classification**: Automatically route leads to me/team/founders/community
- **📋 Directory Scraping**: Scrape event directories for attendees by interests
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

# Run development server (same entrypoint as Cloud Run)
make run-api

# Or via Docker Compose (matches production layout)
docker compose up api

# Run listener service
uv run python apps/listener/main.py
```

## Environment Variables

Required environment variables (see `.env.example`):

- **Integrations**: `ZERO_CRM_API_KEY`, `UNIFY_GTM_API_KEY`, `CURSOR_SDK_API_KEY`
- **Google MCP**: `GOOGLE_MCP_CREDENTIALS`, `GOOGLE_MCP_SERVER_URL`
- **Signal Sources**: `TAVILY_API_KEY`
- **Firebase**: `FIREBASE_PROJECT_ID`, `FIREBASE_SERVICE_ACCOUNT_KEY`, `FIREBASE_DATABASE_URL`
- **API auth / persistence** (production — see `infra/cloudrun-env.yaml`):
  - `REQUIRE_FIREBASE_AUTH=true` — iOS/web must send `Authorization: Bearer <firebase_id_token>`
  - `USE_FIRESTORE_STORE=true` — persist dashboard events, connections, and meet results in Firestore (not in-memory only)
- **GCP**: `GCP_PROJECT_ID`, `GCP_SERVICE_ACCOUNT_KEY`, `GCP_REGION`, `PUBSUB_TOPIC`
- **Community**: `COMMUNITY_GROUPS_ENABLED`, `COMMUNITY_PERMISSIONS`
- **User Config**: `USER_ROLE`, `TEAM_SIZE`, `COMPANY_STAGE`

## Team Secrets (Google Secret Manager)

Rather than passing `.env` files around, shared API keys live in **Google Secret
Manager** for the team's GCP project. At startup the app pulls them into the
process environment, so all existing `os.getenv(...)` calls keep working.

**One-time setup (each developer):**

```bash
gcloud auth application-default login   # ADC for Secret Manager access
export GCP_PROJECT_ID=<your-shared-project-id>   # or set in .env
```

**Seed the shared secrets once (from a working .env):**

```bash
make secrets-push        # uploads non-empty secrets from .env → Secret Manager
```

**Teammates pull them:**

```bash
make secrets-pull        # writes the shared secrets into their local .env
# or rely on runtime loading — just `make run-api` and secrets load automatically
make secrets-list        # see what's stored
```

**How resolution works at runtime** (`packages/core/secrets.py`):
1. Local `.env` / real environment wins (developer overrides for testing).
2. Anything still unset is filled from Secret Manager.
3. If no `GCP_PROJECT_ID`, no credentials, or the SDK is missing, it logs a
   warning and falls back to `.env`-only — so nothing breaks for local dev.
   Set `DISABLE_SECRET_MANAGER=true` to opt out entirely.

Secret ids equal the env-var names (e.g. secret `TAVILY_API_KEY`). Pure config
knobs (URLs, booleans, sample rates) are skipped by `secrets-push` and stay in
`.env`. Use `--prefix WARMTH_` on the CLI to namespace secrets within a project.

## Integrations

- **On-Device Listening (iOS)**: Soniqo CoreML wake-word detection + SFSpeechRecognizer (on-device ASR) with an ICP custom language model; NLTagger social-graph extraction → `POST /api/signals` (see [iOS README](./iOS/Warmth-iOS/README.md))
- **Signal Detection (backend)**: Tavily Search
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

Warmth deploys to Google Cloud Platform and Firebase via Makefile targets (no Terraform module in this repo):

| Target | What it deploys |
|--------|-----------------|
| `make deploy-api` | FastAPI → Cloud Run (`warmth-api`) |
| `make deploy-web` | Web build → Firebase Hosting + Firestore rules |
| `make deploy-rules` | Firestore security rules only |
| `make secrets-push` / `pull` / `list` | Google Secret Manager sync |
| `make smoke-docker` | Local Docker build + `/health` check |

Infrastructure components:

- **API**: GCP Cloud Run
- **Web**: Firebase Hosting
- **Database**: Firebase Firestore (Admin SDK only; client rules deny all)
- **Demo video**: GCS bucket `warmth-gtm-hackathon-landing` (separate from Firebase Storage)
- **Messaging / scheduling**: GCP Pub/Sub, Cloud Scheduler (optional)

### Cloud Run IAM

The Cloud Run service account needs:

- `roles/secretmanager.secretAccessor` — startup secret loading via `API_SECRET_ALLOWLIST` in [`packages/core/secrets.py`](packages/core/secrets.py)
- Firebase Admin / Firestore access (default compute SA often sufficient with ADC)

Ensure `FIREBASE_SERVICE_ACCOUNT_KEY` in Secret Manager is the **JSON body** of the
service account, not a local file path.

### Firebase Storage rules

Firebase Storage is not enabled by default on the project. Enable it in the
[Firebase console](https://console.firebase.google.com/project/warmth-gtm-hackathon/storage)
before deploying `storage.rules`. Until then, `make deploy-web` deploys hosting
and Firestore rules only.

### Deploy API to Cloud Run

```bash
gcloud run deploy warmth-api \
  --source . \
  --region us-central1 \
  --project warmth-gtm-hackathon \
  --env-vars-file infra/cloudrun-env.yaml
```

Ensure `FIREBASE_SERVICE_ACCOUNT_KEY` in Secret Manager contains the **JSON body**
of the Firebase Admin service account (not a local file path). Cloud Run loads
secrets at startup via `packages/core/secrets.py`.

### Dashboard data in Firestore

With `USE_FIRESTORE_STORE=true`, each user's dashboard slice is stored under:

```
users/{uid}/events/{eventId}
users/{uid}/connections/{connectionId}     # includes _warmth score blob
users/{uid}/connections/{connectionId}/meet/latest
users/{uid}/signal_index/{signalId}
config/community_members
```

The owner demo account (`dzakwan1844@gmail.com`) is auto-seeded with the GTM
Hackathon roster on bootstrap or first dashboard load. To (re)seed manually:

```bash
# ADC or FIREBASE_SERVICE_ACCOUNT_KEY required; pulls team secrets if GCP_PROJECT_ID is set
export GCP_PROJECT_ID=warmth-gtm-hackathon
uv run python scripts/migrate_user_demo_to_firestore.py dzakwan1844@gmail.com
```

Replace the email with any Firebase Auth user to seed that uid's Firestore
roster from `data/gtm_hackathon_attendees.json`.

### Web dashboard

```bash
cd web && npm run build
firebase deploy --only hosting
```

## License

MIT License — see LICENSE file for details
