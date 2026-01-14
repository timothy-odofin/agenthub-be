"""
Unit tests for LLM Service.

Tests:
- Provider configuration validation
- Getting available providers
- Getting specific provider information
- Error handling for missing/unconfigured providers
"""

import pytest
from types import SimpleNamespace
from unittest.mock import Mock, patch
from app.services.llm_service import LLMService


class TestLLMServiceValidation:
    """Test provider configuration validation methods."""
    
    def test_is_provider_configured_with_valid_api_key(self):
        """Test that provider with valid API key is considered configured."""
        mock_config = Mock()
        mock_config.api_key = "sk-valid-key-123"
        
        result = LLMService._is_provider_configured("openai", mock_config)
        
        assert result is True
    
    def test_is_provider_configured_with_missing_api_key(self):
        """Test that provider with missing API key is not configured."""
        mock_config = Mock()
        mock_config.api_key = None
        
        result = LLMService._is_provider_configured("openai", mock_config)
        
        assert result is False
    
    def test_is_provider_configured_with_unresolved_env_var(self):
        """Test that provider with unresolved env variable is not configured."""
        mock_config = Mock()
        mock_config.api_key = "${OPENAI_API_KEY}"
        
        result = LLMService._is_provider_configured("openai", mock_config)
        
        assert result is False
    
    def test_is_provider_configured_ollama_with_valid_base_url(self):
        """Test that Ollama with valid base_url is configured (no API key needed)."""
        mock_config = Mock()
        mock_config.base_url = "http://localhost:11434"
        
        result = LLMService._is_provider_configured("ollama", mock_config)
        
        assert result is True
    
    def test_is_provider_configured_ollama_with_missing_base_url(self):
        """Test that Ollama without base_url is not configured."""
        mock_config = Mock()
        mock_config.base_url = None
        
        result = LLMService._is_provider_configured("ollama", mock_config)
        
        assert result is False
    
    def test_is_provider_configured_ollama_with_unresolved_base_url(self):
        """Test that Ollama with unresolved base_url env var is not configured."""
        mock_config = Mock()
        mock_config.base_url = "${OLLAMA_BASE_URL}"
        
        result = LLMService._is_provider_configured("ollama", mock_config)
        
        assert result is False
    
    def test_validate_provider_configured_success(self):
        """Test that validation passes for configured provider."""
        mock_config = Mock()
        mock_config.api_key = "sk-valid-key"
        
        # Should not raise any exception
        LLMService._validate_provider_configured("openai", mock_config)
    
    def test_validate_provider_configured_raises_for_missing_api_key(self):
        """Test that validation raises ValueError for missing API key."""
        mock_config = Mock()
        mock_config.api_key = None
        
        with pytest.raises(ValueError, match="not configured.*missing API key"):
            LLMService._validate_provider_configured("openai", mock_config)
    
    def test_validate_provider_configured_raises_for_ollama_missing_base_url(self):
        """Test that validation raises ValueError for Ollama without base_url."""
        mock_config = Mock()
        mock_config.base_url = None
        
        with pytest.raises(ValueError, match="not configured.*missing or invalid base_url"):
            LLMService._validate_provider_configured("ollama", mock_config)


class TestModelValidation:
    """Test model validation for providers."""
    
    @patch('app.core.config.settings')
    def test_validate_model_returns_default_when_no_model_provided(self, mock_settings):
        """Test that default model is returned when no model is provided."""
        mock_openai = SimpleNamespace(
            api_key="sk-valid-key",
            model="gpt-4o-mini",
            model_versions=["gpt-4", "gpt-4o-mini", "gpt-5"]
        )
        mock_settings.llm = SimpleNamespace(openai=mock_openai)
        
        result = LLMService.validate_model_for_provider("openai", model=None)
        
        assert result == "gpt-4o-mini"
    
    @patch('app.core.config.settings')
    def test_validate_model_accepts_valid_model(self, mock_settings):
        """Test that validation passes when model is in model_versions."""
        mock_openai = SimpleNamespace(
            api_key="sk-valid-key",
            model="gpt-4o-mini",
            model_versions=["gpt-4", "gpt-4o-mini", "gpt-5"]
        )
        mock_settings.llm = SimpleNamespace(openai=mock_openai)
        
        result = LLMService.validate_model_for_provider("openai", model="gpt-5")
        
        assert result == "gpt-5"
    
    @patch('app.core.config.settings')
    def test_validate_model_rejects_invalid_model(self, mock_settings):
        """Test that validation raises error when model not in model_versions."""
        mock_openai = SimpleNamespace(
            api_key="sk-valid-key",
            model="gpt-4o-mini",
            model_versions=["gpt-4", "gpt-4o-mini", "gpt-5"]
        )
        mock_settings.llm = SimpleNamespace(openai=mock_openai)
        
        with pytest.raises(ValueError, match="Model 'gpt-3' is not supported"):
            LLMService.validate_model_for_provider("openai", model="gpt-3")
    
    @patch('app.core.config.settings')
    def test_validate_model_raises_for_nonexistent_provider(self, mock_settings):
        """Test that validation raises error for unknown provider."""
        mock_settings.llm = SimpleNamespace()
        
        with pytest.raises(ValueError, match="Provider 'unknown' not found"):
            LLMService.validate_model_for_provider("unknown", model="gpt-4")
    
    @patch('app.core.config.settings')
    def test_validate_model_raises_for_unconfigured_provider(self, mock_settings):
        """Test that validation raises error for provider without API key."""
        mock_openai = SimpleNamespace(
            api_key="${OPENAI_API_KEY}",  # Unresolved env var
            model="gpt-4",
            model_versions=["gpt-4", "gpt-5"]
        )
        mock_settings.llm = SimpleNamespace(openai=mock_openai)
        
        with pytest.raises(ValueError, match="not configured.*missing API key"):
            LLMService.validate_model_for_provider("openai", model="gpt-4")
    
    @patch('app.core.config.settings')
    def test_validate_model_raises_when_no_default_and_no_model_provided(self, mock_settings):
        """Test that validation raises error when no default model and none provided."""
        mock_openai = SimpleNamespace(
            api_key="sk-valid-key",
            model=None,  # No default model
            model_versions=["gpt-4", "gpt-5"]
        )
        mock_settings.llm = SimpleNamespace(openai=mock_openai)
        
        with pytest.raises(ValueError, match="has no default model configured"):
            LLMService.validate_model_for_provider("openai", model=None)
    
    @patch('app.core.config.settings')
    def test_validate_model_allows_any_model_when_no_versions_list(self, mock_settings):
        """Test that validation passes when model_versions is empty (allows any)."""
        mock_openai = SimpleNamespace(
            api_key="sk-valid-key",
            model="gpt-4",
            model_versions=[]  # No restrictions
        )
        mock_settings.llm = SimpleNamespace(openai=mock_openai)
        
        # Should not raise, even though "custom-model" isn't in the list
        result = LLMService.validate_model_for_provider("openai", model="custom-model")
        assert result == "custom-model"


class TestGetAvailableProviders:
    """Test getting list of available providers."""
    
    @patch('app.core.config.settings')
    def test_get_available_providers_returns_configured_providers(self, mock_settings):
        """Test that only configured providers are returned."""
        # Setup mock settings using SimpleNamespace for clean __dict__ access
        mock_default = SimpleNamespace(provider="openai")
        mock_openai = SimpleNamespace(
            api_key="sk-valid-key",
            display_name="OpenAI",
            model_versions=["gpt-4", "gpt-5-mini"],
            model="gpt-5-mini"
        )
        mock_anthropic = SimpleNamespace(
            api_key="sk-anthropic-key",
            display_name="Anthropic (Claude)",
            model_versions=["claude-3-opus", "claude-3-sonnet"],
            model="claude-3-sonnet"
        )
        mock_groq = SimpleNamespace(api_key="${GROQ_API_KEY}")  # Unresolved - should be skipped
        
        mock_llm = SimpleNamespace(
            default=mock_default,
            openai=mock_openai,
            anthropic=mock_anthropic,
            groq=mock_groq,
            _private='should_be_skipped'
        )
        mock_settings.llm = mock_llm
        
        # Call the method
        result = LLMService.get_available_providers()
        
        # Assertions
        assert len(result) == 2  # Only OpenAI and Anthropic (Groq not configured)
        
        # Check OpenAI
        openai_provider = next((p for p in result if p['name'] == 'openai'), None)
        assert openai_provider is not None
        assert openai_provider['display_name'] == "OpenAI"
        assert openai_provider['model_versions'] == ["gpt-4", "gpt-5-mini"]
        assert openai_provider['default_model'] == "gpt-5-mini"
        assert openai_provider['is_default'] is True
        
        # Check Anthropic
        anthropic_provider = next((p for p in result if p['name'] == 'anthropic'), None)
        assert anthropic_provider is not None
        assert anthropic_provider['display_name'] == "Anthropic (Claude)"
        assert anthropic_provider['is_default'] is False
    
    @patch('app.core.config.settings')
    def test_get_available_providers_with_ollama(self, mock_settings):
        """Test that Ollama is included when base_url is configured."""
        mock_ollama = SimpleNamespace(
            base_url="http://localhost:11434",
            display_name="Ollama (Local)",
            model_versions=["llama3", "mistral"],
            model="llama3"
        )
        mock_default = SimpleNamespace(provider="ollama")
        
        mock_llm = SimpleNamespace(
            default=mock_default,
            ollama=mock_ollama
        )
        mock_settings.llm = mock_llm
        
        result = LLMService.get_available_providers()
        
        assert len(result) == 1
        assert result[0]['name'] == 'ollama'
        assert result[0]['is_default'] is True
    
    @patch('app.core.config.settings')
    def test_get_available_providers_handles_missing_display_name(self, mock_settings):
        """Test that missing display_name uses capitalized provider name."""
        mock_openai = SimpleNamespace(
            api_key="sk-key",
            model_versions=["gpt-4"],
            model="gpt-4"
            # No display_name attribute
        )
        mock_default = SimpleNamespace(provider="openai")
        
        mock_llm = SimpleNamespace(
            default=mock_default,
            openai=mock_openai
        )
        mock_settings.llm = mock_llm
        
        result = LLMService.get_available_providers()
        
        assert result[0]['display_name'] == "Openai"  # Capitalized provider name
    
    @patch('app.core.config.settings')
    def test_get_available_providers_returns_empty_when_none_configured(self, mock_settings):
        """Test that empty list is returned when no providers are configured."""
        mock_default = SimpleNamespace(provider="openai")
        
        mock_llm = SimpleNamespace(default=mock_default)
        mock_settings.llm = mock_llm
        
        result = LLMService.get_available_providers()
        
        assert result == []


class TestGetProviderInfo:
    """Test getting specific provider information."""
    
    @patch('app.core.config.settings')
    def test_get_provider_info_returns_complete_details(self, mock_settings):
        """Test that provider info includes all expected fields."""
        mock_openai = Mock()
        mock_openai.api_key = "sk-valid-key"
        mock_openai.display_name = "OpenAI"
        mock_openai.model_versions = ["gpt-4", "gpt-5-mini"]
        mock_openai.model = "gpt-5-mini"
        mock_openai.base_url = "https://api.openai.com/v1"
        mock_openai.timeout = 60
        mock_openai.max_tokens = 4096
        
        mock_default = Mock()
        mock_default.provider = "openai"
        
        mock_llm = Mock()
        mock_llm.openai = mock_openai
        mock_llm.default = mock_default
        mock_settings.llm = mock_llm
        
        result = LLMService.get_provider_info("openai")
        
        assert result['name'] == "openai"
        assert result['display_name'] == "OpenAI"
        assert result['model_versions'] == ["gpt-4", "gpt-5-mini"]
        assert result['default_model'] == "gpt-5-mini"
        assert result['is_default'] is True
        assert result['base_url'] == "https://api.openai.com/v1"
        assert result['timeout'] == 60
        assert result['max_tokens'] == 4096
    
    @patch('app.core.config.settings')
    def test_get_provider_info_raises_for_nonexistent_provider(self, mock_settings):
        """Test that ValueError is raised for provider that doesn't exist."""
        mock_llm = Mock()
        mock_llm.nonexistent = None
        mock_settings.llm = mock_llm
        
        with pytest.raises(ValueError, match="not found in configuration"):
            LLMService.get_provider_info("nonexistent")
    
    @patch('app.core.config.settings')
    def test_get_provider_info_raises_for_unconfigured_provider(self, mock_settings):
        """Test that ValueError is raised for provider without API key."""
        mock_openai = Mock()
        mock_openai.api_key = "${OPENAI_API_KEY}"  # Unresolved
        
        mock_llm = Mock()
        mock_llm.openai = mock_openai
        mock_settings.llm = mock_llm
        
        with pytest.raises(ValueError, match="not configured.*missing API key"):
            LLMService.get_provider_info("openai")
    
    @patch('app.core.config.settings')
    def test_get_provider_info_for_non_default_provider(self, mock_settings):
        """Test that is_default is False for non-default provider."""
        mock_anthropic = Mock()
        mock_anthropic.api_key = "sk-anthropic-key"
        mock_anthropic.display_name = "Anthropic"
        mock_anthropic.model_versions = ["claude-3-opus"]
        mock_anthropic.model = "claude-3-opus"
        mock_anthropic.base_url = "https://api.anthropic.com"
        mock_anthropic.timeout = 60
        mock_anthropic.max_tokens = 4096
        
        mock_default = Mock()
        mock_default.provider = "openai"  # Different from anthropic
        
        mock_llm = Mock()
        mock_llm.anthropic = mock_anthropic
        mock_llm.default = mock_default
        mock_settings.llm = mock_llm
        
        result = LLMService.get_provider_info("anthropic")
        
        assert result['is_default'] is False
