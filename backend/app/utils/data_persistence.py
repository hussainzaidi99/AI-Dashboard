import os
import json
import logging
from typing import Optional, Any
from app.config import get_upload_path
from app.utils.cache import cache_manager
from app.utils.json_encoder import deserialize_from_json

logger = logging.getLogger(__name__)

async def get_processed_data(file_id: str) -> Optional[Any]:
    """
    Get processed data for a file, checking cache first and then disk persistence.
    If found on disk but not in cache, it re-hydrates the cache.
    """
    cache_key = f"processed_result:{file_id}"
    
    # 1. Try Cache
    data = cache_manager.get(cache_key)
    if data:
        return data
        
    # 2. Try Disk
    persistence_path = get_upload_path(f"{file_id}.json")
    if os.path.exists(persistence_path):
        try:
            with open(persistence_path, 'r') as f:
                # Use custom deserializer for proper type handling
                data = deserialize_from_json(f.read())
            
            # Re-hydrate cache
            cache_manager.set(cache_key, data, expire=86400)
            logger.info(f"Re-hydrated cache from disk for file: {file_id}")
            return data
        except Exception as e:
            logger.error(f"Error reading persistence file for {file_id}: {str(e)}")
            
    return None
