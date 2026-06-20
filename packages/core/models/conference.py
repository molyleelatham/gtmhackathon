"""Deprecated shim — import from event_directory instead."""
from .event_directory import EventAttendee, EventDirectory

Conference = EventDirectory
ConferenceAttendee = EventAttendee

__all__ = ["Conference", "ConferenceAttendee", "EventAttendee", "EventDirectory"]
