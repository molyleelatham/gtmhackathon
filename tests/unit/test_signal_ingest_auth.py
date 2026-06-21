"""Tests for signal ingest auth checks."""

from unittest.mock import patch
from uuid import uuid4

import pytest
from warmth.apps.lifecycle import signal_ingest

from packages.core.schemas.event_audio_signal import EventAudioSignal, IOSPersonNode


@pytest.mark.asyncio
async def test_ingest_ios_signal_rejects_user_mismatch():
    payload = EventAudioSignal(
        id=uuid4(),
        person=IOSPersonNode(name="Alex"),
        raw_text="hello",
        icp_pre_score=50.0,
        user_uid="other-user",
    )
    with patch.object(signal_ingest, "auth_required", return_value=True), patch.object(
        signal_ingest, "get_user_id", return_value="authenticated-user"
    ):
        result = await signal_ingest.ingest_ios_signal(payload)
    assert result["status"] == "error"
    assert result["reason"] == "user_mismatch"
