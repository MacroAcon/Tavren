from fastapi import APIRouter, HTTPException
from fastapi.responses import HTMLResponse, FileResponse
import logging
import pathlib
from app.config import settings

# Get logger
log = logging.getLogger("app")

# Create router
static_router = APIRouter(tags=["static"])

# Endpoint to serve the dashboard HTML
@static_router.get("/dashboard", response_class=FileResponse)
async def get_dashboard():
    """Serve the main dashboard HTML page."""
    dashboard_path = settings.STATIC_DIR / "index.html"
    log.debug(f"Serving dashboard page from {dashboard_path}")
    
    if not dashboard_path.is_file():
        log.error(f"Dashboard file not found at {dashboard_path}")
        return HTMLResponse(content="Dashboard file not found.", status_code=404)
    
    return FileResponse(dashboard_path)

# Endpoint to serve the buyer dashboard HTML
@static_router.get("/buyer-dashboard", response_class=FileResponse)
async def get_buyer_dashboard():
    """Serve the buyer dashboard HTML page."""
    dashboard_path = settings.STATIC_DIR / "buyer.html"
    log.debug(f"Serving buyer dashboard page from {dashboard_path}")
    
    if not dashboard_path.is_file():
        log.error(f"Buyer dashboard file not found at {dashboard_path}")
        return HTMLResponse(content="Buyer dashboard file not found.", status_code=404)
    
    return FileResponse(dashboard_path)

# Endpoint to serve the offer feed HTML
@static_router.get("/offer-feed", response_class=FileResponse)
async def get_offer_feed_page():
    """Serve the offer feed HTML page."""
    dashboard_path = settings.STATIC_DIR / "offer.html"
    log.debug(f"Serving offer feed page from {dashboard_path}")
    
    if not dashboard_path.is_file():
        log.error(f"Offer feed file not found at {dashboard_path}")
        return HTMLResponse(content="Offer feed file not found.", status_code=404)
    
    return FileResponse(dashboard_path)

# Endpoint to serve the suggestion success dashboard HTML
@static_router.get("/suggestion-dashboard", response_class=FileResponse)
async def get_suggestion_dashboard_page():
    """Serve the suggestion dashboard HTML page."""
    dashboard_path = settings.STATIC_DIR / "suggestion.html"
    log.debug(f"Serving suggestion dashboard page from {dashboard_path}")
    
    if not dashboard_path.is_file():
        log.error(f"Suggestion dashboard file not found at {dashboard_path}")
        return HTMLResponse(content="Suggestion dashboard file not found.", status_code=404)
    
    return FileResponse(dashboard_path)

# Endpoint to serve the wallet page HTML
@static_router.get("/wallet", response_class=FileResponse)
async def get_wallet_page():
    """Serve the wallet HTML page."""
    dashboard_path = settings.STATIC_DIR / "wallet.html"
    log.debug(f"Serving wallet page from {dashboard_path}")
    
    if not dashboard_path.is_file():
        log.error(f"Wallet page file not found at {dashboard_path}")
        return HTMLResponse(content="Wallet page file not found.", status_code=404)
    
    return FileResponse(dashboard_path) 