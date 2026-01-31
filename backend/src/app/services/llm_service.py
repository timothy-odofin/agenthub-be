"""
LLM Service for managing LLM provider information.

Provides functionality to:
- List available (configured) LLM providers
- Get detailed information about specific providers
- Validate provider configuration
"""

from typing import List, Dict, Any
from app.core.utils.logger import get_logger

logger = get_logger(__name__)


def _get_settings():
    """Lazy load settings to avoid circular import. Import only when needed."""
    from app.core.config import settings
    return settings


class LLMService:
    """Service for managing LLM provider information."""
    
    @staticmethod
    def _is_provider_configured(provider_name: str, provider_config: Any) -> bool:
        """
        Check if a provider is properly configured and ready to use.
        
        Args:
            provider_name: The provider identifier (e.g., "openai")
            provider_config: The provider configuration object
            
        Returns:
            bool: True if provider is configured, False otherwise
            
        Validates:
        - Ollama (local) requires valid base_url
        - Other providers require valid API key (not None, not unresolved env var)
        """
        # Ollama is local, doesn't need API key but needs base_url
        if provider_name == 'ollama':
            base_url = getattr(provider_config, 'base_url', None)
            return base_url is not None and not base_url.startswith('${')
        
        # All other providers require API key
        api_key = getattr(provider_config, 'api_key', None)
        
        # Check if API key exists and is not an unresolved environment variable
        if not api_key or api_key.startswith('${'):
            return False
        
        return True
    
    @staticmethod
    def _validate_provider_configured(provider_name: str, provider_config: Any) -> None:
        """
        Validate that a provider is configured, raise ValueError if not.
        
        Args:
            provider_name: The provider identifier
            provider_config: The provider configuration object
            
        Raises:
            ValueError: If provider is not properly configured
        """
        if not LLMService._is_provider_configured(provider_name, provider_config):
            if provider_name == 'ollama':
                raise ValueError(
                    f"Provider '{provider_name}' not configured (missing or invalid base_url)"
                )
            else:
                raise ValueError(
                    f"Provider '{provider_name}' not configured (missing API key)"
                )
    
    @staticmethod
    def validate_model_for_provider(provider_name: str, model: str = None) -> str:
        """
        Validate that a model is supported by the provider.
        If no model is provided, return the provider's default model.
        
        Args:
            provider_name: The provider identifier (e.g., "openai")
            model: Optional model name to validate
            
        Returns:
            str: The validated model name (or default if none provided)
            
        Raises:
            ValueError: If provider not found, not configured, or model not supported
        """
        settings = _get_settings()
        provider_config = getattr(settings.llm, provider_name, None)
        
        if not provider_config:
            raise ValueError(f"Provider '{provider_name}' not found in configuration")
        
        # Validate provider is configured
        LLMService._validate_provider_configured(provider_name, provider_config)
        
        # Get provider's default model and available models
        default_model = getattr(provider_config, 'model', None)
        model_versions = getattr(provider_config, 'model_versions', [])
        
        # If no model provided, use default
        if not model:
            if not default_model:
                raise ValueError(f"Provider '{provider_name}' has no default model configured")
            return default_model
        
        # If model provided, validate it's in the supported list
        if model_versions and model not in model_versions:
            raise ValueError(
                f"Model '{model}' is not supported by provider '{provider_name}'. "
                f"Available models: {', '.join(model_versions)}"
            )
        
        return model
    
    @staticmethod
    def get_available_providers() -> List[Dict[str, Any]]:
        """
        Get list of available (configured) LLM providers.
        
        Returns only providers that have required configuration (e.g., API key).
        Filters from settings.llm and returns only needed properties.
        
        Returns:
            List of provider info dicts with:
            - name: Provider identifier (e.g., "openai")
            - display_name: Human-readable name
            - model_versions: List of available models
            - default_model: The default model for this provider
            - is_default: Whether this is the system default provider
        """
        settings = _get_settings()
        available_providers = []
        
        # Get the system default provider name
        default_provider_name = settings.llm.default.provider
        
        # Iterate through settings.llm items (key-value pairs)
        for provider_name, provider_config in settings.llm.__dict__.items():
            # Skip 'default' and private attributes
            if provider_name == 'default' or provider_name.startswith('_'):
                continue
            
            # Check if provider is configured - skip if not
            if not LLMService._is_provider_configured(provider_name, provider_config):
                logger.debug(f"Skipping {provider_name} - not configured")
                continue
            
            # Extract only the properties we need for frontend
            provider_info = {
                "name": provider_name,
                "display_name": getattr(provider_config, 'display_name', provider_name.capitalize()),
                "model_versions": getattr(provider_config, 'model_versions', []),
                "default_model": getattr(provider_config, 'model', None),
                "is_default": (provider_name == default_provider_name)
            }
            
            available_providers.append(provider_info)
        
        logger.info(f"Found {len(available_providers)} available LLM providers")
        return available_providers
    
    @staticmethod
    def get_provider_info(provider_name: str) -> Dict[str, Any]:
        """
        Get detailed information about a specific provider.
        
        Args:
            provider_name: The provider identifier (e.g., "openai")
            
        Returns:
            Provider configuration dict with additional details:
            - name: Provider identifier
            - display_name: Human-readable name
            - model_versions: List of available models
            - default_model: Default model for this provider
            - is_default: Whether this is the system default
            - base_url: API base URL
            - timeout: Request timeout in seconds
            - max_tokens: Maximum tokens limit
            
        Raises:
            ValueError: If provider not found or not configured
        """
        settings = _get_settings()
        provider_config = getattr(settings.llm, provider_name, None)
        
        if not provider_config:
            raise ValueError(f"Provider '{provider_name}' not found in configuration")
        
        # Validate provider is configured - raises ValueError if not
        LLMService._validate_provider_configured(provider_name, provider_config)
        
        default_provider_name = settings.llm.default.provider
        
        return {
            "name": provider_name,
            "display_name": getattr(provider_config, 'display_name', provider_name.capitalize()),
            "model_versions": getattr(provider_config, 'model_versions', []),
            "default_model": getattr(provider_config, 'model', None),
            "is_default": (provider_name == default_provider_name),
            "base_url": getattr(provider_config, 'base_url', None),
            "timeout": getattr(provider_config, 'timeout', None),
            "max_tokens": getattr(provider_config, 'max_tokens', None)
        }


# Singleton instance for convenience
llm_service = LLMService()
