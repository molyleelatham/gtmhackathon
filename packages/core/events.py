from datetime import datetime
from typing import Any, Optional
from pydantic import BaseModel, Field
from .models.signal import Signal


class DomainEvent(BaseModel):
    event_id: str = Field(default_factory=lambda: f"evt_{datetime.now().timestamp()}")
    event_type: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    data: dict[str, Any] = Field(default_factory=dict)


class SignalDetected(DomainEvent):
    event_type: str = "signal_detected"
    data: dict[str, Any] = Field(default_factory=lambda: {
        "signal": None,  # Signal object
        "source": "",
        "icp_pre_score": None
    })


class LeadEnriched(DomainEvent):
    event_type: str = "lead_enriched"
    data: dict[str, Any] = Field(default_factory=lambda: {
        "lead_id": "",
        "enrichment_data": {},
        "icp_score": 0
    })


class LeadScored(DomainEvent):
    event_type: str = "lead_scored"
    data: dict[str, Any] = Field(default_factory=lambda: {
        "lead_id": "",
        "score": 0,
        "scoring_method": ""
    })


class LeadPushedToCRM(DomainEvent):
    event_type: str = "lead_pushed_to_crm"
    data: dict[str, Any] = Field(default_factory=lambda: {
        "lead_id": "",
        "crm_system": "zero",
        "crm_lead_id": "",
        "success": True
    })


class WorkflowTriggered(DomainEvent):
    event_type: str = "workflow_triggered"
    data: dict[str, Any] = Field(default_factory=lambda: {
        "lead_id": "",
        "workflow_id": "",
        "workflow_system": "lightfern",
        "trigger_type": ""
    })