from fastapi import FastAPI, Depends, HTTPException, Request
from fastapi.staticfiles import StaticFiles
import logging

# Rate Limiting
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from .database import get_db, async_engine
from .models import Base
# from .database import engine # Remove sync engine import
from .config import settings, setup_logging
from .middleware import RateLimitHeaderMiddleware, RequestTimingMiddleware

# Import routers
from .routers import (
    static_router,
    consent_router,
    consent_dashboard_router,
    buyer_router,
    offer_router,
    reward_router,
    wallet_router,
    payout_router,
    auth_router,
    data_packaging_router,
    insight_router,
    dsr_router,
    agent_router
)

from .routers.buyer_data import buyer_data_router
from .routers.llm_router import llm_router
from .routers.embedding_router import embedding_router
from .routers.consent_ledger import consent_ledger_router
from .routers.consent_export import router as consent_export_router
from app.routers import users, data, consent, payment, embeddings, evaluation
from .routers import user_router

# Import exception handlers
from .exceptions import register_exception_handlers
# Import new centralized error handlers
from .errors import get_exception_handlers

from fastapi.middleware.cors import CORSMiddleware

# Call logging setup early
setup_logging()

# Get a logger instance for this module
log = logging.getLogger("app")

# Rate Limiter Setup
limiter = Limiter(key_func=get_remote_address)

# Async database engine (already defined in database.py)
# from .database import async_engine # No need to import again if imported above

# Create FastAPI app
app = FastAPI(
    title="Tavren Backend API",
    description="API for managing consent events, buyer trust, and wallet operations",
    version="0.1.0"
)

# Create tables at startup instead of on import to avoid side effects
@app.on_event("startup")
async def create_tables():
    """Create database tables on application startup."""
    log.info("Creating database tables if they don't exist...")
    try:
        async with async_engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        log.info("Database tables created successfully")
    except Exception as e:
        log.error(f"Error creating database tables: {str(e)}")
        # Don't fail startup - tables might already exist or will be created by migrations

# Add startup event for other initialization tasks
@app.on_event("startup")
async def startup_event():
    log.info("Running startup event...")
    
    # Create data directory if it doesn't exist
    data_dir = settings.DATA_DIR
    if not data_dir.exists():
        log.info(f"Creating data directory: {data_dir}")
        data_dir.mkdir(parents=True, exist_ok=True)

# Apply Rate Limiter to App
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Add custom middleware
app.add_middleware(RequestTimingMiddleware)
app.add_middleware(RateLimitHeaderMiddleware)

# Add CORS middleware for frontend development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],  # Frontend dev servers
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register old exception handlers (legacy)
register_exception_handlers(app)

# Register new centralized exception handlers
for exception_class, handler in get_exception_handlers().items():
    app.add_exception_handler(exception_class, handler)

# Mount the static directory
if not settings.STATIC_DIR.is_dir():
    log.warning(f"Static directory not found at {settings.STATIC_DIR}. Static files may not serve correctly.")
app.mount("/static", StaticFiles(directory=settings.STATIC_DIR), name="static")

# Include routers
# Static page routes
app.include_router(static_router)

# Consent routes
app.include_router(consent_router)
app.include_router(consent_dashboard_router)
app.include_router(consent_ledger_router)
app.include_router(consent_export_router)

# DSR routes
app.include_router(dsr_router)

# Buyer routes
app.include_router(buyer_router)
app.include_router(buyer_data_router)

# Wallet and payout routes
app.include_router(reward_router)
app.include_router(wallet_router)
app.include_router(payout_router)

# Agent communication routes
app.include_router(agent_router)

# Data packaging routes
app.include_router(data_packaging_router)

# Insight processing routes (experimental)
app.include_router(insight_router)

# LLM integration routes
app.include_router(llm_router)

# Embedding and vector search routes
app.include_router(embedding_router)

# Authentication router
app.include_router(auth_router)

# Add a simple root endpoint
@app.get("/")
@limiter.limit("5/minute")
async def root(request: Request):
    """Root endpoint that redirects to the API documentation."""
    return {"message": "Welcome to Tavren API. See /docs for API documentation."}

# Include routers
app.include_router(users.router)  
app.include_router(data.router)
app.include_router(consent.router)
app.include_router(payment.router)
app.include_router(embeddings.router)
app.include_router(evaluation.router)  # Add the evaluation router
app.include_router(user_router)  # Add the user router

# For direct execution with Python
if __name__ == "__main__":
    import uvicorn
    log.info("Starting application with Uvicorn...")
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)