"""
Enhanced LLM factory using the new Settings system.
This shows how to integrate profile-based configuration with your existing factory pattern.
"""

from typing import Optional
from app.core.constants import LLMProvider
from app.core.utils.logger import get_logger
from app.core.config import Settings
from app.llm.base.base_llm_provider import BaseLLMProvider
from app.llm.base.llm_registry import LLMRegistry

logger = get_logger(__name__)


class EnhancedLLMFactory:
    """Enhanced LLM Factory using the new Settings system."""

    _instance: Optional['EnhancedLLMFactory'] = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    @staticmethod
    def get_llm(provider: Optional[LLMProvider] = None, user_config: Optional[dict] = None) -> BaseLLMProvider:
        """
        Get an LLM instance for the specified provider with settings integration.
        
        Args:
            provider: LLM provider to use (optional - will use settings default)
            user_config: Optional user configuration to override settings
            
        Returns:
            LLM provider instance
            
        Raises:
            ValueError: If provider is not available or not registered
        """
        settings = Settings.instance()
        user_config = user_config or {}
        
        # Determine provider from user config, parameter, or settings
        if provider is None:
            if 'provider' in user_config:
                provider_str = user_config['provider']
            elif hasattr(settings, 'llm') and hasattr(settings.llm, 'provider'):
                provider_str = settings.llm.provider
            else:
                raise ValueError("No LLM provider specified and no default configured in settings")
            
            try:
                provider = LLMProvider(provider_str)
            except ValueError:
                raise ValueError(f"Invalid provider '{provider_str}'. "
                               f"Valid providers: {[p.value for p in LLMProvider]}")
        
        # Validate provider is registered
        if not LLMRegistry.is_provider_registered(provider):
            available = LLMRegistry.list_providers()
            raise ValueError(f"LLM provider '{provider}' not available. Available: {available}")
        
        # Get provider class and create instance with settings-based configuration
        provider_class = LLMRegistry.get_provider_class(provider)
        
        # Build configuration from settings + user overrides
        config = EnhancedLLMFactory._build_provider_config(provider, user_config)
        
        # Create instance with configuration
        llm_instance = provider_class(config=config)
        
        logger.info(f"Created LLM instance: {provider} with config keys: {list(config.keys())}")
        return llm_instance

    @staticmethod
    def _build_provider_config(provider: LLMProvider, user_config: dict) -> dict:
        """
        Build provider configuration from settings and user overrides.
        
        Args:
            provider: LLM provider
            user_config: User configuration overrides
            
        Returns:
            Complete configuration dictionary
        """
        settings = Settings.instance()
        config = {}
        
        # Base LLM settings
        if hasattr(settings, 'llm'):
            config.update({
                'model': getattr(settings.llm, 'model', None),
                'temperature': getattr(settings.llm, 'temperature', 0.1),
                'max_tokens': getattr(settings.llm, 'max_tokens', 4096),
                'timeout': getattr(settings.llm, 'timeout', 60),
            })
            
            # Provider-specific settings
            provider_name = provider.value.lower()
            if hasattr(settings.llm, provider_name):
                provider_settings = getattr(settings.llm, provider_name)
                if hasattr(provider_settings, '__dict__'):
                    provider_config = {k: v for k, v in provider_settings.__dict__.items() 
                                     if not k.startswith('_')}
                    config.update(provider_config)
        
        # Apply user overrides
        config.update(user_config)
        
        # Remove None values
        config = {k: v for k, v in config.items() if v is not None}
        
        logger.debug(f"Built config for {provider}: {config}")
        return config

    @staticmethod
    def get_default_llm(user_config: Optional[dict] = None) -> BaseLLMProvider:
        """Get the default LLM instance based on settings configuration."""
        return EnhancedLLMFactory.get_llm(provider=None, user_config=user_config)

    @staticmethod
    def get_available_models(provider: Optional[LLMProvider] = None) -> list[str]:
        """
        Get available models for a provider based on settings.
        
        Args:
            provider: LLM provider (optional - uses settings default)
            
        Returns:
            List of available model names
        """
        settings = Settings.instance()
        
        if provider is None:
            if hasattr(settings, 'llm') and hasattr(settings.llm, 'provider'):
                provider_str = settings.llm.provider
                try:
                    provider = LLMProvider(provider_str)
                except ValueError:
                    return []
            else:
                return []
        
        # Get models from settings
        provider_name = provider.value.lower()
        if (hasattr(settings, 'llm') and 
            hasattr(settings.llm, provider_name) and 
            hasattr(getattr(settings.llm, provider_name), 'available_models')):
            return getattr(getattr(settings.llm, provider_name), 'available_models', [])
        
        return []

    @staticmethod
    def get_provider_config(provider: LLMProvider) -> dict:
        """
        Get configuration for a specific provider from settings.
        
        Args:
            provider: LLM provider
            
        Returns:
            Provider configuration dictionary
        """
        return EnhancedLLMFactory._build_provider_config(provider, {})

    @staticmethod
    def list_available_providers() -> list[str]:
        """List all available LLM providers from registry."""
        return LLMRegistry.list_providers()

    @staticmethod
    def is_provider_available(provider: LLMProvider) -> bool:
        """
        Check if a provider is available and properly configured.
        
        Args:
            provider: LLM provider to check
            
        Returns:
            True if provider is registered and has valid configuration
        """
        try:
            # Check if registered
            if not LLMRegistry.is_provider_registered(provider):
                return False
            
            # Check if has configuration in settings
            config = EnhancedLLMFactory._build_provider_config(provider, {})
            return bool(config)  # Has some configuration
            
        except Exception as e:
            logger.warning(f"Error checking provider {provider} availability: {e}")
            return False

    @staticmethod
    def reload_settings():
        """Reload settings configuration (useful for testing or config updates)."""
        settings = Settings.instance()
        settings.reload()
        logger.info("Settings reloaded for LLM factory")

    @staticmethod
    def get_settings_info() -> dict:
        """Get information about current settings configuration."""
        settings = Settings.instance()
        
        info = {
            'profiles': settings.get_profile_names(),
            'has_llm_config': hasattr(settings, 'llm'),
            'default_provider': None,
            'available_providers': EnhancedLLMFactory.list_available_providers(),
            'configured_providers': []
        }
        
        if hasattr(settings, 'llm'):
            info['default_provider'] = getattr(settings.llm, 'provider', None)
            
            # Check which providers have configuration
            for provider_enum in LLMProvider:
                provider_name = provider_enum.value.lower()
                if hasattr(settings.llm, provider_name):
                    info['configured_providers'].append(provider_enum.value)
        
        return info


# Example usage functions for demonstration
def demonstrate_enhanced_llm_factory():
    """Demonstrate the enhanced LLM factory with Settings integration."""
    print("=== Enhanced LLM Factory Demonstration ===\n")
    
    factory = EnhancedLLMFactory()
    
    # Show settings info
    print("1. Settings Information:")
    info = factory.get_settings_info()
    for key, value in info.items():
        print(f"   {key}: {value}")
    
    print("\n2. Available Providers:")
    providers = factory.list_available_providers()
    for provider in providers:
        print(f"   - {provider}")
    
    print("\n3. Provider Configuration Examples:")
    try:
        # Try to get OpenAI config
        openai_config = factory.get_provider_config(LLMProvider.OPENAI)
        print(f"   OpenAI config: {openai_config}")
    except Exception as e:
        print(f"   OpenAI config error: {e}")
    
    # Example: Create LLM with default settings
    print("\n4. Creating LLM with Settings:")
    try:
        llm = factory.get_default_llm()
        print(f"   Default LLM created successfully: {type(llm).__name__}")
    except Exception as e:
        print(f"   Error creating default LLM: {e}")
    
    # Example: Create LLM with user overrides
    print("\n5. Creating LLM with User Overrides:")
    try:
        custom_llm = factory.get_default_llm({
            'temperature': 0.9,
            'max_tokens': 2048
        })
        print(f"   Custom LLM created successfully: {type(custom_llm).__name__}")
    except Exception as e:
        print(f"   Error creating custom LLM: {e}")


if __name__ == "__main__":
    demonstrate_enhanced_llm_factory()
