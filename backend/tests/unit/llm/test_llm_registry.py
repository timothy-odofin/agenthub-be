"""
Unit tests for LLMRegistry class.

Tests the registry pattern for managing LLM provider classes with proper registration
and lookup functionality. Following Python open-source testing best practices.
"""

import pytest
from unittest.mock import patch, Mock
from typing import Set, Dict, Any, List, AsyncGenerator

from app.llm.base.llm_registry import LLMRegistry
from app.llm.base.base_llm_provider import BaseLLMProvider, LLMResponse
from app.core.constants import LLMProvider, LLMCapability
from app.schemas.llm_output import LLMOutputBase, StructuredLLMResponse


class MockLLMProvider(BaseLLMProvider):
    """Mock LLM provider implementation for testing."""
    
    def __init__(self, provider_name: str = "mock"):
        self.provider_name = provider_name
        self.config = {"api_key": "test_key", "model": "test_model"}
        self._initialized = False
        self.client = None
        self._supported_capabilities = {LLMCapability.CHAT, LLMCapability.STREAMING}
    
    def get_config_name(self) -> str:
        return self.provider_name
    
    def validate_config(self) -> None:
        if not self.config.get("api_key"):
            raise ValueError("API key is required")
    
    async def initialize(self) -> None:
        self._initialized = True
        self.client = Mock()
    
    async def generate(self, prompt: str, **kwargs) -> LLMResponse:
        return LLMResponse(
            content=f"Mock response for: {prompt}",
            usage={"tokens": 10},
            metadata={"model": "mock_model"}
        )
    
    async def stream_generate(self, prompt: str, **kwargs) -> AsyncGenerator[str, None]:
        for chunk in ["Mock ", "streaming ", "response"]:
            yield chunk
    
    def get_available_models(self) -> List[str]:
        return ["mock_model_1", "mock_model_2"]
    
    def supports_capability(self, capability: LLMCapability) -> bool:
        return capability in self._supported_capabilities


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
    
    yield
    
    # Restore original state
    LLMRegistry._registry = original_registry
    LLMRegistry._providers_imported = original_imported
    LLMRegistry._auto_import_enabled = original_auto_import


class TestLLMRegistry:
    """Test suite for LLMRegistry class."""
    
    def test_register_decorator_functionality(self, clean_llm_registry):
        """Test that the register decorator properly registers providers."""
        # Arrange & Act
        @LLMRegistry.register(LLMProvider.OPENAI)
        class TestLLMProvider(MockLLMProvider):
            def __init__(self):
                super().__init__("openai")
        
        # Assert
        assert LLMRegistry.is_provider_registered(LLMProvider.OPENAI)
        assert LLMRegistry.get_provider_class(LLMProvider.OPENAI) == TestLLMProvider
    
    def test_register_multiple_providers(self, clean_llm_registry):
        """Test registering multiple different providers."""
        # Arrange & Act
        @LLMRegistry.register(LLMProvider.OPENAI)
        class OpenAIMockProvider(MockLLMProvider):
            def __init__(self):
                super().__init__("openai")
        
        @LLMRegistry.register(LLMProvider.ANTHROPIC)
        class AnthropicMockProvider(MockLLMProvider):
            def __init__(self):
                super().__init__("anthropic")
        
        @LLMRegistry.register(LLMProvider.GROQ)
        class GroqMockProvider(MockLLMProvider):
            def __init__(self):
                super().__init__("groq")
        
        # Assert
        assert len(LLMRegistry._registry) == 3
        assert LLMRegistry.is_provider_registered(LLMProvider.OPENAI)
        assert LLMRegistry.is_provider_registered(LLMProvider.ANTHROPIC)
        assert LLMRegistry.is_provider_registered(LLMProvider.GROQ)
        
        # Check specific providers
        assert LLMRegistry.get_provider_class(LLMProvider.OPENAI) == OpenAIMockProvider
        assert LLMRegistry.get_provider_class(LLMProvider.ANTHROPIC) == AnthropicMockProvider
        assert LLMRegistry.get_provider_class(LLMProvider.GROQ) == GroqMockProvider
    
    def test_register_override_warning(self, clean_llm_registry):
        """Test that registering the same provider twice works (last one wins)."""
        # Arrange
        @LLMRegistry.register(LLMProvider.OPENAI)
        class FirstProvider(MockLLMProvider):
            pass
        
        @LLMRegistry.register(LLMProvider.OPENAI)
        class SecondProvider(MockLLMProvider):
            pass
        
        # Assert
        assert LLMRegistry.get_provider_class(LLMProvider.OPENAI) == SecondProvider
    
    def test_get_provider_class_success(self, clean_llm_registry):
        """Test successful provider class retrieval."""
        # Arrange
        @LLMRegistry.register(LLMProvider.OPENAI)
        class TestProvider(MockLLMProvider):
            pass
        
        # Act
        provider_class = LLMRegistry.get_provider_class(LLMProvider.OPENAI)
        
        # Assert
        assert provider_class == TestProvider
    
    def test_get_provider_class_not_registered_raises_value_error(self, clean_llm_registry):
        """Test that getting an unregistered provider raises ValueError."""
        # Act & Assert
        with pytest.raises(ValueError) as exc_info:
            LLMRegistry.get_provider_class(LLMProvider.OPENAI)
        
        error_message = str(exc_info.value)
        assert "LLM provider 'LLMProvider.OPENAI' not found in registry" in error_message
        assert "Available:" in error_message
    
    def test_list_providers_empty(self, clean_llm_registry):
        """Test listing providers when registry is empty."""
        # Act
        providers = LLMRegistry.list_providers()
        
        # Assert
        assert providers == []
    
    def test_list_providers_populated(self, clean_llm_registry):
        """Test listing providers when registry has providers."""
        # Arrange
        @LLMRegistry.register(LLMProvider.OPENAI)
        class OpenAIProvider(MockLLMProvider):
            pass
        
        @LLMRegistry.register(LLMProvider.GROQ)
        class GroqProvider(MockLLMProvider):
            pass
        
        # Act
        providers = LLMRegistry.list_providers()
        
        # Assert
        assert len(providers) == 2
        assert LLMProvider.OPENAI in providers
        assert LLMProvider.GROQ in providers
    
    def test_is_provider_registered_true(self, clean_llm_registry):
        """Test is_provider_registered returns True for registered provider."""
        # Arrange
        @LLMRegistry.register(LLMProvider.OPENAI)
        class TestProvider(MockLLMProvider):
            pass
        
        # Act & Assert
        assert LLMRegistry.is_provider_registered(LLMProvider.OPENAI) is True
    
    def test_is_provider_registered_false(self, clean_llm_registry):
        """Test is_provider_registered returns False for unregistered provider."""
        # Act & Assert
        assert LLMRegistry.is_provider_registered(LLMProvider.OPENAI) is False
    
    @pytest.mark.parametrize("provider", [
        LLMProvider.OPENAI,
        LLMProvider.ANTHROPIC,
        LLMProvider.GROQ,
        LLMProvider.GOOGLE,
        LLMProvider.OLLAMA,
    ])
    def test_register_all_enum_providers(self, clean_llm_registry, provider):
        """Test registering providers for all LLMProvider enum values."""
        # Arrange & Act
        @LLMRegistry.register(provider)
        class ParameterizedProvider(MockLLMProvider):
            def __init__(self):
                super().__init__(provider.value)
        
        # Assert
        assert LLMRegistry.is_provider_registered(provider)
        assert LLMRegistry.get_provider_class(provider) == ParameterizedProvider
    
    def test_ensure_providers_imported_called(self, clean_llm_registry):
        """Test that _ensure_providers_imported is called by registry methods."""
        # Arrange
        with patch.object(LLMRegistry, '_ensure_providers_imported') as mock_import:
            # Act
            LLMRegistry.list_providers()
            LLMRegistry.is_provider_registered(LLMProvider.OPENAI)
            try:
                LLMRegistry.get_provider_class(LLMProvider.OPENAI)
            except ValueError:
                pass  # Expected when provider not registered
            
            # Assert
            assert mock_import.call_count == 3
    
    def test_registry_state_persistence_across_operations(self, clean_llm_registry):
        """Test that registry state persists across multiple operations."""
        # Arrange
        @LLMRegistry.register(LLMProvider.OPENAI)
        class PersistentProvider(MockLLMProvider):
            pass
        
        # Act & Assert
        # First check
        assert LLMRegistry.is_provider_registered(LLMProvider.OPENAI)
        
        # List providers
        providers = LLMRegistry.list_providers()
        assert LLMProvider.OPENAI in providers
        
        # Get provider class
        provider_class = LLMRegistry.get_provider_class(LLMProvider.OPENAI)
        assert provider_class == PersistentProvider
        
        # Check again - should still be there
        assert LLMRegistry.is_provider_registered(LLMProvider.OPENAI)
    
    def test_decorator_returns_original_class(self, clean_llm_registry):
        """Test that the register decorator returns the original class unchanged."""
        # Arrange
        @LLMRegistry.register(LLMProvider.OPENAI)
        class OriginalProvider(MockLLMProvider):
            test_attribute = "original_value"
        
        # Assert
        assert hasattr(OriginalProvider, 'test_attribute')
        assert OriginalProvider.test_attribute == "original_value"
        assert LLMRegistry.get_provider_class(LLMProvider.OPENAI) == OriginalProvider


class TestLLMRegistryEdgeCases:
    """Test suite for LLMRegistry edge cases and error handling."""
    
    def test_register_with_invalid_provider_class(self, clean_llm_registry):
        """Test registering with a class that doesn't inherit from BaseLLMProvider."""
        # Arrange & Act - This should still work (registry doesn't enforce inheritance)
        @LLMRegistry.register(LLMProvider.OPENAI)
        class InvalidProviderWithDecorator:
            pass
        
        # Assert - Registry accepts any class, validation happens at runtime
        assert LLMRegistry.is_provider_registered(LLMProvider.OPENAI)
        assert LLMRegistry.get_provider_class(LLMProvider.OPENAI) == InvalidProviderWithDecorator
    
    def test_registry_thread_safety_simulation(self, clean_llm_registry):
        """Test registry operations that might be called concurrently."""
        # Arrange
        @LLMRegistry.register(LLMProvider.OPENAI)
        class ThreadSafeProvider(MockLLMProvider):
            pass
        
        # Act - Simulate concurrent access patterns
        results = []
        for _ in range(10):
            results.append(LLMRegistry.is_provider_registered(LLMProvider.OPENAI))
            results.append(LLMRegistry.get_provider_class(LLMProvider.OPENAI) == ThreadSafeProvider)
            results.append(LLMProvider.OPENAI in LLMRegistry.list_providers())
        
        # Assert - All operations should succeed consistently
        assert all(results)
    
    def test_ensure_providers_imported_handles_import_error(self, clean_llm_registry):
        """Test that _ensure_providers_imported handles import errors gracefully."""
        # Arrange - Enable auto-import for this test and mock the import to raise an ImportError 
        LLMRegistry.set_auto_import(True)
        
        def mock_import(name, *args, **kwargs):
            if name == 'app.llm.providers':
                raise ImportError("Module not found")
            # For other imports, don't intercept - use original import
            raise ImportError(f"Unmocked import: {name}")
        
        # Act & Assert - Should not raise exception
        with patch('builtins.__import__', side_effect=mock_import):
            try:
                LLMRegistry._ensure_providers_imported()
                # The flag should remain False after the failed import
                assert LLMRegistry._providers_imported is False
            except ImportError:
                pytest.fail("_ensure_providers_imported should handle import errors gracefully")
    
    def test_providers_imported_flag_behavior(self, clean_llm_registry):
        """Test that _providers_imported flag works correctly."""
        # Arrange - Enable auto-import for this test 
        LLMRegistry.set_auto_import(True)
        assert LLMRegistry._providers_imported is False
        
        # Act - Mock successful import to test the flag setting
        import types
        mock_module = types.ModuleType('mock_providers')
        
        with patch('builtins.__import__') as mock_import:
            # Configure mock to succeed for providers module
            def side_effect(name, *args, **kwargs):
                if name == 'app.llm.providers':
                    # Simulate successful import by returning a mock module
                    return mock_module
                # For other imports, don't intercept - use original import
                raise ImportError(f"Unmocked import: {name}")
            
            mock_import.side_effect = side_effect
            LLMRegistry._ensure_providers_imported()
        
        # Assert
        assert LLMRegistry._providers_imported is True
        
        # Test that subsequent calls don't re-import
        with patch('builtins.__import__') as mock_import_2:
            LLMRegistry._ensure_providers_imported()
            # The import should not be called again since flag is True
            assert not mock_import_2.called
        initial_registry_state = LLMRegistry._registry.copy()
        LLMRegistry._ensure_providers_imported()  # Should be a no-op
        assert LLMRegistry._registry == initial_registry_state
