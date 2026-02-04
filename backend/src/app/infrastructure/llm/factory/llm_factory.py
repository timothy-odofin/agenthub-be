"""
Factory for creating LLM instances.
"""

from typing import Optional
from app.core.constants import LLMProvider
from app.core.utils.logger import get_logger
from app.infrastructure.llm.base.base_llm_provider import BaseLLMProvider
from app.infrastructure.llm.base.llm_registry import LLMRegistry

logger = get_logger(__name__)


class LLMFactory:
    """Factory class for creating LLM instances."""

    _instance: Optional['LLMFactory'] = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    @classmethod
    def reset_for_testing(cls):
        """Reset factory singleton for testing."""
        cls._instance = None

    @staticmethod
    def get_llm(provider: LLMProvider) -> BaseLLMProvider:
        """
        Get an LLM instance for the specified provider.
        
        Args:
            provider: LLM provider to use (required)
            
        Returns:
            LLM provider instance (lazy initialization)
            
        Raises:
            ValueError: If provider is not available or not registered
        """
        # Validate provider is registered
        if not LLMRegistry.is_provider_registered(provider):
            available = LLMRegistry.list_providers()
            raise ValueError(f"LLM provider '{provider}' not available. Available: {available}")
        
        # Get provider class and create instance
        provider_class = LLMRegistry.get_provider_class(provider)
        llm_instance = provider_class()  # Provider self-configures and handles lazy initialization
        
        logger.info(f"Created LLM instance: {provider}")
        return llm_instance

    @staticmethod
    def get_llm_by_name(
        provider_name: Optional[str] = None,
        model: Optional[str] = None
    ) -> BaseLLMProvider:
        """
        Get an LLM instance by provider name string with optional model specification.
        
        This method bridges the gap between string provider names (from frontend/API)
        and the enum-based get_llm() method. It also validates the model if provided.
        
        Args:
            provider_name: String name of the provider (e.g., "openai", "anthropic").
                          If None, uses the default provider from configuration.
            model: Optional model name to validate. If None, uses provider's default.
                   Note: Model validation is performed but actual model selection
                   is handled by the provider's configuration.
            
        Returns:
            LLM provider instance configured for the specified provider
            
        Raises:
            ValueError: If provider name is invalid or model is not supported
        """
        # Import here to avoid circular imports
        from app.core.config.framework.settings import settings
        from app.services.llm_service import LLMService
        
        # Get provider name - use default if not specified
        if not provider_name:
            provider_name = settings.get_section('llm.default.provider')
            if not provider_name:
                raise ValueError("No provider specified and no default provider configured")
        
        # Convert string to enum
        try:
            provider = LLMProvider(provider_name.lower())
        except ValueError:
            valid_providers = [p.value for p in LLMProvider]
            raise ValueError(
                f"Invalid provider '{provider_name}'. Valid providers: {valid_providers}"
            )
        
        # Validate model if provided (this also returns the validated/default model)
        validated_model = LLMService.validate_model_for_provider(provider_name, model)
        
        logger.info(
            f"Getting LLM for provider='{provider_name}', "
            f"requested_model='{model}', validated_model='{validated_model}'"
        )
        
        # Get the LLM instance using the enum-based method
        # Note: The actual model configuration is handled by the provider's settings
        # The validated_model is logged for transparency but may need additional
        # implementation in the provider classes to support runtime model selection
        return LLMFactory.get_llm(provider)

    @staticmethod
    def get_default_llm() -> BaseLLMProvider:
        """Get the default LLM instance based on configuration."""
        # Import here to avoid circular imports
        from app.core.config.framework.settings import settings
        
        default_provider_str = settings.get_section('llm.default.provider')
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
            from app.core.config.framework.settings import settings
            provider_config = settings.get_section(f'llm.{provider.value}')
            
            return (LLMRegistry.is_provider_registered(provider) and 
                   bool(provider_config))
        except Exception:
            return False
