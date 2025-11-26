"""
Factory for creating connection manager instances.

Provides a centralized factory for creating and managing different
types of connection managers using the registry pattern.
"""

from typing import Optional, List
from app.connections.base.connection_registry import ConnectionType, ConnectionRegistry
from app.connections.base.base_connection_manager import BaseConnectionManager
from app.core.utils.logger import get_logger

logger = get_logger(__name__)


class ConnectionFactory:
    """Factory class for creating connection manager instances."""

    _instance: Optional['ConnectionFactory'] = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    @staticmethod
    def get_connection_manager(connection_type: ConnectionType) -> BaseConnectionManager:
        """
        Get a connection manager instance for the specified connection type.
        
        Args:
            connection_type: The type of connection manager to create
            
        Returns:
            Connection manager instance (not connected)
            
        Raises:
            ValueError: If connection type is not available or not registered
        """
        # Validate connection type is registered
        if not ConnectionRegistry.is_connection_registered(connection_type):
            available = ConnectionRegistry.list_connections()
            raise ValueError(f"Connection type '{connection_type}' not available. Available: {available}")
        
        # Get connection manager class and create instance
        manager_class = ConnectionRegistry.get_connection_manager_class(connection_type)
        connection_manager = manager_class()  # Manager self-configures from ConnectionConfig
        
        logger.info(f"Created connection manager: {connection_type}")
        return connection_manager

    @staticmethod
    def list_available_connections() -> List[ConnectionType]:
        """List all available connection types."""
        return ConnectionRegistry.list_connections()
    
    @staticmethod
    def is_connection_available(connection_type: ConnectionType) -> bool:
        """
        Check if a connection type is available and properly configured.
        
        Args:
            connection_type: The connection type to check
            
        Returns:
            bool: True if available and configured, False otherwise
        """
        try:
            # Import here to avoid circular imports
            from app.core.config.connection_config import connection_config
            
            # Check if registered and has valid config
            is_registered = ConnectionRegistry.is_connection_registered(connection_type)
            has_config = connection_config.validate_connection_config(connection_type.value)
            
            return is_registered and has_config
        except Exception as e:
            logger.warning(f"Error checking connection availability for {connection_type}: {e}")
            return False
    
    @staticmethod
    def get_connection_status() -> dict:
        """
        Get status of all registered connection types.
        
        Returns:
            Dict with connection status information
        """
        status = {
            'total_registered': 0,
            'available_connections': [],
            'unavailable_connections': [],
            'connection_details': {}
        }
        
        registered_connections = ConnectionRegistry.list_connections()
        status['total_registered'] = len(registered_connections)
        
        for connection_type in registered_connections:
            is_available = ConnectionFactory.is_connection_available(connection_type)
            
            if is_available:
                status['available_connections'].append(connection_type.value)
            else:
                status['unavailable_connections'].append(connection_type.value)
            
            status['connection_details'][connection_type.value] = {
                'available': is_available,
                'registered': True,
                'manager_class': ConnectionRegistry.get_connection_manager_class(connection_type).__name__
            }
        
        return status
