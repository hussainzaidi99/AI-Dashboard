"""
Credit Check Middleware - Pre-flight credit validation
Checks user balance before processing AI requests using Redis cache
"""

from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from typing import Callable
import logging

logger = logging.getLogger(__name__)

# AI endpoints that require credit checks
AI_ENDPOINTS = {
    "/api/v1/ai/insights": 5000,      # Estimated 5k tokens
    "/api/v1/ai/query": 3000,         # Estimated 3k tokens
    "/api/v1/ai/ask": 2000,           # Estimated 2k tokens
    "/api/v1/ai/ask/stream": 2000,    # Estimated 2k tokens
    "/api/v1/charts/recommend": 1000, # Estimated 1k tokens
}

class CreditCheckMiddleware(BaseHTTPMiddleware):
    """
    Middleware to check user credits before processing AI requests.
    Uses Redis caching to minimize latency (<5ms overhead).
    """
    
    async def dispatch(self, request: Request, call_next: Callable):
        """
        Check credits before processing request.
        
        Flow:
        1. Check if endpoint requires credits
        2. Extract user_id from request state
        3. Check cache for balance
        4. If cache miss, query MongoDB
        5. Validate sufficient balance
        6. Proceed or return 402 error
        """
        
        # 1. Check if this endpoint requires credit validation
        path = request.url.path
        if path not in AI_ENDPOINTS:
            # Not an AI endpoint, skip check
            return await call_next(request)
        
        estimated_cost = AI_ENDPOINTS[path]
        
        # 2. Extract user_id from request state (set by auth middleware)
        user_id = None
        if hasattr(request.state, 'user'):
            user_id = request.state.user.user_id
        
        # 3. Skip check for anonymous users (if allowed)
        if not user_id or user_id == "anonymous":
            logger.debug(f"Skipping credit check for anonymous user on {path}")
            return await call_next(request)
        
        # 4. Check balance (cache first, then DB)
        try:
            from app.core.credit_cache import get_cached_balance, cache_balance
            from app.core.billing import BillingService
            
            # Try cache first
            cached_balance = await get_cached_balance(user_id)
            
            if cached_balance is not None:
                # Cache hit - fast path
                balance = cached_balance
                logger.debug(f"Credit check (cache): user={user_id}, balance={balance}, required={estimated_cost}")
            else:
                # Cache miss - query MongoDB
                logger.debug(f"Credit check (DB): user={user_id}, querying MongoDB...")
                user = await BillingService.get_user_for_billing(user_id)
                balance = user.active_balance if user else 0
                
                # Cache the result for next time
                await cache_balance(user_id, balance, ttl=300)
                logger.debug(f"Credit check (DB): user={user_id}, balance={balance}, required={estimated_cost}")
            
            # 5. Validate sufficient balance
            if balance < estimated_cost:
                logger.warning(f"Insufficient credits: user={user_id}, balance={balance}, required={estimated_cost}")
                raise HTTPException(
                    status_code=402,
                    detail=f"Insufficient credits. Required: {estimated_cost} tokens, Available: {balance} tokens. Please upgrade your plan."
                )
            
            # 6. Proceed with request
            logger.info(f"Credit check passed: user={user_id}, balance={balance}, required={estimated_cost}")
            return await call_next(request)
            
        except HTTPException:
            raise  # Re-raise HTTP exceptions
        except Exception as e:
            # Log error but allow request to proceed (fail-open for availability)
            logger.error(f"Credit check failed (allowing request): {str(e)}")
            return await call_next(request)
