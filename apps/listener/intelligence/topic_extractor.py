import re
from collections import Counter


class TopicExtractor:
    """Extract main topics from conversation transcripts"""

    def __init__(self):
        # Common business/tech topics
        self.topic_keywords = {
            "funding": ["funding", "investment", "series", "venture", "investor", "raise", "capital"],
            "hiring": ["hiring", "recruiting", "team", "scaling", "growth", "position", "role"],
            "technology": ["tech", "software", "platform", "ai", "ml", "infrastructure", "stack"],
            "sales": ["sales", "revenue", "pipeline", "crm", "deals", "quota", "targets"],
            "marketing": ["marketing", "brand", "campaign", "leads", "acquisition", "growth"],
            "product": ["product", "features", "roadmap", "development", "launch", "users"],
            "operations": ["operations", "ops", "process", "workflow", "efficiency", "automation"],
            "strategy": ["strategy", "vision", "mission", "goals", "planning", "execution"],
            "competition": ["competition", "competitors", "market", "landscape", "differentiation"],
            "customer": ["customer", "users", "clients", "satisfaction", "retention", "churn"],
            "partnership": ["partnership", "partner", "collaboration", "integration", "ecosystem"]
        }

    def extract_topics(self, transcript: str, top_n: int = 5) -> list[str]:
        """
        Extract main topics from conversation transcript

        Args:
            transcript: Conversation transcript text
            top_n: Number of top topics to return

        Returns:
            List of top topics mentioned
        """
        transcript_lower = transcript.lower()

        # Count mentions of each topic
        topic_scores = {}
        for topic, keywords in self.topic_keywords.items():
            score = sum(1 for keyword in keywords if keyword in transcript_lower)
            if score > 0:
                topic_scores[topic] = score

        # Sort by score and return top N
        sorted_topics = sorted(topic_scores.items(), key=lambda x: x[1], reverse=True)
        return [topic for topic, score in sorted_topics[:top_n]]

    def extract_key_phrases(self, transcript: str, max_phrases: int = 10) -> list[str]:
        """
        Extract key phrases from transcript

        Args:
            transcript: Conversation transcript text
            max_phrases: Maximum number of phrases to extract

        Returns:
            List of key phrases
        """
        # Simple noun phrase extraction
        sentences = re.split(r'[.!?]+', transcript)

        phrases = []
        for sentence in sentences:
            sentence = sentence.strip()
            if len(sentence) > 10:  # Ignore very short sentences
                # Extract potential phrases (capitalized words sequences)
                phrase_candidates = re.findall(r'[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*', sentence)
                phrases.extend(phrase_candidates)

        # Count phrase frequency
        phrase_counts = Counter(phrases)

        # Return most common phrases
        return [phrase for phrase, count in phrase_counts.most_common(max_phrases)]
