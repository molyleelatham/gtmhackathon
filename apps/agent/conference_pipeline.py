"""Deprecated shim — import from event_pipeline instead."""
from .event_pipeline import EventPipeline

ConferencePipeline = EventPipeline

__all__ = ["ConferencePipeline", "EventPipeline"]
