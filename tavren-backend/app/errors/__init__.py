"""
Errors module for Tavren backend.
Provides centralized error handling throughout the application.
"""

# Make exception handlers available from the errors package
from app.errors.handlers import (
    handle_custom_exception,
    handle_validation_exception,
    get_exception_handlers
) 