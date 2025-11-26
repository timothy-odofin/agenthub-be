"""
Registry for connection managers.

Provides a centralized registry for discovering and managing different
types of connection managers using the decorator pattern.
"""

from typing import Dict, Type, List, Any, TYPE_CHECKING
from app.core.enums import ConnectionType
from app.core.utils.logger import get_logger

if TYPE_CHECKING:
    from .base_connection_manager import BaseConnectionManager

logger = get_logger(__name__)


class ConnectionRegistry:
    """Registry for connection manager classes."""
    
    _registry: Dict[ConnectionType, Type['BaseConnectionManager']] = {}
    
    @classmethod
    def register(cls, connection_type: ConnectionType):
        """
        Decorator to register a connection manager class.
        
        Args:
            connection_type: The type of connection this manager handles
            
        Returns:
            The decorator function
        """
        def decorator(connection_manager_class):
            cls._registry[connection_type] = connection_manager_class
            logger.info(f"Registered connection manager: {connection_type} -> {connection_manager_class.__name__}")
            return connection_manager_class
        return decorator
    
    @classmethod
    def get_connection_manager_class(cls, connection_type: ConnectionType) -> Type['BaseConnectionManager']:
        """
        Get the connection manager class for a specific connection type.
        
        Args:
            connection_type: The connection type
            
        Returns:
            The connection manager class
            
        Raises:
            KeyError: If connection type is not registered
        """
        if connection_type not in cls._registry:
            available = list(cls._registry.keys())
            raise KeyError(f"Connection type '{connection_type}' not registered. Available: {available}")
        
        return cls._registry[connection_type]
    
    @classmethod
    def is_connection_registered(cls, connection_type: ConnectionType) -> bool:
        """
        Check if a connection type is registered.
        
        Args:
            connection_type: The connection type to check
            
        Returns:
            bool: True if registered, False otherwise
        """
        return connection_type in cls._registry
    
    @classmethod
    def list_connections(cls) -> List[ConnectionType]:
        """
        List all registered connection types.
        
        Returns:
            List of registered connection types
        """
        return list(cls._registry.keys())
    
    @classmethod
    def get_registry_info(cls) -> Dict[str, Any]:
        """
        Get information about the registry.
        
        Returns:
            Dict with registry statistics and registered connections
        """
        return {
            'total_registered': len(cls._registry),
            'connection_types': [conn_type.value for conn_type in cls._registry.keys()],
            'managers': [manager.__name__ for manager in cls._registry.values()]
        }
