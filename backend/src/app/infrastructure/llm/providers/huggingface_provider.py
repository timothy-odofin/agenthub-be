"""
HuggingFace LLM provider implementation.
"""

from typing import Dict, Any, List, AsyncGenerator
from langchain_huggingface import HuggingFaceEndpoint
from langchain_core.messages import HumanMessage
from app.core.constants import LLMProvider, LLMCapability
from app.infrastructure.llm.base.base_llm_provider import BaseLLMProvider, LLMResponse
from app.infrastructure.llm.base.llm_registry import LLMRegistry
from app.core.utils.logger import get_logger

logger = get_logger(__name__)


@LLMRegistry.register(LLMProvider.HUGGINGFACE)
class HuggingFaceLLM(BaseLLMProvider):
    """HuggingFace LLM provider implementation."""
    
    def __init__(self):
        super().__init__()
        self._supported_capabilities = {
            LLMCapability.CHAT,
            LLMCapability.CODE_GENERATION,
        }
    
    def get_config_name(self) -> str:
        """Return the configuration name for HuggingFace provider."""
        return LLMProvider.HUGGINGFACE.value
    
    def validate_config(self) -> None:
        """Validate HuggingFace provider configuration."""
        if not self.config.get('api_key'):
            raise ValueError("HuggingFace provider requires 'api_key' in configuration")
        
        # Validate model (repo_id)
        model = self.config.get('default_model')
        if not model:
            raise ValueError("HuggingFace provider requires 'default_model' in configuration")
        
        # Validate temperature
        temperature = self.config.get('temperature')
        if temperature is not None and (temperature < 0 or temperature > 1):
            raise ValueError("HuggingFace temperature must be between 0 and 1")
        
        # Validate max_tokens
        max_tokens = self.config.get('max_tokens')
        if max_tokens is not None and max_tokens <= 0:
            raise ValueError("HuggingFace max_tokens must be greater than 0")
        
        logger.info(f"HuggingFace provider configuration validated successfully")
    
    @property
    def provider_name(self) -> str:
        """Get provider name."""
        return "huggingface"
    
    async def initialize(self) -> None:
        """Initialize the HuggingFace LangChain client."""
        try:
            self.client = HuggingFaceEndpoint(
                repo_id=self.config.get('default_model', self.default_model),
                huggingfacehub_api_token=self.config.get('api_key'),
                temperature=self.config.get('temperature', 0.7),
                max_length=self.config.get('max_tokens', 512)
            )
            self._initialized = True
            logger.info(f"HuggingFace LLM provider initialized with model: {self.config.get('model', self.default_model)}")
        except Exception as e:
            logger.error(f"Failed to initialize HuggingFace provider: {e}")
            raise
    
    async def generate(self, prompt: str, **kwargs) -> LLMResponse:
        """Generate text using HuggingFace LangChain API."""
        try:
            # Note: HuggingFaceEndpoint doesn't use HumanMessage format
            # It uses direct text input
            response = await self.client.ainvoke(prompt, **kwargs)
            
            return LLMResponse(
                content=response,
                usage={}  # HuggingFace endpoint doesn't return usage stats
            )
        except Exception as e:
            logger.error(f"HuggingFace generation failed: {e}")
            raise
    
    async def stream_generate(self, prompt: str, **kwargs) -> AsyncGenerator[str, None]:
        """Stream generate text using HuggingFace LangChain API."""
        try:
            # Note: HuggingFaceEndpoint may not support streaming
            # Fallback to regular generation
            response = await self.generate(prompt, **kwargs)
            # Simulate streaming by yielding the full response
            yield response.content
        except Exception as e:
            logger.error(f"HuggingFace streaming failed: {e}")
            raise
    
    def get_available_models(self) -> List[str]:
        """Get available HuggingFace models."""
        # TODO: Return actual HuggingFace models
        return [
            "meta-llama/Llama-2-7b-chat-hf",
            "meta-llama/Llama-2-13b-chat-hf",
            "mistralai/Mixtral-8x7B-Instruct-v0.1",
            "microsoft/DialoGPT-medium",
        ]
    
    def supports_capability(self, capability: LLMCapability) -> bool:
        """Check if provider supports specific capability."""
        return capability in self._supported_capabilities
