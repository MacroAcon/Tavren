"""
Middleware for the Tavren application.
"""

from fastapi import Request, Response
import logging
import time
from starlette.middleware.base import BaseHTTPMiddleware

# Set up logging
log = logging.getLogger("app")

class RateLimitHeaderMiddleware(BaseHTTPMiddleware):
    """
    Middleware to add rate limit headers to responses.
    """
    async def dispatch(self, request: Request, call_next):
        """
        Process request/response and add rate limit headers if they exist.
        
        Args:
            request: FastAPI request object
            call_next: Next middleware or endpoint handler
            
        Returns:
            Response with added rate limit headers if applicable
        """
        # Initialize rate limit info in request state
        request.state.rate_limit_remaining = None
        request.state.rate_limit_reset = None
        
        # Process the request through the route handler
        response = await call_next(request)
        
        # Add rate limit headers if they were set during processing
        if hasattr(request.state, "rate_limit_remaining") and request.state.rate_limit_remaining is not None:
            response.headers["X-RateLimit-Remaining"] = str(request.state.rate_limit_remaining)
            
        if hasattr(request.state, "rate_limit_reset") and request.state.rate_limit_reset is not None:
            response.headers["X-RateLimit-Reset"] = str(request.state.rate_limit_reset)
        
        return response

class RequestTimingMiddleware(BaseHTTPMiddleware):
    """
    Middleware to add timing information to responses.
    """
    async def dispatch(self, request: Request, call_next):
        """
        Process request/response and measure processing time.
        
        Args:
            request: FastAPI request object
            call_next: Next middleware or endpoint handler
            
        Returns:
            Response with added timing header
        """
        start_time = time.time()
        
        # Process the request
        response = await call_next(request)
        
        # Calculate and add processing time
        process_time = time.time() - start_time
        response.headers["X-Process-Time"] = f"{process_time:.4f} sec"
        
        # Log timing for significant operations
        if process_time > 1.0:  # Log if operation took more than a second
            log.info(f"Slow operation: {request.method} {request.url.path} took {process_time:.4f} sec")
        
        return response 