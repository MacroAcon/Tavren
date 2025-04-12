from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base
# Import the settings instance
from .config import settings

# Async engine setup
# Note: asyncpg requires the database URL scheme to be postgresql+asyncpg
# We might need to adjust the settings.DATABASE_URL format if it's not already correct.
# Assuming settings.DATABASE_URL is like "postgresql+asyncpg://user:password@host/db"
async_engine = create_async_engine(
    settings.DATABASE_URL,
    echo=True, # Optional: for debugging SQL statements
)

# Async session setup
AsyncSessionLocal = sessionmaker(
    bind=async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)

Base = declarative_base()

async def get_db() -> AsyncSession:
    """
    Asynchronous database dependency that creates a new SQLAlchemy AsyncSession
    for each request and ensures it is closed when the request is complete.
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close() # Ensure session is closed asynchronously