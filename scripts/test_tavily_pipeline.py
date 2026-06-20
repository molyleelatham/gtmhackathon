import asyncio
import os
import sys
from dotenv import load_dotenv

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

load_dotenv()

from packages.core.models.icp import ICPConfig
from packages.integrations.tavily.client import TavilyClient
from packages.integrations.tavily.signal_extractor import TavilySignalExtractor


async def test_tavily_integration():
    """Test Tavily integration for signal detection"""
    print("🧪 Testing Tavily Integration...")
    
    # Check API key
    if not os.getenv("TAVILY_API_KEY"):
        print("❌ TAVILY_API_KEY environment variable not set")
        return
    
    try:
        # Initialize components
        print("📦 Initializing Tavily client...")
        tavily_client = TavilyClient()
        
        print("📦 Loading ICP configuration...")
        icp_config = ICPConfig()
        
        print("📦 Creating signal extractor...")
        signal_extractor = TavilySignalExtractor(tavily_client, icp_config)
        
        # Test signal extraction
        print("🔍 Extracting signals...")
        signals = await signal_extractor.extract_signals()
        
        print(f"✅ Found {len(signals)} signals:")
        
        for i, signal in enumerate(signals, 1):
            print(f"\n{i}. {signal.company_name}")
            print(f"   Type: {signal.signal_type.value}")
            print(f"   Source: {signal.source}")
            print(f"   Keywords: {', '.join(signal.keywords_hit)}")
            print(f"   Score: {signal.icp_pre_score}")
            print(f"   Text: {signal.raw_text[:200]}...")
        
        # Test search directly
        print("\n🔍 Testing direct search...")
        results = await tavily_client.search("RevOps hiring HubSpot", max_results=3)
        print(f"✅ Search returned {len(results.get('results', []))} results")
        
        print("\n✅ Tavily integration test completed successfully!")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(test_tavily_integration())