"""
Utilities for converting DynamicConfig objects to standard Python data structures.

This module provides helpers for converting between DynamicConfig objects
and standard dictionaries/lists for integration with Pydantic models and other systems.
"""
from typing import Any


def dynamic_config_to_dict(config: Any) -> Any:
    """
    Convert DynamicConfig objects to standard Python dictionaries recursively.
    
    This utility handles nested structures including:
    - DynamicConfig objects → dictionaries
    - Lists containing DynamicConfig objects
    - Nested dictionaries with DynamicConfig values
    - Primitive values (returned as-is)
    
    Args:
        config: The configuration object to convert (DynamicConfig, dict, list, or primitive)
        
    Returns:
        Standard Python data structure (dict, list, or primitive value)
        
    Example:
        >>> from app.core.config.dynamic_config import DynamicConfig
        >>> config = DynamicConfig({'name': 'test', 'nested': DynamicConfig({'value': 42})})
        >>> result = dynamic_config_to_dict(config)
        >>> print(result)  # {'name': 'test', 'nested': {'value': 42}}
    """
    # Check if it's a DynamicConfig object by class name to avoid import issues
    if hasattr(config, '__class__') and config.__class__.__name__ == 'DynamicConfig':
        # DynamicConfig stores the original data in _data attribute
        if hasattr(config, '_data'):
            return dynamic_config_to_dict(config._data)
        else:
            # Fallback: extract non-private attributes
            result = {}
            for attr in dir(config):
                if not attr.startswith('_') and not callable(getattr(config, attr)):
                    value = getattr(config, attr)
                    result[attr] = dynamic_config_to_dict(value)
            return result
    
    elif isinstance(config, list):
        # Recursively convert list items
        return [dynamic_config_to_dict(item) for item in config]
    
    elif isinstance(config, dict):
        # Recursively convert dictionary values
        return {k: dynamic_config_to_dict(v) for k, v in config.items()}
    
    else:
        # Return primitive values (str, int, bool, None, etc.) as-is
        return config


def dict_to_pydantic_compatible(data: Any) -> Any:
    """
    Convert data structures to be compatible with Pydantic model validation.
    
    This is a specialized version of dynamic_config_to_dict that also handles
    additional conversions that might be needed for Pydantic compatibility.
    
    Args:
        data: The data to convert
        
    Returns:
        Pydantic-compatible data structure
    """
    # First convert any DynamicConfig objects
    converted = dynamic_config_to_dict(data)
    
    # Additional Pydantic-specific conversions can be added here
    # For example:
    # - Converting non-standard types to strings
    # - Handling special date/time formats
    # - Normalizing field names
    
    return converted


def extract_config_section(config: Any, section_path: str, default: Any = None) -> Any:
    """
    Extract a specific section from a configuration object using dot notation.
    
    Args:
        config: Configuration object (DynamicConfig, dict, etc.)
        section_path: Dot-separated path to the desired section (e.g., "database.postgres")
        default: Default value to return if section not found
        
    Returns:
        The requested configuration section or default value
        
    Example:
        >>> config = {'database': {'postgres': {'host': 'localhost'}}}
        >>> host = extract_config_section(config, 'database.postgres.host')
        >>> print(host)  # 'localhost'
    """
    # Convert to dict first if needed
    data = dynamic_config_to_dict(config)
    
    # Navigate through the path
    current = data
    for part in section_path.split('.'):
        if isinstance(current, dict) and part in current:
            current = current[part]
        else:
            return default
    
    return current
