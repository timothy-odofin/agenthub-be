"""
Azure OpenAI LLM provider implementation.
"""

from typing import List, AsyncGenerator

from langchain_core.messages import HumanMessage
from langchain_openai import AzureChatOpenAI

from app.core.constants import LLMProvider, LLMCapability
from app.core.utils.logger import get_logger
from app.infrastructure.llm.base.base_llm_provider import BaseLLMProvider, LLMResponse
from app.infrastructure.llm.base.llm_registry import LLMRegistry

logger = get_logger(__name__)


@LLMRegistry.register(LLMProvider.AZURE_OPENAI)
class AzureOpenAILLM(BaseLLMProvider):
    """Azure OpenAI LLM provider implementation."""
    
    def __init__(self):
        super().__init__()
        self._supported_capabilities = {
            LLMCapability.CHAT,
            LLMCapability.CODE_GENERATION,
            LLMCapability.FUNCTION_CALLING,
            LLMCapability.STREAMING,
        }

    def get_config_name(self) -> str:
        """Return the configuration name for Azure OpenAI provider."""
        return "azure"  # Maps to settings.llm.azure
    
    def validate_config(self) -> None:
        """Validate Azure OpenAI provider configuration."""
        required_fields = ['api_key', 'endpoint']
        
        for field in required_fields:
            if not self.config.get(field):
                raise ValueError(f"Azure OpenAI provider requires '{field}' in configuration")
        
        # Validate API version format if provided
        api_version = self.config.get('api_version')
        if api_version and not isinstance(api_version, str):
            raise ValueError("Azure OpenAI api_version must be a string")
        
        # Validate temperature
        temperature = self.config.get('temperature')
        if temperature is not None and (temperature < 0 or temperature > 2):
            raise ValueError("Azure OpenAI temperature must be between 0 and 2")
        
        # Validate max_tokens
        max_tokens = self.config.get('max_tokens')
        if max_tokens is not None and max_tokens <= 0:
            raise ValueError("Azure OpenAI max_tokens must be greater than 0")
        
        logger.info(f"Azure OpenAI provider configuration validated successfully")
    
    @property
    def provider_name(self) -> str:
        """Get provider name."""
        return "azure_openai"
    
    async def initialize(self) -> None:
        """Initialize the Azure OpenAI LangChain client."""
        try:
            # Azure OpenAI specific configuration
            azure_endpoint = self.config.get('endpoint')
            api_key = self.config.get('api_key')
            api_version = self.config.get('api_version', '2024-02-15-preview')
            deployment_name = self.config.get('model', self.default_model)
            
            self.client = AzureChatOpenAI(
                azure_endpoint=azure_endpoint,
                api_key=api_key,
                api_version=api_version,
                deployment_name=deployment_name,
                temperature=self.config.get('temperature', 0.7),
                max_tokens=self.config.get('max_tokens', None),
                streaming=True  # Enable streaming capability
            )
            self._initialized = True
            logger.info(
                f"Azure OpenAI LLM provider initialized with deployment: {deployment_name}, "
                f"endpoint: {azure_endpoint}, api_version: {api_version}"
            )
        except Exception as e:
            logger.error(f"Failed to initialize Azure OpenAI provider: {e}")
            raise
    
    async def generate(self, prompt: str, **kwargs) -> LLMResponse:
        """Generate text using Azure OpenAI LangChain API."""
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
            logger.error(f"Azure OpenAI generation failed: {e}")
            raise
    
    async def stream_generate(self, prompt: str, **kwargs) -> AsyncGenerator[str, None]:
        """Stream generate text using Azure OpenAI LangChain API."""
        try:
            # Create message
            message = HumanMessage(content=prompt)
            
            # Stream response using LangChain
            async for chunk in self.client.astream([message], **kwargs):
                if chunk.content:
                    yield chunk.content
        except Exception as e:
            logger.error(f"Azure OpenAI streaming failed: {e}")
            raise
    
    def get_available_models(self) -> List[str]:
        """Get available Azure OpenAI deployment models.
        
        Note: Azure OpenAI uses deployment names, which are configured
        by the user in their Azure portal. Common deployment patterns:
        """
        return [
            "gpt-4",
            "gpt-4-32k",
            "gpt-4-turbo",
            "gpt-35-turbo",
            "gpt-35-turbo-16k",
            "gpt-4o",
            "gpt-4o-mini",
        ]
    
    def supports_capability(self, capability: LLMCapability) -> bool:
        """Check if provider supports specific capability."""
        return capability in self._supported_capabilities
