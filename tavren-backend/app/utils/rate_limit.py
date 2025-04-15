"""
Rate limiting utility for API endpoints.
Uses Redis to track and limit request rates.
"""

import time
import logging
from typing import Optional, Tuple, Dict, Any
from fastapi import Request, HTTPException, Depends, Depends
import redis.asyncio as redis
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db

from app.config import settings
from app.auth import get_current_active_user

# Set up logging
log = logging.getLogger("tavren.rate_limit")

# Configure Redis connection for rate limiting
redis_client = None
try:
    # Get Redis URL from settings with a safe default for development
    redis_url = getattr(settings, "REDIS_URL", "redis://localhost:6379/0")
    
    # Validate Redis URL scheme
    if not any(redis_url.startswith(scheme) for scheme in ["redis://", "rediss://", "unix://"]):
        log.warning("Redis disabled - invalid REDIS_URL scheme. Must be one of: redis://, rediss://, unix://")
    else:
        redis_client = redis.from_url(redis_url, encoding="utf-8", decode_responses=True)
        log.info("Redis rate limiter initialized successfully")
except Exception as e:
    log.warning(f"Redis disabled - failed to initialize: {str(e)}")
    redis_client = None

def get_redis_status() -> str:
    """
    Get the current status of Redis connection.
    
    Returns:
        str: "connected" if Redis is available, "disabled (fallback)" otherwise
    """
    return "connected" if redis_client else "disabled (fallback)"

class RateLimiter:
    """
    Rate limiter for API endpoints using Redis or memory-based fallback.
    """
    def __init__(self, times: int = 10, seconds: int = 60, prefix: str = "rate_limit"):
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
        # In-memory store fallback if Redis is not available
        self._memory_store: Dict[str, Dict[str, Any]] = {}
        
    async def _get_rate_limit_key(self, request: Request, user_id: Optional[str] = None) -> str:
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
        if redis_client:
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
                log.error(f"Error checking rate limit with Redis: {e}")
                # Fall back to in-memory store
                return await self._memory_increment_and_check(key)
        else:
            # Redis not available, use in-memory store
            return await self._memory_increment_and_check(key)
    
    async def _memory_increment_and_check(self, key: str) -> Tuple[bool, int, int]:
        """
        In-memory fallback for rate limiting when Redis is not available.
        
        Args:
            key: Rate limit key
            
        Returns:
            Tuple of (is_allowed, current_count, ttl)
        """
        now = time.time()
        
        if key in self._memory_store:
            data = self._memory_store[key]
            # Check if window has expired
            if now > data["expires_at"]:
                # Reset
                self._memory_store[key] = {
                    "count": 1,
                    "expires_at": now + self.seconds
                }
                return True, 1, self.seconds
            else:
                # Window still active
                if data["count"] < self.times:
                    data["count"] += 1
                    return True, data["count"], int(data["expires_at"] - now)
                else:
                    return False, data["count"], int(data["expires_at"] - now)
        else:
            # New key
            self._memory_store[key] = {
                "count": 1,
                "expires_at": now + self.seconds
            }
            return True, 1, self.seconds
    
    async def __call__(self, request: Request, user_id: Optional[str] = None) -> None:
        """
        Check if a request is allowed based on rate limits.
        
        Args:
            request: FastAPI request object
            user_id: User ID for authenticated users
            
        Raises:
            HTTPException: If rate limit is exceeded
        """
        key = await self._get_rate_limit_key(request, user_id)
        
        allowed, current, ttl = await self._increment_and_check(key)
        
        # Add rate limit headers to the response
        request.state.rate_limit_remaining = self.times - current
        request.state.rate_limit_reset = ttl
        
        if not allowed:
            log.warning(f"Rate limit exceeded for key: {key}")
            raise HTTPException(
                status_code=429,
                detail=f"Rate limit exceeded. Try again in {ttl} seconds.",
                headers={"Retry-After": str(ttl)}
            )
    
    # New methods for DSR rate limiting
    
    async def check_rate_limit(self, key: str, limit: int = 1, period: int = 86400) -> bool:
        """
        Check if a specific key is rate limited.
        
        Args:
            key: Rate limit key (e.g., "dsr:export:user123")
            limit: Number of allowed requests in the period
            period: Time period in seconds
            
        Returns:
            Boolean indicating if the operation is allowed
        """
        redis_key = f"{self.prefix}:{key}"
        
        if redis_client:
            try:
                # Get current count and TTL from Redis
                pipeline = redis_client.pipeline()
                await pipeline.get(redis_key)
                await pipeline.ttl(redis_key)
                result = await pipeline.execute()
                
                current = int(result[0]) if result[0] else 0
                
                # If we're at or over the limit, deny
                if current >= limit:
                    return False
                
                # Otherwise, allow (but don't increment yet)
                return True
                
            except Exception as e:
                log.error(f"Error checking DSR rate limit with Redis: {e}")
                # Fall back to in-memory check
                return self._memory_check_limit(key, limit)
        else:
            # Redis not available, use in-memory check
            return self._memory_check_limit(key, limit)
    
    def _memory_check_limit(self, key: str, limit: int) -> bool:
        """
        In-memory check if a key is rate limited.
        
        Args:
            key: Rate limit key
            limit: Request limit
            
        Returns:
            Boolean indicating if the operation is allowed
        """
        redis_key = f"{self.prefix}:{key}"
        
        if redis_key in self._memory_store:
            data = self._memory_store[redis_key]
            # Check if window is still active and we're at/over limit
            now = time.time()
            if now <= data["expires_at"] and data["count"] >= limit:
                return False
            
        # Either not in store, window expired, or under limit
        return True
    
    async def update_rate_limit(self, key: str, period: int = 86400) -> None:
        """
        Update the rate limit for a key after a successful operation.
        Used primarily for DSR requests.
        
        Args:
            key: Rate limit key (e.g., "dsr:export:user123")
            period: Time period in seconds
        """
        redis_key = f"{self.prefix}:{key}"
        
        if redis_client:
            try:
                # Check if key exists
                exists = await redis_client.exists(redis_key)
                
                if exists:
                    # Increment existing key
                    await redis_client.incr(redis_key)
                else:
                    # Create new key with expiry
                    await redis_client.set(redis_key, 1, ex=period)
                    
            except Exception as e:
                log.error(f"Error updating DSR rate limit with Redis: {e}")
                # Fall back to in-memory update
                self._memory_update_limit(key, period)
        else:
            # Redis not available, use in-memory update
            self._memory_update_limit(key, period)
    
    def _memory_update_limit(self, key: str, period: int) -> None:
        """
        In-memory update of rate limit for a key.
        
        Args:
            key: Rate limit key
            period: Time period in seconds
        """
        redis_key = f"{self.prefix}:{key}"
        now = time.time()
        
        if redis_key in self._memory_store:
            data = self._memory_store[redis_key]
            # Increment if window is still active
            if now <= data["expires_at"]:
                data["count"] += 1
            else:
                # Window expired, reset
                self._memory_store[redis_key] = {
                    "count": 1,
                    "expires_at": now + period
                }
        else:
            # New key
            self._memory_store[redis_key] = {
                "count": 1,
                "expires_at": now + period
            }
    
    async def get_last_request_time(self, key: str) -> Optional[datetime]:
        """
        Get the timestamp of the last request for a key.
        Used primarily for DSR requests.
        
        Args:
            key: Rate limit key (e.g., "dsr:export:user123")
            
        Returns:
            Datetime of the last request, or None if no requests have been made
        """
        # For DSR rate limits, we don't actually store the last request time
        # but we can approximate based on TTL
        redis_key = f"{self.prefix}:{key}"
        
        if redis_client:
            try:
                ttl = await redis_client.ttl(redis_key)
                
                if ttl <= 0:
                    return None
                    
                # If we have a TTL, estimate the last request time
                # This is an approximation since we don't store exact timestamps
                current_time = datetime.now()
                period = await redis_client.get(f"{redis_key}:period") or 86400  # Default to 1 day
                period = int(period)
                
                # Estimate when it was last set based on TTL
                estimated_time = current_time - timedelta(seconds=period - ttl)
                return estimated_time
                
            except Exception as e:
                log.error(f"Error getting last request time from Redis: {e}")
                # Fall back to returning None
                return None
        
        # If using memory store or Redis fails, we don't have enough info
        return None

# Define different rate limits for various endpoint types
standard_rate_limit = RateLimiter(times=60, seconds=60)  # 60 requests per minute
auth_rate_limit = RateLimiter(times=10, seconds=60, prefix="auth_rate_limit")  # 10 auth requests per minute

# Rate limiter instance that can be used directly in classes
rate_limiter_instance = RateLimiter()

def get_rate_limiter() -> RateLimiter:
    """Dependency injection for the rate limiter."""
    return rate_limiter_instance

# Create a singleton instance
_rate_limiter = None

async def get_rate_limiter(db = Depends(get_db)) -> RateLimiter:
    """Dependency injection for the rate limiter."""
    global _rate_limiter
    if _rate_limiter is None:
        _rate_limiter = RateLimiter(db)
    return _rate_limiter

# Define different rate limits for various endpoint types
# More generous limits for simple reads, stricter for complex operations
default_rate_limit = RateLimiter(times=60, seconds=60, prefix="default")
search_rate_limit = RateLimiter(times=30, seconds=60, prefix="search")
complex_search_rate_limit = RateLimiter(times=10, seconds=60, prefix="complex_search")
embedding_creation_rate_limit = RateLimiter(times=10, seconds=60, prefix="embedding_creation") 