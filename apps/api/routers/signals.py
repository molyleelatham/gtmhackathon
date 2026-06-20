"""POST /api/signals — iOS ingress (CapturedSignal + legacy EventAudioSignal)."""
from typing import Any

from fastapi import APIRouter, Request, Response
from pydantic import ValidationError

from ...lifecycle.signal_ingest import ingest_captured_signal, ingest_ios_signal
from ....packages.core.schemas.captured_signal import CapturedSignalPayload
from ....packages.core.schemas.event_audio_signal import EventAudioSignal

router = APIRouter(tags=["signals"])


def _status_code(result: dict[str, Any]) -> int:
    if result.get("status") == "duplicate":
        return 200
    return 202


@router.post("/api/signals")
async def receive_ios_signal(request: Request, response: Response):
    """Accept iOS capture signals and run meet → score → Gmail draft handoff.

    Supports both payloads:
    - **CapturedSignal** (Xcode app): `session_id`, `transcript_excerpt`, `icp_keyword_score`
    - **EventAudioSignal** (legacy wake-word pipeline): `icp_pre_score`, `raw_text`

    Scoring, lead data, and person context are packaged into a Gmail draft so
    Lightfern can populate/polish inside Gmail; the human completes and sends.
    """
    body = await request.json()

    if "session_id" in body:
        try:
            payload = CapturedSignalPayload.model_validate(body)
        except ValidationError as exc:
            return {"status": "error", "reason": "invalid_captured_signal", "detail": exc.errors()}
        result = await ingest_captured_signal(payload)
    else:
        try:
            payload = EventAudioSignal.model_validate(body)
        except ValidationError as exc:
            return {"status": "error", "reason": "invalid_signal", "detail": exc.errors()}
        result = await ingest_ios_signal(payload)

    response.status_code = _status_code(result)
    return result
