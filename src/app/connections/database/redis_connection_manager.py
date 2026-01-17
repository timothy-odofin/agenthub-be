"""
Redis connection manager implementation.

Provides connection management for Redis cache with proper
configuration validation and health checking.
Supports both direct Redis protocol and Upstash REST API.
"""

from typing import Any, Optional, Union
import redis.asyncio as redis
from redis.asyncio import Redis, ConnectionPool
from redis.exceptions import ConnectionError as RedisConnectionError, TimeoutError

from app.connections.base import AsyncBaseConnectionManager, ConnectionRegistry, ConnectionType
from app.core.utils.logger import get_logger

logger = get_logger(__name__)


@ConnectionRegistry.register(ConnectionType.REDIS)
class RedisConnectionManager(AsyncBaseConnectionManager):
    """Redis connection manager implementation with REST API fallback."""
    
    def __init__(self):
        super().__init__()
        self._connection_pool: Optional[ConnectionPool] = None
        self._redis_client: Optional[Redis] = None
        self._use_rest_api: bool = False
    
    def get_connection_name(self) -> str:
        """Return the configuration name for Redis."""
        return ConnectionType.REDIS.value
    
    def validate_config(self) -> None:
        """Validate Redis configuration."""
        required_fields = ['host', 'port']
        
        for field in required_fields:
            if not self.config.get(field):
                raise ValueError(f"Redis connection requires '{field}' in configuration")
        
        # Validate port
        port = self.config.get('port')
        if not isinstance(port, int) or port <= 0 or port > 65535:
            raise ValueError(f"Redis port must be a valid port number (1-65535), got: {port}")
        
        # Validate database number
        database = self.config.get('db', 0)  # Use 'db' instead of 'database'
        if not isinstance(database, int) or database < 0 or database > 15:
            raise ValueError(f"Redis database must be between 0-15, got: {database}")
        
        # Validate pool size
        pool_size = self.config.get('connection_pool_size', 10)
        if not isinstance(pool_size, int) or pool_size <= 0:
            raise ValueError(f"Redis connection_pool_size must be a positive integer, got: {pool_size}")
        
        logger.info("Redis connection configuration validated successfully")
    
    async def connect(self) -> Redis:
        """Establish Redis connection with automatic fallback to REST API."""
        if self._redis_client:
            try:
                await self._redis_client.ping()
                return self._redis_client
            except Exception:
                # Connection might be stale, recreate
                await self.disconnect()
        
        # DEBUG: Log all Redis config (FULL CREDENTIALS FOR DEBUGGING)
        logger.info("=" * 70)
        logger.info("🔍 REDIS CONNECTION DEBUG INFO (FULL CREDENTIALS)")
        logger.info("=" * 70)
        logger.info(f"Config keys available: {list(self.config.keys())}")
        logger.info(f"REDIS_HOST: {self.config.get('host')}")
        logger.info(f"REDIS_PORT: {self.config.get('port')}")
        logger.info(f"REDIS_DB: {self.config.get('db')}")
        logger.info(f"REDIS_SSL: {self.config.get('ssl')}")
        logger.info(f"REDIS_REST_URL: {self.config.get('rest_url')}")
        
        # ⚠️ TEMPORARY: Log full credentials for debugging
        rest_token = self.config.get('rest_token')
        if rest_token:
            logger.info(f"REDIS_REST_TOKEN: {rest_token}")
        else:
            logger.info("REDIS_REST_TOKEN: NOT SET")
        
        password = self.config.get('password')
        if password:
            logger.info(f"REDIS_PASSWORD: {password}")
        else:
            logger.info("REDIS_PASSWORD: NOT SET")
        
        logger.info("=" * 70)
        
        # Try REST API first if configured
        rest_url = self.config.get('rest_url')
        rest_token = self.config.get('rest_token')
        
        if rest_url and rest_token:
            try:
                logger.info(f"🌐 Attempting Upstash REST API connection to {rest_url}...")
                from .upstash_rest_client import UpstashRestClient
                
                self._redis_client = UpstashRestClient(
                    rest_url=rest_url,
                    rest_token=rest_token,
                    timeout=self.config.get('socket_timeout', 10)
                )
                
                # Test connection
                await self._redis_client.ping()
                
                self._connection = self._redis_client
                self._is_connected = True
                self._use_rest_api = True
                
                logger.info(f"✅ Upstash REST API connection established to {rest_url}")
                return self._redis_client
                
            except Exception as e:
                logger.warning(f"⚠️  Upstash REST API connection failed: {e}")
                logger.warning("Falling back to direct Redis protocol...")
        else:
            logger.info(f"ℹ️  REST API not configured (rest_url={bool(rest_url)}, rest_token={bool(rest_token)})")
            logger.info("Using direct Redis protocol connection...")
        
        # Fall back to direct Redis protocol
        try:
            logger.info("🔌 Attempting direct Redis protocol connection...")
            
            # Build connection pool parameters
            pool_params = {
                'host': self.config['host'],
                'port': self.config['port'],
                'db': self.config.get('db', 0),  # Use 'db' instead of 'database'
                'password': self.config.get('password'),
                'max_connections': self.config.get('connection_pool_size', 10),
                'socket_timeout': self.config.get('socket_timeout', 5),
                'socket_connect_timeout': self.config.get('socket_connect_timeout', 5),
                'health_check_interval': self.config.get('health_check_interval', 30),
                'retry_on_timeout': True,
                'decode_responses': True  # Automatically decode byte responses to strings
            }
            
            logger.info(f"Connection params: host={pool_params['host']}, port={pool_params['port']}, db={pool_params['db']}")
            
            # Handle SSL configuration for Redis 5.x
            # In Redis 5.x, SSL is configured via connection_class, not a boolean parameter
            # Convert string 'true'/'false' to boolean
            use_ssl = self.config.get('ssl', False)
            if isinstance(use_ssl, str):
                use_ssl = use_ssl.lower() in ('true', '1', 'yes')
            
            logger.info(f"SSL/TLS: {use_ssl}")
            
            if use_ssl:
                # Import SSL connection class only if needed
                from redis.asyncio.connection import SSLConnection
                pool_params['connection_class'] = SSLConnection
                # Add SSL cert requirements if specified
                if self.config.get('ssl_cert_reqs'):
                    import ssl
                    pool_params['ssl_cert_reqs'] = getattr(ssl, self.config['ssl_cert_reqs'], ssl.CERT_REQUIRED)
                if self.config.get('ssl_ca_certs'):
                    pool_params['ssl_ca_certs'] = self.config['ssl_ca_certs']
                
                logger.info("✅ Redis SSL/TLS connection class configured")
            
            # Create connection pool
            logger.info("Creating connection pool...")
            self._connection_pool = redis.ConnectionPool(**pool_params)
            
            # Create Redis client
            logger.info("Creating Redis client...")
            self._redis_client = redis.Redis(connection_pool=self._connection_pool)
            
            # Test connection
            logger.info("Testing connection with PING...")
            await self._redis_client.ping()
            
            self._connection = self._redis_client
            self._is_connected = True
            self._use_rest_api = False
            
            logger.info(f"✅ Redis direct connection established to {self.config['host']}:{self.config['port']}")
            logger.info("=" * 70)
            return self._redis_client
            
        except Exception as e:
            self._connection = None
            self._is_connected = False
            logger.error(f"❌ Direct Redis connection failed: {type(e).__name__}: {e}")
            logger.error(f"Error details: {str(e)}")
            logger.error("=" * 70)
            raise ConnectionError(f"Redis connection failed: {e}")
    
    async def disconnect(self) -> None:
        """Close Redis connection."""
        if self._redis_client:
            try:
                await self._redis_client.aclose()
                logger.info("Redis connection closed")
            except Exception as e:
                logger.warning(f"Error closing Redis connection: {e}")
            finally:
                self._redis_client = None
        
        if self._connection_pool:
            try:
                await self._connection_pool.aclose()
            except Exception as e:
                logger.warning(f"Error closing Redis connection pool: {e}")
            finally:
                self._connection_pool = None
        
        self._connection = None
        self._is_connected = False
    
    def is_healthy(self) -> bool:
        """Check if Redis connection is healthy."""
        if not self._redis_client:
            return False
        
        try:
            # This is a sync check - for async health check, use async_is_healthy()
            return True  # Basic check - connection exists
        except Exception:
            return False
    
    async def async_is_healthy(self) -> bool:
        """Async health check for Redis connection."""
        if not self._redis_client:
            return False
        
        try:
            await self._redis_client.ping()
            return True
        except Exception:
            return False
    
    # Redis-specific convenience methods
    
    async def get(self, key: str) -> Optional[str]:
        """Get value by key."""
        await self.ensure_connected()
        return await self._redis_client.get(key)
    
    async def set(self, key: str, value: Any, ex: Optional[int] = None) -> bool:
        """Set key-value pair with optional expiration."""
        await self.ensure_connected()
        return await self._redis_client.set(key, value, ex=ex)
    
    async def delete(self, *keys: str) -> int:
        """Delete keys."""
        await self.ensure_connected()
        return await self._redis_client.delete(*keys)
    
    async def exists(self, *keys: str) -> int:
        """Check if keys exist."""
        await self.ensure_connected()
        return await self._redis_client.exists(*keys)
    
    async def expire(self, key: str, seconds: int) -> bool:
        """Set expiration for key."""
        await self.ensure_connected()
        return await self._redis_client.expire(key, seconds)
    
    async def hget(self, name: str, key: str) -> Optional[str]:
        """Get hash field value."""
        await self.ensure_connected()
        return await self._redis_client.hget(name, key)
    
    async def hset(self, name: str, key: str, value: Any) -> int:
        """Set hash field value."""
        await self.ensure_connected()
        return await self._redis_client.hset(name, key, value)
    
    async def lpush(self, name: str, *values: Any) -> int:
        """Push values to list (left side)."""
        await self.ensure_connected()
        return await self._redis_client.lpush(name, *values)
    
    async def rpop(self, name: str) -> Optional[str]:
        """Pop value from list (right side)."""
        await self.ensure_connected()
        return await self._redis_client.rpop(name)
    
    async def sadd(self, name: str, *values: Any) -> int:
        """Add values to set."""
        await self.ensure_connected()
        return await self._redis_client.sadd(name, *values)
    
    async def smembers(self, name: str) -> set:
        """Get all members of set."""
        await self.ensure_connected()
        return await self._redis_client.smembers(name)
    
    async def srem(self, name: str, *values: Any) -> int:
        """Remove values from set."""
        await self.ensure_connected()
        return await self._redis_client.srem(name, *values)
    
    async def ttl(self, key: str) -> int:
        """Get time-to-live for key in seconds."""
        await self.ensure_connected()
        return await self._redis_client.ttl(key)
    
    async def incr(self, key: str, amount: int = 1) -> int:
        """Increment key by amount."""
        await self.ensure_connected()
        return await self._redis_client.incrby(key, amount)
    
    async def scan(self, cursor: int = 0, match: Optional[str] = None, count: int = 10) -> tuple:
        """Scan keys matching pattern."""
        await self.ensure_connected()
        return await self._redis_client.scan(cursor=cursor, match=match, count=count)
    
    def get_connection_stats(self) -> dict:
        """Get Redis connection statistics."""
        if not self._connection_pool:
            return {'status': 'not_connected'}
        
        return {
            'status': 'connected',
            'max_connections': self._connection_pool.max_connections,
            'created_connections': self._connection_pool.created_connections,
            'available_connections': len(self._connection_pool._available_connections),
            'in_use_connections': len(self._connection_pool._in_use_connections)
        }