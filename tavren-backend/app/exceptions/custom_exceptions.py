from fastapi import HTTPException, status
from typing import Optional, Dict, Any


class TavrenBaseException(HTTPException):
    """Base exception class for Tavren-specific exceptions."""
    
    def __init__(
        self,
        status_code: int,
        detail: str,
        error_code: str = None,
        headers: Optional[Dict[str, Any]] = None
    ):
        super().__init__(status_code=status_code, detail=detail, headers=headers)
        self.error_code = error_code


class ResourceNotFoundException(TavrenBaseException):
    """Exception raised when a requested resource is not found."""
    
    def __init__(self, detail: str = "Resource not found", error_code: str = "RESOURCE_NOT_FOUND"):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=detail,
            error_code=error_code
        )


class InsufficientBalanceError(TavrenBaseException):
    """Exception raised when a user has insufficient balance for a requested operation."""
    
    def __init__(self, 
                detail: str = "Insufficient balance for the requested operation", 
                error_code: str = "INSUFFICIENT_BALANCE"):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=detail,
            error_code=error_code
        )


class PayoutProcessingError(TavrenBaseException):
    """Exception raised when there's an error processing a payout request."""
    
    def __init__(self, 
                detail: str = "Error processing payout request", 
                error_code: str = "PAYOUT_PROCESSING_ERROR"):
        super().__init__(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=detail,
            error_code=error_code
        )


class BelowMinimumThresholdError(TavrenBaseException):
    """Exception raised when a requested payout is below the minimum threshold."""
    
    def __init__(self, 
                detail: str = "Requested amount is below the minimum threshold", 
                error_code: str = "BELOW_MINIMUM_THRESHOLD"):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=detail,
            error_code=error_code
        )


class InvalidStatusTransitionError(TavrenBaseException):
    """Exception raised when attempting an invalid status transition for a payout."""
    
    def __init__(self, 
                detail: str = "Invalid status transition", 
                error_code: str = "INVALID_STATUS_TRANSITION"):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=detail,
            error_code=error_code
        ) 