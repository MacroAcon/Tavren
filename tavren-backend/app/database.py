from fastapi import Depends
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base
from typing import AsyncGenerator, Callable

# Import the settings instance
from .config import settings
from sqlalchemy import event
from sqlalchemy.schema import DDL

# Async engine setup
# Note: asyncpg requires the database URL scheme to be postgresql+asyncpg
# We might need to adjust the settings.DATABASE_URL format if it's not already correct.
# Assuming settings.DATABASE_URL is like "postgresql+asyncpg://user:password@host/db"
async_engine = create_async_engine(
    settings.DATABASE_URL,
    echo=True, # Optional: for debugging SQL statements
)

# Create pgvector extension if using PostgreSQL
if settings.DATABASE_URL.startswith('postgresql'):
    @event.listens_for(async_engine.sync_engine, "first_connect")
    def create_pgvector_extension(conn, conn_record):
        # Execute the CREATE EXTENSION command to enable pgvector
        conn.execute(DDL('CREATE EXTENSION IF NOT EXISTS vector;'))

# Async session setup
AsyncSessionLocal = sessionmaker(
    bind=async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)

Base = declarative_base()

# Use this directly - not inside a Pydantic model
async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Asynchronous database session generator.
    Provides a database session for each request and ensures it's closed afterward.
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()

# Use this function to get the dependency
def get_db() -> Callable:
    """
    Returns a dependency that provides a database session.
    Use this in FastAPI endpoints instead of referencing get_db_session directly.
    """
    return Depends(get_db_session)