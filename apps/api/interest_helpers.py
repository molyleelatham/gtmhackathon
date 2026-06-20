"""Helpers for merging iOS / meet-pipeline interest signals onto connections."""
from __future__ import annotations

from typing import Any


def merge_interests(*sources: list[str] | None) -> list[str]:
    """De-dupe interests preserving first-seen order."""
    seen: set[str] = set()
    merged: list[str] = []
    for source in sources:
        if not source:
            continue
        for item in source:
            key = item.strip()
            if not key:
                continue
            norm = key.lower()
            if norm in seen:
                continue
            seen.add(norm)
            merged.append(key)
    return merged


def interests_from_knowledge_graph(people: list[dict[str, Any]] | None) -> list[str]:
    """Pull topic weights + values + communication style from PersonNode dumps."""
    if not people:
        return []
    primary = people[0]
    topics = list((primary.get("topic_weights") or {}).keys())
    values = list(primary.get("values") or [])
    styles = list(primary.get("communication_style") or [])
    learnings = list(primary.get("learnings") or [])
    return merge_interests(topics, values, styles, learnings)


def interests_from_meet_summary(summary: dict[str, Any], payload_interests: list[str]) -> list[str]:
    signal = summary.get("signal") or {}
    signal_interests = list(signal.get("interests") or [])
    kg_interests = interests_from_knowledge_graph(summary.get("people"))
    return merge_interests(payload_interests, signal_interests, kg_interests)
