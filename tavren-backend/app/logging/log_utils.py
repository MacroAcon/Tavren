"""
Standardized logging utilities for consistent logging throughout the application.
"""
import logging
import traceback
import json
from typing import Any, Dict, Optional
from datetime import datetime

# Initialize the logger
log = logging.getLogger("app")

def get_logger(name: Optional[str] = None) -> logging.Logger:
    """
    Get a properly configured logger instance.
    
    Args:
        name: Optional logger name (defaults to 'app')
        
    Returns:
        A configured logger instance
    """
    logger_name = name or "app"
    return logging.getLogger(logger_name)

def log_api_request(
    endpoint: str,
    method: str,
    params: Optional[Dict[str, Any]] = None,
    user_id: Optional[str] = None
) -> None:
    """
    Log an API request with consistent formatting.
    
    Args:
        endpoint: API endpoint being called
        method: HTTP method (GET, POST, etc.)
        params: Optional request parameters
        user_id: Optional user ID making the request
    """
    logger = get_logger()
    
    log_data = {
        "timestamp": datetime.utcnow().isoformat(),
        "type": "api_request",
        "endpoint": endpoint,
        "method": method
    }
    
    if params:
        # Avoid logging sensitive information
        if "password" in params:
            params = {**params, "password": "********"}
        if "access_token" in params:
            params = {**params, "access_token": "********"}
        log_data["params"] = params
        
    if user_id:
        log_data["user_id"] = user_id
        
    try:
        logger.info(f"API Request: {json.dumps(log_data)}")
    except Exception:
        # Fall back to simple format if JSON fails
        logger.info(f"API Request: {endpoint} {method}")

def log_exception(
    e: Exception,
    context: Optional[str] = None,
    user_id: Optional[str] = None,
    include_traceback: bool = True
) -> None:
    """
    Log an exception with consistent formatting.
    
    Args:
        e: The exception to log
        context: Optional context information
        user_id: Optional user ID related to the exception
        include_traceback: Whether to include the traceback
    """
    logger = get_logger()
    
    log_data = {
        "timestamp": datetime.utcnow().isoformat(),
        "type": "exception",
        "exception_type": type(e).__name__,
        "exception_message": str(e)
    }
    
    if context:
        log_data["context"] = context
        
    if user_id:
        log_data["user_id"] = user_id
    
    if include_traceback:
        tb = traceback.format_exc()
        log_data["traceback"] = tb
        
    logger.error(f"Exception: {log_data['exception_type']}: {log_data['exception_message']}")
    
    if include_traceback:
        logger.error(f"Traceback: {tb}")

def log_event(
    event_type: str,
    message: str,
    details: Optional[Dict[str, Any]] = None,
    user_id: Optional[str] = None,
    level: str = "info"
) -> None:
    """
    Log an application event with consistent formatting.
    
    Args:
        event_type: Type of event being logged
        message: Event message
        details: Optional event details
        user_id: Optional user ID related to the event
        level: Log level (debug, info, warning, error, critical)
    """
    logger = get_logger()
    
    log_data = {
        "timestamp": datetime.utcnow().isoformat(),
        "type": "event",
        "event_type": event_type,
        "message": message
    }
    
    if details:
        log_data["details"] = details
        
    if user_id:
        log_data["user_id"] = user_id
        
    log_method = getattr(logger, level.lower(), logger.info)
    log_method(f"Event: {event_type} - {message}") 