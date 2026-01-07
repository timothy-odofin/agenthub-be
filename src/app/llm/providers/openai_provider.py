"""
OpenAI LLM provider implementation.
"""

from typing import List, AsyncGenerator

from langchain_core.messages import HumanMessage
from langchain_openai import ChatOpenAI

from app.core.constants import LLMProvider, LLMCapability
from app.core.utils.logger import get_logger
from app.llm.base.base_llm_provider import BaseLLMProvider, LLMResponse
from app.llm.base.llm_registry import LLMRegistry

logger = get_logger(__name__)


@LLMRegistry.register(LLMProvider.OPENAI)
class OpenAILLM(BaseLLMProvider):
    """OpenAI LLM provider implementation."""
    
    def __init__(self):
        super().__init__()
        self._supported_capabilities = {
            LLMCapability.CHAT,
            LLMCapability.CODE_GENERATION,
            LLMCapability.FUNCTION_CALLING,
            LLMCapability.STREAMING,
        }

    def get_config_name(self) -> str:
        """Return the configuration name for OpenAI provider."""
        return LLMProvider.OPENAI.value
    
    def validate_config(self) -> None:
        """Validate OpenAI provider configuration."""
        if not self.config.get('api_key'):
            raise ValueError("OpenAI provider requires 'api_key' in configuration")
        
        # Validate model if provided
        model = self.config.get('default_model')
        if model and model not in self.get_available_models():
            logger.warning(f"Model '{model}' may not be available. Available models: {self.get_available_models()}")
        
        # Validate temperature
        temperature = self.config.get('temperature')
        if temperature is not None and (temperature < 0 or temperature > 2):
            raise ValueError("OpenAI temperature must be between 0 and 2")
        
        # Validate max_tokens
        max_tokens = self.config.get('max_tokens')
        if max_tokens is not None and max_tokens <= 0:
            raise ValueError("OpenAI max_tokens must be greater than 0")
        logger.info(f"OpenAI provider configuration validated successfully")
    
    @property
    def provider_name(self) -> str:
        """Get provider name."""
        return "openai"
    
    async def initialize(self) -> None:
        """Initialize the OpenAI LangChain client."""
        try:
            self.client = ChatOpenAI(
                api_key=self.config.get('api_key'),
                model=self.config.get('default_model', self.default_model),
                temperature=self.config.get('temperature', 0.7),
                max_tokens=self.config.get('max_tokens', None),
                streaming=True  # Enable streaming capability
            )
            self._initialized = True
            logger.info(f"OpenAI LLM provider initialized with model: {self.client.model_name}")
        except Exception as e:
            logger.error(f"Failed to initialize OpenAI provider: {e}")
            raise
    
    async def generate(self, prompt: str, **kwargs) -> LLMResponse:
        """Generate text using OpenAI LangChain API."""
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
            logger.error(f"OpenAI generation failed: {e}")
            raise
    
    async def stream_generate(self, prompt: str, **kwargs) -> AsyncGenerator[str, None]:
        """Stream generate text using OpenAI LangChain API."""
        try:
            # Create message
            message = HumanMessage(content=prompt)
            
            # Stream response using LangChain
            async for chunk in self.client.astream([message], **kwargs):
                if chunk.content:
                    yield chunk.content
        except Exception as e:
            logger.error(f"OpenAI streaming failed: {e}")
            raise
    
    def get_available_models(self) -> List[str]:
        """Get available OpenAI models."""
        # TODO: Return actual OpenAI models
        return [
            "gpt-5-mini",
            "gpt-4-turbo",
            "gpt-4",
            "gpt-3.5-turbo",
            "gpt-4o",
            "gpt-4o-mini",
        ]
    
    def supports_capability(self, capability: LLMCapability) -> bool:
        """Check if provider supports specific capability."""
        return capability in self._supported_capabilities
