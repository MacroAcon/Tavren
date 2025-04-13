"""
Centralized error handling utilities.
"""
import logging
from typing import Callable, Dict, Any, Type
from fastapi import Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from sqlalchemy.exc import SQLAlchemyError

from app.exceptions.custom_exceptions import (
    ResourceNotFoundException,
    InsufficientBalanceError,
    InvalidStatusTransitionError,
    BelowMinimumThresholdError,
    PayoutProcessingError
)
from app.constants.status import (
    HTTP_404_NOT_FOUND,
    HTTP_400_BAD_REQUEST,
    HTTP_422_UNPROCESSABLE_ENTITY,
    HTTP_500_INTERNAL_SERVER_ERROR,
    STATUS_ERROR
)

log = logging.getLogger("app")

# Map exceptions to status codes and custom messages
exception_handlers: Dict[Type[Exception], Dict[str, Any]] = {
    ResourceNotFoundException: {
        "status_code": HTTP_404_NOT_FOUND,
        "message": "The requested resource was not found."
    },
    InsufficientBalanceError: {
        "status_code": HTTP_400_BAD_REQUEST,
        "message": "Insufficient balance for the requested operation."
    },
    BelowMinimumThresholdError: {
        "status_code": HTTP_400_BAD_REQUEST,
        "message": "Amount is below the minimum threshold for this operation."
    },
    InvalidStatusTransitionError: {
        "status_code": HTTP_400_BAD_REQUEST,
        "message": "Invalid status transition."
    },
    PayoutProcessingError: {
        "status_code": HTTP_500_INTERNAL_SERVER_ERROR,
        "message": "Error processing payment."
    },
    SQLAlchemyError: {
        "status_code": HTTP_500_INTERNAL_SERVER_ERROR,
        "message": "Database error occurred."
    }
}

async def handle_custom_exception(request: Request, exc: Exception) -> JSONResponse:
    """
    Handle custom exceptions and return appropriate response.
    
    Args:
        request: The request that triggered the exception
        exc: The exception instance
        
    Returns:
        JSONResponse with appropriate status code and error details
    """
    exception_class = exc.__class__
    exception_info = exception_handlers.get(
        exception_class, 
        {"status_code": HTTP_500_INTERNAL_SERVER_ERROR, "message": "Internal server error"}
    )
    
    status_code = exception_info["status_code"]
    default_message = exception_info["message"]
    
    # Use exception message if available, otherwise use default
    message = str(exc) if str(exc) else default_message
    
    log.error(f"Exception handled: {exception_class.__name__}: {message}")
    
    return JSONResponse(
        status_code=status_code,
        content={
            "status": STATUS_ERROR,
            "message": message,
            "error_type": exception_class.__name__
        }
    )

async def handle_validation_exception(request: Request, exc: RequestValidationError) -> JSONResponse:
    """
    Handle validation exceptions from pydantic models.
    
    Args:
        request: The request that triggered the exception
        exc: The validation exception
        
    Returns:
        JSONResponse with validation error details
    """
    log.warning(f"Validation error: {exc.errors()}")
    
    return JSONResponse(
        status_code=HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "status": STATUS_ERROR,
            "message": "Validation error",
            "details": exc.errors()
        }
    )

def get_exception_handlers() -> Dict[Type[Exception], Callable]:
    """
    Get all exception handlers for FastAPI app initialization.
    
    Returns:
        Dictionary mapping exception types to handler functions
    """
    handlers = {}
    
    # Add all custom exception handlers
    for exception_class in exception_handlers.keys():
        handlers[exception_class] = handle_custom_exception
    
    # Add validation exception handler
    handlers[RequestValidationError] = handle_validation_exception
    
    return handlers 