"""
Caching utilities with TTL support
"""

from functools import wraps
from datetime import datetime, timedelta
from typing import Dict, Tuple, Any, Callable
import hashlib
import json


# In-memory cache with TTL
_cache: Dict[str, Tuple[Any, datetime]] = {}
MAX_CACHE_SIZE = 1000


def generate_cache_key(func_name: str, args: tuple, kwargs: dict) -> str:
    """
    Generate unique cache key from function arguments
    
    Args:
        func_name: Name of the function
        args: Positional arguments
        kwargs: Keyword arguments
        
    Returns:
        MD5 hash of the function signature
    """
    # Filter out non-serializable objects like Request
    from fastapi import Request
    
    # Filter args - exclude Request objects
    serializable_args = []
    for arg in args:
        if not isinstance(arg, Request):
            try:
                # Try to convert to string for hashing
                serializable_args.append(str(arg) if not isinstance(arg, (str, int, float, bool, type(None))) else arg)
            except:
                # Skip if can't serialize
                pass
    
    # Filter kwargs - exclude Request objects and other non-serializable types
    serializable_kwargs = {}
    for key, value in kwargs.items():
        if not isinstance(value, Request):
            try:
                # Try to use simple types directly, convert complex types to string
                if isinstance(value, (str, int, float, bool, type(None))):
                    serializable_kwargs[key] = value
                else:
                    serializable_kwargs[key] = str(value)
            except:
                # Skip if can't serialize
                pass
    
    key_data = {
        "func": func_name,
        "args": serializable_args,
        "kwargs": sorted(serializable_kwargs.items())
    }
    key_string = json.dumps(key_data, sort_keys=True)
    return hashlib.md5(key_string.encode()).hexdigest()


def clear_cache() -> int:
    """
    Clear all cached entries
    
    Returns:
        Number of entries cleared
    """
    global _cache
    count = len(_cache)
    _cache.clear()
    return count


def evict_expired() -> int:
    """
    Remove expired entries from cache
    
    Returns:
        Number of entries evicted
    """
    global _cache
    now = datetime.now()
    expired_keys = [key for key, (_, expires_at) in _cache.items() if now >= expires_at]
    
    for key in expired_keys:
        del _cache[key]
    
    return len(expired_keys)


def evict_lru() -> None:
    """
    Evict least recently used entries if cache is too large
    Uses simple FIFO for now (can be enhanced with actual LRU tracking)
    """
    global _cache
    
    if len(_cache) > MAX_CACHE_SIZE:
        # Remove oldest 10% of entries
        to_remove = len(_cache) - MAX_CACHE_SIZE
        keys_to_remove = list(_cache.keys())[:to_remove]
        
        for key in keys_to_remove:
            del _cache[key]


def cache_with_ttl(seconds: int) -> Callable:
    """
    Decorator for caching function results with TTL
    
    Args:
        seconds: Time to live in seconds
        
    Returns:
        Decorated function
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            # Clean up expired entries periodically
            evict_expired()
            evict_lru()
            
            # Generate cache key
            cache_key = generate_cache_key(func.__name__, args, kwargs)
            
            # Check cache
            if cache_key in _cache:
                cached_data, expires_at = _cache[cache_key]
                if datetime.now() < expires_at:
                    # Cache hit
                    if isinstance(cached_data, dict):
                        cached_data["_cache_status"] = "HIT"
                        cached_data["_cache_expires_at"] = expires_at.isoformat()
                    return cached_data
            
            # Cache miss - execute function
            result = await func(*args, **kwargs)
            
            # Store in cache
            expires_at = datetime.now() + timedelta(seconds=seconds)
            _cache[cache_key] = (result, expires_at)
            
            # Add cache metadata
            if isinstance(result, dict):
                result["_cache_status"] = "MISS"
                result["_cache_expires_at"] = expires_at.isoformat()
            
            return result
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            # Clean up expired entries periodically
            evict_expired()
            evict_lru()
            
            # Generate cache key
            cache_key = generate_cache_key(func.__name__, args, kwargs)
            
            # Check cache
            if cache_key in _cache:
                cached_data, expires_at = _cache[cache_key]
                if datetime.now() < expires_at:
                    # Cache hit
                    if isinstance(cached_data, dict):
                        cached_data["_cache_status"] = "HIT"
                        cached_data["_cache_expires_at"] = expires_at.isoformat()
                    return cached_data
            
            # Cache miss - execute function
            result = func(*args, **kwargs)
            
            # Store in cache
            expires_at = datetime.now() + timedelta(seconds=seconds)
            _cache[cache_key] = (result, expires_at)
            
            # Add cache metadata
            if isinstance(result, dict):
                result["_cache_status"] = "MISS"
                result["_cache_expires_at"] = expires_at.isoformat()
            
            return result
        
        # Return appropriate wrapper based on function type
        import inspect
        if inspect.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator
