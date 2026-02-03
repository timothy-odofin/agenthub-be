"""
Ollama LLM provider implementation.
"""

from typing import Dict, Any, List, AsyncGenerator
from langchain_ollama import ChatOllama
from langchain_core.messages import HumanMessage
from app.core.constants import LLMProvider, LLMCapability
from app.llm.base.base_llm_provider import BaseLLMProvider, LLMResponse
from app.llm.base.llm_registry import LLMRegistry
from app.core.utils.logger import get_logger

logger = get_logger(__name__)


@LLMRegistry.register(LLMProvider.OLLAMA)
class OllamaLLM(BaseLLMProvider):
    """Ollama local LLM provider implementation."""
    
    def __init__(self):
        super().__init__()
        self._supported_capabilities = {
            LLMCapability.CHAT,
            LLMCapability.CODE_GENERATION,
            LLMCapability.STREAMING,
        }
    
    def get_config_name(self) -> str:
        """Return the configuration name for Ollama provider."""
        return LLMProvider.OLLAMA.value
    
    def validate_config(self) -> None:
        """Validate Ollama provider configuration."""
        # Validate model
        model = self.config.get('default_model')
        if not model:
            raise ValueError("Ollama provider requires 'default_model' in configuration")
        
        # Validate base_url
        base_url = self.config.get('base_url')
        if not base_url:
            raise ValueError("Ollama provider requires 'base_url' in configuration")
        
        # Validate temperature
        temperature = self.config.get('temperature')
        if temperature is not None and (temperature < 0 or temperature > 2):
            raise ValueError("Ollama temperature must be between 0 and 2")
        
        # Validate timeout
        timeout = self.config.get('timeout')
        if timeout is not None and timeout <= 0:
            raise ValueError("Ollama timeout must be greater than 0")
        
        logger.info(f"Ollama provider configuration validated successfully")
    
    @property
    def provider_name(self) -> str:
        """Get provider name."""
        return "ollama"
    
    async def initialize(self) -> None:
        """Initialize the Ollama LangChain client."""
        try:
            self.client = ChatOllama(
                model=self.config.get('default_model', self.default_model),
                base_url=self.config.get('base_url', 'http://localhost:11434'),
                temperature=self.config.get('temperature', 0.7),
                num_predict=self.config.get('max_tokens', None)
            )
            self._initialized = True
            logger.info(f"Ollama LLM provider initialized with model: {self.client.model}")
        except Exception as e:
            logger.error(f"Failed to initialize Ollama provider: {e}")
            raise
    
    async def generate(self, prompt: str, **kwargs) -> LLMResponse:
        """Generate text using Ollama LangChain API."""
        try:
            # Create message
            message = HumanMessage(content=prompt)
            
            # Generate response using LangChain
            response = await self.client.ainvoke([message], **kwargs)
            
            return LLMResponse(
                content=response.content,
                usage={}  # Ollama doesn't provide detailed usage stats
            )
        except Exception as e:
            logger.error(f"Ollama generation failed: {e}")
            raise
    
    async def stream_generate(self, prompt: str, **kwargs) -> AsyncGenerator[str, None]:
        """Stream generate text using Ollama LangChain API."""
        try:
            # Create message
            message = HumanMessage(content=prompt)
            
            # Stream response using LangChain
            async for chunk in self.client.astream([message], **kwargs):
                if chunk.content:
                    yield chunk.content
        except Exception as e:
            logger.error(f"Ollama streaming failed: {e}")
            raise
    
    def get_available_models(self) -> List[str]:
        """Get available Ollama models."""
        # TODO: Return actual Ollama models from local instance
        # response = await self.client.list()
        # return [model['name'] for model in response['models']]
        return [
            "llama3",
            "llama3:70b",
            "codellama",
            "mistral",
            "gemma",
        ]
    
    def supports_capability(self, capability: LLMCapability) -> bool:
        """Check if provider supports specific capability."""
        return capability in self._supported_capabilities
