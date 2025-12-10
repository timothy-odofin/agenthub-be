"""
Abstract base class for all connection managers.

This module provides a unified interface for managing connections to databases,
vector stores, and external services with proper configuration validation.
"""

from abc import ABC, abstractmethod
from typing import Any, Optional, Dict
from app.core.utils.logger import get_logger

logger = get_logger(__name__)


class BaseConnectionManager(ABC):
    """Abstract base class for all connection managers."""
    
    def __init__(self):
        """
        Initialize the connection manager with configuration.
        
        Uses template method pattern - child defines connection name,
        base class retrieves configuration and validates it.
        """
        # Get connection-specific configuration
        connection_name = self.get_connection_name()
        config_source = self._get_config_source(connection_name)
        self.config = config_source.get_connection_config(connection_name)
        
        # Initialize connection state
        self._connection: Optional[Any] = None
        self._is_connected: bool = False
        
        # Validate configuration early to fail fast
        self.validate_config()
        
        logger.info(f"Initialized {self.__class__.__name__} connection manager")
    
    def _get_config_source(self, connection_name: str) -> Any:
        """
        Get the appropriate configuration source for a connection.
        
        Uses the config source registry to automatically determine
        the correct config source based on decorator registrations.
        
        Args:
            connection_name: The name of the connection
            
        Returns:
            The appropriate configuration source
        """
        from app.core.config.framework.registry import ConfigSourceRegistry
        
       
        return ConfigSourceRegistry.get_config_source(connection_name)
       
    @abstractmethod
    def get_connection_name(self) -> str:
        """
        Return the configuration name/key for this connection manager.
        
        Returns:
            str: The configuration key to retrieve from the config source
        """
        pass
    
    @abstractmethod
    def validate_config(self) -> None:
        """
        Validate the connection configuration.
        
        This method should check that all required configuration parameters
        are present and valid for the specific connection type.
        
        Raises:
            ValueError: If configuration is invalid or missing required parameters
        """
        pass
    
    @abstractmethod
    def connect(self) -> Any:
        """
        Establish the connection.
        
        Returns:
            The connection object/client
            
        Raises:
            ConnectionError: If connection cannot be established
        """
        pass
    
    @abstractmethod
    def disconnect(self) -> None:
        """
        Close the connection and cleanup resources.
        """
        pass
    
    @abstractmethod
    def is_healthy(self) -> bool:
        """
        Check if the connection is healthy and operational.
        
        Returns:
            bool: True if connection is healthy, False otherwise
        """
        pass
    
    # Concrete methods
    
    @property
    def is_connected(self) -> bool:
        """Check if connection is established."""
        return self._is_connected
    
    @property
    def connection(self) -> Any:
        """Get the connection object."""
        return self._connection
    
    def ensure_connected(self) -> Any:
        """
        Ensure connection is established, connect if needed.
        
        Returns:
            The connection object
        """
        if not self.is_connected or not self.is_healthy():
            self.connect()
        return self._connection
    
    def reconnect(self) -> Any:
        """
        Force reconnection by disconnecting and connecting again.
        
        Returns:
            The new connection object
        """
        if self.is_connected:
            self.disconnect()
        return self.connect()
    
    def get_connection_info(self) -> Dict[str, Any]:
        """
        Get connection information for debugging/monitoring.
        
        Returns:
            Dict with connection status and basic info
        """
        return {
            'connection_type': self.__class__.__name__,
            'connection_name': self.get_connection_name(),
            'is_connected': self.is_connected,
            'is_healthy': self.is_healthy() if self.is_connected else None,
            'config_keys': list(self.config.keys()) if self.config else []
        }
    
    def __enter__(self):
        """Sync context manager entry."""
        self.ensure_connected()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Sync context manager exit."""
        self.disconnect()
