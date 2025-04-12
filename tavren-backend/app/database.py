import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

load_dotenv()

# Default to SQLite for local dev, use DATABASE_URL env var if set
# The path './tavren_dev.db' assumes the app runs from 'tavren-backend/'
SQLALCHEMY_DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./tavren_dev.db")

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    # Add check_same_thread only if using SQLite
    connect_args={"check_same_thread": False} if SQLALCHEMY_DATABASE_URL.startswith("sqlite") else {}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()