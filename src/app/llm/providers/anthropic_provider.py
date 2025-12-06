"""
Anthropic LLM provider implementation.
"""

from typing import Dict, Any, List, AsyncGenerator
from langchain_anthropic import ChatAnthropic
from langchain_core.messages import HumanMessage
from app.core.constants import LLMProvider, LLMCapability
from app.llm.base.base_llm_provider import BaseLLMProvider, LLMResponse
from app.llm.base.llm_registry import LLMRegistry
from app.core.utils.logger import get_logger

logger = get_logger(__name__)


@LLMRegistry.register(LLMProvider.ANTHROPIC)
class AnthropicLLM(BaseLLMProvider):
    """Anthropic Claude LLM provider implementation."""
    
    def __init__(self):
        super().__init__()
        self._supported_capabilities = {
            LLMCapability.CHAT,
            LLMCapability.CODE_GENERATION,
            LLMCapability.STREAMING,
        }

    def get_config_name(self) -> str:
        """Return the configuration name for Anthropic provider."""
        return LLMProvider.ANTHROPIC.value
    
    def validate_config(self) -> None:
        """Validate Anthropic provider configuration."""
        if not self.config.get('api_key'):
            raise ValueError("Anthropic provider requires 'api_key' in configuration")
        
        # Validate model if provided
        model = self.config.get('default_model')
        if model and model not in self.get_available_models():
            logger.warning(f"Model '{model}' may not be available. Available models: {self.get_available_models()}")
        
        # Validate temperature (Anthropic uses 0-1 range)
        temperature = self.config.get('temperature')
        if temperature is not None and (temperature < 0 or temperature > 1):
            raise ValueError("Anthropic temperature must be between 0 and 1")
        
        # Validate max_tokens (Anthropic has specific limits)
        max_tokens = self.config.get('max_tokens')
        if max_tokens is not None and (max_tokens <= 0 or max_tokens > 4096):
            raise ValueError("Anthropic max_tokens must be between 1 and 4096")
        
        logger.info(f"Anthropic provider configuration validated successfully")

    
    async def initialize(self) -> None:
        """Initialize the Anthropic LangChain client."""
        try:
            self.client = ChatAnthropic(
                api_key=self.config.get('api_key'),
                model=self.config.get('default_model', self.default_model),
                temperature=self.config.get('temperature', 0.7),
                max_tokens=self.config.get('max_tokens', None)
            )
            self._initialized = True
            logger.info(f"Anthropic LLM provider initialized with model: {self.client.model}")
        except Exception as e:
            logger.error(f"Failed to initialize Anthropic provider: {e}")
            raise
    
    async def generate(self, prompt: str, **kwargs) -> LLMResponse:
        """Generate text using Anthropic LangChain API."""
        try:
            # Create message
            message = HumanMessage(content=prompt)
            
            # Generate response using LangChain
            response = await self.client.ainvoke([message], **kwargs)
            
            # Extract usage information if available
            usage_metadata = getattr(response, 'usage_metadata', {}) or {}
            
            return LLMResponse(
                content=response.content,
                usage=usage_metadata
            )
        except Exception as e:
            logger.error(f"Anthropic generation failed: {e}")
            raise
    
    async def stream_generate(self, prompt: str, **kwargs) -> AsyncGenerator[str, None]:
        """Stream generate text using Anthropic LangChain API."""
        try:
            # Create message
            message = HumanMessage(content=prompt)
            
            # Stream response using LangChain
            async for chunk in self.client.astream([message], **kwargs):
                if chunk.content:
                    yield chunk.content
        except Exception as e:
            logger.error(f"Anthropic streaming failed: {e}")
            raise
    
    def get_available_models(self) -> List[str]:
        """Get available Anthropic models."""
        # TODO: Return actual Anthropic models
        return [
            "claude-3-sonnet-20240229",
            "claude-3-opus-20240229",
            "claude-3-haiku-20240307",
            "claude-3-5-sonnet-20241022",
        ]
    
    def supports_capability(self, capability: LLMCapability) -> bool:
        """Check if provider supports specific capability."""
        return capability in self._supported_capabilities
