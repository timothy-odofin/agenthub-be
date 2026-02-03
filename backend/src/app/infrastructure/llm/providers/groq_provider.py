"""
Groq LLM provider implementation.
"""

from typing import Dict, Any, List, AsyncGenerator
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage
from app.core.constants import LLMProvider, LLMCapability
from app.infrastructure.llm.base.base_llm_provider import BaseLLMProvider, LLMResponse
from app.infrastructure.llm.base.llm_registry import LLMRegistry
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
        """Get available Groq models (all open source models)."""
        return [
            # Llama 3.3 (Latest - November 2025)
            "llama-3.3-70b-versatile",
            
            # Llama 3.1 Series
            "llama-3.1-70b-versatile", 
            "llama-3.1-8b-instant",
            
            # Llama 3.0 Series
            "llama3-70b-8192",
            "llama3-8b-8192",
            
            # Llama 3 with Tool Use (Function Calling)
            "llama3-groq-70b-8192-tool-use-preview",
            "llama3-groq-8b-8192-tool-use-preview",
            
            # Mixtral Series (Mistral AI - Mixture of Experts)
            "mixtral-8x7b-32768",
            "mixtral-8x22b-32768",
            
            # Gemma Series (Google)
            "gemma-7b-it",
            "gemma2-9b-it",
            
            # Legacy models (still available but not recommended for new projects)
            "llama2-70b-4096",
        ]
    
    def supports_capability(self, capability: LLMCapability) -> bool:
        """Check if provider supports specific capability."""
        return capability in self._supported_capabilities
    
    def get_recommended_models(self) -> Dict[str, str]:
        """Get recommended models for different use cases."""
        return {
            'default': 'llama-3.3-70b-versatile',          # Latest and most capable
            'fast': 'llama-3.1-8b-instant',                # Best speed/quality balance
            'tools': 'llama3-groq-70b-8192-tool-use-preview',  # Function calling
            'complex': 'mixtral-8x22b-32768',               # Complex reasoning
            'lightweight': 'gemma2-9b-it',                 # Lightweight tasks
        }
    
    def get_model_info(self, model_name: str) -> Dict[str, Any]:
        """Get detailed information about a specific model."""
        model_info = {
            # Llama 3.3
            'llama-3.3-70b-versatile': {
                'family': 'Llama 3.3', 'size': '70B', 'context': '8K',
                'strengths': ['Latest capabilities', 'General purpose', 'High quality'],
                'use_cases': ['Production', 'Complex reasoning', 'General chat']
            },
            
            # Llama 3.1
            'llama-3.1-70b-versatile': {
                'family': 'Llama 3.1', 'size': '70B', 'context': '8K',
                'strengths': ['Excellent quality', 'Reliable', 'Well-tested'],
                'use_cases': ['Production', 'Complex tasks', 'Long conversations']
            },
            'llama-3.1-8b-instant': {
                'family': 'Llama 3.1', 'size': '8B', 'context': '8K',
                'strengths': ['Ultra-fast', 'Cost effective', 'Good quality'],
                'use_cases': ['High throughput', 'Real-time chat', 'Simple tasks']
            },
            
            # Tool use models
            'llama3-groq-70b-8192-tool-use-preview': {
                'family': 'Llama 3', 'size': '70B', 'context': '8K',
                'strengths': ['Function calling', 'Tool integration', 'Structured output'],
                'use_cases': ['Agent workflows', 'API integration', 'Structured tasks']
            },
            'llama3-groq-8b-8192-tool-use-preview': {
                'family': 'Llama 3', 'size': '8B', 'context': '8K',
                'strengths': ['Fast function calls', 'Tool use', 'Lightweight'],
                'use_cases': ['Fast agents', 'Simple tool use', 'High-volume APIs']
            },
            
            # Mixtral
            'mixtral-8x7b-32768': {
                'family': 'Mixtral', 'size': '8x7B MoE', 'context': '32K',
                'strengths': ['Long context', 'Mixture of experts', 'Multilingual'],
                'use_cases': ['Long documents', 'Code analysis', 'Research']
            },
            'mixtral-8x22b-32768': {
                'family': 'Mixtral', 'size': '8x22B MoE', 'context': '32K',
                'strengths': ['Very capable', 'Long context', 'Complex reasoning'],
                'use_cases': ['Advanced research', 'Complex analysis', 'Expert tasks']
            },
            
            # Gemma
            'gemma-7b-it': {
                'family': 'Gemma', 'size': '7B', 'context': '8K',
                'strengths': ['Lightweight', 'Fast', 'Google-trained'],
                'use_cases': ['Simple tasks', 'Education', 'Prototyping']
            },
            'gemma2-9b-it': {
                'family': 'Gemma 2', 'size': '9B', 'context': '8K',
                'strengths': ['Improved quality', 'Fast', 'Efficient'],
                'use_cases': ['Balanced tasks', 'Development', 'Quick responses']
            },
        }
        
        return model_info.get(model_name, {
            'family': 'Unknown', 'size': 'Unknown', 'context': 'Unknown',
            'strengths': ['Model info not available'],
            'use_cases': ['General purpose']
        })
    
    def is_tool_use_model(self, model_name: str) -> bool:
        """Check if a model supports enhanced tool use/function calling."""
        tool_use_models = [
            'llama3-groq-70b-8192-tool-use-preview',
            'llama3-groq-8b-8192-tool-use-preview'
        ]
        return model_name in tool_use_models
