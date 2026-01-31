"""
LLM providers package initialization.
"""

from app.core.utils.dynamic_import import import_providers

# Provider modules configuration: (module_name, class_name)
PROVIDER_MODULES = [
    ('openai_provider', 'OpenAILLM'),
    ('azure_openai_provider', 'AzureOpenAILLM'),
    ('anthropic_provider', 'AnthropicLLM'),
    ('groq_provider', 'GroqLLM'),
    ('huggingface_provider', 'HuggingFaceLLM'),
    ('ollama_provider', 'OllamaLLM'),
    ('google_provider', 'GoogleLLM'),
]

# Import providers using the generic utility
__all__ = import_providers(__name__, PROVIDER_MODULES, globals())
