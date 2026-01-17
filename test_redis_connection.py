#!/usr/bin/env python3
"""
Test Redis connection locally to diagnose issues.
"""

import asyncio
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

async def test_redis_connection():
    """Test Redis connection with different configurations."""
    
    # Get config from environment
    host = os.getenv('REDIS_HOST', 'localhost').strip('"')
    port = int(os.getenv('REDIS_PORT', '6379'))
    password = os.getenv('REDIS_PASSWORD', '').strip('"')
    db = int(os.getenv('REDIS_DB', '0'))
    ssl_enabled = os.getenv('REDIS_SSL', 'false').lower() in ('true', '1', 'yes')
    
    print("=" * 70)
    print("🔧 Redis Connection Test")
    print("=" * 70)
    print(f"Host: {host}")
    print(f"Port: {port}")
    print(f"DB: {db}")
    print(f"SSL Enabled: {ssl_enabled}")
    print(f"Password: {'*' * min(len(password), 20)}...")
    print("=" * 70)
    print()
    
    # Test 1: Basic connection with SSL
    print("📡 Test 1: Connecting with SSL/TLS...")
    try:
        import redis.asyncio as redis
        from redis.asyncio.connection import SSLConnection
        
        if ssl_enabled:
            pool = redis.ConnectionPool(
                host=host,
                port=port,
                password=password if password else None,
                db=db,
                connection_class=SSLConnection,
                decode_responses=True,
                socket_timeout=10,
                socket_connect_timeout=10,
                retry_on_timeout=True,
                health_check_interval=30
            )
        else:
            pool = redis.ConnectionPool(
                host=host,
                port=port,
                password=password if password else None,
                db=db,
                decode_responses=True,
                socket_timeout=10,
                socket_connect_timeout=10,
                retry_on_timeout=True
            )
        
        client = redis.Redis(connection_pool=pool)
        
        # Test ping
        response = await client.ping()
        print(f"✅ PING successful! Response: {response}")
        
        # Test set/get
        test_key = "test:connection"
        test_value = "Hello from AgentHub!"
        
        await client.set(test_key, test_value, ex=60)
        print(f"✅ SET successful! Key: {test_key}")
        
        retrieved = await client.get(test_key)
        print(f"✅ GET successful! Value: {retrieved}")
        
        # Clean up
        await client.delete(test_key)
        print(f"✅ DELETE successful!")
        
        # Get server info
        info = await client.info('server')
        print(f"\n📊 Server Info:")
        print(f"   Redis Version: {info.get('redis_version', 'N/A')}")
        print(f"   OS: {info.get('os', 'N/A')}")
        print(f"   Uptime: {info.get('uptime_in_seconds', 0)} seconds")
        
        await client.close()
        
        print("\n" + "=" * 70)
        print("🎉 All tests PASSED! Redis connection is working.")
        print("=" * 70)
        return True
        
    except redis.AuthenticationError as e:
        print(f"❌ Authentication Failed: {e}")
        print("\n💡 Possible fixes:")
        print("   1. Check REDIS_PASSWORD is correct")
        print("   2. Verify password in Upstash dashboard")
        return False
        
    except redis.ConnectionError as e:
        print(f"❌ Connection Failed: {e}")
        print("\n💡 Possible fixes:")
        print("   1. Check REDIS_HOST and REDIS_PORT are correct")
        print("   2. Verify SSL is enabled (REDIS_SSL=true for Upstash)")
        print("   3. Check firewall/network settings")
        print("   4. Verify Upstash database is active")
        return False
        
    except Exception as e:
        print(f"❌ Unexpected Error: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_with_different_ports():
    """Test connection with Upstash REST port."""
    
    host = os.getenv('REDIS_HOST', 'localhost').strip('"')
    password = os.getenv('REDIS_PASSWORD', '').strip('"')
    
    print("\n" + "=" * 70)
    print("🔄 Test 2: Trying alternative port (TLS port 6380)...")
    print("=" * 70)
    
    try:
        import redis.asyncio as redis
        from redis.asyncio.connection import SSLConnection
        
        pool = redis.ConnectionPool(
            host=host,
            port=6380,  # Alternative TLS port
            password=password if password else None,
            db=0,
            connection_class=SSLConnection,
            decode_responses=True,
            socket_timeout=10,
            socket_connect_timeout=10
        )
        
        client = redis.Redis(connection_pool=pool)
        response = await client.ping()
        print(f"✅ Connection successful on port 6380! Response: {response}")
        await client.close()
        return True
        
    except Exception as e:
        print(f"❌ Port 6380 also failed: {e}")
        return False


if __name__ == '__main__':
    print("\n🚀 Starting Redis Connection Tests...\n")
    
    # Run main test
    success = asyncio.run(test_redis_connection())
    
    # If main test failed, try alternative port
    if not success:
        asyncio.run(test_with_different_ports())
    
    print("\n✨ Testing complete!\n")
