from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
import logging
from .custom_exceptions import (
    TavrenBaseException,
    ResourceNotFoundException,
    InsufficientBalanceError,
    PayoutProcessingError,
    BelowMinimumThresholdError,
    InvalidStatusTransitionError
)

# Get logger
log = logging.getLogger("app")

def register_exception_handlers(app: FastAPI) -> None:
    """
    Register all custom exception handlers with the FastAPI application.
    
    Args:
        app: The FastAPI application instance
    """
    
    @app.exception_handler(TavrenBaseException)
    async def tavren_exception_handler(request: Request, exc: TavrenBaseException):
        """
        Handler for all Tavren-specific exceptions.
        Ensures consistent error response format and proper logging.
        """
        # Log the exception with appropriate level based on status code
        if exc.status_code >= 500:
            log.error(f"Server error: {exc.detail}", exc_info=True)
        elif exc.status_code >= 400:
            log.warning(f"Client error: {exc.detail}")
        else:
            log.info(f"Other exception: {exc.detail}")
            
        # Return a structured JSON response
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": {
                    "code": exc.error_code,
                    "message": exc.detail,
                    "status_code": exc.status_code,
                }
            }
        )
    
    # Register specific exception handlers for more detailed logging/handling
    
    @app.exception_handler(ResourceNotFoundException)
    async def resource_not_found_handler(request: Request, exc: ResourceNotFoundException):
        log.warning(f"Resource not found: {exc.detail}")
        return await tavren_exception_handler(request, exc)
    
    @app.exception_handler(InsufficientBalanceError)
    async def insufficient_balance_handler(request: Request, exc: InsufficientBalanceError):
        log.warning(f"Insufficient balance: {exc.detail}")
        return await tavren_exception_handler(request, exc)
    
    @app.exception_handler(PayoutProcessingError)
    async def payout_processing_error_handler(request: Request, exc: PayoutProcessingError):
        log.error(f"Payout processing error: {exc.detail}", exc_info=True)
        return await tavren_exception_handler(request, exc)
    
    @app.exception_handler(BelowMinimumThresholdError)
    async def below_minimum_threshold_handler(request: Request, exc: BelowMinimumThresholdError):
        log.warning(f"Below minimum threshold: {exc.detail}")
        return await tavren_exception_handler(request, exc)
    
    @app.exception_handler(InvalidStatusTransitionError)
    async def invalid_status_transition_handler(request: Request, exc: InvalidStatusTransitionError):
        log.warning(f"Invalid status transition: {exc.detail}")
        return await tavren_exception_handler(request, exc)
    
    # Global exception handler for unhandled exceptions
    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        log.error(f"Unhandled exception: {str(exc)}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={
                "error": {
                    "code": "INTERNAL_SERVER_ERROR",
                    "message": "An unexpected error occurred",
                    "status_code": 500,
                }
            }
        ) 