#backend/app/core/mongodb_conns.py

"""
MongoDB Connection and Beanie Initialization
Handles Motor client and Beanie ODM setup
"""

import logging
from motor.motor_asyncio import AsyncIOMotorClient
from beanie import init_beanie
import sys

from app.config import settings
from app.models.mongodb_models import (
    User,
    FileUpload,
    ProcessingJob,
    ChartData,
    Dashboard,
    DataProfile,
    QualityReport,
    TokenUsage,
    EmailVerification
)

logger = logging.getLogger(__name__)

# List of all Beanie models to initialize
BEANIE_MODELS = [
    User,
    FileUpload,
    ProcessingJob,
    ChartData,
    Dashboard,
    DataProfile,
    QualityReport,
    TokenUsage,
    EmailVerification
]

async def init_mongodb():
    """
    Initialize MongoDB connection and Beanie ODM
    Call this on application startup
    """
    if not settings.MONGODB_URL:
        logger.error("MONGODB_URL is not set in environment variables.")
        return False
        
    try:
        # Create Motor client
        client = AsyncIOMotorClient(settings.MONGODB_URL)
        
        # Initialize Beanie with specified database and models
        await init_beanie(
            database=client[settings.MONGODB_DB_NAME],
            document_models=BEANIE_MODELS
        )
        
        # Test connection
        await client.admin.command('ping')
        
        logger.info("MongoDB initialized successfully")
        logger.info(f"Connected to database: {settings.MONGODB_DB_NAME}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to initialize MongoDB: {str(e)}")
        return False

async def check_mongodb_connection():
    """
    Check if MongoDB connection is active
    """
    try:
        client = AsyncIOMotorClient(settings.MONGODB_URL)
        await client.admin.command('ping')
        return True
    except Exception:
        return False
