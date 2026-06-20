from contextlib import asynccontextmanager
from dotenv import load_dotenv

# Load env: local .env first (developer overrides), then fill gaps from the
# shared Google Secret Manager project. Must run before clients read os.getenv.
load_dotenv()
from ...packages.core.secrets import load_secrets_into_env  # noqa: E402
load_secrets_into_env()

from fastapi import FastAPI  # noqa: E402
from fastapi.middleware.cors import CORSMiddleware  # noqa: E402
from ..listener.engine import PassiveListener  # noqa: E402
from ...infra.firebase.firestore import FirestoreClient  # noqa: E402
from ...packages.core.models.icp import ICPConfig  # noqa: E402


# Global state
listener_instance = None
firestore_client = None
icp_config = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup and shutdown events"""
    global listener_instance, firestore_client, icp_config
    
    # Startup
    print("🚀 Starting Warmth API...")
    
    # Initialize Firebase Firestore
    try:
        firestore_client = FirestoreClient()
        print("✅ Firebase Firestore initialized")
    except Exception as e:
        print(f"⚠️  Firebase initialization failed: {e}")
    
    # Load ICP configuration
    icp_config = ICPConfig()
    print("✅ ICP configuration loaded")
    
    # Initialize passive listener
    try:
        from ...packages.integrations.tavily.client import TavilyClient
        from ...packages.integrations.tavily.signal_extractor import TavilySignalExtractor
        
        tavily_client = TavilyClient()
        signal_extractor = TavilySignalExtractor(tavily_client, icp_config)
        
        listener_instance = PassiveListener(
            icp_config=icp_config,
            signal_extractor=signal_extractor,
            firestore_client=firestore_client
        )
        print("✅ Passive listener initialized")
    except Exception as e:
        print(f"⚠️  Listener initialization failed: {e}")
    
    yield
    
    # Shutdown
    print("🛑 Shutting down Warmth API...")
    if listener_instance:
        await listener_instance.stop()


# Create FastAPI app
app = FastAPI(
    title="Warmth API",
    description="Passive Social Listening × GTM Signal Intelligence",
    version="0.1.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "warmth-api",
        "listener_running": listener_instance is not None
    }


# Lifecycle routers: onboarding -> before-meet -> meet -> post-meet + dashboard data
from .routers import onboarding, premeet, meet, postmeet, data, conferences, signals

app.include_router(onboarding.router)
app.include_router(premeet.router)
app.include_router(meet.router)
app.include_router(postmeet.router)
app.include_router(data.router)
app.include_router(conferences.router)
app.include_router(signals.router)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)