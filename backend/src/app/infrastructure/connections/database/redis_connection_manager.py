"""
Redis connection manager implementation.

Provides connection management for Redis cache with proper
configuration validation and health checking.
"""

from typing import Any, Optional
import ssl
import redis.asyncio as redis
from redis.asyncio import Redis, ConnectionPool
from redis.asyncio.connection import SSLConnection
from redis.exceptions import ConnectionError as RedisConnectionError, TimeoutError

from app.infrastructure.connections.base import AsyncBaseConnectionManager, ConnectionRegistry, ConnectionType
from app.core.utils.logger import get_logger

logger = get_logger(__name__)


@ConnectionRegistry.register(ConnectionType.REDIS)
class RedisConnectionManager(AsyncBaseConnectionManager):
    """Redis connection manager implementation."""
    
    def __init__(self):
        super().__init__()
        self._connection_pool: Optional[ConnectionPool] = None
        self._redis_client: Optional[Redis] = None
    
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
        """Establish Redis connection."""
        if self._redis_client:
            try:
                await self._redis_client.ping()
                return self._redis_client
            except Exception:
                # Connection might be stale, recreate
                await self.disconnect()
        
        try:
            # Build connection pool parameters
            pool_params = {
                'host': self.config['host'],
                'port': self.config['port'],
                'db': self.config.get('db', 0),
                'password': self.config.get('password'),
                'max_connections': self.config.get('connection_pool_size', 10),
                'socket_timeout': self.config.get('socket_timeout', 5),
                'socket_connect_timeout': self.config.get('socket_connect_timeout', 5),
                'health_check_interval': self.config.get('health_check_interval', 30),
                'retry_on_timeout': True,
                'decode_responses': True
            }
            
            # Handle SSL configuration (simplified for Hugging Face compatibility)
            use_ssl = self.config.get('ssl', False)
            if isinstance(use_ssl, str):
                use_ssl = use_ssl.lower() in ('true', '1', 'yes')
            
            if use_ssl:
                pool_params['connection_class'] = SSLConnection
                # Don't set ssl_cert_reqs in pool_params - let it use defaults
                # Allow custom SSL cert requirements if specified
                if self.config.get('ssl_ca_certs'):
                    pool_params['ssl_ca_certs'] = self.config['ssl_ca_certs']
            
            # Create connection pool
            self._connection_pool = redis.ConnectionPool(**pool_params)
            
            # Create Redis client
            self._redis_client = redis.Redis(connection_pool=self._connection_pool)
            
            # Test connection
            await self._redis_client.ping()
            
            self._connection = self._redis_client
            self._is_connected = True
            
            logger.info(f"Redis connection established to {self.config['host']}:{self.config['port']}")
            return self._redis_client
            
        except Exception as e:
            self._connection = None
            self._is_connected = False
            logger.error(f"Redis connection failed: {type(e).__name__}: {e}")
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
        
        stats = {
            'status': 'connected',
            'max_connections': self._connection_pool.max_connections,
        }
        
        # Try to get additional stats if available (API may vary by version)
        try:
            if hasattr(self._connection_pool, 'created_connections'):
                stats['created_connections'] = self._connection_pool.created_connections
            if hasattr(self._connection_pool, '_available_connections'):
                stats['available_connections'] = len(self._connection_pool._available_connections)
            if hasattr(self._connection_pool, '_in_use_connections'):
                stats['in_use_connections'] = len(self._connection_pool._in_use_connections)
        except Exception:
            pass
        
        return stats