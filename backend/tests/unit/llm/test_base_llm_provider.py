"""
Unit tests for BaseLLMProvider abstract base class.

Tests the abstract interface and common functionality for LLM providers.
Following Python open-source testing best practices.
"""

import pytest
from abc import ABC
from unittest.mock import Mock, AsyncMock
from typing import List, Dict, Any, AsyncGenerator

from app.infrastructure.llm.base.base_llm_provider import BaseLLMProvider, LLMResponse
from app.core.constants import LLMCapability


class ConcreteLLMProvider(BaseLLMProvider):
    """Concrete implementation of BaseLLMProvider for testing."""
    
    def __init__(self, provider_name: str = "test_provider"):
        self.provider_name = provider_name
        self._initialized = False
        self.client = None
        self._supported_capabilities = {LLMCapability.CHAT, LLMCapability.STREAMING}
        self._validation_should_fail = False
        self._init_should_fail = False
        
    def get_config_name(self) -> str:
        return f"llm.{self.provider_name}"
    
    def validate_config(self) -> None:
        if self._validation_should_fail:
            raise ValueError("Configuration validation failed")
    
    async def initialize(self) -> None:
        if self._init_should_fail:
            raise RuntimeError("Initialization failed")
        self._initialized = True
        self.client = Mock()
    
    async def generate(self, prompt: str, **kwargs) -> LLMResponse:
        if not self._initialized:
            raise RuntimeError("Provider not initialized")
        return LLMResponse(
            content=f"Generated response for: {prompt}",
            usage={"input_tokens": 10, "output_tokens": 20, "total_tokens": 30},
            metadata={"model": f"{self.provider_name}_model", "provider": self.provider_name}
        )
    
    async def stream_generate(self, prompt: str, **kwargs) -> AsyncGenerator[str, None]:
        if not self._initialized:
            raise RuntimeError("Provider not initialized")
        chunks = ["Streaming ", "response ", f"for: {prompt}"]
        for chunk in chunks:
            yield chunk
    
    def get_available_models(self) -> List[str]:
        return [f"{self.provider_name}_model_1", f"{self.provider_name}_model_2"]
    
    def supports_capability(self, capability: LLMCapability) -> bool:
        return capability in self._supported_capabilities
    
    # Test helper methods
    def set_validation_failure(self, should_fail: bool):
        """Set whether validation should fail."""
        self._validation_should_fail = should_fail
    
    def set_init_failure(self, should_fail: bool):
        """Set whether initialization should fail."""
        self._init_should_fail = should_fail
    
    def set_supported_capabilities(self, capabilities: set):
        """Set the supported capabilities."""
        self._supported_capabilities = capabilities


class IncompleteLLMProvider(BaseLLMProvider):
    """Incomplete implementation to test abstract method enforcement."""
    
    def get_config_name(self) -> str:
        return "incomplete"
    
    # Missing implementations of abstract methods


@pytest.fixture
def concrete_provider():
    """Fixture providing a concrete LLM provider instance."""
    return ConcreteLLMProvider("test_llm")


class TestBaseLLMProvider:
    """Test suite for BaseLLMProvider abstract base class."""
    
    def test_is_abstract_base_class(self):
        """Test that BaseLLMProvider is an abstract base class."""
        # Assert
        assert issubclass(BaseLLMProvider, ABC)
        assert BaseLLMProvider.__abstractmethods__
    
    def test_cannot_instantiate_abstract_class(self):
        """Test that BaseLLMProvider cannot be instantiated directly."""
        # Act & Assert
        with pytest.raises(TypeError):
            BaseLLMProvider()
    
    def test_concrete_implementation_can_be_instantiated(self, concrete_provider):
        """Test that concrete implementation can be instantiated."""
        # Assert
        assert isinstance(concrete_provider, BaseLLMProvider)
        assert concrete_provider.provider_name == "test_llm"
    
    def test_incomplete_implementation_cannot_be_instantiated(self):
        """Test that incomplete implementation cannot be instantiated."""
        # Act & Assert
        with pytest.raises(TypeError) as exc_info:
            IncompleteLLMProvider()
        
        # Should mention missing abstract methods
        error_message = str(exc_info.value)
        assert "abstract" in error_message.lower()
    
    def test_get_config_name_implementation(self, concrete_provider):
        """Test get_config_name implementation."""
        # Act
        config_name = concrete_provider.get_config_name()
        
        # Assert
        assert config_name == "llm.test_llm"
    
    def test_validate_config_success(self, concrete_provider):
        """Test successful config validation."""
        # Act & Assert - Should not raise exception
        try:
            concrete_provider.validate_config()
        except Exception as e:
            pytest.fail(f"validate_config should not raise exception: {e}")
    
    def test_validate_config_failure(self, concrete_provider):
        """Test config validation failure."""
        # Arrange
        concrete_provider.set_validation_failure(True)
        
        # Act & Assert
        with pytest.raises(ValueError) as exc_info:
            concrete_provider.validate_config()
        
        assert "Configuration validation failed" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_initialize_success(self, concrete_provider):
        """Test successful provider initialization."""
        # Arrange
        assert not concrete_provider._initialized
        
        # Act
        await concrete_provider.initialize()
        
        # Assert
        assert concrete_provider._initialized is True
        assert concrete_provider.client is not None
    
    @pytest.mark.asyncio
    async def test_initialize_failure(self, concrete_provider):
        """Test provider initialization failure."""
        # Arrange
        concrete_provider.set_init_failure(True)
        
        # Act & Assert
        with pytest.raises(RuntimeError) as exc_info:
            await concrete_provider.initialize()
        
        assert "Initialization failed" in str(exc_info.value)
        assert concrete_provider._initialized is False
    
    @pytest.mark.asyncio
    async def test_generate_success(self, concrete_provider):
        """Test successful text generation."""
        # Arrange
        await concrete_provider.initialize()
        test_prompt = "Tell me a joke"
        
        # Act
        response = await concrete_provider.generate(test_prompt)
        
        # Assert
        assert isinstance(response, LLMResponse)
        assert response.content == f"Generated response for: {test_prompt}"
        assert response.usage["total_tokens"] == 30
        assert response.metadata["provider"] == "test_llm"
    
    @pytest.mark.asyncio
    async def test_generate_not_initialized(self, concrete_provider):
        """Test generation fails when provider not initialized."""
        # Arrange
        test_prompt = "Test prompt"
        
        # Act & Assert
        with pytest.raises(RuntimeError) as exc_info:
            await concrete_provider.generate(test_prompt)
        
        assert "Provider not initialized" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_stream_generate_success(self, concrete_provider):
        """Test successful streaming generation."""
        # Arrange
        await concrete_provider.initialize()
        test_prompt = "Tell me a story"
        
        # Act
        chunks = []
        async for chunk in concrete_provider.stream_generate(test_prompt):
            chunks.append(chunk)
        
        # Assert
        assert len(chunks) == 3
        assert chunks == ["Streaming ", "response ", f"for: {test_prompt}"]
    
    @pytest.mark.asyncio
    async def test_stream_generate_not_initialized(self, concrete_provider):
        """Test streaming generation fails when provider not initialized."""
        # Arrange
        test_prompt = "Test prompt"
        
        # Act & Assert
        with pytest.raises(RuntimeError) as exc_info:
            # Consume the async generator to trigger the exception
            async for _ in concrete_provider.stream_generate(test_prompt):
                pass
        
        assert "Provider not initialized" in str(exc_info.value)
    
    def test_get_available_models(self, concrete_provider):
        """Test getting available models."""
        # Act
        models = concrete_provider.get_available_models()
        
        # Assert
        assert isinstance(models, list)
        assert len(models) == 2
        assert "test_llm_model_1" in models
        assert "test_llm_model_2" in models
    
    @pytest.mark.parametrize("capability,expected", [
        (LLMCapability.CHAT, True),
        (LLMCapability.STREAMING, True),
        (LLMCapability.FUNCTION_CALLING, False),
        (LLMCapability.MULTIMODAL, False),
    ])
    def test_supports_capability(self, concrete_provider, capability, expected):
        """Test capability support checking."""
        # Act
        supports = concrete_provider.supports_capability(capability)
        
        # Assert
        assert supports is expected
    
    def test_supports_capability_custom_set(self, concrete_provider):
        """Test capability support with custom capability set."""
        # Arrange
        custom_capabilities = {LLMCapability.FUNCTION_CALLING, LLMCapability.MULTIMODAL}
        concrete_provider.set_supported_capabilities(custom_capabilities)
        
        # Act & Assert
        assert concrete_provider.supports_capability(LLMCapability.FUNCTION_CALLING) is True
        assert concrete_provider.supports_capability(LLMCapability.MULTIMODAL) is True
        assert concrete_provider.supports_capability(LLMCapability.CHAT) is False
        assert concrete_provider.supports_capability(LLMCapability.STREAMING) is False


class TestLLMResponse:
    """Test suite for LLMResponse data class."""
    
    def test_llm_response_creation(self):
        """Test creating LLMResponse instance."""
        # Arrange
        content = "Test response"
        usage = {"tokens": 100}
        metadata = {"model": "test-model"}
        
        # Act
        response = LLMResponse(content=content, usage=usage, metadata=metadata)
        
        # Assert
        assert response.content == content
        assert response.usage == usage
        assert response.metadata == metadata
    
    def test_llm_response_with_optional_fields(self):
        """Test creating LLMResponse with optional fields."""
        # Arrange
        content = "Test response"
        
        # Act
        response = LLMResponse(content=content)
        
        # Assert
        assert response.content == content
        assert response.usage == {}
        assert response.metadata == {}
    
    def test_llm_response_equality(self):
        """Test LLMResponse equality comparison."""
        # Arrange
        response1 = LLMResponse(
            content="Test",
            usage={"tokens": 10},
            metadata={"model": "test"}
        )
        response2 = LLMResponse(
            content="Test",
            usage={"tokens": 10},
            metadata={"model": "test"}
        )
        response3 = LLMResponse(
            content="Different",
            usage={"tokens": 10},
            metadata={"model": "test"}
        )
        
        # Act & Assert
        assert response1 == response2
        assert response1 != response3
    
    def test_llm_response_string_representation(self):
        """Test LLMResponse string representation."""
        # Arrange
        response = LLMResponse(
            content="Test response",
            usage={"tokens": 50},
            metadata={"model": "gpt-4"}
        )
        
        # Act
        str_repr = str(response)
        
        # Assert
        assert "Test response" in str_repr
        assert "LLMResponse" in str_repr


class TestBaseLLMProviderEdgeCases:
    """Test suite for BaseLLMProvider edge cases and error handling."""
    
    @pytest.mark.asyncio
    async def test_multiple_initialization_calls(self, concrete_provider):
        """Test multiple calls to initialize."""
        # Act
        await concrete_provider.initialize()
        first_client = concrete_provider.client
        
        await concrete_provider.initialize()  # Should not fail
        second_client = concrete_provider.client
        
        # Assert
        assert concrete_provider._initialized is True
        # Implementation may or may not replace client - both are valid
        assert second_client is not None
    
    @pytest.mark.asyncio
    async def test_generate_with_kwargs(self, concrete_provider):
        """Test generation with additional keyword arguments."""
        # Arrange
        await concrete_provider.initialize()
        
        # Act
        response = await concrete_provider.generate(
            "Test prompt",
            temperature=0.7,
            max_tokens=100,
            custom_param="test"
        )
        
        # Assert
        assert isinstance(response, LLMResponse)
        assert "Test prompt" in response.content
    
    @pytest.mark.asyncio
    async def test_stream_generate_with_kwargs(self, concrete_provider):
        """Test streaming generation with additional keyword arguments."""
        # Arrange
        await concrete_provider.initialize()
        
        # Act
        chunks = []
        async for chunk in concrete_provider.stream_generate(
            "Test prompt",
            temperature=0.5,
            stream=True
        ):
            chunks.append(chunk)
        
        # Assert
        assert len(chunks) > 0
        assert all(isinstance(chunk, str) for chunk in chunks)
    
    def test_get_available_models_empty_list(self):
        """Test provider with no available models."""
        # Arrange
        class EmptyModelsProvider(ConcreteLLMProvider):
            def get_available_models(self) -> List[str]:
                return []
        
        provider = EmptyModelsProvider()
        
        # Act
        models = provider.get_available_models()
        
        # Assert
        assert models == []
    
    def test_supports_capability_all_capabilities(self, concrete_provider):
        """Test provider that supports all capabilities."""
        # Arrange
        all_capabilities = set(LLMCapability)
        concrete_provider.set_supported_capabilities(all_capabilities)
        
        # Act & Assert
        for capability in LLMCapability:
            assert concrete_provider.supports_capability(capability) is True
    
    def test_supports_capability_no_capabilities(self, concrete_provider):
        """Test provider that supports no capabilities."""
        # Arrange
        concrete_provider.set_supported_capabilities(set())
        
        # Act & Assert
        for capability in LLMCapability:
            assert concrete_provider.supports_capability(capability) is False
    
    @pytest.mark.asyncio
    async def test_concurrent_generation_calls(self, concrete_provider):
        """Test concurrent generation calls."""
        import asyncio
        
        # Arrange
        await concrete_provider.initialize()
        prompts = ["Prompt 1", "Prompt 2", "Prompt 3"]
        
        # Act
        tasks = [concrete_provider.generate(prompt) for prompt in prompts]
        responses = await asyncio.gather(*tasks)
        
        # Assert
        assert len(responses) == 3
        for i, response in enumerate(responses):
            assert isinstance(response, LLMResponse)
            assert f"Prompt {i+1}" in response.content
    
    def test_provider_inheritance_chain(self, concrete_provider):
        """Test that concrete provider properly inherits from BaseLLMProvider."""
        # Assert
        assert isinstance(concrete_provider, BaseLLMProvider)
        assert isinstance(concrete_provider, ABC)
        assert hasattr(concrete_provider, 'validate_config')
        assert hasattr(concrete_provider, 'initialize')
        assert hasattr(concrete_provider, 'generate')
        assert hasattr(concrete_provider, 'stream_generate')
        assert hasattr(concrete_provider, 'get_available_models')
        assert hasattr(concrete_provider, 'supports_capability')
    
    def test_abstract_methods_list(self):
        """Test that all expected methods are abstract."""
        # Get abstract methods
        abstract_methods = BaseLLMProvider.__abstractmethods__
        
        # Assert
        expected_abstract_methods = {
            'get_config_name',
            'validate_config',
            'initialize',
            'generate',
            'stream_generate',
            'get_available_models',
            'supports_capability'
        }
        
        assert abstract_methods == expected_abstract_methods
