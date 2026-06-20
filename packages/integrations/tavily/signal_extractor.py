import re
from typing import Optional
from datetime import datetime
from ...core.models.signal import Signal, SignalType
from ...core.models.icp import ICPConfig
from .client import TavilyClient


class TavilySignalExtractor:
    """Extract GTM signals from Tavily search results"""
    
    def __init__(self, tavily_client: TavilyClient, icp_config: ICPConfig):
        self.tavily_client = tavily_client
        self.icp_config = icp_config
        
        # Compile regex patterns for ICP keywords
        self.keyword_patterns = [
            re.compile(rf"\b{re.escape(keyword)}\b", re.IGNORECASE)
            for keyword in icp_config.keywords
        ]
    
    async def extract_signals(self, query: Optional[str] = None) -> list[Signal]:
        """
        Extract signals from Tavily search results
        
        Args:
            query: Optional search query (defaults to ICP keywords)
        
        Returns:
            List of detected signals
        """
        search_query = query or " OR ".join(self.icp_config.keywords)
        
        try:
            search_results = await self.tavily_client.search_gtm_signals(
                keywords=self.icp_config.keywords
            )
        except Exception as e:
            print(f"Error searching Tavily: {e}")
            return []
        
        signals = []
        
        for result in search_results:
            # Check if content matches ICP keywords
            content = result.get("content", "")
            title = result.get("title", "")
            combined_text = f"{title} {content}"
            
            keywords_hit = self._extract_keywords(combined_text)
            
            if keywords_hit:
                # Determine signal type based on keywords
                signal_type = self._classify_signal_type(keywords_hit, combined_text)
                
                # Extract company name if possible
                company_name = self._extract_company_name(title, content)
                
                signal = Signal(
                    company_name=company_name or "Unknown Company",
                    company_domain=self._extract_domain(result.get("url", "")),
                    signal_type=signal_type,
                    raw_text=combined_text,
                    source="tavily_search",
                    keywords_hit=keywords_hit,
                    detected_at=datetime.utcnow()
                )
                
                signals.append(signal)
        
        return signals
    
    def _extract_keywords(self, text: str) -> list[str]:
        """Extract ICP keywords that appear in the text"""
        keywords_hit = []
        for pattern in self.keyword_patterns:
            if pattern.search(text):
                # Extract the actual keyword from the pattern
                keyword = pattern.pattern.split(r"\b")[1]
                if keyword not in keywords_hit:
                    keywords_hit.append(keyword)
        return keywords_hit
    
    def _classify_signal_type(self, keywords: list[str], text: str) -> SignalType:
        """Classify the signal type based on keywords and context"""
        text_lower = text.lower()
        
        # Hiring signals
        hiring_keywords = ["hiring", "job", "career", "opening", "position", "role"]
        if any(kw in text_lower for kw in hiring_keywords):
            return SignalType.HIRING
        
        # Funding signals
        funding_keywords = ["funding", "investment", "series", "raised", "venture", "investor"]
        if any(kw in text_lower for kw in funding_keywords):
            return SignalType.FUNDING
        
        # Tech adoption signals
        tech_keywords = ["hubspot", "salesforce", "pipeline", "crm", "revops", "automation"]
        if any(kw in text_lower for kw in tech_keywords):
            return SignalType.TECH
        
        # Default to intent
        return SignalType.INTENT
    
    def _extract_company_name(self, title: str, content: str) -> Optional[str]:
        """Extract company name from title or content"""
        # Simple heuristic: take the first significant word from title
        words = title.split()
        if words:
            return words[0]
        return None
    
    def _extract_domain(self, url: str) -> Optional[str]:
        """Extract domain from URL"""
        if not url:
            return None
        
        try:
            from urllib.parse import urlparse
            parsed = urlparse(url)
            return parsed.netloc
        except Exception:
            return None