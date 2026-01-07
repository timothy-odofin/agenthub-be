"""
LLM configuration utilities.
"""

from app.core.config.application.llm import llm_config as core_llm_config


class LLMConfig:
    """LLM configuration management."""
    
    @staticmethod
    def get_provider_config(provider: str) -> dict:
        """Get configuration for a specific LLM provider."""
        return core_llm_config.get_provider_config(provider)
    
    @staticmethod
    def get_default_provider() -> str:
        """Get the default LLM provider."""
        return core_llm_config.get_default_provider()
    
    @staticmethod
    def get_default_model(provider: str) -> str:
        """Get the default model for a provider."""
        return core_llm_config.get_default_model(provider)
    
    @staticmethod
    def validate_provider_config(provider: str) -> bool:
        """Validate that a provider has required configuration."""
        provider_config = LLMConfig.get_provider_config(provider)
        
        # Basic validation - check for API key if required
        if provider in ['groq', 'openai', 'anthropic', 'google', 'huggingface']:
            api_key = provider_config.get('api_key')
            if not api_key:
                return False
        
        # Check for base URL if required
        base_url = provider_config.get('base_url')
        if provider in ['ollama'] and not base_url:
            return False
            
        return True
