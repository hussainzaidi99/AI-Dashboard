"""
Simple script to clear Redis cache
Run this when you need to clear all cached data
"""

import redis

def clear_redis_cache():
    """Clear all Redis cache"""
    try:
        # Connect to Redis (default localhost:6379)
        r = redis.Redis(
            host='localhost',
            port=6379,
            db=0,
            decode_responses=True
        )
        
        # Test connection
        r.ping()
        print("✅ Connected to Redis")
        
        # Get all keys
        all_keys = r.keys('*')
        print(f"📊 Found {len(all_keys)} cached items")
        
        if all_keys:
            # Show what will be deleted
            print("\n🗑️  Keys to be deleted:")
            for key in all_keys[:10]:  # Show first 10
                print(f"   - {key}")
            if len(all_keys) > 10:
                print(f"   ... and {len(all_keys) - 10} more")
            
            # Clear all
            r.flushdb()
            print("\n✅ Redis cache cleared successfully!")
            print("ℹ️  You can now upload files fresh without old cached data")
        else:
            print("ℹ️  Redis cache is already empty")
            
    except redis.ConnectionError:
        print("❌ Could not connect to Redis. Is Redis running?")
        print("   Start Redis with: redis-server")
    except Exception as e:
        print(f"❌ Error: {str(e)}")

if __name__ == "__main__":
    print("🧹 Redis Cache Cleaner\n")
    clear_redis_cache()
