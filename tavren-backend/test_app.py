"""
Simple test app for debugging purposes.
"""
from fastapi import FastAPI
from app.database import get_db, async_engine
from app.models import Base
from app.routers.agent import router as agent_router

# Create a minimal test app
app = FastAPI(title="Tavren Test App")

# Create tables at startup
@app.on_event("startup")
async def create_tables():
    """Create database tables on application startup."""
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

# Include just the agent router
app.include_router(agent_router)

# Add a simple root endpoint
@app.get("/")
async def root():
    """Root endpoint."""
    return {"message": "Welcome to Tavren Test API"}

# For direct execution
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("test_app:app", host="0.0.0.0", port=8000, reload=True) 