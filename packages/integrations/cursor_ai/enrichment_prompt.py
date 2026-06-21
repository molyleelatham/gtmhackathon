from typing import Any

import json


class CursorEnrichmentPrompts:
    """Prompt templates for Cursor SDK operations"""

    @staticmethod
    def get_scoring_prompt(
        company_name: str,
        company_data: dict[str, Any],
        signals: list[dict[str, Any]],
        icp_config: dict[str, Any]
    ) -> str:
        """Generate prompt for lead scoring"""
        return f"""
You are a GTM intelligence expert. Score the following lead based on ICP fit and buying signals.

Company: {company_name}
Company Data: {json.dumps(company_data, indent=2)}
Detected Signals: {json.dumps(signals, indent=2)}
ICP Configuration: {json.dumps(icp_config, indent=2)}

Analyze the lead and provide:
1. ICP Fit Score (0-100)
2. Signal Strength Score (0-100)
3. Overall Score (0-100)
4. Key Insights
5. Recommendations

Return as JSON with keys: icp_score, signal_score, overall_score, insights, recommendations
"""

    @staticmethod
    def get_crm_payload_prompt(
        lead_data: dict[str, Any],
        enrichment_data: dict[str, Any],
        target_system: str
    ) -> str:
        """Generate prompt for CRM payload generation"""
        return f"""
You are a CRM integration specialist. Generate a properly formatted payload for {target_system} CRM.

Lead Data: {json.dumps(lead_data, indent=2)}
Enrichment Data: {json.dumps(enrichment_data, indent=2)}

Generate a CRM payload that includes:
1. Contact information
2. Company information
3. Lead score and qualification
4. Buying signals summary
5. Recommended next steps

Return as JSON matching the {target_system} CRM API format.
"""

    @staticmethod
    def get_signal_analysis_prompt(
        signals: list[dict[str, Any]],
        context: dict[str, Any]
    ) -> str:
        """Generate prompt for signal analysis"""
        return f"""
You are a GTM signal analyst. Analyze the following buying signals.

Signals: {json.dumps(signals, indent=2)}
Context: {json.dumps(context, indent=2)}

Provide:
1. Signal categorization (hiring, funding, tech, intent)
2. Urgency assessment
3. Company readiness indicators
4. Recommended outreach timing
5. Key talking points

Return as JSON with keys: categories, urgency, readiness, timing, talking_points
"""
