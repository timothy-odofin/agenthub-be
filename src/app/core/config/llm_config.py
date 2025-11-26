"""
LLM configuration management.
"""

import os
from app.core.utils.single_ton import SingletonMeta


class LLMConfig(metaclass=SingletonMeta):
    """LLM configuration for all providers."""
    
    @property
    def llm_config(self) -> dict:
        """LLM configuration for all providers"""
        return {
            'default_provider': os.getenv('DEFAULT_LLM_PROVIDER', 'groq'),
            'default_model': os.getenv('DEFAULT_LLM_MODEL', 'llama-3.3-70b-versatile'),
            
            # Provider-specific configs
            'groq': self.groq_config,
            'openai': self.openai_config,
            'anthropic': self.anthropic_config,
            'huggingface': self.huggingface_config,
            'ollama': self.ollama_config,
            'google': self.google_config,
        }
    
    @property
    def groq_config(self) -> dict:
        """Groq LLM configuration"""
        return {
            'api_key': os.getenv('GROQ_API_KEY'),
            'base_url': os.getenv('GROQ_BASE_URL', 'https://api.groq.com/openai/v1'),
            'default_model': os.getenv('GROQ_DEFAULT_MODEL', 'llama-3.3-70b-versatile'),
            'timeout': int(os.getenv('GROQ_TIMEOUT', '60')),
            'max_tokens': int(os.getenv('GROQ_MAX_TOKENS', '4000')),
            'temperature': float(os.getenv('GROQ_TEMPERATURE', '0.7')),
        }
    
    @property
    def openai_config(self) -> dict:
        """OpenAI LLM configuration"""
        return {
            'api_key': os.getenv('OPENAI_API_KEY'),
            'base_url': os.getenv('OPENAI_BASE_URL', 'https://api.openai.com/v1'),
            'default_model': os.getenv('OPENAI_DEFAULT_MODEL', 'gpt-4-turbo'),
            'timeout': int(os.getenv('OPENAI_TIMEOUT', '60')),
            'max_tokens': int(os.getenv('OPENAI_MAX_TOKENS', '4000')),
            'temperature': float(os.getenv('OPENAI_TEMPERATURE', '0.7')),
            'organization': os.getenv('OPENAI_ORGANIZATION'),
        }
    
    @property
    def anthropic_config(self) -> dict:
        """Anthropic Claude LLM configuration"""
        return {
            'api_key': os.getenv('ANTHROPIC_API_KEY'),
            'base_url': os.getenv('ANTHROPIC_BASE_URL', 'https://api.anthropic.com'),
            'default_model': os.getenv('ANTHROPIC_DEFAULT_MODEL', 'claude-3-sonnet-20240229'),
            'timeout': int(os.getenv('ANTHROPIC_TIMEOUT', '60')),
            'max_tokens': int(os.getenv('ANTHROPIC_MAX_TOKENS', '4000')),
            'temperature': float(os.getenv('ANTHROPIC_TEMPERATURE', '0.7')),
        }
    
    @property
    def huggingface_config(self) -> dict:
        """HuggingFace LLM configuration"""
        return {
            'api_key': os.getenv('HUGGINGFACE_API_KEY'),
            'base_url': os.getenv('HUGGINGFACE_BASE_URL', 'https://api-inference.huggingface.co/models'),
            'default_model': os.getenv('HUGGINGFACE_DEFAULT_MODEL', 'meta-llama/Llama-2-7b-chat-hf'),
            'timeout': int(os.getenv('HUGGINGFACE_TIMEOUT', '120')),
            'max_tokens': int(os.getenv('HUGGINGFACE_MAX_TOKENS', '2000')),
            'temperature': float(os.getenv('HUGGINGFACE_TEMPERATURE', '0.7')),
        }
    
    @property
    def ollama_config(self) -> dict:
        """Ollama local LLM configuration"""
        return {
            'base_url': os.getenv('OLLAMA_BASE_URL', 'http://localhost:11434'),
            'default_model': os.getenv('OLLAMA_DEFAULT_MODEL', 'llama3'),
            'timeout': int(os.getenv('OLLAMA_TIMEOUT', '120')),
            'keep_alive': os.getenv('OLLAMA_KEEP_ALIVE', '5m'),
            'temperature': float(os.getenv('OLLAMA_TEMPERATURE', '0.7')),
        }
    
    @property
    def google_config(self) -> dict:
        """Google Gemini LLM configuration"""
        return {
            'api_key': os.getenv('GOOGLE_API_KEY'),
            'base_url': os.getenv('GOOGLE_BASE_URL', 'https://generativelanguage.googleapis.com/v1'),
            'default_model': os.getenv('GOOGLE_DEFAULT_MODEL', 'gemini-pro'),
            'timeout': int(os.getenv('GOOGLE_TIMEOUT', '60')),
            'max_tokens': int(os.getenv('GOOGLE_MAX_TOKENS', '4000')),
            'temperature': float(os.getenv('GOOGLE_TEMPERATURE', '0.7')),
        }
    
    # Convenience methods for direct access
    def get_provider_config(self, provider: str) -> dict:
        """Get configuration for a specific LLM provider."""
        return self.llm_config.get(provider, {})
    
    def get_default_provider(self) -> str:
        """Get the default LLM provider."""
        return self.llm_config.get('default_provider', 'groq')
    
    def get_default_model(self, provider: str) -> str:
        """Get the default model for a provider."""
        provider_config = self.get_provider_config(provider)
        return provider_config.get('default_model', '')


# Create singleton instance
llm_config = LLMConfig()
