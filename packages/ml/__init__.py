"""Warmth ML package.

Stubs for the data/ML pipeline that powers warmth scoring, clustering, and
lead prioritization. The real models are intended to be implemented by the
Warmth team; these stubs define the interfaces and return placeholder values
so the rest of the lifecycle can be wired end-to-end.
"""
from .clustering import LeadClusterer
from .lead_scorer import LeadScorer
from .pipeline import MeetIntelligencePipeline, RoutingDecision, RoutingTarget
from .warmth_model import WarmthFeatures, WarmthModel

__all__ = [
    "WarmthModel",
    "WarmthFeatures",
    "LeadClusterer",
    "LeadScorer",
    "MeetIntelligencePipeline",
    "RoutingDecision",
    "RoutingTarget",
]
