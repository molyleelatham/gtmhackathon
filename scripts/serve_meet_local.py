"""Lightweight localhost server for the MEET stage (encoders + models).

Boots ONLY the meet path — no Firebase, no Google Secret Manager, no audio deps —
so you can test "data -> encoders -> models" locally with just fastapi/uvicorn.

Run from the repo root (the dir containing `warmth/`):

    pip install fastapi uvicorn      # if not already installed
    python warmth/scripts/serve_meet_local.py
    # -> http://127.0.0.1:8000/docs

Endpoints:
    GET  /health
    POST /meet/encode    diarized transcript            -> MeetingSignal + KG
    POST /meet/signals   structured MeetingSignal        -> RoutingDecision (models)
    POST /meet/process   diarized transcript (encode+run)-> signal + decision
"""
import asyncio
import os
import sys
from typing import Optional

# Make `warmth` importable as a package regardless of CWD.
_REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

# Load warmth/.env so CURSOR_SDK_API_KEY (and friends) are available to the
# AI-agent extractor. Without this the agent path silently falls back.
try:
    from dotenv import load_dotenv

    load_dotenv(os.path.join(_REPO_ROOT, "warmth", ".env"))
except Exception:
    pass

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from warmth.apps.lifecycle.meet import MeetPipeline
from warmth.apps.listener.intelligence.meet_encoder import MeetEncoder
from warmth.packages.core.models.meeting_signal import MeetingSignal, TopicTime

app = FastAPI(title="Warmth MEET (local)", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

encoder = MeetEncoder()                      # heuristic encoders
agent_encoder = MeetEncoder(use_agent=True)  # AI-agent-backed encoders (Cursor SDK)
pipeline = MeetPipeline()


def _encoder_for(use_agent: bool) -> MeetEncoder:
    return agent_encoder if use_agent else encoder


async def _encode(req: "EncodeRequest"):
    """Run the (possibly blocking, AI-agent) encode off the event loop."""
    enc = _encoder_for(req.use_agent)
    return await asyncio.to_thread(
        enc.encode,
        [t.model_dump() for t in req.turns],
        req.self_speaker_id,
        _attrs(req),
        req.event_id,
        req.connection_id,
    )


# --------------------------------------------------------------------------
# Request models
# --------------------------------------------------------------------------
class Turn(BaseModel):
    speaker: int
    text: str


class SpeakerAttr(BaseModel):
    name: Optional[str] = None
    company: Optional[str] = None
    role: Optional[str] = None


class EncodeRequest(BaseModel):
    turns: list[Turn]
    self_speaker_id: int = 0
    speaker_attrs: dict[int, SpeakerAttr] = {}
    event_id: Optional[str] = None
    connection_id: Optional[str] = None
    use_agent: bool = False  # True -> populate context via the Cursor SDK agent


class TopicTimeInput(BaseModel):
    topic: str
    seconds: float = 0.0


class MeetingSignalInput(BaseModel):
    event_id: Optional[str] = None
    connection_id: Optional[str] = None
    name: Optional[str] = None
    company: Optional[str] = None
    role: Optional[str] = None
    origin: Optional[str] = None
    interests: list[str] = []
    background: Optional[str] = None
    topic_time: list[TopicTimeInput] = []
    most_time_topic: Optional[str] = None
    what_you_learned: list[str] = []
    most_interesting: Optional[str] = None
    transcript_excerpt: Optional[str] = None


# --------------------------------------------------------------------------
# Helpers
# --------------------------------------------------------------------------
def _attrs(req: EncodeRequest) -> dict[int, dict]:
    return {sid: a.model_dump() for sid, a in req.speaker_attrs.items()}


def _signal_from_input(payload: MeetingSignalInput) -> MeetingSignal:
    return MeetingSignal(
        event_id=payload.event_id,
        connection_id=payload.connection_id,
        name=payload.name,
        company=payload.company,
        role=payload.role,
        origin=payload.origin,
        interests=payload.interests,
        background=payload.background,
        topic_time=[TopicTime(**t.model_dump()) for t in payload.topic_time],
        most_time_topic=payload.most_time_topic,
        what_you_learned=payload.what_you_learned,
        most_interesting=payload.most_interesting,
        transcript_excerpt=payload.transcript_excerpt,
    )


# --------------------------------------------------------------------------
# Endpoints
# --------------------------------------------------------------------------
@app.get("/health")
async def health():
    return {"status": "healthy", "service": "warmth-meet-local"}


@app.post("/meet/encode")
async def encode(req: EncodeRequest):
    """ENCODERS: diarized transcript -> MeetingSignal + per-person knowledge graph.

    Set `use_agent: true` to populate the per-person context with the Cursor SDK
    agent instead of the lexical heuristics.
    """
    signal, kg = await _encode(req)
    return {
        "engine": "cursor-agent" if req.use_agent else "heuristic",
        "signal": signal.model_dump(),
        "knowledge_graph": {
            "session_id": kg.session_id,
            "people": [p.model_dump() for p in kg.people()],
        },
    }


@app.post("/meet/signals")
async def signals(payload: MeetingSignalInput):
    """MODELS: structured MeetingSignal -> ML pipeline routing decision."""
    signal = _signal_from_input(payload)
    decision = await pipeline.process(signal, community_members=[])
    return decision.model_dump()


@app.post("/meet/process")
async def process(req: EncodeRequest):
    """ENCODERS + MODELS: diarized transcript straight through to a decision."""
    signal, kg = await _encode(req)
    decision = await pipeline.process(signal, community_members=[])
    return {
        "engine": "cursor-agent" if req.use_agent else "heuristic",
        "signal": signal.model_dump(),
        "people": [p.model_dump() for p in kg.people()],
        "decision": decision.model_dump(),
    }


if __name__ == "__main__":
    import uvicorn

    host = os.getenv("MEET_HOST", "127.0.0.1")
    port = int(os.getenv("MEET_PORT", "8077"))
    uvicorn.run(app, host=host, port=port)
