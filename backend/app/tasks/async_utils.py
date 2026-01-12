#backend/app/tasks/async_utils.py
import asyncio
from typing import Any, Coroutine
import logging

logger = logging.getLogger(__name__)

def run_async(coro: Coroutine[Any, Any, Any]) -> Any:
    """
    Helper to run async functions in synchronous context (like Celery).
    
    Args:
        coro: The coroutine to run
        
    Returns:
        The result of the coroutine
    """
    try:
        # Check if there's a running event loop
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None

    if loop and loop.is_running():
        # This shouldn't happen in a standard Celery worker, 
        # but if it does, we use a new thread or nested loop.
        # For simplicity in this env, we try running it in the loop.
        logger.debug("Event loop already running, using asyncio.run in fallback")
        return asyncio.run(coro)
    
    return asyncio.run(coro)
