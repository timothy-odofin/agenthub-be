#!/usr/bin/env python3
"""
Test Redis connection using the actual RedisConnectionManager class.
"""

import asyncio
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

# Load environment variables
load_dotenv()

async def test_redis_connection():
    """Test Redis connection using RedisConnectionManager."""
    
    print("=" * 70)
    print("🔧 Redis Connection Test (Using RedisConnectionManager)")
    print("=" * 70)
    
    # Get config from environment
    host = os.getenv('REDIS_HOST', 'localhost').strip('"')
    port = int(os.getenv('REDIS_PORT', '6379'))
    password = os.getenv('REDIS_PASSWORD', '').strip('"')
    db = int(os.getenv('REDIS_DB', '0'))
    ssl_enabled = os.getenv('REDIS_SSL', 'false').lower() in ('true', '1', 'yes')
    
    print(f"Host: {host}")
    print(f"Port: {port}")
    print(f"DB: {db}")
    print(f"SSL Enabled: {ssl_enabled}")
    print(f"Password: {'*' * min(len(password), 20)}...")
    print("=" * 70)
    print()
    
    try:
        # Import the actual RedisConnectionManager
        from app.connections.database.redis_connection_manager import RedisConnectionManager
        from app.connections.base import ConnectionType
        
        print("📡 Test 1: Creating RedisConnectionManager instance...")
        manager = RedisConnectionManager()
        
        print("✅ RedisConnectionManager instance created")
        
        print("\n📡 Test 2: Validating configuration...")
        manager.validate_config()
        print("✅ Configuration validated")
        
        print("\n📡 Test 3: Connecting to Redis...")
        client = await manager.connect()
        print("✅ Connection established")
        
        print("\n📡 Test 4: Testing PING...")
        response = await client.ping()
        print(f"✅ PING successful! Response: {response}")
        
        print("\n📡 Test 5: Testing SET operation...")
        test_key = "test:connection:manager"
        test_value = "Hello from RedisConnectionManager!"
        await manager.set(test_key, test_value, ex=60)
        print(f"✅ SET successful! Key: {test_key}")
        
        print("\n📡 Test 6: Testing GET operation...")
        retrieved = await manager.get(test_key)
        print(f"✅ GET successful! Value: {retrieved}")
        
        print("\n📡 Test 7: Testing EXISTS operation...")
        exists = await manager.exists(test_key)
        print(f"✅ EXISTS successful! Result: {exists}")
        
        print("\n� Test 8: Testing TTL operation...")
        ttl = await manager.ttl(test_key)
        print(f"✅ TTL successful! Remaining: {ttl} seconds")
        
        print("\n📡 Test 9: Testing DELETE operation...")
        deleted = await manager.delete(test_key)
        print(f"✅ DELETE successful! Keys deleted: {deleted}")
        
        print("\n📡 Test 10: Testing health check...")
        is_healthy = await manager.async_is_healthy()
        print(f"✅ Health check successful! Status: {is_healthy}")
        
        print("\n📊 Connection Stats:")
        stats = manager.get_connection_stats()
        for key, value in stats.items():
            print(f"   {key}: {value}")
        
        print("\n📡 Test 11: Disconnecting...")
        await manager.disconnect()
        print("✅ Disconnected successfully")
        
        print("\n" + "=" * 70)
        print("🎉 All tests PASSED! RedisConnectionManager is working correctly.")
        print("=" * 70)
        return True
        
    except Exception as e:
        print(f"\n❌ Test Failed: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        print("\n" + "=" * 70)
        return False


if __name__ == '__main__':
    print("\n🚀 Starting Redis Connection Tests...\n")
    
    # Run test
    success = asyncio.run(test_redis_connection())
    
    print("\n✨ Testing complete!\n")
    
    sys.exit(0 if success else 1)
