"""
Configuration source registry using decorator pattern.

This module provides a clean decorator-based approach for registering
which configuration source should handle each connection type.
"""

from typing import Dict, Any, List, Optional
from abc import ABC, abstractmethod
from app.core.utils.single_ton import SingletonMeta


class SingletonABCMeta(type(ABC), SingletonMeta):
    """Metaclass that combines ABC and SingletonMeta functionality."""
    pass


class BaseConfigSource(ABC, metaclass=SingletonABCMeta):
    """Abstract base class for configuration sources."""
    
    @abstractmethod
    def get_connection_config(self, connection_name: str) -> dict:
        """Get configuration for a specific connection."""
        pass


class ConfigSourceRegistry:
    """Registry that maps connection names to their config source instances."""
    
    _connection_to_config: Dict[str, BaseConfigSource] = {}
    
    @classmethod
    def register_connections(cls, connection_names: List[str]):
        """
        Decorator to register which connections a config source handles.
        
        Usage:
            @ConfigSourceRegistry.register_connections(['postgres', 'redis'])
            class DatabaseConfig(BaseConfigSource):
                def get_connection_config(self, connection_name: str) -> dict:
                    # Implementation
        
        Args:
            connection_names: List of connection names this config source handles
            
        Returns:
            Decorator function
        """
        def decorator(config_class):
            # Instantiate the config source
            config_instance = config_class()
            
            # Register each connection name to this config source
            for connection_name in connection_names:
                cls._connection_to_config[connection_name] = config_instance
            
            return config_class
        
        return decorator
    
    @classmethod
    def get_config_source(cls, connection_name: str) -> BaseConfigSource:
        """
        Get the config source for a connection name.
        
        Args:
            connection_name: The connection name to look up
            
        Returns:
            The config source instance
            
        Raises:
            ValueError: If connection name is not registered
        """
        config_source = cls._connection_to_config.get(connection_name)
        if not config_source:
            available_connections = list(cls._connection_to_config.keys())
            raise ValueError(
                f"No config source registered for connection '{connection_name}'. "
                f"Available connections: {available_connections}"
            )
        
        return config_source
    
    @classmethod
    def get_registered_connections(cls) -> List[str]:
        """Get list of all registered connection names."""
        return list(cls._connection_to_config.keys())
    
    @classmethod
    def get_registry_info(cls) -> Dict[str, Any]:
        """Get information about registered connections and their config sources."""
        registry_info = {}
        for connection_name, config_source in cls._connection_to_config.items():
            config_class_name = config_source.__class__.__name__
            if config_class_name not in registry_info:
                registry_info[config_class_name] = []
            registry_info[config_class_name].append(connection_name)
        
        return registry_info


# Create a convenience decorator function for cleaner imports
register_connections = ConfigSourceRegistry.register_connections
