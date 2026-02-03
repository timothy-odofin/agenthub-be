"""
Upstash Redis REST API client for serverless environments.

This provides a Redis-compatible interface using Upstash's REST API,
which is more reliable in serverless/containerized environments like
Hugging Face Spaces.
"""

from typing import Any, Optional, Union
import httpx
import json
from app.core.utils.logger import get_logger

logger = get_logger(__name__)


class UpstashRestClient:
    """
    Redis client that uses Upstash REST API instead of direct Redis protocol.
    
    This is more reliable for serverless environments where direct TCP connections
    may be blocked or unstable.
    """
    
    def __init__(
        self,
        rest_url: str,
        rest_token: str,
        timeout: int = 10
    ):
        """
        Initialize Upstash REST client.
        
        Args:
            rest_url: Upstash REST URL (e.g., https://xxx.upstash.io)
            rest_token: Upstash REST token
            timeout: Request timeout in seconds
        """
        self.rest_url = rest_url.rstrip('/')
        self.rest_token = rest_token
        self.timeout = timeout
        self._client = httpx.AsyncClient(
            headers={
                "Authorization": f"Bearer {rest_token}",
                "Content-Type": "application/json"
            },
            timeout=timeout
        )
        logger.info(f"Initialized Upstash REST client for {rest_url}")
    
    async def _execute(self, command: list) -> Any:
        """
        Execute a Redis command via REST API.
        
        Args:
            command: Redis command as list (e.g., ['GET', 'mykey'])
            
        Returns:
            Command result
        """
        try:
            response = await self._client.post(
                self.rest_url,
                json=command
            )
            response.raise_for_status()
            
            result = response.json()
            
            # Upstash REST API returns: {"result": <value>}
            if isinstance(result, dict) and "result" in result:
                return result["result"]
            return result
            
        except httpx.HTTPStatusError as e:
            logger.error(f"Upstash REST API HTTP error: {e.response.status_code} - {e.response.text}")
            raise
        except Exception as e:
            logger.error(f"Upstash REST API error: {e}")
            raise
    
    async def ping(self) -> bool:
        """Test connection with PING command."""
        result = await self._execute(["PING"])
        return result == "PONG"
    
    async def get(self, key: str) -> Optional[str]:
        """Get value by key."""
        return await self._execute(["GET", key])
    
    async def set(
        self,
        key: str,
        value: str,
        ex: Optional[int] = None,
        px: Optional[int] = None,
        nx: bool = False,
        xx: bool = False
    ) -> bool:
        """
        Set key to value with optional expiration.
        
        Args:
            key: Key name
            value: Value to set
            ex: Expiration in seconds
            px: Expiration in milliseconds
            nx: Only set if key doesn't exist
            xx: Only set if key exists
        """
        command = ["SET", key, value]
        
        if ex is not None:
            command.extend(["EX", str(ex)])
        if px is not None:
            command.extend(["PX", str(px)])
        if nx:
            command.append("NX")
        if xx:
            command.append("XX")
        
        result = await self._execute(command)
        return result == "OK" or result is True
    
    async def delete(self, *keys: str) -> int:
        """Delete one or more keys."""
        if not keys:
            return 0
        return await self._execute(["DEL", *keys])
    
    async def exists(self, *keys: str) -> int:
        """Check if keys exist."""
        if not keys:
            return 0
        return await self._execute(["EXISTS", *keys])
    
    async def expire(self, key: str, seconds: int) -> bool:
        """Set key expiration in seconds."""
        result = await self._execute(["EXPIRE", key, str(seconds)])
        return result == 1
    
    async def ttl(self, key: str) -> int:
        """Get remaining TTL in seconds (-1 if no expiry, -2 if doesn't exist)."""
        return await self._execute(["TTL", key])
    
    async def incr(self, key: str) -> int:
        """Increment key value by 1."""
        return await self._execute(["INCR", key])
    
    async def decr(self, key: str) -> int:
        """Decrement key value by 1."""
        return await self._execute(["DECR", key])
    
    async def hget(self, key: str, field: str) -> Optional[str]:
        """Get hash field value."""
        return await self._execute(["HGET", key, field])
    
    async def hset(self, key: str, field: str, value: str) -> int:
        """Set hash field value."""
        return await self._execute(["HSET", key, field, value])
    
    async def hgetall(self, key: str) -> dict:
        """Get all hash fields and values."""
        result = await self._execute(["HGETALL", key])
        # Convert flat list [k1, v1, k2, v2] to dict
        if isinstance(result, list):
            return dict(zip(result[::2], result[1::2]))
        return result or {}
    
    async def lpush(self, key: str, *values: str) -> int:
        """Push values to list head."""
        return await self._execute(["LPUSH", key, *values])
    
    async def rpush(self, key: str, *values: str) -> int:
        """Push values to list tail."""
        return await self._execute(["RPUSH", key, *values])
    
    async def lrange(self, key: str, start: int, stop: int) -> list:
        """Get list elements in range."""
        return await self._execute(["LRANGE", key, str(start), str(stop)])
    
    async def sadd(self, key: str, *members: str) -> int:
        """Add members to set."""
        return await self._execute(["SADD", key, *members])
    
    async def smembers(self, key: str) -> set:
        """Get all set members."""
        result = await self._execute(["SMEMBERS", key])
        return set(result) if result else set()
    
    async def zadd(self, key: str, mapping: dict) -> int:
        """Add scored members to sorted set."""
        command = ["ZADD", key]
        for member, score in mapping.items():
            command.extend([str(score), member])
        return await self._execute(command)
    
    async def zrange(
        self,
        key: str,
        start: int,
        stop: int,
        withscores: bool = False
    ) -> list:
        """Get sorted set members in range."""
        command = ["ZRANGE", key, str(start), str(stop)]
        if withscores:
            command.append("WITHSCORES")
        return await self._execute(command)
    
    async def flushdb(self) -> bool:
        """Delete all keys in current database."""
        result = await self._execute(["FLUSHDB"])
        return result == "OK"
    
    async def close(self):
        """Close HTTP client."""
        await self._client.aclose()
    
    async def aclose(self):
        """Alias for close() to match redis.asyncio interface."""
        await self.close()
