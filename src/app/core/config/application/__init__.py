"""
Application-specific configurations.

Configuration classes for application-level settings and 
domain-specific configurations like LLM providers.
"""

from .app import AppConfig
from .llm import llm_config

# Create lazy loader for app_config to avoid circular imports
def get_app_config():
    """Get the app config instance (lazy loaded)."""
    return AppConfig()

__all__ = [
    'AppConfig',
    'get_app_config', 
    'llm_config'
]
