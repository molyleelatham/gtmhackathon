import pytest
import os
from dotenv import load_dotenv

# Load environment variables for tests
load_dotenv()


@pytest.fixture
def icp_config():
    """Fixture providing default ICP configuration"""
    from packages.core.models.icp import ICPConfig
    return ICPConfig()


@pytest.fixture
def sample_signal():
    """Fixture providing a sample signal"""
    from packages.core.models.signal import Signal, SignalType
    return Signal(
        company_name="Test Company",
        company_domain="testcompany.com",
        signal_type=SignalType.HIRING,
        raw_text="Test Company is hiring for RevOps position",
        source="tavily_search",
        keywords_hit=["RevOps", "hiring"]
    )


@pytest.fixture
def sample_lead():
    """Fixture providing a sample lead"""
    from packages.core.models.lead import Lead
    return Lead(
        company_name="Test Company",
        company_domain="testcompany.com",
        contact_name="John Doe",
        contact_email="john@testcompany.com",
        icp_score=75,
        signal_source="tavily_search"
    )