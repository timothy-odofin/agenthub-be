"""
Application-specific configurations.

Configuration classes for application-level settings and 
domain-specific configurations like LLM providers.
"""

from .app import app_config
from .llm import llm_config

__all__ = [
    'app_config',
    'llm_config'
]
