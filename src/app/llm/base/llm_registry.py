"""
Registry for managing LLM providers.
"""

from typing import Dict, Type, Optional
from app.core.constants import LLMProvider
from app.core.utils.logger import get_logger

logger = get_logger(__name__)


class LLMRegistry:
    """Central registry that keeps track of all available LLM providers."""
    _registry: Dict[str, Type] = {}
    _providers_imported: bool = False

    @classmethod
    def register(cls, provider: LLMProvider):
        """Decorator to register a LLM provider class under a given name."""
        def decorator(provider_cls):
            cls._registry[provider] = provider_cls
            logger.debug(f"Registered LLM provider: {provider}")
            return provider_cls
        return decorator

    @classmethod
    def _ensure_providers_imported(cls):
        """Ensure all providers are imported for registration."""
        if cls._providers_imported:
            return
            
        # Import providers module to trigger registration
        import app.llm.providers
        cls._providers_imported = True

    @classmethod
    def get_provider_class(cls, provider: LLMProvider) -> Optional[Type]:
        """Get a registered LLM provider class by name."""
        # Import providers to ensure registration
        cls._ensure_providers_imported()
        
        if provider not in cls._registry:
            available = list(cls._registry.keys())
            raise ValueError(f"LLM provider '{provider}' not found in registry. Available: {available}")
        return cls._registry[provider]

    @classmethod
    def list_providers(cls) -> list[str]:
        """List all registered LLM providers."""
        # Import providers to ensure registration
        cls._ensure_providers_imported()
        return list(cls._registry.keys())
    
    @classmethod
    def is_provider_registered(cls, provider: LLMProvider) -> bool:
        """Check if a provider is registered."""
        # Import providers to ensure registration
        cls._ensure_providers_imported()
        return provider in cls._registry
