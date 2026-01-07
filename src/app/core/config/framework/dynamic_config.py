"""
Dynamic configuration class that provides dot notation access to configuration data.
"""
import logging
from typing import Dict, Any

# Use standard logging to avoid circular import
logger = logging.getLogger(__name__)


class DynamicConfig:
    """
    Dynamic configuration class that converts dictionaries to objects with dot notation access.
    
    Example:
        config_data = {"database": {"host": "localhost", "port": 5432}}
        config = DynamicConfig(config_data)
        print(config.database.host)  # "localhost"
        print(config.database.port)  # 5432
    """
    
    def __init__(self, data: Dict[str, Any]):
        """
        Initialize dynamic configuration from dictionary data.
        
        Args:
            data: Dictionary containing configuration data
        """
        if isinstance(data, dict):
            self._data = data.copy() if data else {}
        else:
            # Handle non-dict data by wrapping it
            self._data = {'value': data} if data is not None else {}
        self._setup_attributes()
    
    def _setup_attributes(self):
        """Set up object attributes from configuration data."""
        for key, value in self._data.items():
            # Convert keys to valid Python attribute names
            attr_name = self._sanitize_key(key)
            
            if isinstance(value, dict):
                # Recursively create nested DynamicConfig objects
                setattr(self, attr_name, DynamicConfig(value))
            elif isinstance(value, list):
                # Handle lists that might contain dictionaries
                setattr(self, attr_name, self._process_list(value))
            else:
                # Set primitive values directly
                setattr(self, attr_name, value)
    
    def _process_list(self, items: list) -> list:
        """Process list items, converting dictionaries to DynamicConfig objects."""
        processed_items = []
        for item in items:
            if isinstance(item, dict):
                processed_items.append(DynamicConfig(item))
            else:
                processed_items.append(item)
        return processed_items
    
    def _sanitize_key(self, key: str) -> str:
        """
        Sanitize configuration keys to be valid Python attribute names.
        
        Args:
            key: Original key from configuration
            
        Returns:
            Sanitized key safe to use as Python attribute
        """
        # Replace invalid characters with underscores
        sanitized = key.replace('-', '_').replace('.', '_').replace(' ', '_')
        
        # Ensure it doesn't start with a number
        if sanitized and sanitized[0].isdigit():
            sanitized = f"_{sanitized}"
            
        # Handle reserved keywords
        if sanitized in ['class', 'def', 'return', 'if', 'else', 'for', 'while']:
            sanitized = f"{sanitized}_"
            
        return sanitized
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        Get a configuration value by key with optional default.
        
        Args:
            key: Configuration key (supports dot notation like "database.host")
            default: Default value if key is not found
            
        Returns:
            Configuration value or default
        """
        try:
            keys = key.split('.')
            current = self
            
            for k in keys:
                sanitized_k = self._sanitize_key(k)
                if hasattr(current, sanitized_k):
                    current = getattr(current, sanitized_k)
                else:
                    return default
                    
            return current
        except Exception:
            return default
    
    def has(self, key: str) -> bool:
        """
        Check if a configuration key exists.
        
        Args:
            key: Configuration key (supports dot notation)
            
        Returns:
            True if key exists, False otherwise
        """
        try:
            keys = key.split('.')
            current = self
            
            for k in keys:
                sanitized_k = self._sanitize_key(k)
                if hasattr(current, sanitized_k):
                    current = getattr(current, sanitized_k)
                else:
                    return False
                    
            return True
        except Exception:
            return False
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the configuration back to a dictionary.
        
        Returns:
            Dictionary representation of the configuration
        """
        return self._data.copy()
    
    def update(self, data: Dict[str, Any]):
        """
        Update configuration with new data.
        
        Args:
            data: New configuration data to merge
        """
        if data:
            self._data.update(data)
            # Clear existing attributes
            for attr in list(self.__dict__.keys()):
                if not attr.startswith('_'):
                    delattr(self, attr)
            # Recreate attributes with updated data
            self._setup_attributes()
    
    def __repr__(self) -> str:
        """String representation of the configuration."""
        return f"DynamicConfig({self._data})"
    
    def __str__(self) -> str:
        """Human-readable string representation."""
        return str(self._data)
    
    def __getitem__(self, key: str) -> Any:
        """Support dictionary-style access."""
        sanitized_key = self._sanitize_key(key)
        if hasattr(self, sanitized_key):
            return getattr(self, sanitized_key)
        raise KeyError(f"Configuration key '{key}' not found")
    
    def __contains__(self, key: str) -> bool:
        """Support 'in' operator."""
        return self.has(key)
