"""
Utilities for formatting API responses in a consistent format.
"""
import logging
from typing import Any, Dict, Optional, Union
from fastapi import HTTPException

from app.constants.status import (
    STATUS_SUCCESS, 
    STATUS_ERROR,
    HTTP_500_INTERNAL_SERVER_ERROR,
    DETAIL_INTERNAL_SERVER_ERROR
)

log = logging.getLogger("app")

def format_success_response(
    data: Any = None, 
    message: Optional[str] = None, 
    metadata: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Format a successful API response in a standard structure.
    
    Args:
        data: The main response data
        message: Optional success message
        metadata: Optional metadata dictionary
        
    Returns:
        A standardized response dictionary
    """
    response = {
        "status": STATUS_SUCCESS,
        "data": data
    }
    
    if message:
        response["message"] = message
        
    if metadata:
        response["metadata"] = metadata
        
    return response

def format_error_response(
    message: str, 
    error_code: Optional[int] = None,
    details: Optional[Any] = None
) -> Dict[str, Any]:
    """
    Format an error response in a standard structure.
    
    Args:
        message: Error message
        error_code: Optional internal error code
        details: Optional additional error details
        
    Returns:
        A standardized error response dictionary
    """
    response = {
        "status": STATUS_ERROR,
        "message": message
    }
    
    if error_code:
        response["error_code"] = error_code
        
    if details:
        response["details"] = details
        
    return response

def handle_exception(
    e: Exception, 
    status_code: int = HTTP_500_INTERNAL_SERVER_ERROR,
    default_message: str = DETAIL_INTERNAL_SERVER_ERROR,
    log_error: bool = True
) -> None:
    """
    Handle exceptions in a consistent way throughout the API.
    
    Args:
        e: The exception to handle
        status_code: HTTP status code to return
        default_message: Default message if exception has no str representation
        log_error: Whether to log the error
        
    Raises:
        HTTPException: Always raises this with formatted details
    """
    error_message = str(e) if str(e) else default_message
    
    if log_error:
        log.error(f"Error handled: {error_message}", exc_info=True)
        
    raise HTTPException(
        status_code=status_code,
        detail=error_message
    ) 