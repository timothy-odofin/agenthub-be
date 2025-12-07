"""
PostgreSQL connection manager implementation.

Provides connection management for PostgreSQL databases with proper
configuration validation and health checking.
"""

import asyncio
from typing import Any, Optional
import asyncpg
from asyncpg import Connection, Pool

from app.connections.base import BaseConnectionManager, ConnectionRegistry, ConnectionType
from app.core.utils.logger import get_logger

logger = get_logger(__name__)


@ConnectionRegistry.register(ConnectionType.POSTGRES)
class PostgresConnectionManager(BaseConnectionManager):
    """PostgreSQL connection manager implementation."""
    
    def __init__(self):
        super().__init__()
        self._connection_pool: Optional[Pool] = None
    
    def get_connection_name(self) -> str:
        """Return the configuration name for PostgreSQL."""
        return ConnectionType.POSTGRES.value
    
    def get_config_source(self) -> Any:
        """Return the database configuration source."""
        from app.core.config.providers.database import database_config
        return database_config
    
    def validate_config(self) -> None:
        """Validate PostgreSQL configuration."""
        required_fields = ['host', 'port', 'database', 'username', 'password']
        
        for field in required_fields:
            if not self.config.get(field):
                raise ValueError(f"PostgreSQL connection requires '{field}' in configuration")
        
        # Validate port is valid
        port = self.config.get('port')
        if not isinstance(port, int) or port <= 0 or port > 65535:
            raise ValueError(f"PostgreSQL port must be a valid port number (1-65535), got: {port}")
        
        # Validate pool settings
        pool_size = self.config.get('pool_size', 10)
        if not isinstance(pool_size, int) or pool_size <= 0:
            raise ValueError(f"PostgreSQL pool_size must be a positive integer, got: {pool_size}")
        
        logger.info("PostgreSQL connection configuration validated successfully")
    
    async def connect(self) -> Pool:
        """Establish PostgreSQL connection pool."""
        if self._connection_pool and not self._connection_pool.is_closing():
            return self._connection_pool
        
        try:
            # Build connection string
            connection_string = (
                f"postgresql://{self.config['username']}:{self.config['password']}"
                f"@{self.config['host']}:{self.config['port']}/{self.config['database']}"
            )
            
            # Add SSL mode if specified
            if self.config.get('ssl_mode'):
                connection_string += f"?sslmode={self.config['ssl_mode']}"
            
            # Create connection pool
            self._connection_pool = await asyncpg.create_pool(
                connection_string,
                min_size=1,
                max_size=self.config.get('pool_size', 10),
                max_inactive_connection_lifetime=300,
                timeout=self.config.get('connection_timeout', 30),
                command_timeout=60
            )
            
            # Test the connection
            async with self._connection_pool.acquire() as conn:
                await conn.execute('SELECT 1')
            
            self._connection = self._connection_pool
            self._is_connected = True
            
            logger.info(f"PostgreSQL connection pool established to {self.config['host']}:{self.config['port']}")
            return self._connection_pool
            
        except Exception as e:
            self._connection = None
            self._is_connected = False
            logger.error(f"Failed to connect to PostgreSQL: {e}")
            raise ConnectionError(f"PostgreSQL connection failed: {e}")
    
    async def disconnect(self) -> None:
        """Close PostgreSQL connection pool."""
        if self._connection_pool:
            try:
                await self._connection_pool.close()
                logger.info("PostgreSQL connection pool closed")
            except Exception as e:
                logger.warning(f"Error closing PostgreSQL connection pool: {e}")
            finally:
                self._connection_pool = None
                self._connection = None
                self._is_connected = False
    
    def is_healthy(self) -> bool:
        """Check if PostgreSQL connection is healthy."""
        if not self._connection_pool or self._connection_pool.is_closing():
            return False
        
        try:
            # Check if pool has available connections
            return self._connection_pool.get_size() > 0
        except Exception:
            return False
    
    async def execute_query(self, query: str, *args) -> Any:
        """
        Execute a query using the connection pool.
        
        Args:
            query: SQL query to execute
            *args: Query parameters
            
        Returns:
            Query result
        """
        await self.ensure_connected()
        
        async with self._connection_pool.acquire() as conn:
            return await conn.fetch(query, *args)
    
    async def execute_command(self, command: str, *args) -> str:
        """
        Execute a command (INSERT, UPDATE, DELETE) using the connection pool.
        
        Args:
            command: SQL command to execute
            *args: Command parameters
            
        Returns:
            Command status
        """
        await self.ensure_connected()
        
        async with self._connection_pool.acquire() as conn:
            return await conn.execute(command, *args)
    
    async def get_connection(self) -> Connection:
        """
        Get a single connection from the pool.
        
        Returns:
            Database connection (must be released back to pool)
        """
        await self.ensure_connected()
        return await self._connection_pool.acquire()
    
    def get_pool_stats(self) -> dict:
        """
        Get connection pool statistics.
        
        Returns:
            Dict with pool statistics
        """
        if not self._connection_pool:
            return {'status': 'not_connected'}
        
        return {
            'status': 'connected',
            'size': self._connection_pool.get_size(),
            'max_size': self._connection_pool.get_max_size(),
            'min_size': self._connection_pool.get_min_size(),
            'idle_connections': self._connection_pool.get_idle_size(),
            'is_closing': self._connection_pool.is_closing()
        }