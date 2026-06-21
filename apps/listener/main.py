import asyncio
import os

from dotenv import load_dotenv

# Load environment variables: local .env first (developer overrides), then fill
# any gaps from the shared Google Secret Manager project.
load_dotenv()
from ...packages.core.secrets import load_secrets_into_env  # noqa: E402

load_secrets_into_env()

from ...infra.firebase.firestore import FirestoreClient
from ...packages.core.models.icp import ICPConfig
from ...packages.integrations.tavily.client import TavilyClient
from ...packages.integrations.tavily.signal_extractor import TavilySignalExtractor
from .engine import PassiveListener


async def main():
    """Main entry point for the listener service"""
    print("🚀 Starting Warmth Listener Service...")

    # Check required environment variables
    required_vars = ["TAVILY_API_KEY", "FIREBASE_SERVICE_ACCOUNT_KEY"]
    missing_vars = [var for var in required_vars if not os.getenv(var)]

    if missing_vars:
        print(f"❌ Missing required environment variables: {missing_vars}")
        return

    try:
        # Initialize components
        print("📦 Initializing components...")

        icp_config = ICPConfig()
        tavily_client = TavilyClient()
        signal_extractor = TavilySignalExtractor(tavily_client, icp_config)
        firestore_client = FirestoreClient()

        # Create and start listener
        listener = PassiveListener(
            icp_config=icp_config,
            signal_extractor=signal_extractor,
            firestore_client=firestore_client
        )

        print("✅ Components initialized successfully")
        print("🎯 Starting signal detection...")

        # Start the listener (this will run indefinitely)
        await listener.start()

    except KeyboardInterrupt:
        print("\n🛑 Received interrupt signal, shutting down...")
    except Exception as e:
        print(f"❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
