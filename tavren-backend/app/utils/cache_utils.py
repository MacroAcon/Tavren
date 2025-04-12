"""
Caching utilities for improving performance of API operations.
Provides both in-memory and Redis-based caching mechanisms.
"""

import json
import logging
import pickle
from typing import Any, Dict, Optional, Union, List, Callable, TypeVar
import time
import asyncio
from functools import wraps
from cachetools import TTLCache
from app.config import settings

# Set up logging
log = logging.getLogger("app")

# Type variable for generic functions
T = TypeVar('T')

# In-memory cache for small data with TTL
# Configurable size and TTL
in_memory_cache = TTLCache(
    maxsize=settings.CACHE_MAX_SIZE, 
    ttl=settings.CACHE_TTL_SECONDS
)

# Configure Redis if available
redis_client = None
if settings.REDIS_URL:
    try:
        import redis.asyncio as aioredis
        redis_client = aioredis.from_url(
            settings.REDIS_URL,
            encoding="utf-8",
            decode_responses=False  # We'll handle decoding ourselves
        )
        log.info(f"Redis cache initialized at {settings.REDIS_URL}")
    except ImportError:
        log.warning("Redis packages not installed. Redis caching will be disabled.")
    except Exception as e:
        log.error(f"Failed to initialize Redis: {str(e)}")

# Check if Redis is available
async def is_redis_available() -> bool:
    """Check if Redis connection is working."""
    if redis_client is None:
        return False
    
    try:
        await redis_client.ping()
        return True
    except Exception:
        return False

async def get_from_cache(key: str) -> Optional[Any]:
    """
    Get item from cache (tries Redis first, then in-memory).
    
    Args:
        key: Cache key
        
    Returns:
        Cached value or None if not found
    """
    # Try Redis first
    if redis_client and await is_redis_available():
        try:
            data = await redis_client.get(key)
            if data:
                return pickle.loads(data)
        except Exception as e:
            log.warning(f"Redis get failed for key {key}: {str(e)}")
    
    # Fall back to in-memory cache
    return in_memory_cache.get(key)

async def set_in_cache(key: str, value: Any, ttl: Optional[int] = None) -> bool:
    """
    Store item in cache (both Redis and in-memory).
    
    Args:
        key: Cache key
        value: Value to store
        ttl: Optional TTL in seconds (overrides default)
        
    Returns:
        Success status
    """
    # Default TTL
    ttl = ttl or settings.CACHE_TTL_SECONDS
    
    # Store in Redis if available
    redis_success = False
    if redis_client and await is_redis_available():
        try:
            serialized = pickle.dumps(value)
            redis_success = await redis_client.setex(key, ttl, serialized)
        except Exception as e:
            log.warning(f"Redis set failed for key {key}: {str(e)}")
    
    # Always store in in-memory cache as backup
    try:
        in_memory_cache[key] = value
        return True
    except Exception as e:
        log.warning(f"In-memory cache set failed for key {key}: {str(e)}")
        return redis_success

async def delete_from_cache(key: str) -> bool:
    """
    Delete item from cache.
    
    Args:
        key: Cache key
        
    Returns:
        Success status
    """
    # Delete from Redis if available
    redis_success = False
    if redis_client and await is_redis_available():
        try:
            redis_success = await redis_client.delete(key)
        except Exception as e:
            log.warning(f"Redis delete failed for key {key}: {str(e)}")
    
    # Always delete from in-memory cache
    try:
        if key in in_memory_cache:
            del in_memory_cache[key]
        return True
    except Exception as e:
        log.warning(f"In-memory cache delete failed for key {key}: {str(e)}")
        return redis_success

def cache_key_builder(*args, **kwargs) -> str:
    """
    Build a cache key from arguments.
    
    Args:
        *args: Positional arguments
        **kwargs: Keyword arguments
        
    Returns:
        Cache key string
    """
    # Combine args and kwargs into a single string
    args_str = ':'.join(str(arg) for arg in args if arg is not None)
    kwargs_str = ':'.join(f"{k}={v}" for k, v in sorted(kwargs.items()) if v is not None)
    
    if args_str and kwargs_str:
        return f"{args_str}:{kwargs_str}"
    elif args_str:
        return args_str
    else:
        return kwargs_str

def cached(prefix: str, ttl: Optional[int] = None):
    """
    Decorator for caching function results.
    
    Args:
        prefix: Prefix for cache keys
        ttl: Optional TTL in seconds
        
    Returns:
        Decorator function
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Build cache key
            key_parts = [prefix]
            
            # Add function name
            key_parts.append(func.__name__)
            
            # Add arguments as part of the key
            key_suffix = cache_key_builder(*args, **kwargs)
            if key_suffix:
                key_parts.append(key_suffix)
                
            cache_key = ':'.join(key_parts)
            
            # Try to get from cache
            cached_result = await get_from_cache(cache_key)
            if cached_result is not None:
                log.debug(f"Cache hit for {cache_key}")
                return cached_result
            
            # If not in cache, call the function
            result = await func(*args, **kwargs)
            
            # Store in cache
            await set_in_cache(cache_key, result, ttl)
            
            return result
        return wrapper
    return decorator

# Specialized function for caching embeddings
async def cache_embedding(
    embedding_id: Union[int, str],
    embedding_data: Dict[str, Any],
    ttl: Optional[int] = None
) -> bool:
    """
    Cache an embedding with specialized handling.
    
    Args:
        embedding_id: ID of the embedding
        embedding_data: Embedding data to cache
        ttl: Optional TTL in seconds
        
    Returns:
        Success status
    """
    cache_key = f"embedding:{embedding_id}"
    return await set_in_cache(cache_key, embedding_data, ttl)

async def get_cached_embedding(embedding_id: Union[int, str]) -> Optional[Dict[str, Any]]:
    """
    Get a cached embedding.
    
    Args:
        embedding_id: ID of the embedding
        
    Returns:
        Cached embedding data or None if not found
    """
    cache_key = f"embedding:{embedding_id}"
    return await get_from_cache(cache_key)

async def cache_vector_search(
    query_hash: str,
    results: List[Dict[str, Any]],
    ttl: Optional[int] = None
) -> bool:
    """
    Cache vector search results.
    
    Args:
        query_hash: Hash of the search query and parameters
        results: Search results to cache
        ttl: Optional TTL in seconds
        
    Returns:
        Success status
    """
    cache_key = f"vector_search:{query_hash}"
    return await set_in_cache(cache_key, results, ttl)

async def get_cached_vector_search(query_hash: str) -> Optional[List[Dict[str, Any]]]:
    """
    Get cached vector search results.
    
    Args:
        query_hash: Hash of the search query and parameters
        
    Returns:
        Cached search results or None if not found
    """
    cache_key = f"vector_search:{query_hash}"
    return await get_from_cache(cache_key) 