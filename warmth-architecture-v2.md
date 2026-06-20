# Warmth — Active Event Intelligence Platform

> **Active Event Companion × Auto Connection System**
> GTM Hackathon · June 2026 · Stack: Python · FastAPI · Cursor SDK · Porcupine · Deepgram · Zero CRM · UnifyGTM · Google MCP

---

## Vision Overview

Warmth is an active event intelligence system that works like "Siri for events." When you attend events, Warmth:

1. **Wake Word Activation**: Say "Hey Anna" to start recording conversations (using Porcupine wake word detection)
2. **Lead Classification**: Automatically classifies leads for you, your team, founders, or community/friends
3. **Directory Scraping**: Scrapes event directories to identify attendees by interests (funding, investors, founders)
4. **First Connections**: Makes initial connections by scraping data, enriching with Zero CRM → UnifyGTM → drafting emails via Google MCP
5. **Real-time Intelligence**: During conversations, captures interests, topics discussed, what you learned, what they care about, and values
6. **CRM Integration**: Sends all conversation intelligence to CRM automatically
7. **Auto Agents**: Creates automated outbound strategies for follow-up
8. **Community Sharing**: Shares intelligence with closed groups (friends, founders)

---

## Repository Structure

```
warmth/
├── README.md
├── pyproject.toml                    # uv/poetry project config
├── .env.example                      # all API keys template
├── docker-compose.yml                # local dev stack
├── Makefile                          # dev commands
│
├── apps/
│   ├── api/                          # FastAPI backend (main service)
│   │   ├── main.py                   # app entrypoint, lifespan
│   │   ├── config.py                 # pydantic-settings config
│   │   ├── deps.py                   # shared DI (db, redis, clients)
│   │   │
│   │   ├── routers/
│   │   │   ├── conversations.py      # GET/POST /conversations (real-time intelligence)
│   │   │   ├── leads.py              # GET/POST /leads, /leads/{id}/enrich
│   │   │   ├── connections.py        # GET/POST /connections (first connections)
│   │   │   ├── event_runs.py        # GET/POST /event-runs (directory scraping)
│   │   │   ├── agents.py             # GET/POST /agents (auto outbound strategy)
│   │   │   ├── community.py          # GET/POST /community (sharing features)
│   │   │   └── icp.py                # GET/PUT /icp/config
│   │   │
│   │   └── middleware/
│   │       ├── auth.py               # API key / JWT auth
│   │       └── ratelimit.py          # token bucket per integration
│   │
│   ├── listener/                     # Active event listener service
│   │   ├── main.py                   # async entrypoint
│   │   ├── engine.py                 # ActiveListener orchestrator
│   │   │
│   │   ├── wake_word/                # Wake word detection (Porcupine)
│   │   │   ├── porcupine_detector.py # "Hey Anna" wake word detection
│   │   │   ├── audio_capture.py      # Continuous audio capture
│   │   │   └── state_manager.py      # Recording state management
│   │   │
│   │   ├── asr/                      # Event ASR layer
│   │   │   ├── event_listener.py  # Deepgram Nova-3 WebSocket stream
│   │   │   ├── noise_suppressor.py     # RNNoise / Krisp SDK pre-processing
│   │   │   ├── diariser.py             # Speaker separation + filtering
│   │   │   └── transcript_buffer.py    # Rolling 30s context window
│   │   │
│   │   ├── classifier/
│   │   │   ├── keyword_engine.py     # Regex + fuzzy keyword matching
│   │   │   ├── nlp_classifier.py     # HuggingFace zero-shot classifier
│   │   │   ├── lead_classifier.py    # Lead routing (me/team/founders/community)
│   │   │   └── signal_types.py       # Enum: HIRING | FUNDING | TECH | INTENT
│   │   │
│   │   ├── intelligence/             # Conversation intelligence
│   │   │   ├── topic_extractor.py    # Extract conversation topics
│   │   │   ├── interest_analyzer.py  # Analyze interests & values
│   │   │   ├── learning_tracker.py   # Track what was learned
│   │   │   └── sentiment_analyzer.py # Sentiment and values analysis
│   │   │
│   │   └── filters/
│   │       ├── icp_filter.py         # Company size / ARR pre-filter
│   │       └── dedup.py              # Firebase Firestore dedup
│   │
│   ├── scraper/                      # Event directory scraper
│   │   ├── main.py                   # async entrypoint
│   │   ├── engine.py                 # Scraper orchestrator
│   │   ├── directory_parser.py       # Parse event directories
│   │   ├── attendee_extractor.py     # Extract attendee information
│   │   ├── interest_matcher.py       # Match interests (funding, investors, founders)
│   │   └── sources/
│   │       ├── base.py               # abstract ScraperSource
│   │       ├── web_scraper.py        # Generic web scraper
│   │       └── pdf_parser.py         # PDF directory parser
│   │
│   └── agent/                        # Auto agent system
│       ├── main.py                   # async entrypoint
│       ├── engine.py                 # Agent orchestrator
│       ├── outbound_strategy.py      # Auto outbound strategy creation
│       ├── email_generator.py        # Generate personalized emails
│       ├── followup_scheduler.py     # Schedule follow-ups
│       └── templates/
│           ├── email_templates.py    # Email templates
│           └── strategy_templates.py # Strategy templates
│
├── packages/
│   ├── core/                         # Shared domain models
│   │   ├── models/
│   │   │   ├── signal.py             # Signal(company, type, source, raw_text, ts)
│   │   │   ├── lead.py               # Lead(contact, company, signals, icp_score)
│   │   │   ├── conversation.py       # Conversation intelligence model
│   │   │   ├── connection.py         # First connection model
│   │   │   ├── event.py         # Event directory model
│   │   │   ├── community.py          # Community sharing model
│   │   │   ├── agent.py              # Auto agent model
│   │   │   ├── icp.py                # ICPConfig(size_range, arr_range, tech_stack)
│   │   │   └── enrichment.py         # EnrichedLead(firmographics, contacts, funding)
│   │   ├── schemas/
│   │   │   ├── signal_schema.py      # Pydantic v2 input/output
│   │   │   ├── lead_schema.py
│   │   │   ├── conversation_schema.py # Conversation intelligence schema
│   │   │   ├── connection_schema.py   # First connection schema
│   │   │   ├── event_schema.py   # Event directory schema
│   │   │   ├── community_schema.py    # Community sharing schema
│   │   │   ├── agent_schema.py        # Auto agent schema
│   │   │   ├── zero_crm_schema.py    # Zero CRM push payload shape
│   │   │   └── transcript_schema.py  # ASR transcript + speaker events
│   │   └── events.py                 # Domain events (SignalDetected, LeadEnriched...)
│   │
│   ├── integrations/
│   │   ├── asr/                      # ASR integration package
│   │   │   ├── deepgram/
│   │   │   │   ├── client.py         # Deepgram Nova-3 WebSocket client
│   │   │   │   ├── config.py         # keyterms, diarize, endpointing params
│   │   │   │   └── stream_handler.py # Async receive + interim/final handling
│   │   │   ├── noise/
│   │   │   │   ├── rnnoise.py        # RNNoise WASM/native wrapper
│   │   │   │   └── krisp.py          # Krisp SDK wrapper (optional, better)
│   │   │   └── porcupine/            # Wake word detection
│   │   │       ├── detector.py       # Porcupine wake word detector
│   │   │       └── keywords.py       # Custom wake word training
│   │   │
│   │   ├── zero_crm/
│   │   │   ├── client.py             # Zero.inc REST client (async httpx)
│   │   │   ├── mapper.py             # Lead → Zero CRM deal/contact shape
│   │   │   └── webhooks.py           # Inbound Zero CRM webhooks
│   │   ├── unify_gtm/
│   │   │   ├── client.py             # UnifyGTM enrichment API
│   │   │   └── normaliser.py         # Normalise firmographic response
│   │   ├── tavily/
│   │   │   ├── client.py             # Tavily search API for signal detection
│   │   │   └── signal_extractor.py   # Extract signals from search results
│   │   ├── google_mcp/               # Google MCP integration
│   │   │   ├── client.py             # Google MCP client for email/docs
│   │   │   ├── email_draft.py        # Draft emails via Google MCP
│   │   │   └── docs_sync.py          # Sync conversation notes to Google Docs
│   │   └── cursor_ai/
│   │       ├── client.py             # Cursor SDK for agent operations
│   │       ├── enrichment_prompt.py  # Cursor SDK: auto-generate CRM payloads
│   │       └── conversation_prompt.py # Conversation analysis prompts
│   │
│   └── ml/
│       ├── icp_classifier/
│       │   ├── model.py
│       │   ├── train.py
│       │   ├── predict.py
│       │   └── features.py
│       ├── signal_scorer/
│       │   ├── scorer.py
│       │   └── weights.yaml
│       ├── conversation_analyzer/     # ★ NEW — Conversation ML models
│       │   ├── topic_model.py        # Topic extraction model
│       │   ├── interest_classifier.py # Interest classification
│       │   └── sentiment_analyzer.py  # Sentiment analysis
│       └── embeddings/
│           └── company_embedder.py
│
├── infra/
│   ├── firebase/
│   │   ├── firestore.py              # Firebase Firestore client
│   │   ├── auth.py                   # Firebase Authentication
│   │   └── config.py                 # Firebase config
│   ├── gcp/
│   │   ├── cloud_functions/
│   │   │   ├── enrich_lead.py        # Cloud Function for lead enrichment
│   │   │   ├── score_lead.py         # Cloud Function for Cursor SDK scoring
│   │   │   └── trigger_workflow.py   # Cloud Function for workflow triggers
│   │   ├── cloud_scheduler/
│   │   │   └── scheduler.py          # GCP Cloud Scheduler config
│   │   └── pubsub/
│   │       └── publisher.py          # Pub/Sub for async messaging
│   └── terraform/
│       ├── main.tf                   # Terraform config for GCP resources
│       └── variables.tf              # Terraform variables
│
├── db/
│   ├── firestore/
│   │   ├── collections.py             # Firestore collection definitions
│   │   ├── models.py                  # Firestore data models
│   │   └── client.py                  # Firestore client wrapper
│   └── migrations/
│       └── firestore_indexes.py      # Firestore index definitions
│
├── tests/
│   ├── unit/
│   │   ├── test_keyword_engine.py
│   │   ├── test_icp_filter.py
│   │   ├── test_scorer.py
│   │   ├── test_lead_classifier.py   # ★ NEW
│   │   ├── test_topic_extractor.py   # ★ NEW
│   │   └── test_porcupine_detector.py # ★ NEW
│   ├── integration/
│   │   ├── test_zero_crm_client.py
│   │   ├── test_unify_enrichment.py
│   │   ├── test_tavily_search.py
│   │   ├── test_cursor_sdk.py
│   │   ├── test_google_mcp.py        # ★ NEW
│   │   ├── test_deepgram_stream.py
│   │   └── test_full_pipeline.py
│   └── conftest.py
│
└── scripts/
    ├── seed_signals.py
    ├── backfill_leads.py
    ├── export_icp.py
    ├── test_mic_pipeline.py
    ├── test_tavily_pipeline.py
    ├── test_porcupine_pipeline.py    # ★ NEW
    └── test_event_scraper.py   # ★ NEW
```

---

## System Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│  LAYER 0 — WAKE WORD + AUDIO INGESTION (apps/listener/wake_word/) │
│                                                                     │
│  "Hey Anna" → Porcupine Wake Word Detection                         │
│       ↓                                                             │
│  State Manager → Start Recording Mode                              │
│       ↓                                                             │
│  Audio Capture (PyAudio, 16kHz, mono)                              │
│       ↓                                                             │
│  noise_suppressor.py  ←── RNNoise (free) or Krisp SDK              │
│       ↓  (clean audio chunks, 50ms / 800 frames)                   │
│  event_listener.py                                             │
│       ↓  (WebSocket stream)                                         │
│  Deepgram Nova-3 API                                                │
│       model=nova-3                                                  │
│       diarize=true          ← speaker A vs B vs C                  │
│       keyterm=RevOps        ← boosted vocabulary                   │
│       interim_results=true  ← catch signals mid-sentence           │
│       endpointing=500       ← 500ms silence = utterance end        │
│       ↓  (transcript + speaker_id + confidence)                    │
│  diariser.py ──▶ filter out self-speaker (your own voice)          │
│       ↓                                                             │
│  transcript_buffer.py ──▶ 30s rolling context window               │
└───────────────────────────────────────┬─────────────────────────────┘
                                        │ transcript events
┌───────────────────────────────────────▼─────────────────────────────┐
│  LAYER 1 — LEAD CLASSIFICATION + INTELLIGENCE EXTRACTION           │
│                                                                     │
│  Transcript ──▶ lead_classifier.py                                │
│       ↓                                                             │
│  Classify: ME | TEAM | FOUNDERS | COMMUNITY                         │
│       ↓                                                             │
│  topic_extractor.py ──▶ What topics discussed?                     │
│  interest_analyzer.py ──▶ What do they care about?                 │
│  learning_tracker.py ──▶ What did you learn?                       │
│  sentiment_analyzer.py ──▶ Values + sentiment                      │
│       ↓                                                             │
│  Conversation Intelligence Model                                   │
│       ↓                                                             │
│  Firebase Firestore ──▶ Store conversation data                    │
└───────────────────────────────────────┬─────────────────────────────┘
                                        │
┌───────────────────────────────────────▼─────────────────────────────┐
│  LAYER 2 — CONFERENCE DIRECTORY SCRAPING                           │
│                                                                     │
│  Event URL/PDF ──▶ directory_parser.py                        │
│       ↓                                                             │
│  attendee_extractor.py ──▶ Extract attendee info                   │
│       ↓                                                             │
│  interest_matcher.py ──▶ Match by interest (funding, investors)    │
│       ↓                                                             │
│  First Connection Candidates                                        │
└───────────────────────────────────────┬─────────────────────────────┘
                                        │
┌───────────────────────────────────────▼─────────────────────────────┐
│  LAYER 3 — ENRICHMENT PIPELINE                                      │
│                                                                     │
│  Zero CRM → existing contact lookup + enrichment                    │
│  UnifyGTM → firmographics, funding, technographics                 │
│  Cursor SDK → AI-powered analysis + scoring                        │
└───────────────────────────────────────┬─────────────────────────────┘
                                        │
┌───────────────────────────────────────▼─────────────────────────────┐
│  LAYER 4 — CONNECTION + OUTBOUND AUTOMATION                         │
│                                                                     │
│  Google MCP → Draft personalized email                              │
│  Cursor SDK → Generate outbound strategy                            │
│  Auto Agents → Schedule follow-ups, track engagement                │
│  Community → Share with closed groups (friends/founders)            │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Key Features

### 1. Wake Word Detection ("Hey Anna")

```python
# apps/listener/wake_word/porcupine_detector.py
import pvporcupine

class PorcupineWakeWordDetector:
    def __init__(self, access_key: str):
        self.porcupine = pvporcupine.create(
            access_key=access_key,
            keyword_paths=["hey_anna.ppn"],  # Custom wake word
            sensitivities=[0.5]
        )
    
    def detect_wake_word(self, audio_frame: bytes) -> bool:
        """Detect if wake word was spoken"""
        result = self.porcupine.process(audio_frame)
        return result >= 0
```

### 2. Lead Classification

```python
# apps/listener/classifier/lead_classifier.py
from enum import Enum

class LeadRouting(str, Enum):
    ME = "me"              # Direct leads for me
    TEAM = "team"          # Leads for my team
    FOUNDERS = "founders"  # Leads for founders
    COMMUNITY = "community" # Leads for friends/community

class LeadClassifier:
    def classify_lead(self, conversation: dict, context: dict) -> LeadRouting:
        """Classify who this lead is for based on conversation content"""
        # Analyze conversation topics, company size, funding stage, etc.
        # Return appropriate routing
        pass
```

### 3. Event Directory Scraping

```python
# apps/scraper/directory_parser.py
class ConferenceDirectoryParser:
    async def parse_directory(self, source: str) -> list[Attendee]:
        """Parse event directory from URL or PDF"""
        if source.endswith('.pdf'):
            return await self._parse_pdf(source)
        else:
            return await self._parse_web(source)
    
    async def _parse_pdf(self, pdf_path: str) -> list[Attendee]:
        """Extract attendees from PDF directory"""
        pass
    
    async def _parse_web(self, url: str) -> list[Attendee]:
        """Scrape attendees from web directory"""
        pass
```

### 4. Conversation Intelligence

```python
# apps/listener/intelligence/topic_extractor.py
class TopicExtractor:
    def extract_topics(self, transcript: str) -> list[str]:
        """Extract main topics from conversation"""
        # Use NLP to extract key topics
        pass

# apps/listener/intelligence/interest_analyzer.py
class InterestAnalyzer:
    def analyze_interests(self, transcript: str) -> dict:
        """Analyze what the person cares about"""
        return {
            "interests": [],
            "values": [],
            "pain_points": [],
            "goals": []
        }
```

### 5. Google MCP Integration

```python
# packages/integrations/google_mcp/email_draft.py
class GoogleMCPEmailClient:
    async def draft_email(
        self,
        to_email: str,
        subject: str,
        body: str,
        context: dict
    ) -> str:
        """Draft email using Google MCP"""
        # Use Google MCP to create email draft
        pass
```

### 6. Community Sharing

```python
# packages/core/models/community.py
class CommunityShare(BaseModel):
    id: str
    conversation_id: str
    shared_with: list[str]  # Community group IDs
    shared_by: str
    permissions: str  # read, comment, edit
    shared_at: datetime
```

---

## Environment Variables

```bash
# .env.example

# Wake Word Detection
PORCUPINE_ACCESS_KEY=

# ASR
DEEPGRAM_API_KEY=
FILTER_SELF_SPEAKER=true
MIC_SAMPLE_RATE=16000
NOISE_SUPPRESSION=rnnoise

# Integrations
ZERO_CRM_API_KEY=
ZERO_CRM_BASE_URL=https://api.zero.inc/v1
UNIFY_GTM_API_KEY=
UNIFY_GTM_BASE_URL=https://api.unifygtm.com/v1
CURSOR_SDK_API_KEY=

# Google MCP
GOOGLE_MCP_CREDENTIALS=
GOOGLE_MCP_SCOPES="gmail,docs"

# Signal Sources
TAVILY_API_KEY=

# Firebase
FIREBASE_PROJECT_ID=
FIREBASE_SERVICE_ACCOUNT_KEY=
FIREBASE_DATABASE_URL=

# GCP
GCP_PROJECT_ID=
GCP_SERVICE_ACCOUNT_KEY=
GCP_REGION=us-central1
PUBSUB_TOPIC=signal-events

# Community
COMMUNITY_GROUPS_ENABLED=true
COMMUNITY_PERMISSIONS=default
```

---

## Tech Stack Summary

|| Layer | Technology |
||---|---|
|| Wake Word Detection | **Porcupine** (custom "Hey Anna" wake word) |
|| ASR — Event | **Deepgram Nova-3** (WebSocket streaming, diarize, keyterms) |
|| Audio Pre-processing | **RNNoise** (free, on-device) or Krisp SDK |
|| Mic Capture | PyAudio (16kHz, mono, 50ms chunks) |
|| API | FastAPI + Pydantic v2 |
|| Lead Classification | Custom routing logic + ML classifier |
|| Directory Scraping | BeautifulSoup + PDFParser |
|| Conversation Intelligence | Cursor SDK + HuggingFace Transformers |
|| Enrichment | UnifyGTM + Zero CRM |
|| Email Automation | **Google MCP** (Gmail + Google Docs) |
|| Auto Agents | Cursor SDK + Custom scheduling |
|| Community Sharing | Firebase Firestore + Custom permissions |
|| Workers | GCP Cloud Functions + Pub/Sub |
|| Database | Firebase Firestore |
|| Auth | Firebase Authentication |
|| Deployment | GCP Cloud Run + Cloud Functions |
|| Package Mgmt | uv |
|| Testing | pytest + pytest-asyncio |

---

This architecture transforms Warmth from a passive listening system into an active event intelligence companion that helps you make meaningful connections, capture valuable conversation insights, and automate follow-up strategies intelligently.