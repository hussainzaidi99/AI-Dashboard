"""
Credit Cache - Redis-based caching for user credit balances
Reduces latency from ~50-100ms (MongoDB) to ~1-2ms (Redis)
"""

import redis.asyncio as redis
from typing import Optional
import json
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

# Redis client (singleton)
_redis_client: Optional[redis.Redis] = None

async def get_redis_client() -> redis.Redis:
    """Get or create Redis client instance."""
    global _redis_client
    if _redis_client is None:
        from app.config import settings
        _redis_client = redis.Redis(
            host=getattr(settings, 'REDIS_HOST', 'localhost'),
            port=getattr(settings, 'REDIS_PORT', 6379),
            db=getattr(settings, 'REDIS_DB', 0),
            decode_responses=True
        )
    return _redis_client

async def get_cached_balance(user_id: str) -> Optional[int]:
    """
    Get user balance from cache. Returns None if not cached.
    
    Returns:
        int: Active balance in tokens, or None if cache miss
    """
    try:
        client = await get_redis_client()
        key = f"user_credits:{user_id}"
        data = await client.get(key)
        
        if data:
            parsed = json.loads(data)
            logger.debug(f"Cache HIT for user {user_id}: {parsed['active_balance']} tokens")
            return parsed['active_balance']
        
        logger.debug(f"Cache MISS for user {user_id}")
        return None
    except Exception as e:
        logger.error(f"Redis error (non-critical, falling back to DB): {str(e)}")
        return None  # Fallback to DB query

async def cache_balance(user_id: str, balance: int, ttl: int = 300):
    """
    Cache user balance with TTL (default 5 minutes).
    
    Args:
        user_id: User identifier
        balance: Active token balance
        ttl: Time-to-live in seconds (default: 300 = 5 minutes)
    """
    try:
        client = await get_redis_client()
        key = f"user_credits:{user_id}"
        data = json.dumps({
            "active_balance": balance,
            "last_updated": datetime.utcnow().isoformat(),
            "cached_at": datetime.utcnow().isoformat()
        })
        await client.setex(key, ttl, data)
        logger.debug(f"Cached balance for user {user_id}: {balance} tokens (TTL: {ttl}s)")
    except Exception as e:
        logger.error(f"Failed to cache balance (non-critical): {str(e)}")

async def invalidate_balance_cache(user_id: str):
    """
    Invalidate cache after token deduction.
    Called immediately after balance changes to ensure accuracy.
    """
    try:
        client = await get_redis_client()
        key = f"user_credits:{user_id}"
        await client.delete(key)
        logger.debug(f"Invalidated cache for user {user_id}")
    except Exception as e:
        logger.error(f"Failed to invalidate cache (non-critical): {str(e)}")
