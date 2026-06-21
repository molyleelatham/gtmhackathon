from packages.core.models.signal import Signal, SignalType


class TestKeywordEngine:
    """Test keyword extraction and matching"""

    def test_icp_keyword_detection(self, icp_config):
        """Test that ICP keywords are properly detected"""
        test_text = "We are looking for a RevOps specialist and use HubSpot for pipeline visibility"

        found_keywords = []
        for keyword in icp_config.keywords:
            if keyword.lower() in test_text.lower():
                found_keywords.append(keyword)

        assert "RevOps" in found_keywords
        assert "HubSpot" in found_keywords
        assert "pipeline visibility" in found_keywords

    def test_signal_type_classification(self):
        """Test signal type classification based on keywords"""
        hiring_text = "We are hiring for a Sales Engineer position"
        funding_text = "We just closed our Series B funding round"
        tech_text = "We use Salesforce for our CRM pipeline"

        # Simple classification logic
        def classify_signal(text):
            text_lower = text.lower()
            if "hiring" in text_lower or "position" in text_lower:
                return SignalType.HIRING
            elif "funding" in text_lower or "series" in text_lower:
                return SignalType.FUNDING
            elif "salesforce" in text_lower or "hubspot" in text_lower or "pipeline" in text_lower:
                return SignalType.TECH
            else:
                return SignalType.INTENT

        assert classify_signal(hiring_text) == SignalType.HIRING
        assert classify_signal(funding_text) == SignalType.FUNDING
        assert classify_signal(tech_text) == SignalType.TECH

    def test_signal_creation(self):
        """Test Signal model creation"""
        signal = Signal(
            company_name="Test Corp",
            signal_type=SignalType.HIRING,
            raw_text="Test Corp is hiring",
            source="tavily_search",
            keywords_hit=["hiring"]
        )

        assert signal.company_name == "Test Corp"
        assert signal.signal_type == SignalType.HIRING
        assert signal.source == "tavily_search"
        assert "hiring" in signal.keywords_hit
        assert signal.id is not None
