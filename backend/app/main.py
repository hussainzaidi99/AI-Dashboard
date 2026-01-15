#backend/app/main.py

"""
AI Data Visualization Dashboard - Backend
Main FastAPI Application Entry Point
"""

import sys
import os
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import typing

# Monkeypatch for ForwardRef in Python 3.12 (uncomment if legacy pydantic/langchain issues occur)
# Monkeypatch for ForwardRef in Python 3.12 (uncomment if legacy pydantic/langchain issues occur)
# Monkeypatch for ForwardRef in Python 3.12 (uncomment if legacy pydantic/langchain issues occur)
if sys.version_info >= (3, 12):
    orig_evaluate = typing.ForwardRef._evaluate
    def patched_evaluate(self, globalns, localns, type_params=None, recursive_guard=frozenset()):
        # Handle legacy Pydantic behaviour where recursive_guard is passed as 3rd positional argument
        if isinstance(type_params, (set, frozenset)) and recursive_guard == frozenset():
            recursive_guard = type_params
            type_params = None
        return orig_evaluate(self, globalns, localns, type_params, recursive_guard=recursive_guard)
    typing.ForwardRef._evaluate = patched_evaluate

from app.config import settings
from app.core.mongodb_conns import init_mongodb, check_mongodb_connection
from app.api.v1 import upload, processing, charts, data, ai, export, auth
from app.utils.cache import cache_manager

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(settings.LOG_FILE) if settings.LOG_FILE else logging.NullHandler()
    ]
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize MongoDB (Beanie)
    try:
        success = await init_mongodb()
        if not success:
            logger.error("Failed to initialize MongoDB")
            if not settings.DEBUG:
                raise RuntimeError("MongoDB initialization failed")
    except Exception as e:
        logger.error(f"Error during MongoDB initialization: {e}")
        if not settings.DEBUG:
            raise

    yield

    # Shutdown logic can be added here if needed
    logger.info("Application shutdown complete")


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    lifespan=lifespan
)

# Set up CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API Routers
app.include_router(upload.router, prefix=f"{settings.API_V1_PREFIX}/upload", tags=["Upload"])
app.include_router(processing.router, prefix=f"{settings.API_V1_PREFIX}/processing", tags=["Processing"])
app.include_router(charts.router, prefix=f"{settings.API_V1_PREFIX}/charts", tags=["Charts"])
app.include_router(data.router, prefix=f"{settings.API_V1_PREFIX}/data", tags=["Data"])
app.include_router(ai.router, prefix=f"{settings.API_V1_PREFIX}/ai", tags=["AI"])
app.include_router(export.router, prefix=f"{settings.API_V1_PREFIX}/export", tags=["Export"])
app.include_router(auth.router, prefix=f"{settings.API_V1_PREFIX}/auth", tags=["Auth"])


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "AI Data Visualization Dashboard API",
        "version": settings.APP_VERSION,
        "docs": "/docs",
        "health": "/health"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    # Check MongoDB connection
    db_healthy = await check_mongodb_connection()
    
    # Check Redis connection
    redis_healthy = cache_manager.enabled and cache_manager.redis_client is not None
    try:
        if redis_healthy:
            cache_manager.redis_client.ping()
    except Exception:
        redis_healthy = False
    
    return {
        "status": "healthy" if db_healthy and redis_healthy else "degraded",
        "version": settings.APP_VERSION,
        "database_type": "mongodb + redis",
        "mongodb": "connected" if db_healthy else "disconnected",
        "redis": "connected" if redis_healthy else "disconnected",
        "features": {
            "ai_recommendations": settings.ENABLE_AI_RECOMMENDATIONS,
            "export_pdf": settings.ENABLE_EXPORT_PDF,
            "export_excel": settings.ENABLE_EXPORT_EXCEL,
            "websocket": settings.ENABLE_WEBSOCKET,
            "caching": settings.ENABLE_CACHING
        }
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)