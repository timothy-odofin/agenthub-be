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
    _auto_import_enabled: bool = True  # Allow disabling for tests

    @classmethod
    def register(cls, provider: LLMProvider):
        """Decorator to register a LLM provider class under a given name."""
        def decorator(provider_cls):
            cls._registry[provider] = provider_cls
            logger.debug(f"Registered LLM provider: {provider}")
            return provider_cls
        return decorator

    @classmethod
    def set_auto_import(cls, enabled: bool):
        """Control auto-import behavior for testing."""
        cls._auto_import_enabled = enabled

    @classmethod
    def reset_for_testing(cls):
        """Reset registry state for testing."""
        cls._registry.clear()
        cls._providers_imported = False
        cls._auto_import_enabled = True

    @classmethod
    def _ensure_providers_imported(cls):
        """Ensure all providers are imported for registration."""
        if cls._providers_imported or not cls._auto_import_enabled:
            return
            
        try:
            # Import providers module to trigger registration
            import app.infrastructure.llm.providers
            cls._providers_imported = True
        except ImportError:
            # Log the error but don't fail - providers might be registered manually
            pass

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
