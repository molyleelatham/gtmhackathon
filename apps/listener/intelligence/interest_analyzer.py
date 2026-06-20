import re


class InterestAnalyzer:
    """Analyze what people care about from conversations"""
    
    def __init__(self):
        # Interest categories
        self.interest_patterns = {
            "technology_interests": [
                r"interested in (?:new|latest|emerging) technology",
                r"looking for (?:tech|software|platform)",
                r"excited about (?:ai|machine learning|automation)",
                r"exploring (?:new tools|new solutions)"
            ],
            "business_growth": [
                r"looking to (?:grow|scale|expand)",
                r"interested in (?:growth|scaling|revenue)",
                r"want to (?:increase|improve) (?:sales|revenue)",
                r"focus(ed)? on (?:growth|expansion)"
            ],
            "efficiency": [
                r"looking for (?:efficiency|automation)",
                r"want to (?:streamline|optimize|improve)",
                r"struggling with (?:manual|process|workflow)",
                r"need to (?:save time|reduce costs|improve efficiency)"
            ],
            "innovation": [
                r"interested in (?:innovation|new ideas)",
                r"looking for (?:disruptive|cutting-edge)",
                r"want to (?:innovate|transform|revolutionize)",
                r"excited about (?:new approaches|new methods)"
            ],
            "partnership": [
                r"looking for (?:partners|partnerships|collaboration)",
                r"interested in (?:working together|collaborating)",
                r"open to (?:partnership|integration)",
                r"seeking (?:strategic partnerships|alliances)"
            ]
        }
        
        # Values indicators
        self.value_indicators = {
            "innovation": ["innovative", "cutting-edge", "disruptive", "revolutionary", "breakthrough"],
            "efficiency": ["efficient", "streamlined", "optimized", "automated", "productive"],
            "growth": ["growth", "scale", "expand", "increase", "accelerate"],
            "quality": ["quality", "excellence", "premium", "high-quality", "best-in-class"],
            "accuracy": ["accuracy", "accurate", "precise", "precision", "exact", "correct", "reliable"],
            "customer_focus": ["customer-centric", "user-focused", "customer satisfaction", "user experience"],
            "transparency": ["transparent", "honesty", "openness", "communicative"],
            "collaboration": ["collaborative", "teamwork", "partnership", "cooperation"],
            "sustainability": ["sustainable", "eco-friendly", "green", "environmental", "social impact"]
        }
    
    def analyze_interests(self, transcript: str) -> dict:
        """
        Analyze interests from conversation transcript
        
        Args:
            transcript: Conversation transcript text
        
        Returns:
            Dictionary with interests, values, pain points, and goals
        """
        transcript_lower = transcript.lower()
        
        interests = self._extract_interests(transcript_lower)
        values = self._extract_values(transcript_lower)
        pain_points = self._extract_pain_points(transcript_lower)
        goals = self._extract_goals(transcript_lower)
        
        return {
            "interests": interests,
            "values": values,
            "pain_points": pain_points,
            "goals": goals
        }
    
    def _extract_interests(self, text: str) -> list[str]:
        """Extract interest categories from text"""
        detected_interests = []
        
        for interest, patterns in self.interest_patterns.items():
            for pattern in patterns:
                if re.search(pattern, text):
                    if interest not in detected_interests:
                        detected_interests.append(interest)
                    break
        
        return detected_interests
    
    def _extract_values(self, text: str) -> list[str]:
        """Extract values from text (word-boundary matched to avoid substring
        false positives like "honest" inside "honestly")."""
        detected_values = []

        for value, indicators in self.value_indicators.items():
            for indicator in indicators:
                if re.search(rf"\b{re.escape(indicator)}\b", text):
                    if value not in detected_values:
                        detected_values.append(value)
                    break

        return detected_values
    
    def _extract_pain_points(self, text: str) -> list[str]:
        """Extract pain points from text"""
        pain_point_patterns = [
            r"struggling with (.+?)(?:\.|,| but)",
            r"having trouble with (.+?)(?:\.|,| but)",
            r"frustrated by (.+?)(?:\.|,| but)",
            r"challenge(d)? with (.+?)(?:\.|,| but)",
            r"issue with (.+?)(?:\.|,| but)",
            r"problem with (.+?)(?:\.|,| but)"
        ]
        
        pain_points = []
        for pattern in pain_point_patterns:
            matches = re.findall(pattern, text)
            for match in matches:
                if isinstance(match, tuple):
                    pain_point = match[1] if len(match) > 1 else match[0]
                else:
                    pain_point = match
                
                pain_point = pain_point.strip()
                if pain_point and len(pain_point) > 3:
                    pain_points.append(pain_point)
        
        return list(set(pain_points))  # Remove duplicates
    
    def _extract_goals(self, text: str) -> list[str]:
        """Extract goals from text"""
        goal_patterns = [
            r"looking to (.+?)(?:\.|,| but)",
            r"want to (.+?)(?:\.|,| but)",
            r"hoping to (.+?)(?:\.|,| but)",
            r"planning to (.+?)(?:\.|,| but)",
            r"aiming to (.+?)(?:\.|,| but)",
            r"goal is to (.+?)(?:\.|,| but)"
        ]
        
        goals = []
        for pattern in goal_patterns:
            matches = re.findall(pattern, text)
            for match in matches:
                goal = match.strip()
                if goal and len(goal) > 3:
                    goals.append(goal)
        
        return list(set(goals))  # Remove duplicates