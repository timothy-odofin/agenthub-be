"""
Abstract base class for all connection managers.

This module provides a unified interface for managing connections to databases,
vector stores, and external services with proper configuration validation.
"""

from abc import ABC, abstractmethod
from typing import Any, Optional, Dict, Literal
from src.app.core.utils.logger import get_logger
from src.app.core.config.framework.settings import settings

logger = get_logger(__name__)

# Type hint for valid configuration categories
ConfigCategory = Literal['db', 'external', 'vector']


class BaseConnectionManager(ABC):
    """Abstract base class for all connection managers."""
    
    def __init__(self):
        """
        Initialize the connection manager with configuration from settings.
        
        Uses template method pattern - child defines category and connection name,
        base class retrieves configuration from settings and validates it.
        """
        # Get category and connection name from concrete implementation
        category = self.get_config_category()
        connection_name = self.get_connection_name()
        
        # Get configuration directly from settings using dot notation
        # e.g., settings.db for 'db' category, settings.external for 'external'
        config_section = getattr(settings, category)
        # Access specific connection config (e.g., redis, postgresql, jira)
        self.config = getattr(config_section, connection_name, None)
        
        if self.config is None:
            raise ValueError(
                f"Configuration not found for {category}.{connection_name}. "
                f"Check application-{category}.yaml has '{connection_name}' section"
            )
        
        # Initialize connection state
        self._connection: Optional[Any] = None
        self._is_connected: bool = False
        
        # Validate configuration early to fail fast
        self.validate_config()
        
        logger.info(
            f"Initialized {self.__class__.__name__}",
            extra={
                "category": category,
                "connection_name": connection_name,
                "config_keys": list(self._get_config_dict().keys()) if hasattr(self.config, '_data') else []
            }
        )
    
    def _get_config_dict(self) -> Dict[str, Any]:
        """
        Convert config to dictionary for inspection/validation.
        
        Returns:
            Dictionary representation of config
        """
        from src.app.core.config.utils.config_converter import dynamic_config_to_dict
        return dynamic_config_to_dict(self.config)
    
    @abstractmethod
    def get_config_category(self) -> ConfigCategory:
        """
        Return the configuration category for this connection.
        
        Returns:
            str: One of 'db', 'external', 'vector'
            
        Example:
            def get_config_category(self) -> str:
                return "db"
        """
        pass
    
    @abstractmethod
    def get_connection_name(self) -> str:
        """
        Return the connection name within its category.
        
        Returns:
            str: The connection identifier (e.g., 'redis', 'postgresql', 'jira')
            
        Example:
            def get_connection_name(self) -> str:
                return "redis"
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
