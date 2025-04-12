import pathlib
import os
from pydantic_settings import BaseSettings, SettingsConfigDict

# This ensures correct .env loading regardless of where the app is run
BASE_DIR = pathlib.Path(__file__).resolve().parent.parent
# Define the project root directory (one level up from BASE_DIR)
PROJECT_ROOT = BASE_DIR.parent

class Settings(BaseSettings):
    # Load .env file relative to the project root directory (Tavren/)
    model_config = SettingsConfigDict(env_file=PROJECT_ROOT / '.env', extra='ignore')

    # Database URL: default to local SQLite if not set in .env
    # Make sure the default uses an async driver if .env isn't found
    DATABASE_URL: str = f"sqlite+aiosqlite:///{BASE_DIR / 'app' / 'tavren_dev.db'}"

    # Application settings
    MINIMUM_PAYOUT_THRESHOLD: float = 5.00
    LOG_LEVEL: str = "INFO"

    # Path settings (derived, not from env)
    STATIC_DIR: pathlib.Path = BASE_DIR / "app" / "static"

    # Security settings
    # IMPORTANT: Generate a strong secret key in production!
    # Example: openssl rand -hex 32
    SECRET_KEY: str = "09d25e094faa6ca2556c818166b7a9563b93f7099f6f0f4caa6cf63b88e8d3e7"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30 # Token expiry time

# Create a single instance of the settings to be imported elsewhere
settings = Settings()

# --- Logging Configuration (Example) ---
# You can expand this further
import logging

LOGGING_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "default": {
            "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "default",
            "stream": "ext://sys.stdout",
        },
    },
    "loggers": {
        "uvicorn.error": {"level": "INFO"},
        "uvicorn.access": {"level": "WARNING", "handlers": ["console"]}, # Quieter access logs
        "app": { # Logger for our application
            "handlers": ["console"],
            "level": settings.LOG_LEVEL,
            "propagate": False,
        },
    },
    "root": {
        "handlers": ["console"],
        "level": settings.LOG_LEVEL,
    },
}

def setup_logging():
    logging.config.dictConfig(LOGGING_CONFIG) 