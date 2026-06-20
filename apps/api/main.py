from contextlib import asynccontextmanager
import os
from dotenv import load_dotenv

# Load env: local .env first (developer overrides), then fill gaps from the
# shared Google Secret Manager project. Must run before clients read os.getenv.
load_dotenv()
from ...packages.core.secrets import load_secrets_into_env  # noqa: E402
load_secrets_into_env()

from fastapi import FastAPI  # noqa: E402
from fastapi.middleware.cors import CORSMiddleware  # noqa: E402
from .middleware.auth_middleware import FirebaseAuthMiddleware  # noqa: E402
from .middleware.signal_rate_limit import SignalRateLimitMiddleware  # noqa: E402
from .deps import set_firestore_client  # noqa: E402
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
    
    # Firebase Admin (Auth token verification + optional Firestore)
    from ...infra.firebase.admin import ensure_firebase_initialized

    try:
        ensure_firebase_initialized()
        print("✅ Firebase Admin initialized")
    except Exception as e:
        print(f"⚠️  Firebase Admin initialization failed: {e}")

    try:
        firestore_client = FirestoreClient()
        set_firestore_client(firestore_client)
        print("✅ Firebase Firestore initialized")
    except Exception as e:
        print(f"⚠️  Firebase Firestore initialization failed: {e}")
    
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


# Production hardening flags (set in infra/cloudrun-env.yaml)
_is_deployed = bool(os.getenv("GCP_PROJECT_ID"))
_disable_openapi = os.getenv("DISABLE_OPENAPI", "true" if _is_deployed else "").lower() in (
    "1",
    "true",
    "yes",
)

# Create FastAPI app
app = FastAPI(
    title="Warmth API",
    description="Passive Social Listening × GTM Signal Intelligence",
    version="0.1.0",
    lifespan=lifespan,
    docs_url=None if _disable_openapi else "/docs",
    redoc_url=None if _disable_openapi else "/redoc",
    openapi_url=None if _disable_openapi else "/openapi.json",
)

_cors_origins_raw = os.getenv("WEB_ALLOWED_ORIGINS", "").strip()
if _cors_origins_raw:
    _cors_origins = [
        origin.strip() for origin in _cors_origins_raw.split(",") if origin.strip()
    ]
elif _is_deployed:
    _cors_origins = []
else:
    _cors_origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins,
    allow_credentials=bool(_cors_origins_raw),
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"],
)
app.add_middleware(FirebaseAuthMiddleware)
app.add_middleware(SignalRateLimitMiddleware)


# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint for Cloud Run probes."""
    payload: dict[str, str | bool] = {
        "status": "healthy",
        "service": "warmth-api",
    }
    if not _is_deployed:
        payload["listener_running"] = listener_instance is not None
    return payload


# Lifecycle routers: onboarding -> before-meet -> meet -> post-meet + dashboard data
from .routers import onboarding, premeet, meet, postmeet, data, event_runs, signals, users, conferences

app.include_router(onboarding.router)
app.include_router(users.router)
app.include_router(premeet.router)
app.include_router(meet.router)
app.include_router(postmeet.router)
app.include_router(data.router)
app.include_router(event_runs.router)
app.include_router(conferences.legacy_router)
app.include_router(signals.router)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)