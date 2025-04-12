# tavren-backend/tests/conftest.py
import pytest
import pytest_asyncio
from httpx import AsyncClient
from typing import AsyncGenerator, Generator
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
import asyncio

from app.main import app # Import your FastAPI app
from app.database import Base, get_db # Import Base and async get_db
from app.config import settings

# Use a separate test database if possible
TEST_DATABASE_URL = settings.DATABASE_URL.replace("tavren_dev.db", "tavren_test.db")
# Ensure it's asyncpg compatible if needed
if "sqlite" in TEST_DATABASE_URL:
     # In-memory SQLite for async tests
     TEST_DATABASE_URL = "sqlite+aiosqlite:///./test_db.sqlite" # Use file for persistence across fixtures if needed
elif "postgresql" in TEST_DATABASE_URL and "+asyncpg" not in TEST_DATABASE_URL:
     TEST_DATABASE_URL = TEST_DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://")


# Create async engine and session for testing
async_engine_test = create_async_engine(TEST_DATABASE_URL, echo=False)
AsyncSessionLocalTest = sessionmaker(
    bind=async_engine_test,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)

# Async Override for get_db dependency
async def override_get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocalTest() as session:
        yield session

# Apply the override to the app
app.dependency_overrides[get_db] = override_get_db

@pytest_asyncio.fixture(scope="session", autouse=True)
async def setup_database():
    """Creates database tables before tests and drops them after."""
    async with async_engine_test.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with async_engine_test.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

@pytest_asyncio.fixture(scope="function")
async def session() -> AsyncGenerator[AsyncSession, None]:
    """Provides an async database session fixture for tests."""
    async with AsyncSessionLocalTest() as db_session:
        yield db_session
        # Optional: Clean up specific data added during a test if needed,
        # but setup_database usually handles dropping tables.
        await db_session.rollback() # Ensure clean state if test failed mid-transaction

@pytest_asyncio.fixture(scope="function")
async def async_client(session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """Provides an async test client."""
    async with AsyncClient(app=app, base_url="http://test") as client:
         # You might need to manually inject the session override here
         # if the app instance doesn't pick it up correctly in all contexts
         app.dependency_overrides[get_db] = lambda: session
         yield client
         # Reset overrides after test
         app.dependency_overrides.clear()


# Setup asyncio event loop policy for Windows if needed
# (Sometimes necessary for pytest-asyncio on Windows)
import sys
if sys.platform == "win32":
    @pytest.fixture(scope="session")
    def event_loop_policy(request):
        return asyncio.WindowsSelectorEventLoopPolicy()
