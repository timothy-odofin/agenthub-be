"""
Abstract base class for all LLM providers.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, AsyncGenerator
from enum import Enum

from app.core.constants import LLMCapability


class LLMResponse:
    """Response object for LLM generations."""
    
    def __init__(self, content: str, usage: Optional[Dict[str, Any]] = None, metadata: Optional[Dict[str, Any]] = None):
        self.content = content
        self.usage = usage or {}
        self.metadata = metadata or {}


class BaseLLMProvider(ABC):
    """Abstract base class for all LLM providers."""
    
    def __init__(self):
        # Use template method pattern - child defines config name, base retrieves it
        config_name = self.get_config_name()
        from app.core.config.llm_config import llm_config
        self.config = llm_config.get_provider_config(config_name)
        self.client = None
        self._initialized = False
        # Validate configuration early to fail fast
        self.validate_config()

    @abstractmethod
    def get_config_name(self) -> str:
        """Return the configuration name/key for this provider.
        
        Returns:
            str: The configuration key to retrieve from LLMConfig
        """
        pass

    async def _ensure_initialized(self):
        """Ensure the provider is initialized. Call this before using the client."""
        if not self._initialized:
            await self.initialize()

    @property
    def initialized_client(self):
        """Get the client if initialized, None otherwise. Use this for sync access."""
        return self.client if self._initialized else None

    @abstractmethod
    def validate_config(self) -> None:
        """Validate the provider configuration.
        
        This method should check that all required configuration parameters
        are present and valid for the specific provider.
        
        Raises:
            ValueError: If configuration is invalid or missing required parameters
        """
        pass
    
    @abstractmethod
    async def initialize(self) -> None:
        """Initialize the LLM client."""
        pass
    
    @abstractmethod
    async def generate(self, prompt: str, **kwargs) -> LLMResponse:
        """
        Generate text from prompt.
        
        Args:
            prompt: The input prompt
            **kwargs: Additional generation parameters
            
        Returns:
            LLMResponse with generated content
        """
        pass
    
    @abstractmethod
    async def stream_generate(self, prompt: str, **kwargs) -> AsyncGenerator[str, None]:
        """
        Stream generate text from prompt.
        
        Args:
            prompt: The input prompt
            **kwargs: Additional generation parameters
            
        Yields:
            Chunks of generated text
        """
        pass
    
    @abstractmethod
    def get_available_models(self) -> List[str]:
        """Get list of available models for this provider."""
        pass
    
    @abstractmethod
    def supports_capability(self, capability: LLMCapability) -> bool:
        """Check if provider supports specific capability."""
        pass

    
    @property
    def default_model(self) -> str:
        """Get default model for this provider."""
        return self.config.get('default_model', '')
    
    @property
    def is_initialized(self) -> bool:
        """Check if provider is initialized."""
        return self._initialized
    
    async def ensure_initialized(self):
        """Ensure the provider is initialized."""
        if not self._initialized:
            await self.initialize()
    
    async def close(self) -> None:
        """Close the LLM client connection."""
        if self.client:
            # Override in subclasses if needed
            pass
        self._initialized = False
