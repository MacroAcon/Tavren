"""
Rate limiting utility for API endpoints.
Uses Redis to track and limit request rates.
"""

import time
import logging
from typing import Optional, Tuple
from fastapi import Request, HTTPException, Depends
import redis.asyncio as redis

from app.config import settings
from app.auth import get_current_active_user

# Set up logging
log = logging.getLogger("app")

# Configure Redis connection for rate limiting
try:
    # Use the same Redis instance as the cache if available
    redis_url = getattr(settings, "REDIS_URL", "redis://localhost:6379/0")
    redis_client = redis.from_url(redis_url, encoding="utf-8", decode_responses=True)
except Exception as e:
    log.error(f"Error initializing Redis for rate limiting: {e}")
    redis_client = None


class RateLimiter:
    """
    Rate limiter for API endpoints using Redis.
    """
    def __init__(self, times: int, seconds: int, prefix: str = "rate_limit"):
        """
        Initialize the rate limiter.
        
        Args:
            times: Number of requests allowed in the time period
            seconds: Time period in seconds
            prefix: Redis key prefix for rate limit keys
        """
        self.times = times
        self.seconds = seconds
        self.prefix = prefix
        
    async def _get_rate_limit_key(self, request: Request, user_id: Optional[int] = None) -> str:
        """
        Get the rate limit key for a request.
        
        Args:
            request: FastAPI request object
            user_id: User ID, if authenticated
            
        Returns:
            Redis key for rate limiting
        """
        # If we have a user ID, use that for the key
        if user_id:
            return f"{self.prefix}:{user_id}:{request.url.path}"
        
        # Otherwise use client IP (with fallbacks)
        client_ip = request.client.host if request.client else "unknown"
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            client_ip = forwarded_for.split(",")[0].strip()
            
        return f"{self.prefix}:{client_ip}:{request.url.path}"
    
    async def _increment_and_check(self, key: str) -> Tuple[bool, int, int]:
        """
        Increment the request count and check if rate limit is exceeded.
        
        Args:
            key: Redis key for rate limiting
            
        Returns:
            Tuple of (is_allowed, current_count, ttl)
        """
        if not redis_client:
            # If Redis is not available, allow the request (fail open)
            return True, 0, 0
        
        try:
            pipeline = redis_client.pipeline()
            
            # Get current count and TTL
            await pipeline.get(key)
            await pipeline.ttl(key)
            result = await pipeline.execute()
            
            current = int(result[0]) if result[0] else 0
            ttl = max(result[1], 0) if result[1] else 0
            
            # If key doesn't exist or TTL is negative, reset
            if current == 0 or ttl <= 0:
                await redis_client.set(key, 1, ex=self.seconds)
                return True, 1, self.seconds
            
            # Increment and check if over limit
            if current < self.times:
                await redis_client.incr(key)
                return True, current + 1, ttl
            else:
                return False, current, ttl
                
        except Exception as e:
            log.error(f"Error checking rate limit: {e}")
            # Fail open - if we can't check the rate limit, allow the request
            return True, 0, 0
            
    async def __call__(self, request: Request, user=Depends(get_current_active_user)) -> None:
        """
        Check if a request is allowed based on rate limits.
        
        Args:
            request: FastAPI request object
            user: Authenticated user object
            
        Raises:
            HTTPException: If rate limit is exceeded
        """
        user_id = user.get("id") if user else None
        key = await self._get_rate_limit_key(request, user_id)
        
        allowed, current, ttl = await self._increment_and_check(key)
        
        # Add rate limit headers to the response
        request.state.rate_limit_remaining = self.times - current
        request.state.rate_limit_reset = ttl
        
        if not allowed:
            log.warning(f"Rate limit exceeded for key: {key}")
            raise HTTPException(
                status_code=429,
                detail=f"Rate limit exceeded. Try again in {ttl} seconds."
            )

# Define different rate limits for various endpoint types
# More generous limits for simple reads, stricter for complex operations
default_rate_limit = RateLimiter(times=60, seconds=60, prefix="default")
search_rate_limit = RateLimiter(times=30, seconds=60, prefix="search")
complex_search_rate_limit = RateLimiter(times=10, seconds=60, prefix="complex_search")
embedding_creation_rate_limit = RateLimiter(times=10, seconds=60, prefix="embedding_creation") 