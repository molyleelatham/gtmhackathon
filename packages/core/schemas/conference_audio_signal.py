"""Deprecated shim — import from event_audio_signal instead."""
from .event_audio_signal import EventAudioSignal

ConferenceAudioSignal = EventAudioSignal

__all__ = ["ConferenceAudioSignal", "EventAudioSignal"]
