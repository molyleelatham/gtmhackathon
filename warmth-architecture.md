# Warmth — Technical Architecture & Repository Structure

> **Active Conference Intelligence × Auto Connection Platform**
> GTM Hackathon · June 2026 · Stack: Python · FastAPI · Cursor SDK · Porcupine · Deepgram · Zero CRM · UnifyGTM · Google MCP

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
│   │   │   ├── conversations.py      # GET/POST /conversations
│   │   │   ├── leads.py              # GET/POST /leads, /leads/{id}/enrich
│   │   │   ├── connections.py        # GET/POST /connections (first connections)
│   │   │   ├── conferences.py        # GET/POST /conferences (directory scraping)
│   │   │   ├── agents.py             # GET/POST /agents (auto outbound strategy)
│   │   │   ├── community.py          # GET/POST /community (sharing features)
│   │   │   └── icp.py                # GET/PUT /icp/config
│   │   │
│   │   └── middleware/
│   │       ├── auth.py               # API key / JWT auth
│   │       └── ratelimit.py          # token bucket per integration
│   │
│   ├── listener/                     # Active conference listener service
│   │   ├── main.py                   # async entrypoint
│   │   ├── engine.py                 # ActiveListener orchestrator
│   │   │
│   │   ├── wake_word/                # ★ NEW — Wake word detection (Porcupine)
│   │   │   ├── porcupine_detector.py # "Hey Anna" wake word detection
│   │   │   ├── audio_capture.py      # Continuous audio capture
│   │   │   └── state_manager.py      # Recording state management
│   │   │
│   │   ├── asr/                      # Conference ASR layer
│   │   │   ├── conference_listener.py  # Deepgram Nova-3 WebSocket stream
│   │   │   ├── noise_suppressor.py     # RNNoise / Krisp SDK pre-processing
│   │   │   ├── diariser.py             # Speaker separation + filtering
│   │   │   └── transcript_buffer.py    # Rolling 30s context window
│   │   │
│   │   ├── sources/
│   │   │   ├── base.py               # abstract SignalSource
│   │   │   ├── tavily.py             # Tavily search API for signal detection
│   │   │   └── microphone.py         # live mic source (PyAudio)
│   │   │
│   │   ├── classifier/
│   │   │   ├── keyword_engine.py     # Regex + fuzzy keyword matching
│   │   │   ├── nlp_classifier.py     # HuggingFace zero-shot classifier
│   │   │   ├── lead_classifier.py    # ★ NEW — Lead routing (me/team/founders/community)
│   │   │   └── signal_types.py       # Enum: HIRING | FUNDING | TECH | INTENT
│   │   │
│   │   ├── intelligence/             # ★ NEW — Conversation intelligence
│   │   │   ├── topic_extractor.py    # Extract conversation topics
│   │   │   ├── interest_analyzer.py  # Analyze interests & values
│   │   │   ├── learning_tracker.py   # Track what was learned
│   │   │   └── sentiment_analyzer.py # Sentiment and values analysis
│   │   │
│   │   └── filters/
│   │       ├── icp_filter.py         # Company size / ARR pre-filter
│   │       └── dedup.py              # Firebase Firestore dedup
│   │
│   ├── scraper/                      # ★ NEW — Conference directory scraper
│   │   ├── main.py                   # async entrypoint
│   │   ├── engine.py                 # Scraper orchestrator
│   │   ├── directory_parser.py       # Parse conference directories
│   │   ├── attendee_extractor.py     # Extract attendee information
│   │   ├── interest_matcher.py       # Match interests (funding, investors, founders)
│   │   └── sources/
│   │       ├── base.py               # abstract ScraperSource
│   │       ├── web_scraper.py        # Generic web scraper
│   │       └── pdf_parser.py         # PDF directory parser
│   │
│   └── agent/                        # ★ NEW — Auto agent system
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
│   │   │   ├── icp.py                # ICPConfig(size_range, arr_range, tech_stack)
│   │   │   └── enrichment.py         # EnrichedLead(firmographics, contacts, funding)
│   │   ├── schemas/
│   │   │   ├── signal_schema.py      # Pydantic v2 input/output
│   │   │   ├── lead_schema.py
│   │   │   ├── zero_crm_schema.py    # Zero CRM push payload shape
│   │   │   └── transcript_schema.py  # ★ NEW — ASR transcript + speaker events
│   │   └── events.py                 # Domain events (SignalDetected, LeadEnriched...)
│   │
│   ├── integrations/
│   │   ├── asr/                      # ASR integration package
│   │   │   ├── deepgram/
│   │   │   │   ├── client.py         # Deepgram Nova-3 WebSocket client
│   │   │   │   ├── config.py         # keyterms, diarize, endpointing params
│   │   │   │   └── stream_handler.py # Async receive + interim/final handling
│   │   │   └── noise/
│   │   │       ├── rnnoise.py        # RNNoise WASM/native wrapper
│   │   │       └── krisp.py          # Krisp SDK wrapper (optional, better)
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
│   │   ├── lightfern/
│   │   │   └── workflow.py           # Lightfern GTM workflow triggers
│   │   └── cursor_ai/
│   │       ├── client.py             # Cursor SDK for agent operations
│   │       └── enrichment_prompt.py  # Cursor SDK: auto-generate CRM payloads
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
│   │   │   └── trigger_workflow.py   # Cloud Function for Lightfern triggers
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
│   │   ├── test_lead_mapper.py
│   │   └── test_asr_transcript_parser.py
│   ├── integration/
│   │   ├── test_zero_crm_client.py
│   │   ├── test_unify_enrichment.py
│   │   ├── test_tavily_search.py
│   │   ├── test_cursor_sdk.py
│   │   ├── test_deepgram_stream.py
│   │   └── test_full_pipeline.py
│   └── conftest.py
│
└── scripts/
    ├── seed_signals.py
    ├── backfill_leads.py
    ├── export_icp.py
    ├── test_mic_pipeline.py
    └── test_tavily_pipeline.py
```

---

## System Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│  LAYER 0 — AUDIO INGESTION (apps/listener/asr/)                     │
│                                                                     │
│  Laptop/Phone Mic (PyAudio, 16kHz, mono)                           │
│       ↓                                                             │
│  noise_suppressor.py  ←── RNNoise (free) or Krisp SDK              │
│       ↓  (clean audio chunks, 50ms / 800 frames)                   │
│  conference_listener.py                                             │
│       ↓  (WebSocket stream)                                         │
│  Deepgram Nova-3 API                                                │
│       model=nova-3                                                  │
│       diarize=true          ← speaker A vs B vs C                  │
│       keyterm=RevOps        ← boosted vocabulary                   │
│       keyterm=HubSpot                                               │
│       keyterm=Salesforce                                            │
│       keyterm=pipeline                                              │
│       keyterm=attribution                                           │
│       keyterm=Series                                                │
│       interim_results=true  ← catch signals mid-sentence           │
│       endpointing=500       ← 500ms silence = utterance end        │
│       ↓  (transcript + speaker_id + confidence)                    │
│  diariser.py ──▶ filter out self-speaker (your own voice)          │
│       ↓                                                             │
│  transcript_buffer.py ──▶ 30s rolling context window               │
└───────────────────────────────────────┬─────────────────────────────┘
                                        │ transcript events
┌───────────────────────────────────────▼─────────────────────────────┐
│  LAYER 1 — SIGNAL INGESTION (apps/listener/sources/ + classifier/) │
│                                                                     │
│  Audio transcript ──┐                                              │
│  Tavily Search ─────┼──▶ keyword_engine.py ──▶ nlp_classifier.py  │
│                      │         ↓                                    │
│                      └──▶   Signal(type, company, ts, source)      │
│                              ↓                                     │
│                    Firebase Firestore ──▶ dedup filter             │
└───────────────────────────────────────┬─────────────────────────────┘
                                        │
┌───────────────────────────────────────▼─────────────────────────────┐
│  LAYER 2 — ICP MATCHING + SCORING                                   │
│                                                                     │
│  icp_filter.py → 50-500 emp, $5-50M ARR gate                       │
│  Cursor SDK ML endpoint → ICP probability                           │
│  weights.yaml → signal_scorer.py → score 0-100                      │
│  if score ≥ 50 → enrichment queue                                  │
└───────────────────────────────────────┬─────────────────────────────┘
                                        │
┌───────────────────────────────────────▼─────────────────────────────┐
│  LAYER 3 — ENRICHMENT                                               │
│                                                                     │
│  UnifyGTM → firmographics, funding, technographics                 │
│  Zero.inc → contact lookup (email + LinkedIn)                       │
│  Cursor SDK → CRM payload generation                                │
└───────────────────────────────────────┬─────────────────────────────┘
                                        │
┌───────────────────────────────────────▼─────────────────────────────┐
│  LAYER 4 — ACTIVATION                                               │
│                                                                     │
│  score ≥ 70 → Zero CRM: create contact + deal                      │
│               Lightfern: GTM workflow routing                       │
│               GCP Pub/Sub: async workflow triggers                   │
└─────────────────────────────────────────────────────────────────────┘
```

---

## ASR Integration Detail

### Deepgram Nova-3 WebSocket Client

```python
# packages/integrations/asr/deepgram/client.py
import asyncio, websockets, json, pyaudio
from packages.core.schemas.transcript_schema import TranscriptEvent

DEEPGRAM_URL = (
    "wss://api.deepgram.com/v1/listen"
    "?model=nova-3"
    "&diarize=true"
    "&interim_results=true"
    "&endpointing=500"
    "&keyterm=RevOps&keyterm=HubSpot&keyterm=Salesforce"
    "&keyterm=pipeline&keyterm=attribution&keyterm=Series"
    "&keyterm=Sales+Engineer&keyterm=CRM"
)

class DeepgramConferenceClient:
    def __init__(self, api_key: str, on_transcript):
        self.api_key = api_key
        self.on_transcript = on_transcript  # async callback

    async def stream(self):
        audio = pyaudio.PyAudio()
        mic = audio.open(
            format=pyaudio.paInt16,
            channels=1,
            rate=16000,          # Nova-3 optimal sample rate
            input=True,
            frames_per_buffer=800  # 50ms chunks
        )
        async with websockets.connect(
            DEEPGRAM_URL,
            extra_headers={"Authorization": f"Token {self.api_key}"}
        ) as ws:
            async def send():
                while True:
                    chunk = mic.read(800, exception_on_overflow=False)
                    # Run RNNoise pre-filter on each chunk
                    clean = noise_suppressor.process(chunk)
                    await ws.send(clean)
                    await asyncio.sleep(0)

            async def receive():
                async for msg in ws:
                    data = json.loads(msg)
                    alt = data["channel"]["alternatives"][0]
                    event = TranscriptEvent(
                        transcript=alt["transcript"],
                        speaker=data.get("channel", {}).get("speaker", 0),
                        confidence=alt.get("confidence", 0.0),
                        is_final=data.get("is_final", False),
                        words=alt.get("words", [])
                    )
                    if event.is_final and event.transcript:
                        await self.on_transcript(event)

            await asyncio.gather(send(), receive())
```

### Noise Suppression

```python
# packages/integrations/asr/noise/rnnoise.py
# RNNoise via Python binding — runs on-device, zero latency, free
import rnnoise  # pip install rnnoise-python

class RNNoiseProcessor:
    def __init__(self):
        self.denoiser = rnnoise.RNNoise()

    def process(self, pcm_chunk: bytes) -> bytes:
        # RNNoise expects 480-frame 16kHz chunks
        return self.denoiser.process_chunk(pcm_chunk)
```

### Transcript Schema

```python
# packages/core/schemas/transcript_schema.py
from pydantic import BaseModel

class TranscriptEvent(BaseModel):
    transcript: str
    speaker:    int        # speaker 0, 1, 2... (from diarization)
    confidence: float      # 0.0–1.0
    is_final:   bool
    words:      list[dict] # word-level timestamps

class SpeakerContext(BaseModel):
    speaker_id:     int
    is_self:        bool   # True = your own voice, skip
    utterances:     list[str]
    keywords_hit:   list[str]
    company_hints:  list[str]  # extracted company names
```

### Connecting ASR to the Signal Pipeline

```python
# apps/listener/engine.py (updated)
class PassiveListener:
    def __init__(self, icp_config):
        self.icp = icp_config
        self.keyword_engine = KeywordEngine(icp_config)
        self.asr_client = DeepgramConferenceClient(
            api_key=settings.DEEPGRAM_API_KEY,
            on_transcript=self._handle_transcript  # wired in
        )

    async def _handle_transcript(self, event: TranscriptEvent):
        # Skip your own voice (speaker 0 = first detected = you)
        if event.speaker == 0 and settings.FILTER_SELF_SPEAKER:
            return
        signals = await self.keyword_engine.extract(event.transcript)
        for signal in signals:
            await self._process_signal(signal, source="conference_audio")

    async def run(self):
        # Run ASR stream + all social sources concurrently
        await asyncio.gather(
            self.asr_client.stream(),           # live mic
            self._poll_linkedin(),              # jobs feed
            self._poll_crunchbase(),            # funding webhooks
        )
```

---

## Key Data Models

```python
# packages/core/models/signal.py
class SignalType(str, Enum):
    HIRING  = "hiring"
    FUNDING = "funding"
    TECH    = "tech_adoption"
    INTENT  = "intent"

class Signal(BaseModel):
    id:             str
    company_name:   str
    company_domain: str | None
    signal_type:    SignalType
    raw_text:       str
    source:         str   # "tavily_search"|"conference_audio"
    keywords_hit:   list[str]
    detected_at:    datetime
    icp_pre_score:  float | None

# packages/core/schemas/zero_crm_schema.py
class ZeroCRMPayload(BaseModel):
    contact_name:    str
    contact_email:   str
    company_name:    str
    company_size:    int
    arr_usd:         int | None
    funding_stage:   str | None
    icp_score:       int
    buying_signals:  dict
    signal_source:   str   # "tavily_search"|"conference_audio"
    tags:            list[str]
```

---

## Scoring Formula

```yaml
# packages/ml/signal_scorer/weights.yaml
signal_weights:
  hiring_revops:        30
  hiring_sales_eng:     25
  funding_series_a:     20
  funding_series_b:     25
  tech_hubspot:         10
  tech_salesforce:      10
  tech_ai_ml_intent:    15
  company_size_fit:     10
  arr_fit:              10

# Conference audio gets a small intent boost
# (prospect is actively talking about the problem in person)
source_bonuses:
  conference_audio:     +5   # in-person intent signal
  tavily_search:        +0

thresholds:
  icp_match_min:  50
  crm_push_min:   70
  workflow_min:   80
```

---

## Integration Contracts

```
Integration        Method     Trigger Point                Output
─────────────────────────────────────────────────────────────────────
Deepgram Nova-3    WSS stream  mic active (layer 0)         transcript events
RNNoise            local       before Deepgram send         clean PCM
Tavily Search      POST /search periodic polling          signal results
UnifyGTM           GET /enrich score ≥ 50                  firmographic blob
Zero.inc CRM       POST /leads score ≥ 70                  crm_id
Zero.inc Contact   GET /lookup enrich_lead task            email + linkedin
Lightfern          POST /route LeadEnriched event          workflow_id
Cursor SDK         SDK call    enrich_lead + score tasks   CRM JSON + ML scores
GCP Pub/Sub        PUB /topic signal events               async triggers
Firebase Firestore CRUD        signal storage              persisted documents
```

---

## Hackathon Suitability Assessment

### ✅ What Works Well in a Hackathon

| Component | Effort | Risk | Notes |
|---|---|---|---|
| Deepgram Nova-3 streaming | Low | Low | 10-min setup, free $200 credit, excellent docs |
| FastAPI + WebSocket endpoint | Low | Low | Standard async setup |
| Keyword engine (regex + fuzzy) | Low | Low | Ship in 2h, no ML needed |
| Zero CRM push | Low | Low | REST API, well-documented |
| UnifyGTM enrichment | Medium | Low | API key + single call |
| ICP config UI (already built) | Done | — | Dashboard already covers this |
| RNNoise pre-filter | Medium | Low | pip install, 20 lines of code |

### ⚠️ Simplify These for Hackathon Day

| Component | Full Spec | Hackathon Version |
|---|---|---|
| SCAILE ML scorer | Fine-tuned BERT classifier | **Hardcode weights.yaml + rule-based scorer** — skip the model |
| Redis + Celery workers | Full async queue | **In-process asyncio queue** — no Redis needed locally |
| Postgres + Alembic | Full ORM + migrations | **SQLite + in-memory dict** for the demo |
| Speaker diarisation | Per-speaker filtering | **Disable self-filter** — just process all audio |
| Crunchbase webhooks | Real-time funding alerts | **Mock fixture** — seed 3 fake funding events |
| Faxxing sequences | Multi-channel outreach | **Log to console / toast in UI** — show the trigger, skip API |

### 🚀 Recommended Hackathon Build Order

```
Hour 1-2:  Core listener skeleton
           ├── PyAudio mic → RNNoise → Deepgram WebSocket
           └── Print transcripts to console — verify it works

Hour 3-4:  Keyword engine + ICP filter
           ├── keyword_engine.py with ICP terms
           ├── icp_filter.py (simple dict check)
           └── Signal object created on keyword hit

Hour 5-6:  Enrichment + scoring
           ├── UnifyGTM API call on signal
           ├── Hardcoded weights.yaml scorer
           └── ZeroCRMPayload assembled

Hour 7-8:  Zero CRM push + UI wiring
           ├── zero_crm/client.py POST call
           ├── FastAPI /signals WebSocket (feed to UI)
           └── Dashboard (already built) consumes live feed

Hour 9-10: Polish + demo prep
           ├── Seed 3 mock social signals (LinkedIn + Crunchbase)
           ├── Test full flow: say "we need a RevOps hire" → signal in UI
           └── Screen record backup in case mic fails on stage
```

### 🎯 Demo Script (the killer moment)

```
1. Open EchoLead dashboard (already built)
2. Say out loud near laptop mic:
   "We're looking at HubSpot but our pipeline visibility is terrible,
    we just closed our Series B and need a RevOps hire urgently"
3. Within ~2 seconds:
   - Deepgram transcribes it
   - Keyword engine fires: HubSpot ✓, pipeline visibility ✓,
     Series B ✓, RevOps hire ✓
   - ICP score calculates: 85/100
   - Toast fires: "New Signal Detected · Score 85"
   - Lead appears in pipeline
   - Zero CRM push triggers live
```

### 💰 Hackathon Cost Estimate (full day)

```
Deepgram Nova-3   8h streaming @ 16kHz    ~$3.70   (free $200 credit)
UnifyGTM enrichment  ~50 API calls        ~$0      (free tier)
Zero CRM          ~50 lead pushes         ~$0      (free tier)
Modal (if needed) GPU scorer              ~$2.00   (free credit)
─────────────────────────────────────────────────
Total                                     < $6     effectively free
```

### ⚡ Single-File Hackathon Bootstrap

If time is short, collapse the full architecture into one runnable demo file:

```python
# demo.py — single-file EchoLead hackathon demo
# Run: uv run python demo.py
import asyncio, websockets, json, pyaudio, httpx
from fastapi import FastAPI, WebSocket
from fastapi.staticfiles import StaticFiles
import uvicorn

ICP_KEYWORDS = [
    "RevOps", "Revenue Operations", "Sales Engineer",
    "HubSpot", "Salesforce", "pipeline visibility",
    "attribution", "Series A", "Series B", "manual data entry"
]
WEIGHTS = {
    "RevOps": 30, "Revenue Operations": 30,
    "Sales Engineer": 25, "HubSpot": 10,
    "Salesforce": 10, "pipeline": 15,
    "attribution": 15, "Series A": 20, "Series B": 25
}

app = FastAPI()
connected_clients: list[WebSocket] = []

async def score(keywords_hit):
    return min(sum(WEIGHTS.get(k, 5) for k in keywords_hit), 100)

async def broadcast(signal: dict):
    for ws in connected_clients:
        await ws.send_json(signal)

async def run_deepgram_listener():
    url = (
        "wss://api.deepgram.com/v1/listen"
        "?model=nova-3&diarize=true&interim_results=true"
        "&endpointing=500"
        + "".join(f"&keyterm={k.replace(' ','+')}" for k in ICP_KEYWORDS)
    )
    audio = pyaudio.PyAudio()
    mic = audio.open(format=pyaudio.paInt16, channels=1,
                     rate=16000, input=True, frames_per_buffer=800)
    async with websockets.connect(
        url, extra_headers={"Authorization": f"Token {DEEPGRAM_API_KEY}"}
    ) as ws:
        async def send():
            while True:
                await ws.send(mic.read(800, exception_on_overflow=False))
                await asyncio.sleep(0)
        async def receive():
            async for msg in ws:
                data = json.loads(msg)
                text = data["channel"]["alternatives"][0]["transcript"]
                if data.get("is_final") and text:
                    hits = [k for k in ICP_KEYWORDS if k.lower() in text.lower()]
                    if hits:
                        s = await score(hits)
                        await broadcast({
                            "transcript": text, "keywords": hits,
                            "score": s, "source": "conference_audio"
                        })
        await asyncio.gather(send(), receive())

@app.websocket("/ws/signals")
async def signals_ws(ws: WebSocket):
    await ws.accept()
    connected_clients.append(ws)
    try:
        while True: await ws.receive_text()
    finally:
        connected_clients.remove(ws)

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.create_task(run_deepgram_listener())
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

---

## Environment Variables

```bash
# .env.example

# ASR
DEEPGRAM_API_KEY=
FILTER_SELF_SPEAKER=true     # skip speaker 0 (your own voice)
MIC_SAMPLE_RATE=16000
NOISE_SUPPRESSION=rnnoise    # rnnoise | krisp | none

# Integrations
ZERO_CRM_API_KEY=
ZERO_CRM_BASE_URL=https://api.zero.inc/v1
UNIFY_GTM_API_KEY=
UNIFY_GTM_BASE_URL=https://api.unifygtm.com/v1
LIGHTFERN_WEBHOOK_URL=
CURSOR_SDK_API_KEY=

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

# ML
HF_MODEL_PATH=models/icp-classifier-v1
```

---

## Dev Setup

```bash
# Install
git clone https://github.com/your-org/echolead && cd echolead
uv sync

# Install audio deps (macOS)
brew install portaudio
pip install pyaudio rnnoise-python

# Install audio deps (Ubuntu)
sudo apt install portaudio19-dev && pip install pyaudio rnnoise-python

# Smoke test mic pipeline
uv run python scripts/test_mic_pipeline.py

# Start full stack
docker compose up -d
uv run alembic upgrade head
uv run uvicorn apps.api.main:app --reload --port 8000
uv run python apps/listener/main.py

# OR: hackathon single-file mode
DEEPGRAM_API_KEY=xxx uv run python demo.py
```

---

## Tech Stack Summary

| Layer | Technology |
|---|---|
| ASR — Conference | **Deepgram Nova-3** (WebSocket streaming, diarize, keyterms) |
| Audio Pre-processing | **RNNoise** (free, on-device) or Krisp SDK |
| Mic Capture | PyAudio (16kHz, mono, 50ms chunks) |
| API | FastAPI + Pydantic v2 + asyncpg |
| Listener | Python asyncio + httpx + Redis Streams |
| ML Scoring | HuggingFace Transformers + SCAILE.tech GPU endpoint |
| Workers | Celery + Redis broker |
| Database | PostgreSQL (Alembic) · SQLite for hackathon |
| Cache / Dedup | Redis + bloom filter |
| Deployment | Modal (GPU listener + scorer), Docker |
| AI Enrichment | Claude SDK (Anthropic) via Cursor AI |
| Package Mgmt | uv |
| Testing | pytest + pytest-asyncio |

---

## Phone-as-Client: Mobile Mic Capture Architecture

> The phone is the passive listener device. It sits in your shirt pocket at the conference,
> browser open, mic streaming to your laptop over HTTPS tunnel.

### The Two Problems & Solutions

#### Problem 1 — HTTPS Requirement for `getUserMedia`

`getUserMedia` (the browser mic API) **only works on `https://` or `localhost`**.
On your phone hitting `http://192.168.x.x:8000` (LAN IP) the browser hard-blocks mic access.

**Solution: Cloudflare Tunnel (zero config, free)**

```bash
# Install once
brew install cloudflared          # macOS
# or: curl -L https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64 -o cloudflared

# Start tunnel — run alongside your FastAPI app
cloudflared tunnel --url http://localhost:8000
# → https://random-name.trycloudflare.com  ← open this on your phone
```

- No account needed for quick tunnels
- ngrok works identically: `ngrok http 8000`
- Cloudflared preferred at conferences (more reliable, no rate limits)

---

#### Problem 2 — Getting Audio to the Server

Two patterns — choose based on whether live transcription latency matters for your demo:

**Option A: Record-then-Upload** *(recommended for hackathon demo)*

Simplest. Phone records a chunk (e.g. 5–10s), POSTs the blob, server transcribes.
Perceived latency: ~1–2s. Good enough for the demo flow.

```javascript
// phone-client/index.html — served by FastAPI as static file
const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
const rec = new MediaRecorder(stream, { mimeType: 'audio/webm;codecs=opus' });
const chunks = [];

rec.ondataavailable = e => chunks.push(e.data);
rec.onstop = async () => {
  const blob = new Blob(chunks, { type: 'audio/webm' });
  const form = new FormData();
  form.append('audio', blob, 'chunk.webm');
  await fetch('/api/audio/upload', { method: 'POST', body: form });
};

// Record in 8-second rolling chunks for passive listening feel
setInterval(() => {
  rec.stop();
  rec.start();
}, 8000);

rec.start();
```

**Option B: Real-time WebSocket Streaming** *(more impressive demo, more work)*

Phone pushes raw PCM chunks over WebSocket → server pipes directly to Deepgram.
Latency: ~300ms end-to-end. Worth it if you want words appearing live on the dashboard.

```javascript
// AudioWorklet approach — low overhead, works on mobile Chrome/Safari
const ctx = new AudioContext({ sampleRate: 16000 });
await ctx.audioWorklet.addModule('/static/pcm-processor.js');

const source = ctx.createMediaStreamSource(stream);
const worklet = new AudioWorkletNode(ctx, 'pcm-processor');
const ws = new WebSocket('wss://random-name.trycloudflare.com/ws/audio');

worklet.port.onmessage = ({ data }) => {
  if (ws.readyState === WebSocket.OPEN) ws.send(data);  // raw PCM Int16
};
source.connect(worklet);
```

```javascript
// /static/pcm-processor.js — AudioWorklet processor
class PCMProcessor extends AudioWorkletProcessor {
  process(inputs) {
    const input = inputs[0][0];
    if (input) {
      // Convert Float32 → Int16 for Deepgram
      const pcm = new Int16Array(input.length);
      for (let i = 0; i < input.length; i++) {
        pcm[i] = Math.max(-32768, Math.min(32767, input[i] * 32768));
      }
      this.port.postMessage(pcm.buffer, [pcm.buffer]);
    }
    return true;
  }
}
registerProcessor('pcm-processor', PCMProcessor);
```

---

### FastAPI Endpoints

```python
# apps/api/routers/audio.py
from fastapi import APIRouter, UploadFile, File, WebSocket
from packages.integrations.asr.deepgram.client import DeepgramConferenceClient
from apps.listener.classifier.keyword_engine import KeywordEngine

router = APIRouter(prefix="/api/audio")

# ── Option A: blob upload endpoint ────────────────────────────────────
@router.post("/upload")
async def upload_audio(audio: UploadFile = File(...)):
    """
    Phone POSTs a webm/opus blob every ~8s.
    Transcribe via Deepgram REST, run keyword engine, emit signal.
    """
    audio_bytes = await audio.read()

    # Deepgram REST (not WebSocket) for batch chunks
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            "https://api.deepgram.com/v1/listen"
            "?model=nova-3&diarize=false&keyterm=RevOps&keyterm=HubSpot"
            "&keyterm=Salesforce&keyterm=pipeline&keyterm=Series",
            headers={
                "Authorization": f"Token {settings.DEEPGRAM_API_KEY}",
                "Content-Type": "audio/webm",
            },
            content=audio_bytes,
            timeout=10.0,
        )

    transcript = resp.json()["results"]["channels"][0]["alternatives"][0]["transcript"]
    if transcript:
        signals = await keyword_engine.extract(transcript)
        for signal in signals:
            await signal_bus.emit(signal)   # → enrichment pipeline

    return {"transcript": transcript, "signals_detected": len(signals)}


# ── Option B: real-time WebSocket stream ──────────────────────────────
@router.websocket("/ws/audio")
async def audio_ws(ws: WebSocket):
    """
    Phone streams raw PCM Int16 chunks.
    Pipe directly to Deepgram WebSocket — bidirectional proxy.
    """
    await ws.accept()

    DEEPGRAM_URL = (
        "wss://api.deepgram.com/v1/listen"
        "?model=nova-3&encoding=linear16&sample_rate=16000"
        "&diarize=true&interim_results=true&endpointing=500"
        "&keyterm=RevOps&keyterm=HubSpot&keyterm=Salesforce"
        "&keyterm=pipeline&keyterm=attribution&keyterm=Series"
    )

    async with websockets.connect(
        DEEPGRAM_URL,
        extra_headers={"Authorization": f"Token {settings.DEEPGRAM_API_KEY}"}
    ) as dg_ws:

        async def phone_to_deepgram():
            async for chunk in ws.iter_bytes():
                await dg_ws.send(chunk)

        async def deepgram_to_pipeline():
            async for msg in dg_ws:
                data = json.loads(msg)
                text = data["channel"]["alternatives"][0]["transcript"]
                is_final = data.get("is_final", False)
                if is_final and text:
                    signals = await keyword_engine.extract(text)
                    for sig in signals:
                        await signal_bus.emit(sig)
                    # Echo transcript back to phone UI
                    await ws.send_json({"transcript": text, "signals": len(signals)})

        await asyncio.gather(phone_to_deepgram(), deepgram_to_pipeline())
```

---

### Phone UI (Served from FastAPI)

```python
# apps/api/main.py — serve the phone client as a static page
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

app.mount("/static", StaticFiles(directory="phone-client/static"), name="static")

@app.get("/listen")
async def phone_client():
    return FileResponse("phone-client/index.html")
# → open https://random-name.trycloudflare.com/listen on your phone
```

```html
<!-- phone-client/index.html — minimal, mobile-first -->
<!DOCTYPE html>
<html>
<head>
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <title>EchoLead Listener</title>
  <style>
    body { font-family: system-ui; background: #0d0e10; color: #e2e4ed;
           display: flex; flex-direction: column; align-items: center;
           justify-content: center; height: 100dvh; gap: 1rem; margin: 0; }
    .pulse { width: 80px; height: 80px; border-radius: 50%;
             background: #00d4aa20; border: 2px solid #00d4aa;
             display: flex; align-items: center; justify-content: center;
             font-size: 2rem; animation: pulse 2s ease-in-out infinite; }
    @keyframes pulse { 0%,100%{transform:scale(1)} 50%{transform:scale(1.08)} }
    .status { font-size: 0.85rem; color: #7c8298; }
    .signal-log { font-size: 0.75rem; color: #00d4aa; max-width: 300px;
                  text-align: center; min-height: 2rem; }
  </style>
</head>
<body>
  <div class="pulse">🎙</div>
  <div class="status" id="status">Connecting...</div>
  <div class="signal-log" id="log"></div>
  <script>
    const BASE = window.location.origin;
    const ws = new WebSocket(BASE.replace('https','wss').replace('http','ws') + '/api/audio/ws/audio');
    let mediaStream, audioCtx, worklet;

    ws.onopen = async () => {
      document.getElementById('status').textContent = '🟢 Listening passively';
      mediaStream = await navigator.mediaDevices.getUserMedia({ audio: true });
      audioCtx = new AudioContext({ sampleRate: 16000 });
      await audioCtx.audioWorklet.addModule('/static/pcm-processor.js');
      const source = audioCtx.createMediaStreamSource(mediaStream);
      worklet = new AudioWorkletNode(audioCtx, 'pcm-processor');
      worklet.port.onmessage = ({ data }) => {
        if (ws.readyState === 1) ws.send(data);
      };
      source.connect(worklet);
    };

    ws.onmessage = ({ data }) => {
      const { transcript, signals } = JSON.parse(data);
      if (signals > 0) {
        document.getElementById('log').textContent =
          `⚡ ${signals} signal${signals>1?'s':''} detected`;
      }
    };

    ws.onclose = () => {
      document.getElementById('status').textContent = '🔴 Disconnected';
    };
  </script>
</body>
</html>
```

---

### Full Phone → Server Data Flow

```
Phone (browser, HTTPS)
  └── navigator.mediaDevices.getUserMedia({ audio: true })
        └── AudioWorklet (PCM Float32 → Int16, 16kHz)
              └── WebSocket send (raw PCM chunks, ~50ms each)
                    │
              [Cloudflare Tunnel]
                    │
              wss://random-name.trycloudflare.com/api/audio/ws/audio
                    │
              FastAPI WebSocket handler
                    └── proxy → Deepgram Nova-3 WebSocket
                          └── transcript events
                                └── keyword_engine.extract()
                                      └── Signal → enrichment → Zero CRM
```

---

### Hackathon Day Runbook (Phone Mode)

```bash
# Terminal 1 — start app
uv run uvicorn apps.api.main:app --reload --port 8000

# Terminal 2 — expose over HTTPS
cloudflared tunnel --url http://localhost:8000
# Copy the https://xxxx.trycloudflare.com URL

# On your phone
# Open: https://xxxx.trycloudflare.com/listen
# Tap allow microphone
# Phone is now a passive conference listener

# Dashboard (judges/audience view)
# Open: https://xxxx.trycloudflare.com  (the main EchoLead dashboard)
# Show on laptop — signals appear live as you speak near the phone
```

### iOS/Android Browser Compatibility

| Browser | getUserMedia | AudioWorklet | WebSocket | Notes |
|---|---|---|---|---|
| Chrome Android | ✅ | ✅ | ✅ | Best choice |
| Safari iOS 17+ | ✅ | ✅ | ✅ | Works, needs user gesture to start |
| Firefox Android | ✅ | ✅ | ✅ | Fine |
| Samsung Internet | ✅ | ⚠️ | ✅ | Fallback to MediaRecorder if AudioWorklet fails |

**iOS gotcha:** AudioContext must be created inside a user gesture (button tap).
Wrap `audioCtx = new AudioContext(...)` in a button `onclick` handler — don't auto-start.
