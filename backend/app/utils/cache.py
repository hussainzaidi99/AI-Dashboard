"""
Cache Utilities
Caching functionality using Redis
"""

#backend/app/utils/cache.py
import json
import hashlib
from typing import Any, Optional, Callable
from functools import wraps
import logging

from app.config import settings

logger = logging.getLogger(__name__)


class CacheManager:
    """Manager for caching operations"""
    
    def __init__(self):
        self.enabled = settings.ENABLE_CACHING
        self.redis_client = None
        
        if self.enabled:
            try:
                import redis
                self.redis_client = redis.from_url(
                    settings.REDIS_URL,
                    decode_responses=True
                )
                # Test connection
                self.redis_client.ping()
                logger.info("Cache enabled: Connected to Redis")
            except Exception as e:
                logger.warning(f"Cache disabled: Could not connect to Redis: {str(e)}")
                self.enabled = False
    
    def get(self, key: str) -> Optional[Any]:
        """
        Get value from cache
        
        Args:
            key: Cache key
        
        Returns:
            Cached value or None
        """
        if not self.enabled or not self.redis_client:
            return None
        
        try:
            value = self.redis_client.get(key)
            if value:
                return json.loads(value)
            return None
        except Exception as e:
            logger.error(f"Cache get error: {str(e)}")
            return None
    
    def set(
        self,
        key: str,
        value: Any,
        expire: Optional[int] = None
    ) -> bool:
        """
        Set value in cache
        
        Args:
            key: Cache key
            value: Value to cache
            expire: Expiration time in seconds
        
        Returns:
            True if successful
        """
        if not self.enabled or not self.redis_client:
            return False
        
        try:
            serialized = json.dumps(value)
            if expire:
                self.redis_client.setex(key, expire, serialized)
            else:
                self.redis_client.set(key, serialized)
            return True
        except Exception as e:
            logger.error(f"Cache set error: {str(e)}")
            return False
    
    def delete(self, key: str) -> bool:
        """
        Delete value from cache
        
        Args:
            key: Cache key
        
        Returns:
            True if successful
        """
        if not self.enabled or not self.redis_client:
            return False
        
        try:
            self.redis_client.delete(key)
            return True
        except Exception as e:
            logger.error(f"Cache delete error: {str(e)}")
            return False
    
    def delete_pattern(self, pattern: str) -> int:
        """
        Delete all keys matching pattern using SCAN (production safe)
        
        Args:
            pattern: Key pattern (e.g., "user:*")
        
        Returns:
            Number of keys deleted
        """
        if not self.enabled or not self.redis_client:
            return 0
        
        try:
            deleted_count = 0
            # Use scan_iter instead of keys() for performance and safety
            for key in self.redis_client.scan_iter(match=pattern, count=500):
                self.redis_client.delete(key)
                deleted_count += 1
            return deleted_count
        except Exception as e:
            logger.error(f"Cache delete pattern error: {str(e)}")
            return 0
    
    def exists(self, key: str) -> bool:
        """
        Check if key exists in cache
        
        Args:
            key: Cache key
        
        Returns:
            True if exists
        """
        if not self.enabled or not self.redis_client:
            return False
        
        try:
            return bool(self.redis_client.exists(key))
        except Exception as e:
            logger.error(f"Cache exists error: {str(e)}")
            return False
    
    def clear_all(self) -> bool:
        """
        Clear all cache
        
        Returns:
            True if successful
        """
        if not self.enabled or not self.redis_client:
            return False
        
        try:
            self.redis_client.flushdb()
            logger.info("Cache cleared")
            return True
        except Exception as e:
            logger.error(f"Cache clear error: {str(e)}")
            return False
    
    def get_stats(self) -> dict:
        """
        Get cache statistics
        
        Returns:
            Statistics dictionary
        """
        if not self.enabled or not self.redis_client:
            return {"enabled": False}
        
        try:
            info = self.redis_client.info()
            return {
                "enabled": True,
                "keys": self.redis_client.dbsize(),
                "memory_used": info.get('used_memory_human'),
                "hits": info.get('keyspace_hits', 0),
                "misses": info.get('keyspace_misses', 0)
            }
        except Exception as e:
            logger.error(f"Cache stats error: {str(e)}")
            return {"enabled": True, "error": str(e)}


# Global cache manager instance
cache_manager = CacheManager()


def generate_cache_key(*args, **kwargs) -> str:
    """
    Generate cache key from arguments
    
    Args:
        *args: Positional arguments
        **kwargs: Keyword arguments
    
    Returns:
        Cache key string
    """
    # Create a string representation of arguments
    key_parts = []
    
    for arg in args:
        if isinstance(arg, (str, int, float, bool)):
            key_parts.append(str(arg))
        else:
            key_parts.append(str(type(arg).__name__))
    
    for k, v in sorted(kwargs.items()):
        if isinstance(v, (str, int, float, bool)):
            key_parts.append(f"{k}:{v}")
    
    key_string = "|".join(key_parts)
    
    # Hash for consistent key length
    return hashlib.md5(key_string.encode()).hexdigest()


def cache_result(
    expire: int = 3600,
    key_prefix: str = "",
    key_generator: Optional[Callable] = None
):
    """
    Decorator to cache function results
    
    Args:
        expire: Expiration time in seconds
        key_prefix: Prefix for cache key
        key_generator: Custom key generator function
    
    Returns:
        Decorated function
    """
    def decorator(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            # Generate cache key
            if key_generator:
                cache_key = key_generator(*args, **kwargs)
            else:
                cache_key = f"{key_prefix}:{func.__name__}:{generate_cache_key(*args, **kwargs)}"
            
            # Try to get from cache
            cached = cache_manager.get(cache_key)
            if cached is not None:
                logger.debug(f"Cache hit: {cache_key}")
                return cached
            
            # Execute function
            result = await func(*args, **kwargs)
            
            # Cache result
            cache_manager.set(cache_key, result, expire)
            logger.debug(f"Cache set: {cache_key}")
            
            return result
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            # Generate cache key
            if key_generator:
                cache_key = key_generator(*args, **kwargs)
            else:
                cache_key = f"{key_prefix}:{func.__name__}:{generate_cache_key(*args, **kwargs)}"
            
            # Try to get from cache
            cached = cache_manager.get(cache_key)
            if cached is not None:
                logger.debug(f"Cache hit: {cache_key}")
                return cached
            
            # Execute function
            result = func(*args, **kwargs)
            
            # Cache result
            cache_manager.set(cache_key, result, expire)
            logger.debug(f"Cache set: {cache_key}")
            
            return result
        
        # Return appropriate wrapper based on function type
        import inspect
        if inspect.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator


def invalidate_cache(key_pattern: str):
    """
    Invalidate cache by pattern
    
    Args:
        key_pattern: Pattern to match (e.g., "user:*")
    """
    deleted = cache_manager.delete_pattern(key_pattern)
    logger.info(f"Invalidated {deleted} cache keys matching '{key_pattern}'")