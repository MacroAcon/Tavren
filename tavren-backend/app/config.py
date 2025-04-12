import pathlib
import os
import logging.config
import secrets
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional

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
    # IMPORTANT: JWT_SECRET_KEY MUST be set in environment variables for production!
    # Example to generate: openssl rand -hex 32
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30 # Token expiry time
    
    # Admin API key for protected operations like user registration
    # Generate with: openssl rand -hex 24
    ADMIN_API_KEY: str

    # Data Packaging settings
    ENCRYPT_DATA_PACKAGES: bool = True
    DATA_ENCRYPTION_KEY: str  # Set in environment variables
    DATA_PACKAGE_TOKEN_EXPIRY_HOURS: int = 24
    DATA_PACKAGE_STORAGE_PATH: pathlib.Path = BASE_DIR / "data_packages"
    MAX_PACKAGE_SIZE_MB: int = 50
    AUDIT_TRAIL_ENABLED: bool = True
    
    # Trust Tier thresholds
    LOW_TRUST_THRESHOLD: float = 0.3  # Below this is low trust
    HIGH_TRUST_THRESHOLD: float = 0.7  # Above this is high trust
    
    # Nvidia LLM API settings
    NVIDIA_API_BASE_URL: str = "https://api.nvidia.com/v1"
    NVIDIA_API_KEY: str = ""  # Must be set in environment variables
    DEFAULT_LLM_MODEL: str = "llama3-70b-instruct"  # Default model for completions
    DEFAULT_EMBEDDING_MODEL: str = "nvidia/embedding-model"
    LLM_MODEL_TEMPERATURE: float = 0.7  # Default temperature setting
    EMBEDDING_DIMENSION: int = 1536  # Default dimension for embeddings
    VECTOR_SEARCH_TOP_K: int = 5  # Default number of results for vector search

    # Cache settings
    REDIS_URL: Optional[str] = None  # Redis connection URL
    CACHE_TTL_SECONDS: int = 3600  # Default TTL for cached items (1 hour)
    CACHE_MAX_SIZE: int = 1000  # Maximum number of items in memory cache
    EMBEDDING_CACHE_TTL: int = 86400  # TTL for embeddings (24 hours)
    SEARCH_CACHE_TTL: int = 1800  # TTL for search results (30 minutes)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Secure defaults only for development - must be properly set in production
        if not self.SECRET_KEY:
            # Check if we're in production by looking for common environment variables
            is_production = os.environ.get('ENVIRONMENT') == 'production' or os.environ.get('ENV') == 'production'
            if is_production:
                raise ValueError("JWT_SECRET_KEY environment variable is required in production mode")
            # In development, generate a random key but log a warning
            self.SECRET_KEY = secrets.token_hex(32)
            import logging
            logging.warning(
                "WARNING: Using a randomly generated SECRET_KEY. "
                "This is only acceptable for development environments. "
                "Set JWT_SECRET_KEY environment variable for production."
            )
            
        if not self.DATA_ENCRYPTION_KEY:
            is_production = os.environ.get('ENVIRONMENT') == 'production' or os.environ.get('ENV') == 'production'
            if is_production:
                raise ValueError("DATA_ENCRYPTION_KEY environment variable is required in production mode")
            # In development, generate a random key but log a warning
            self.DATA_ENCRYPTION_KEY = secrets.token_hex(16)  # 128 bits
            import logging
            logging.warning(
                "WARNING: Using a randomly generated DATA_ENCRYPTION_KEY. "
                "This is only acceptable for development environments. "
                "Set DATA_ENCRYPTION_KEY environment variable for production."
            )
            
        if not self.ADMIN_API_KEY:
            is_production = os.environ.get('ENVIRONMENT') == 'production' or os.environ.get('ENV') == 'production'
            if is_production:
                raise ValueError("ADMIN_API_KEY environment variable is required in production mode")
            # In development, generate a random key but log a warning
            self.ADMIN_API_KEY = secrets.token_hex(24)  # 192 bits
            import logging
            logging.warning(
                "WARNING: Using a randomly generated ADMIN_API_KEY. "
                "This is only acceptable for development environments. "
                "Set ADMIN_API_KEY environment variable for production to protect admin endpoints."
            )
            
        if not self.NVIDIA_API_KEY:
            is_production = os.environ.get('ENVIRONMENT') == 'production' or os.environ.get('ENV') == 'production'
            if is_production:
                raise ValueError("NVIDIA_API_KEY environment variable is required in production mode")
            # In development, generate a placeholder but log a warning
            self.NVIDIA_API_KEY = "nvidia_key_placeholder_for_development"
            import logging
            logging.warning(
                "WARNING: Using a placeholder NVIDIA_API_KEY. "
                "LLM functionality will not work until a valid key is provided. "
                "Set NVIDIA_API_KEY environment variable before using LLM features."
            )

    model_config = SettingsConfigDict(
        env_file=PROJECT_ROOT / '.env',
        extra='ignore',
        env_prefix="",
        env_file_encoding="utf-8"
    )

# Create a single instance of the settings to be imported elsewhere
settings = Settings()

def get_settings():
    """Function to get settings - useful for dependency injection."""
    return settings

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