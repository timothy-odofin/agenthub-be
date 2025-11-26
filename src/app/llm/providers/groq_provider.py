"""
Groq LLM provider implementation.
"""

from typing import Dict, Any, List, AsyncGenerator
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage
from app.core.constants import LLMProvider, LLMCapability
from app.llm.base.base_llm_provider import BaseLLMProvider, LLMResponse
from app.llm.base.llm_registry import LLMRegistry
from app.core.utils.logger import get_logger

logger = get_logger(__name__)


@LLMRegistry.register(LLMProvider.GROQ)
class GroqLLM(BaseLLMProvider):
    """Groq LLM provider implementation."""
    
    def __init__(self):
        super().__init__()
        self._supported_capabilities = {
            LLMCapability.CHAT,
            LLMCapability.FUNCTION_CALLING,
            LLMCapability.STREAMING,
        }
    
    def get_config_name(self) -> str:
        """Return the configuration name for Groq provider."""
        return LLMProvider.GROQ.value
    
    def validate_config(self) -> None:
        """Validate Groq provider configuration."""
        if not self.config.get('api_key'):
            raise ValueError("Groq provider requires 'api_key' in configuration")
        
        # Validate model - Groq has specific models available
        model = self.config.get('default_model', self.default_model)
        available_models = self.get_available_models()
        if model and model not in available_models:
            raise ValueError(f"Groq model '{model}' is not available. Available models: {available_models}")
        
        # Validate temperature
        temperature = self.config.get('temperature')
        if temperature is not None and (temperature < 0 or temperature > 2):
            raise ValueError("Groq temperature must be between 0 and 2")
        
        # Validate max_tokens for Groq's limits
        max_tokens = self.config.get('max_tokens')
        if max_tokens is not None and (max_tokens <= 0 or max_tokens > 32768):
            raise ValueError("Groq max_tokens must be between 1 and 32768")
        
        logger.info(f"Groq provider configuration validated successfully")
    
    @property
    def provider_name(self) -> str:
        """Get provider name."""
        return "groq"
    
    async def initialize(self) -> None:
        """Initialize the Groq LangChain client."""
        try:
            self.client = ChatGroq(
                api_key=self.config.get('api_key'),
                model=self.config.get('default_model', self.default_model),
                temperature=self.config.get('temperature', 0.7),
                max_tokens=self.config.get('max_tokens', None)
            )
            self._initialized = True
            logger.info(f"Groq LLM provider initialized with model: {self.client.model}")
        except Exception as e:
            logger.error(f"Failed to initialize Groq provider: {e}")
            raise
    
    async def generate(self, prompt: str, **kwargs) -> LLMResponse:
        """Generate text using Groq LangChain API."""
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
            logger.error(f"Groq generation failed: {e}")
            raise
    
    async def stream_generate(self, prompt: str, **kwargs) -> AsyncGenerator[str, None]:
        """Stream generate text using Groq LangChain API."""
        try:
            # Create message
            message = HumanMessage(content=prompt)
            
            # Stream response using LangChain
            async for chunk in self.client.astream([message], **kwargs):
                if chunk.content:
                    yield chunk.content
        except Exception as e:
            logger.error(f"Groq streaming failed: {e}")
            raise
    
    def get_available_models(self) -> List[str]:
        """Get available Groq models."""
        # TODO: Return actual Groq models
        return [
            "llama-3.3-70b-versatile",
            "llama-3.1-8b-instant",
            "mixtral-8x7b-32768",
            "gemma-7b-it",
        ]
    
    def supports_capability(self, capability: LLMCapability) -> bool:
        """Check if provider supports specific capability."""
        return capability in self._supported_capabilities
