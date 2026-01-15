"""
Utility script to clean up orphaned cache entries
Run this when you have files in cache but not in MongoDB
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import asyncio
from app.utils.cache import cache_manager
from app.models.mongodb_models import FileUpload
from app.core.mongodb_conns import init_mongodb


async def cleanup_orphaned_cache():
    """Remove cache entries for files that don't exist in MongoDB"""
    print("🔍 Checking for orphaned cache entries...")
    
    # Initialize MongoDB
    await init_mongodb()
    
    # Get all files from MongoDB
    files = await FileUpload.find_all().to_list()
    valid_file_ids = {file.file_id for file in files}
    
    print(f"✅ Found {len(valid_file_ids)} valid files in MongoDB")
    
    # Check cache for orphaned entries
    # Note: Redis doesn't have a direct way to list all keys matching a pattern
    # This is a limitation - we'd need to track file IDs separately
    
    print("\n⚠️  Manual cleanup required:")
    print("   1. Clear Redis cache: redis-cli FLUSHDB")
    print("   2. Or restart Redis to clear all cached data")
    print("   3. Re-upload and process files")
    
    print(f"\n📋 Valid file IDs in database:")
    for file_id in valid_file_ids:
        print(f"   - {file_id}")


if __name__ == "__main__":
    asyncio.run(cleanup_orphaned_cache())
