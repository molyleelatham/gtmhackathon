import httpx
from typing import Optional, Any
import os


class TavilyClient:
    """Client for Tavily Search API to detect GTM signals"""
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("TAVILY_API_KEY")
        self.base_url = "https://api.tavily.com"
        if not self.api_key:
            raise ValueError("TAVILY_API_KEY environment variable must be set")
    
    async def search(
        self,
        query: str,
        search_depth: str = "basic",
        max_results: int = 10,
        include_domains: Optional[list[str]] = None,
        exclude_domains: Optional[list[str]] = None
    ) -> dict[str, Any]:
        """
        Perform a search using Tavily API
        
        Args:
            query: Search query string
            search_depth: "basic" or "advanced"
            max_results: Maximum number of results to return
            include_domains: List of domains to include in search
            exclude_domains: List of domains to exclude from search
        
        Returns:
            Search results dictionary
        """
        url = f"{self.base_url}/search"
        
        payload = {
            "api_key": self.api_key,
            "query": query,
            "search_depth": search_depth,
            "max_results": max_results,
            "include_answer": False,
            "include_raw_content": False,
            "include_images": False
        }
        
        if include_domains:
            payload["include_domains"] = include_domains
        if exclude_domains:
            payload["exclude_domains"] = exclude_domains
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(url, json=payload)
            response.raise_for_status()
            return response.json()
    
    async def search_gtm_signals(
        self,
        keywords: list[str],
        time_range: Optional[str] = None
    ) -> list[dict[str, Any]]:
        """
        Search for GTM-related signals based on keywords
        
        Args:
            keywords: List of ICP keywords to search for
            time_range: Optional time range filter (e.g., "w", "m", "y")
        
        Returns:
            List of potential signal results
        """
        query = " OR ".join(keywords)
        results = await self.search(query, max_results=20)
        
        signals = []
        for result in results.get("results", []):
            signal = {
                "title": result.get("title", ""),
                "url": result.get("url", ""),
                "content": result.get("content", ""),
                "score": result.get("score", 0.0),
                "published_date": result.get("published_date")
            }
            signals.append(signal)
        
        return signals