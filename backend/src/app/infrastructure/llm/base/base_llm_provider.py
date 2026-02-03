"""
Abstract base class for all LLM providers.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, AsyncGenerator, Type, Union
from enum import Enum
import json
import logging
import time

from app.core.constants import LLMCapability
from app.schemas.llm_output import LLMOutputBase, StructuredLLMResponse

try:
    from pydantic_core import PydanticUndefined
except ImportError:
    # Fallback for Pydantic v1
    PydanticUndefined = type('PydanticUndefined', (), {})()

logger = logging.getLogger(__name__)


class LLMResponse:
    """Response object for LLM generations."""
    
    def __init__(self, content: str, usage: Optional[Dict[str, Any]] = None, metadata: Optional[Dict[str, Any]] = None):
        self.content = content
        self.usage = usage if usage is not None else {}
        self.metadata = metadata if metadata is not None else {}
    
    def __eq__(self, other):
        """Check equality based on content, usage, and metadata."""
        if not isinstance(other, LLMResponse):
            return False
        return (self.content == other.content and 
                self.usage == other.usage and 
                self.metadata == other.metadata)
    
    def __str__(self):
        """String representation of LLMResponse."""
        return f"LLMResponse(content='{self.content[:50]}{'...' if len(self.content) > 50 else ''}')"

    def to_structured_response(self, 
                             model_name: str, 
                             provider: str, 
                             output_schema: Optional[Type[LLMOutputBase]] = None,
                             processing_time_ms: Optional[float] = None) -> StructuredLLMResponse:
        """Convert to structured response with optional parsing."""
        structured_output = None
        
        if output_schema:
            try:
                # Try to parse as JSON first
                parsed_data = json.loads(self.content)
                try:
                    structured_output = output_schema(**parsed_data)
                except Exception as validation_error:
                    logger.warning(f"JSON validation failed: {validation_error}, using fallback")
                    # Valid JSON but validation failed, create fallback
                    structured_output = self._create_fallback_output(output_schema)
            except json.JSONDecodeError:
                # Not valid JSON, create fallback structured output
                structured_output = self._create_fallback_output(output_schema)
            except Exception as e:
                logger.warning(f"Failed to parse structured output: {e}")
                structured_output = None

        return StructuredLLMResponse(
            content=self.content,
            structured_output=structured_output,
            usage=self.usage or {},
            metadata=self.metadata or {},
            model_name=model_name,
            provider=provider,
            processing_time_ms=processing_time_ms
        )

    def _create_fallback_output(self, output_schema):
        """Create fallback structured output when parsing fails."""
        # For non-JSON content, create fallback with minimal required fields
        fallback_data = {"success": True}

        # Add default values for required fields based on schema
        # Handle both Pydantic v1 and v2 compatibility
        if hasattr(output_schema, 'model_fields'):
            # Pydantic v2
            schema_fields = output_schema.model_fields
        else:
            # Pydantic v1
            schema_fields = output_schema.__fields__

        for field_name, field_info in schema_fields.items():
            # Check if field has a default value first
            has_default = False
            if hasattr(output_schema, 'model_fields'):
                # Pydantic v2 - check for default value
                if hasattr(field_info, 'default') and field_info.default is not PydanticUndefined:
                    has_default = True
                elif hasattr(field_info, 'default_factory') and field_info.default_factory is not None:
                    has_default = True
            else:
                # Pydantic v1
                has_default = hasattr(field_info, 'default') and field_info.default is not ...

            # Skip fields that already have defaults, unless it's success or reasoning which we always set for fallback
            if has_default and field_name != "success" and field_name != "reasoning":
                continue

            # Check if field is required (no default value)
            is_required = not has_default

            # Only set values for required fields, success, or reasoning (for fallback clarity)
            if is_required or field_name == "success" or field_name == "reasoning":
                # Provide sensible defaults for required fields
                if field_name == "success":
                    fallback_data[field_name] = True  # Always set success to True
                elif field_name == "reasoning":
                    fallback_data[field_name] = "Generated from unstructured content"
                elif field_name == "thought_process":
                    fallback_data[field_name] = "Processed unstructured content"
                elif field_name == "selected_action":
                    fallback_data[field_name] = "respond"
                elif field_name == "confidence_level":
                    fallback_data[field_name] = 0.5
                elif field_name == "response_text":
                    fallback_data[field_name] = "Generated from unstructured content"
                elif field_name == "response_type":
                    fallback_data[field_name] = "direct_answer"
                elif field_name == "content_type":
                    fallback_data[field_name] = "text"
                elif field_name == "quality_score":
                    fallback_data[field_name] = 0.7
                elif field_name == "document_summary":
                    fallback_data[field_name] = self.content[:100] if self.content else "Default summary"
                elif field_name == "session_summary":
                    fallback_data[field_name] = "Session processed"
                elif field_name == "source_type":
                    fallback_data[field_name] = "file"  # Default data source type
                elif field_name == "processed_items":
                    fallback_data[field_name] = 1
                elif field_name == "extraction_method":
                    fallback_data[field_name] = "direct_processing"
                elif field_name == "detected_format":
                    fallback_data[field_name] = "text"
                else:
                    # Generic fallback for other required fields
                    # Get field type (Pydantic v2 compatible)
                    field_type = getattr(field_info, 'annotation', getattr(field_info, 'type_', str))
                    
                    if hasattr(field_type, '__origin__'):
                        # Handle typing generics
                        if str(field_type).startswith('typing.Union'):
                            fallback_data[field_name] = "unknown"
                        else:
                            fallback_data[field_name] = "default"
                    elif field_type == str:
                        fallback_data[field_name] = "default"
                    elif field_type == int:
                        fallback_data[field_name] = 0
                    elif field_type == float:
                        fallback_data[field_name] = 0.0
                    elif field_type == bool:
                        fallback_data[field_name] = False
                    else:
                        fallback_data[field_name] = "default"

        return output_schema(**fallback_data)
class BaseLLMProvider(ABC):
    """Abstract base class for all LLM providers."""
    
    def __init__(self):
        """
        Initialize LLM provider with configuration.
        
        Note: Uses lazy import to avoid circular dependency.
        Config is loaded during provider instantiation.
        """
        # Use template method pattern - child defines config name, base retrieves it
        config_name = self.get_config_name()
        from app.core.config.framework.settings import settings
        self.config = settings.get_section(f'llm.{config_name}')
        self.client = None
        self._initialized = False
        # Validate configuration early to fail fast
        self.validate_config()

    @abstractmethod
    def get_config_name(self) -> str:
        """Return the configuration name/key for this provider.
        
        Returns:
            str: The configuration key to retrieve from settings
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

    async def generate_structured(self, 
                                prompt: str, 
                                output_schema: Type[LLMOutputBase],
                                **kwargs) -> StructuredLLMResponse:
        """
        Generate structured output from prompt.
        
        Args:
            prompt: The input prompt
            output_schema: Expected output structure
            **kwargs: Additional generation parameters
            
        Returns:
            Structured LLM response
        """
        start_time = time.time()
        
        # Enhance prompt for structured output
        structured_prompt = self._create_structured_prompt(prompt, output_schema)
        
        # Generate response
        response = await self.generate(structured_prompt, **kwargs)
        
        # Calculate processing time
        processing_time_ms = (time.time() - start_time) * 1000
        
        # Convert to structured response
        return response.to_structured_response(
            model_name=self.default_model,
            provider=self.get_config_name(),
            output_schema=output_schema,
            processing_time_ms=processing_time_ms
        )

    def _create_structured_prompt(self, prompt: str, output_schema: Type[LLMOutputBase]) -> str:
        """Create an enhanced prompt for structured output."""
        schema_example = {}
        # Check both old and new Pydantic v2 config style
        if hasattr(output_schema, 'Config'):
            if hasattr(output_schema.Config, 'json_schema_extra'):
                schema_example = output_schema.Config.json_schema_extra.get("example", {})
            elif hasattr(output_schema.Config, 'schema_extra'):
                schema_example = output_schema.Config.schema_extra.get("example", {})
        
        structured_prompt = f"""
{prompt}

Please provide a response in the following JSON format:
{json.dumps(schema_example, indent=2)}

Ensure your response is valid JSON that matches the expected structure.
"""
        return structured_prompt
    
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
