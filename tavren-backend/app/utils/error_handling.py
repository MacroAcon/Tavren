"""
Error handling utilities for Tavren API.
"""

import logging
import re
import traceback
from typing import Dict, Any, Optional
import hashlib

# Set up logging
log = logging.getLogger("app")

def sanitize_error_message(error: Exception, include_details: bool = False) -> Dict[str, Any]:
    """
    Sanitize error messages to avoid leaking sensitive information.
    
    Args:
        error: The exception to sanitize
        include_details: Whether to include sanitized details (for dev environments)
        
    Returns:
        Dictionary with sanitized error information
    """
    # Generate an error ID to help with debugging
    error_hash = hashlib.md5(str(error).encode()).hexdigest()[:8]
    error_id = f"ERR-{error_hash}"
    
    # Get the error message
    error_message = str(error)
    
    # Log the full error for debugging
    log.error(f"Error {error_id}: {error_message}", exc_info=True)
    
    # Always sanitize certain patterns that might contain sensitive information
    # This includes SQL statements, file paths, URLs with credentials, and more
    sensitive_patterns = [
        # SQL statements
        (r'(SELECT|INSERT|UPDATE|DELETE|CREATE|ALTER|DROP).*', 'SQL statement'),
        # File paths
        (r'(/[\w/.]+)', '[filepath]'),
        # URLs with credentials
        (r'(https?://[^:]+:[^@]+@)', 'https://[credentials-redacted]@'),
        # API keys, tokens
        (r'(api[_-]?key|token|secret|password|credential)s?\s*[=:]\s*[\'"]([\w-]+)[\'"]', r'\1=***'),
        # Connection strings
        (r'(connection string:).*', r'\1 [redacted]')
    ]
    
    # Apply sanitization patterns
    sanitized_message = error_message
    for pattern, replacement in sensitive_patterns:
        sanitized_message = re.sub(pattern, replacement, sanitized_message, flags=re.IGNORECASE)
    
    # Create the response
    error_response = {
        "error_id": error_id,
        "message": "An error occurred while processing your request"
    }
    
    # For development environments, include more details
    if include_details:
        error_response["details"] = sanitized_message
        error_response["type"] = error.__class__.__name__
    
    return error_response

def get_safe_error_message(error: Exception, is_dev_env: bool = False) -> str:
    """
    Get a safe error message string for API responses.
    
    Args:
        error: The exception to process
        is_dev_env: Whether this is a development environment
        
    Returns:
        Safe error message string
    """
    error_info = sanitize_error_message(error, include_details=is_dev_env)
    
    if is_dev_env and "details" in error_info:
        return f"{error_info['error_id']}: {error_info['details']}"
    else:
        return f"{error_info['error_id']}: {error_info['message']}" 