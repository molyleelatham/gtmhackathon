from enum import Enum
from typing import Optional

from ....packages.core.models.conversation import ConversationIntelligence
from ....packages.core.models.lead import Lead


class LeadRouting(str, Enum):
    ME = "me"              # Direct leads for me
    TEAM = "team"          # Leads for my team
    FOUNDERS = "founders"  # Leads for founders
    COMMUNITY = "community" # Leads for friends/community


class LeadClassifier:
    """Classify leads based on conversation content and context"""

    def __init__(self, user_config: dict):
        """
        Initialize lead classifier with user configuration

        Args:
            user_config: User configuration including role, team structure, etc.
        """
        self.user_role = user_config.get("role", "individual")  # individual, team_lead, founder
        self.team_size = user_config.get("team_size", 1)
        self.company_stage = user_config.get("company_stage", "early")  # early, growth, mature
        self.target_personas = user_config.get("target_personas", [])
        self.community_networks = user_config.get("community_networks", [])

    def classify_lead(
        self,
        conversation: ConversationIntelligence,
        lead: Lead,
        context: Optional[dict] = None
    ) -> LeadRouting:
        """
        Classify who this lead should be routed to

        Args:
            conversation: Conversation intelligence data
            lead: Lead information
            context: Additional context (event, etc.)

        Returns:
            LeadRouting indicating who should handle this lead
        """
        context = context or {}

        # Extract signals from conversation
        funding_keywords = ["funding", "investment", "series", "venture", "investor"]
        founder_keywords = ["founder", "startup", "entrepreneur", "ceo", "co-founder"]
        team_keywords = ["team", "hiring", "recruiting", "scaling", "growth"]
        community_keywords = ["friend", "introduction", "network", "community", "mentor"]

        conversation_text = conversation.transcript.lower()
        topics_text = " ".join(conversation.topics).lower()
        combined_text = f"{conversation_text} {topics_text}"

        # Check for founder-level signals
        founder_signals = sum(1 for kw in founder_keywords if kw in combined_text)
        funding_signals = sum(1 for kw in funding_keywords if kw in combined_text)

        # Check for team-level signals
        team_signals = sum(1 for kw in team_keywords if kw in combined_text)

        # Check for community signals
        community_signals = sum(1 for kw in community_keywords if kw in combined_text)

        # Lead classification logic
        if founder_signals >= 2 or funding_signals >= 2:
            # High-level founder/investor conversations → route to founders
            if self.user_role in ["founder", "team_lead"]:
                return LeadRouting.ME
            else:
                return LeadRouting.FOUNDERS

        elif team_signals >= 2:
            # Team/hiring conversations → route to team
            if self.user_role == "team_lead":
                return LeadRouting.ME
            else:
                return LeadRouting.TEAM

        elif community_signals >= 2:
            # Community/friend connections → route to community
            return LeadRouting.COMMUNITY

        else:
            # Default routing based on user role and company fit
            if self._is_good_personal_fit(lead, conversation):
                return LeadRouting.ME
            elif self._is_team_fit(lead, conversation):
                return LeadRouting.TEAM
            else:
                return LeadRouting.COMMUNITY

    def _is_good_personal_fit(self, lead: Lead, conversation: ConversationIntelligence) -> bool:
        """Check if lead is a good fit for personal handling"""
        # High ICP score + direct relevance
        if lead.icp_score >= 70:
            return True

        # Check if conversation topics match personal interests
        personal_interests = ["revops", "sales", "crm", "pipeline"]
        topic_match = any(
            interest in conversation.topics or interest in conversation.interests
            for interest in personal_interests
        )

        return topic_match

    def _is_team_fit(self, lead: Lead, conversation: ConversationIntelligence) -> bool:
        """Check if lead should be routed to team"""
        # Team-sized companies + hiring signals
        if lead.company_size and lead.company_size >= 10:
            hiring_keywords = ["hiring", "recruiting", "team", "scaling"]
            conversation_text = conversation.transcript.lower()
            hiring_signals = sum(1 for kw in hiring_keywords if kw in conversation_text)

            if hiring_signals >= 1:
                return True

        return False
