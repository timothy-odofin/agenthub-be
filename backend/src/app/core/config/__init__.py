"""
Configuration management package.

This package provides a unified configuration system using YAML-based settings.

The package is organized into:
- framework/: Core configuration framework (Settings, DynamicConfig, YamlLoader, etc.)
- utils/: Configuration utilities and helpers (config_converter, etc.)

Main exports:
- Settings: Singleton settings manager with profile-based configuration
- settings: Module-level settings instance
- DynamicConfig: Dynamic configuration object with dot-notation access
- YamlLoader: YAML file loader with validation

Usage:
    >>> from app.core.config import settings
    >>> 
    >>> # Access configuration via dot notation
    >>> db_host = settings.db.postgres.host
    >>> 
    >>> # Or use get_section with dot-path
    >>> db_host = settings.get_section('db.postgres.host')
    >>> 
    >>> # Convert to plain dictionary
    >>> config_dict = settings.to_dict()
"""

# Import from framework
from .framework import Settings, settings, DynamicConfig, YamlLoader

# Export main configuration system
__all__ = [
    'Settings',
    'settings',
    'DynamicConfig',
    'YamlLoader',
]
