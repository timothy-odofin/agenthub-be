"""
Async base class for connection managers that require async operations.

This module provides an async interface for managing connections to databases
and services that have truly asynchronous clients.
"""

from abc import abstractmethod
from typing import Any
from .base_connection_manager import BaseConnectionManager
from app.core.utils.logger import get_logger

logger = get_logger(__name__)


class AsyncBaseConnectionManager(BaseConnectionManager):
    """Async base class for connection managers that need async operations."""
    
    @abstractmethod
    async def connect(self) -> Any:
        """
        Establish the connection asynchronously.
        
        Returns:
            The connection object/client
            
        Raises:
            ConnectionError: If connection cannot be established
        """
        pass
    
    @abstractmethod
    async def disconnect(self) -> None:
        """
        Close the connection and cleanup resources asynchronously.
        """
        pass
    
    # Override the sync methods from base to make them async
    async def ensure_connected(self) -> Any:
        """
        Ensure connection is established, connect if needed.
        
        Returns:
            The connection object
        """
        if not self.is_connected or not self.is_healthy():
            await self.connect()
        return self._connection
    
    async def reconnect(self) -> Any:
        """
        Force reconnection by disconnecting and connecting again.
        
        Returns:
            The new connection object
        """
        if self.is_connected:
            await self.disconnect()
        return await self.connect()
    
    async def __aenter__(self):
        """Async context manager entry."""
        await self.ensure_connected()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.disconnect()
    
    # Override sync context managers to prevent usage
    def __enter__(self):
        raise NotImplementedError(
            "Use async context manager: async with connection_manager:"
        )
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        raise NotImplementedError(
            "Use async context manager: async with connection_manager:"
        )
