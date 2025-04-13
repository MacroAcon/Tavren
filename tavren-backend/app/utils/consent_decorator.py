import functools
import logging
from typing import Callable, Any, Dict, Optional
from fastapi import HTTPException, status, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.utils.consent_validator import ConsentValidator, get_consent_validator

# Get logger
log = logging.getLogger("app")

def requires_consent(
    data_scope: str,
    purpose: str = "insight_generation",
    user_id_extractor: Callable = lambda request: getattr(request, "user_id", None)
):
    """
    A decorator to ensure API endpoints only process data with valid user consent.
    
    Usage example:
    ```
    @router.post("/some-endpoint")
    @requires_consent(data_scope="location", purpose="insight_generation")
    async def protected_endpoint(
        request: SomeRequest,
        db: AsyncSession = Depends(get_db),
        consent_validator: ConsentValidator = Depends(get_consent_validator)
    ):
        # This endpoint will only run if consent is valid
        pass
    ```
    
    Args:
        data_scope: The data scope required for this endpoint
        purpose: The processing purpose for this endpoint
        user_id_extractor: Function to extract user_id from request object
        
    Returns:
        A decorator function that validates consent before executing the endpoint
    """
    def decorator(endpoint_func):
        @functools.wraps(endpoint_func)
        async def wrapper(*args, **kwargs):
            # Extract dependencies
            db = kwargs.get('db')
            consent_validator = kwargs.get('consent_validator')
            
            # If deps not provided, try to get them
            if db is None or consent_validator is None:
                log.warning("DB or ConsentValidator not found in kwargs, attempting to get through dependencies")
                db = db or Depends(get_db)
                consent_validator = consent_validator or Depends(get_consent_validator)
            
            # Extract request object (typically first positional arg or in kwargs)
            request = args[0] if args else None
            if request is None:
                request_names = ['request', 'req', 'body', 'data']
                for name in request_names:
                    if name in kwargs:
                        request = kwargs[name]
                        break
            
            if request is None:
                log.error("Could not find request object for consent validation")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Internal server error: Could not validate consent"
                )
            
            # Extract user_id using the provided function
            user_id = user_id_extractor(request)
            
            if not user_id:
                log.warning("No user_id found for consent validation")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="User ID is required for this operation"
                )
            
            # Validate consent
            log.info(f"Validating consent for user {user_id}, scope '{data_scope}', purpose '{purpose}'")
            is_allowed, details = await consent_validator.is_processing_allowed(
                user_id=user_id,
                data_scope=data_scope,
                purpose=purpose
            )
            
            if not is_allowed:
                log.warning(f"Consent validation failed: {details['reason']}")
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail={
                        "error": "Consent validation failed",
                        "details": details,
                        "message": "User has not granted or has revoked consent for this operation"
                    }
                )
            
            # Consent is valid, proceed with endpoint execution
            log.info(f"Consent validated for user {user_id}, proceeding with request")
            return await endpoint_func(*args, **kwargs)
        
        return wrapper
    
    return decorator

async def with_consent_check(
    user_id: str,
    data_scope: str,
    purpose: str = "insight_generation",
    db: Optional[AsyncSession] = None,
    consent_validator: Optional[ConsentValidator] = None
) -> Dict[str, Any]:
    """
    A utility function to check consent within a function body.
    
    This is useful for imperative consent checking within a function,
    rather than using the decorator approach.
    
    Usage example:
    ```
    async def some_function(user_id, data_scope, purpose, db=None, consent_validator=None):
        # Check consent first
        consent_result = await with_consent_check(
            user_id=user_id,
            data_scope=data_scope,
            purpose=purpose,
            db=db,
            consent_validator=consent_validator
        )
        
        if not consent_result["is_allowed"]:
            # Handle consent denial
            return {"error": "Consent denied", "details": consent_result["details"]}
            
        # Continue processing if consent is valid
        ...
    ```
    
    Args:
        user_id: ID of the user whose data would be processed
        data_scope: Data category/scope being processed
        purpose: Purpose of the processing
        db: Optional database session
        consent_validator: Optional consent validator instance
        
    Returns:
        Dict containing consent validation result and details
    """
    # Create DB session and validator if not provided
    if db is None:
        db = next(get_db())
    
    if consent_validator is None:
        consent_validator = await get_consent_validator(db)
    
    # Validate consent
    is_allowed, details = await consent_validator.is_processing_allowed(
        user_id=user_id,
        data_scope=data_scope,
        purpose=purpose
    )
    
    return {
        "is_allowed": is_allowed,
        "details": details,
        "user_id": user_id,
        "data_scope": data_scope,
        "purpose": purpose
    } 