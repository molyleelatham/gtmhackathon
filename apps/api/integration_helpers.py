"""Shared helpers for wiring integrations into API routers."""
import os
from typing import Optional

from ...packages.integrations.zero_crm.client import ZeroCRMClient
from ...packages.integrations.unify_gtm.client import UnifyGTMClient
from ...packages.integrations.google_mcp.client import GoogleMCPClient
from ...packages.integrations.lightfern.workflow import LightfernClient
from ...packages.integrations.faxxing.client import FaxxingClient
from ...packages.core.models.lead import Lead
from ...packages.core.models.pre_connection import PreMeetConnection
from ...packages.core.models.meeting_signal import MeetingSignal


def zero_client_optional() -> Optional[ZeroCRMClient]:
    if not os.getenv("ZERO_CRM_API_KEY"):
        return None
    try:
        return ZeroCRMClient()
    except Exception as e:
        print(f"Zero CRM client unavailable: {e}")
        return None


def unify_client_optional() -> Optional[UnifyGTMClient]:
    if not os.getenv("UNIFY_GTM_API_KEY") and not os.getenv("UNIFY_API_KEY"):
        return None
    try:
        return UnifyGTMClient()
    except Exception as e:
        print(f"UnifyGTM client unavailable: {e}")
        return None


def gmail_client_optional() -> Optional[GoogleMCPClient]:
    if not os.getenv("GOOGLE_MCP_SERVER_URL") and not os.getenv("GOOGLE_MCP_CREDENTIALS"):
        return None
    try:
        return GoogleMCPClient()
    except Exception as e:
        print(f"Google MCP client unavailable: {e}")
        return None


def lightfern_client() -> LightfernClient:
    return LightfernClient()


def faxxing_client() -> FaxxingClient:
    return FaxxingClient()


def use_agent_extraction() -> bool:
    return os.getenv("WARMTH_USE_AGENT", "").lower() in ("1", "true", "yes")


def warmth_client_email() -> str:
    """Gmail account Warmth drafts for (Lightfern polishes here)."""
    return os.getenv("WARMTH_CLIENT_EMAIL", "getwarmth@gmail.com").strip()


def warmth_client_name() -> str:
    return os.getenv("WARMTH_CLIENT_NAME", "Warmth").strip()


def lead_from_connection(conn: PreMeetConnection) -> Lead:
    return Lead(
        id=f"lead_{conn.id}",
        company_name=conn.company_name or "Unknown Company",
        contact_name=conn.name,
        contact_email=conn.email,
        company_size=conn.company_size,
        icp_score=int(conn.icp_score),
        signal_source=conn.source,
    )


def lead_from_signal(signal: MeetingSignal, conn: Optional[PreMeetConnection] = None) -> Lead:
    if conn:
        return lead_from_connection(conn)
    return Lead(
        company_name=signal.company or "Unknown Company",
        contact_name=signal.name,
        signal_source="conference_audio",
    )
