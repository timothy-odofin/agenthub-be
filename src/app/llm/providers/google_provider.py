"""
Google LLM provider implementation.
"""

from typing import Dict, Any, List, AsyncGenerator
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage
from app.core.constants import LLMProvider, LLMCapability
from app.llm.base.base_llm_provider import BaseLLMProvider, LLMResponse
from app.llm.base.llm_registry import LLMRegistry
from app.core.utils.logger import get_logger

logger = get_logger(__name__)


@LLMRegistry.register(LLMProvider.GOOGLE)
class GoogleLLM(BaseLLMProvider):
    """Google Gemini LLM provider implementation."""
    
    def __init__(self):
        super().__init__()
        self._supported_capabilities = {
            LLMCapability.CHAT,
            LLMCapability.CODE_GENERATION,
            LLMCapability.MULTIMODAL,
            LLMCapability.STREAMING,
        }

    def get_config_name(self) -> str:
        """Return the configuration name for Google provider."""
        return LLMProvider.GOOGLE.value

    def validate_config(self) -> None:
        """Validate Google provider configuration."""
        if not self.config.get('api_key'):
            raise ValueError("Google provider requires 'api_key' in configuration")
        
        # Validate model
        model = self.config.get('default_model')
        if model and model not in self.get_available_models():
            logger.warning(f"Model '{model}' may not be available. Available models: {self.get_available_models()}")
        
        # Validate temperature
        temperature = self.config.get('temperature')
        if temperature is not None and (temperature < 0 or temperature > 1):
            raise ValueError("Google temperature must be between 0 and 1")
        
        # Validate max_tokens
        max_tokens = self.config.get('max_tokens')
        if max_tokens is not None and max_tokens <= 0:
            raise ValueError("Google max_tokens must be greater than 0")
        
        logger.info(f"Google provider configuration validated successfully")

    
    async def initialize(self) -> None:
        """Initialize the Google LangChain client."""
        try:
            self.client = ChatGoogleGenerativeAI(
                model=self.config.get('default_model', self.default_model),
                google_api_key=self.config.get('api_key'),
                temperature=self.config.get('temperature', 0.7),
                max_tokens=self.config.get('max_tokens', None)
            )
            self._initialized = True
            logger.info(f"Google LLM provider initialized with model: {self.client.model}")
        except Exception as e:
            logger.error(f"Failed to initialize Google provider: {e}")
            raise
    
    async def generate(self, prompt: str, **kwargs) -> LLMResponse:
        """Generate text using Google LangChain API."""
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
            logger.error(f"Google generation failed: {e}")
            raise
    
    async def stream_generate(self, prompt: str, **kwargs) -> AsyncGenerator[str, None]:
        """Stream generate text using Google LangChain API."""
        try:
            # Create message
            message = HumanMessage(content=prompt)
            
            # Stream response using LangChain
            async for chunk in self.client.astream([message], **kwargs):
                if chunk.content:
                    yield chunk.content
        except Exception as e:
            logger.error(f"Google streaming failed: {e}")
            raise
    
    def get_available_models(self) -> List[str]:
        """Get available Google models."""
        # TODO: Return actual Google models
        return [
            "gemini-pro",
            "gemini-pro-vision",
            "gemini-1.5-pro",
            "gemini-1.5-flash",
        ]
    
    def supports_capability(self, capability: LLMCapability) -> bool:
        """Check if provider supports specific capability."""
        return capability in self._supported_capabilities
