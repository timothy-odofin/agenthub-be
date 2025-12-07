"""
LLM configuration management using Settings system.
"""

from typing import Dict, Optional, Any
from app.core.utils.single_ton import SingletonMeta
from ..framework.settings import settings


class LLMConfig(metaclass=SingletonMeta):
    """LLM configuration for all providers using Settings system."""
    
    @property
    def llm_config(self) -> Dict[str, Any]:
        """LLM configuration for all providers"""
        return {
            'default_provider': settings.llm.provider,
            'default_model': settings.llm.model,
            'temperature': settings.llm.temperature,
            'max_tokens': settings.llm.max_tokens,
            'timeout': settings.llm.timeout,
            'max_retries': settings.llm.max_retries,
            
            # Provider-specific configs
            'groq': self.groq_config,
            'openai': self.openai_config,
            'anthropic': self.anthropic_config,
            'huggingface': self.huggingface_config,
            'ollama': self.ollama_config,
            'google': self.google_config,
        }
    
    @property
    def groq_config(self) -> Dict[str, Any]:
        """Groq LLM configuration"""
        if not hasattr(settings.llm, 'groq'):
            return {}
        return {
            'api_key': settings.llm.groq.api_key,
            'base_url': settings.llm.groq.base_url,
            'default_model': settings.llm.groq.model,
            'timeout': settings.llm.groq.timeout,
            'max_tokens': settings.llm.groq.max_tokens,
            'temperature': settings.llm.groq.temperature,
        }
    
    @property
    def openai_config(self) -> Dict[str, Any]:
        """OpenAI LLM configuration"""
        if not hasattr(settings.llm, 'openai'):
            return {}
        return {
            'api_key': settings.llm.openai.api_key,
            'base_url': settings.llm.openai.base_url,
            'default_model': settings.llm.openai.model,
            'timeout': settings.llm.openai.timeout,
            'max_tokens': settings.llm.openai.max_tokens,
            'temperature': settings.llm.openai.temperature,
        }
    
    @property
    def anthropic_config(self) -> Dict[str, Any]:
        """Anthropic Claude LLM configuration"""
        if not hasattr(settings.llm, 'anthropic'):
            return {}
        return {
            'api_key': settings.llm.anthropic.api_key,
            'base_url': settings.llm.anthropic.base_url,
            'default_model': settings.llm.anthropic.model,
            'timeout': settings.llm.anthropic.timeout,
            'max_tokens': settings.llm.anthropic.max_tokens,
            'temperature': settings.llm.anthropic.temperature,
        }
    
    @property
    def huggingface_config(self) -> Dict[str, Any]:
        """HuggingFace LLM configuration"""
        if not hasattr(settings.llm, 'huggingface'):
            return {}
        return {
            'api_key': settings.llm.huggingface.api_key,
            'base_url': settings.llm.huggingface.base_url,
            'default_model': settings.llm.huggingface.model,
            'timeout': settings.llm.huggingface.timeout,
            'max_tokens': settings.llm.huggingface.max_tokens,
            'temperature': settings.llm.huggingface.temperature,
        }
    
    @property
    def ollama_config(self) -> Dict[str, Any]:
        """Ollama local LLM configuration"""
        if not hasattr(settings.llm, 'ollama'):
            return {}
        return {
            'base_url': settings.llm.ollama.base_url,
            'default_model': settings.llm.ollama.model,
            'timeout': settings.llm.ollama.timeout,
            'keep_alive': settings.llm.ollama.keep_alive,
            'temperature': settings.llm.ollama.temperature,
        }
    
    @property
    def google_config(self) -> Dict[str, Any]:
        """Google Gemini LLM configuration"""
        if not hasattr(settings.llm, 'google'):
            return {}
        return {
            'api_key': settings.llm.google.api_key,
            'base_url': settings.llm.google.base_url,
            'default_model': settings.llm.google.model,
            'timeout': settings.llm.google.timeout,
            'max_tokens': settings.llm.google.max_tokens,
            'temperature': settings.llm.google.temperature,
        }
    
    # Convenience methods for direct access
    def get_provider_config(self, provider: str) -> Dict[str, Any]:
        """Get configuration for a specific LLM provider."""
        return self.llm_config.get(provider, {})
    
    def get_default_provider(self) -> str:
        """Get the default LLM provider."""
        return self.llm_config.get('default_provider', 'openai')
    
    def get_default_model(self, provider: Optional[str] = None) -> str:
        """Get the default model for a provider or global default."""
        if provider:
            provider_config = self.get_provider_config(provider)
            return provider_config.get('default_model', '')
        return self.llm_config.get('default_model', '')


# Create singleton instance
llm_config = LLMConfig()
