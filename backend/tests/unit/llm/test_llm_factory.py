"""
Unit tests for LLMFactory class.

Tests the factory pattern for creating LLM provider instances with proper 
initialization and configuration management. Following Python open-source testing best practices.
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock
from typing import Dict, Any, List

from app.infrastructure.llm.factory.llm_factory import LLMFactory
from app.infrastructure.llm.base.llm_registry import LLMRegistry
from app.infrastructure.llm.base.base_llm_provider import BaseLLMProvider, LLMResponse
from app.core.constants import LLMProvider, LLMCapability


class MockSimpleLLMProvider(BaseLLMProvider):
    """Simple mock LLM provider for testing."""
    
    def __init__(self):
        self.provider_name = "mock_provider"
        self._initialized = True
        
    def get_config_name(self) -> str:
        return "mock"
    
    def validate_config(self) -> None:
        pass
    
    async def initialize(self) -> None:
        pass
    
    async def generate(self, prompt: str, **kwargs) -> LLMResponse:
        return LLMResponse(
            content=f"Mock response for: {prompt}",
            usage={"tokens": 10},
            metadata={"model": "mock_model"}
        )
    
    async def stream_generate(self, prompt: str, **kwargs):
        for chunk in ["Mock ", "streaming ", "response"]:
            yield chunk
    
    def get_available_models(self) -> List[str]:
        return ["mock_model_1", "mock_model_2"]
    
    def supports_capability(self, capability: LLMCapability) -> bool:
        return True


@pytest.fixture
def clean_llm_registry():
    """Fixture to ensure clean LLM registry for each test."""
    # Store original state
    original_registry = LLMRegistry._registry.copy()
    original_imported = LLMRegistry._providers_imported
    original_auto_import = getattr(LLMRegistry, '_auto_import_enabled', True)
    
    # Reset and disable auto-import for testing
    LLMRegistry.reset_for_testing()
    LLMRegistry.set_auto_import(False)
    
    # Reset factory singleton
    LLMFactory.reset_for_testing()
    
    yield
    
    # Restore original state
    LLMRegistry._registry = original_registry
    LLMRegistry._providers_imported = original_imported
    LLMRegistry._auto_import_enabled = original_auto_import


@pytest.fixture
def setup_test_providers(clean_llm_registry):
    """Fixture to register test providers."""
    providers = {}
    
    @LLMRegistry.register(LLMProvider.OPENAI)
    class MockOpenAIProvider(MockSimpleLLMProvider):
        def __init__(self):
            super().__init__()
            self.provider_name = "openai"
    
    @LLMRegistry.register(LLMProvider.ANTHROPIC)
    class MockAnthropicProvider(MockSimpleLLMProvider):
        def __init__(self):
            super().__init__()
            self.provider_name = "anthropic"
    
    @LLMRegistry.register(LLMProvider.GROQ)
    class MockGroqProvider(MockSimpleLLMProvider):
        def __init__(self):
            super().__init__()
            self.provider_name = "groq"
    
    providers['openai'] = MockOpenAIProvider
    providers['anthropic'] = MockAnthropicProvider
    providers['groq'] = MockGroqProvider
    
    yield providers


class TestLLMFactory:
    """Test suite for LLMFactory class."""
    
    def test_get_llm_success(self, setup_test_providers):
        """Test successful LLM provider creation."""
        # Prevent loading real providers during test
        original_imported = LLMRegistry._providers_imported
        LLMRegistry._providers_imported = True
        
        try:
            # Act
            llm_instance = LLMFactory.get_llm(LLMProvider.OPENAI)
            
            # Assert
            assert llm_instance is not None
            assert isinstance(llm_instance, MockSimpleLLMProvider)
            assert llm_instance.provider_name == "openai"
            assert llm_instance._initialized is True
        finally:
            LLMRegistry._providers_imported = original_imported
    
    def test_get_llm_unregistered_provider(self, clean_llm_registry):
        """Test getting LLM with unregistered provider raises ValueError."""
        # Prevent automatic loading of real providers
        original_imported = LLMRegistry._providers_imported
        LLMRegistry._providers_imported = True
        
        try:
            # Act & Assert
            with pytest.raises(ValueError) as exc_info:
                LLMFactory.get_llm(LLMProvider.OPENAI)
            
            assert "LLM provider 'LLMProvider.OPENAI' not available" in str(exc_info.value)
            assert "Available:" in str(exc_info.value)
        finally:
            LLMRegistry._providers_imported = original_imported
    
    def test_get_default_llm_success(self, setup_test_providers):
        """Test getting default LLM when configured."""
        # Arrange
        with patch('app.core.config.application.llm.llm_config') as mock_config:
            mock_config.get_default_provider.return_value = "openai"
            
            # Act
            llm_instance = LLMFactory.get_default_llm()
            
            # Assert
            assert llm_instance is not None
            assert llm_instance.provider_name == "openai"
            mock_config.get_default_provider.assert_called_once()
    
    def test_get_default_llm_no_default_configured(self, setup_test_providers):
        """Test getting default LLM when no default is configured."""
        # Arrange
        with patch('app.core.config.application.llm.llm_config') as mock_config:
            mock_config.get_default_provider.return_value = None
            
            # Act & Assert
            with pytest.raises(ValueError) as exc_info:
                LLMFactory.get_default_llm()
            
            assert "No default LLM provider configured" in str(exc_info.value)
    
    def test_get_default_llm_invalid_provider(self, setup_test_providers):
        """Test getting default LLM with invalid provider name."""
        # Arrange
        with patch('app.core.config.application.llm.llm_config') as mock_config:
            mock_config.get_default_provider.return_value = "invalid_provider"
            
            # Act & Assert
            with pytest.raises(ValueError) as exc_info:
                LLMFactory.get_default_llm()
            
            assert "Invalid default provider" in str(exc_info.value)
    
    def test_list_available_providers_empty_registry(self, clean_llm_registry):
        """Test listing providers when registry is empty."""
        # Act
        providers = LLMFactory.list_available_providers()
        
        # Assert
        assert providers == []
    
    def test_list_available_providers_populated_registry(self, setup_test_providers):
        """Test listing providers when registry has providers."""
        # Act
        providers = LLMFactory.list_available_providers()
        
        # Assert
        assert len(providers) == 3
        assert LLMProvider.OPENAI in providers
        assert LLMProvider.ANTHROPIC in providers
        assert LLMProvider.GROQ in providers
    
    def test_is_provider_available_true(self, setup_test_providers):
        """Test is_provider_available returns True for registered provider with config."""
        # Arrange
        with patch('app.core.config.application.llm.llm_config') as mock_config:
            mock_config.get_provider_config.return_value = {"api_key": "test_key"}
            
            # Act & Assert
            assert LLMFactory.is_provider_available(LLMProvider.OPENAI) is True
            mock_config.get_provider_config.assert_called_once_with("openai")
    
    def test_is_provider_available_false_unregistered(self, clean_llm_registry):
        """Test is_provider_available returns False for unregistered provider."""
        # Act & Assert
        assert LLMFactory.is_provider_available(LLMProvider.OPENAI) is False
    
    def test_is_provider_available_false_no_config(self, setup_test_providers):
        """Test is_provider_available returns False when provider has no config."""
        # Arrange
        with patch('app.core.config.application.llm.llm_config') as mock_config:
            mock_config.get_provider_config.return_value = {}  # Empty config
            
            # Act & Assert
            assert LLMFactory.is_provider_available(LLMProvider.OPENAI) is False
    
    def test_is_provider_available_false_config_exception(self, setup_test_providers):
        """Test is_provider_available returns False when config access raises exception."""
        # Arrange
        with patch('app.core.config.application.llm.llm_config') as mock_config:
            mock_config.get_provider_config.side_effect = Exception("Config error")
            
            # Act & Assert
            assert LLMFactory.is_provider_available(LLMProvider.OPENAI) is False
    
    @pytest.mark.parametrize("provider", [
        LLMProvider.OPENAI,
        LLMProvider.ANTHROPIC,
        LLMProvider.GROQ,
    ])
    def test_get_llm_all_registered_providers(self, setup_test_providers, provider):
        """Test creating LLM instances for all registered providers."""
        # Act
        llm_instance = LLMFactory.get_llm(provider)
        
        # Assert
        assert llm_instance is not None
        assert llm_instance.provider_name == provider.value
        assert llm_instance._initialized is True


class TestLLMFactoryEdgeCases:
    """Test suite for LLMFactory edge cases and error handling."""
    
    def test_get_llm_provider_constructor_exception(self, clean_llm_registry):
        """Test LLM creation when provider constructor raises exception."""
        # Arrange
        @LLMRegistry.register(LLMProvider.OPENAI)
        class FailingProvider:
            def __init__(self):
                raise ValueError("Constructor failed")
        
        # Act & Assert
        with pytest.raises(ValueError) as exc_info:
            LLMFactory.get_llm(LLMProvider.OPENAI)
        
        assert "Constructor failed" in str(exc_info.value)
    
    def test_singleton_behavior(self):
        """Test that LLMFactory maintains singleton behavior."""
        # Act
        factory1 = LLMFactory()
        factory2 = LLMFactory()
        
        # Assert
        assert factory1 is factory2
    
    def test_provider_enum_string_conversion(self, setup_test_providers):
        """Test that provider methods work correctly with enum values."""
        # Act & Assert
        providers = LLMFactory.list_available_providers()
        provider_values = [p.value for p in providers]
        
        assert "openai" in provider_values
        assert "anthropic" in provider_values
        assert "groq" in provider_values
    
    def test_concurrent_provider_creation(self, setup_test_providers):
        """Test creating multiple LLM instances for different providers."""
        # Act
        openai_instance = LLMFactory.get_llm(LLMProvider.OPENAI)
        anthropic_instance = LLMFactory.get_llm(LLMProvider.ANTHROPIC)
        groq_instance = LLMFactory.get_llm(LLMProvider.GROQ)
        
        # Assert
        assert all(instance is not None for instance in [openai_instance, anthropic_instance, groq_instance])
        assert all(instance._initialized for instance in [openai_instance, anthropic_instance, groq_instance])
        
        # Check that instances are different and have correct providers
        assert openai_instance.provider_name == "openai"
        assert anthropic_instance.provider_name == "anthropic"
        assert groq_instance.provider_name == "groq"
        
        # Ensure they are different instances
        assert openai_instance is not anthropic_instance
        assert anthropic_instance is not groq_instance
        assert openai_instance is not groq_instance
    
    def test_get_default_llm_with_unregistered_default(self, clean_llm_registry):
        """Test getting default LLM when default provider is valid but not registered."""
        # Arrange
        with patch('app.core.config.application.llm.llm_config') as mock_config:
            mock_config.get_default_provider.return_value = "openai"
            
            # Act & Assert - Should fail because openai provider is not registered
            with pytest.raises(ValueError) as exc_info:
                LLMFactory.get_default_llm()
            
            assert "LLM provider 'LLMProvider.OPENAI' not available" in str(exc_info.value)
    
    def test_list_providers_returns_enum_values(self, setup_test_providers):
        """Test that list_available_providers returns LLMProvider enum values."""
        # Act
        providers = LLMFactory.list_available_providers()
        
        # Assert
        assert all(isinstance(provider, LLMProvider) for provider in providers)
        assert LLMProvider.OPENAI in providers
        assert LLMProvider.ANTHROPIC in providers
        assert LLMProvider.GROQ in providers
    
    def test_factory_static_methods_work_without_instantiation(self, setup_test_providers):
        """Test that all factory methods work as static methods without instantiation."""
        # Act & Assert - All these should work without creating factory instance
        providers = LLMFactory.list_available_providers()
        assert len(providers) == 3
        
        available = LLMFactory.is_provider_available(LLMProvider.OPENAI)
        assert isinstance(available, bool)
        
        llm = LLMFactory.get_llm(LLMProvider.OPENAI)
        assert llm is not None
