"""
Factory for creating LLM instances.
"""

from typing import Optional
from app.core.constants import LLMProvider
from app.core.utils.logger import get_logger
from app.llm.base.base_llm_provider import BaseLLMProvider
from app.llm.base.llm_registry import LLMRegistry

logger = get_logger(__name__)


class LLMFactory:
    """Factory class for creating LLM instances."""

    _instance: Optional['LLMFactory'] = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    @staticmethod
    def get_llm(provider: LLMProvider) -> BaseLLMProvider:
        """
        Get an LLM instance for the specified provider.
        
        Args:
            provider: LLM provider to use (required)
            
        Returns:
            LLM provider instance (not initialized)
            
        Raises:
            ValueError: If provider is not available or not registered
        """
        # Validate provider is registered
        if not LLMRegistry.is_provider_registered(provider):
            available = LLMRegistry.list_providers()
            raise ValueError(f"LLM provider '{provider}' not available. Available: {available}")
        
        # Get provider class and create instance
        provider_class = LLMRegistry.get_provider_class(provider)
        llm_instance = provider_class()  # Provider self-configures from LLMConfig
        
        logger.info(f"Created LLM instance: {provider}")
        return llm_instance

    @staticmethod
    def get_default_llm() -> BaseLLMProvider:
        """Get the default LLM instance based on configuration."""
        # Import here to avoid circular imports
        from app.core.config.llm_config import llm_config
        
        default_provider_str = llm_config.get_default_provider()
        if not default_provider_str:
            raise ValueError("No default LLM provider configured. Set DEFAULT_LLM_PROVIDER environment variable.")
        
        try:
            provider = LLMProvider(default_provider_str)
        except ValueError:
            raise ValueError(f"Invalid default provider '{default_provider_str}'. "
                           f"Valid providers: {[p.value for p in LLMProvider]}")
        
        return LLMFactory.get_llm(provider)

    @staticmethod
    def list_available_providers() -> list[str]:
        """List all available LLM providers."""
        return LLMRegistry.list_providers()
    
    @staticmethod
    def is_provider_available(provider: LLMProvider) -> bool:
        """Check if a provider is available and properly configured."""
        try:
            # Import here to avoid circular imports
            from app.core.config.llm_config import llm_config
            provider_config = llm_config.get_provider_config(provider.value)
            
            return (LLMRegistry.is_provider_registered(provider) and 
                   bool(provider_config))
        except Exception:
            return False
