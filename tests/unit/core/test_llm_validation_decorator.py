"""
Unit tests for LLM validation decorator.

Tests:
- Provider validation (provided, default, invalid)
- Model validation (provided, default, invalid)
- Error handling and HTTP exceptions
- Request body modification
"""

import pytest
from types import SimpleNamespace
from unittest.mock import Mock, patch, MagicMock
from fastapi import HTTPException
from pydantic import BaseModel

from app.core.decorators.llm_validation import validate_llm_params, validate_llm_params_sync


class MockChatRequest(BaseModel):
    """Mock request model for testing."""
    message: str
    provider: str = None
    model: str = None


class TestValidateLLMParamsDecorator:
    """Test the async validate_llm_params decorator."""
    
    @pytest.mark.asyncio
    @patch('app.core.decorators.llm_validation.settings')
    @patch('app.core.decorators.llm_validation.LLMService')
    async def test_uses_default_provider_when_not_provided(self, mock_service, mock_settings):
        """Test that decorator uses default provider when none provided."""
        mock_settings.llm.default.provider = "openai"
        mock_service.validate_model_for_provider.return_value = "gpt-4o-mini"
        
        @validate_llm_params
        async def mock_endpoint(request: MockChatRequest):
            return {"provider": request.provider, "model": request.model}
        
        request = MockChatRequest(message="Hello")
        result = await mock_endpoint(request=request)
        
        # Verify service was called with default provider
        mock_service.validate_model_for_provider.assert_called_once_with("openai", None)
        assert result["provider"] == "openai"
        assert result["model"] == "gpt-4o-mini"
    
    @pytest.mark.asyncio
    @patch('app.core.decorators.llm_validation.settings')
    @patch('app.core.decorators.llm_validation.LLMService')
    async def test_validates_provided_provider(self, mock_service, mock_settings):
        """Test that decorator validates provided provider."""
        mock_service.validate_model_for_provider.return_value = "claude-sonnet-4-5"
        
        @validate_llm_params
        async def mock_endpoint(request: MockChatRequest):
            return {"provider": request.provider, "model": request.model}
        
        request = MockChatRequest(message="Hello", provider="anthropic")
        result = await mock_endpoint(request=request)
        
        # Verify service was called with provided provider
        mock_service.validate_model_for_provider.assert_called_once_with("anthropic", None)
        assert result["provider"] == "anthropic"
        assert result["model"] == "claude-sonnet-4-5"
    
    @pytest.mark.asyncio
    @patch('app.core.decorators.llm_validation.settings')
    @patch('app.core.decorators.llm_validation.LLMService')
    async def test_validates_provided_model(self, mock_service, mock_settings):
        """Test that decorator validates provided model."""
        mock_settings.llm.default.provider = "openai"
        mock_service.validate_model_for_provider.return_value = "gpt-5"
        
        @validate_llm_params
        async def mock_endpoint(request: MockChatRequest):
            return {"provider": request.provider, "model": request.model}
        
        request = MockChatRequest(message="Hello", model="gpt-5")
        result = await mock_endpoint(request=request)
        
        # Verify service was called with provided model
        mock_service.validate_model_for_provider.assert_called_once_with("openai", "gpt-5")
        assert result["model"] == "gpt-5"
    
    @pytest.mark.asyncio
    @patch('app.core.decorators.llm_validation.settings')
    @patch('app.core.decorators.llm_validation.LLMService')
    async def test_validates_both_provider_and_model(self, mock_service, mock_settings):
        """Test validation when both provider and model are provided."""
        mock_service.validate_model_for_provider.return_value = "claude-opus-4-5"
        
        @validate_llm_params
        async def mock_endpoint(request: MockChatRequest):
            return {"provider": request.provider, "model": request.model}
        
        request = MockChatRequest(message="Hello", provider="anthropic", model="claude-opus-4-5")
        result = await mock_endpoint(request=request)
        
        mock_service.validate_model_for_provider.assert_called_once_with("anthropic", "claude-opus-4-5")
        assert result["provider"] == "anthropic"
        assert result["model"] == "claude-opus-4-5"
    
    @pytest.mark.asyncio
    @patch('app.core.decorators.llm_validation.settings')
    @patch('app.core.decorators.llm_validation.LLMService')
    async def test_raises_400_for_invalid_provider(self, mock_service, mock_settings):
        """Test that decorator raises 400 for invalid provider."""
        mock_service.validate_model_for_provider.side_effect = ValueError(
            "Provider 'invalid' not found in configuration"
        )
        
        @validate_llm_params
        async def mock_endpoint(request: MockChatRequest):
            return {"provider": request.provider}
        
        request = MockChatRequest(message="Hello", provider="invalid")
        
        with pytest.raises(HTTPException) as exc_info:
            await mock_endpoint(request=request)
        
        assert exc_info.value.status_code == 400
        assert "not found in configuration" in exc_info.value.detail
    
    @pytest.mark.asyncio
    @patch('app.core.decorators.llm_validation.settings')
    @patch('app.core.decorators.llm_validation.LLMService')
    async def test_raises_400_for_invalid_model(self, mock_service, mock_settings):
        """Test that decorator raises 400 for invalid model."""
        mock_settings.llm.default.provider = "openai"
        mock_service.validate_model_for_provider.side_effect = ValueError(
            "Model 'invalid-model' is not supported by provider 'openai'"
        )
        
        @validate_llm_params
        async def mock_endpoint(request: MockChatRequest):
            return {"model": request.model}
        
        request = MockChatRequest(message="Hello", model="invalid-model")
        
        with pytest.raises(HTTPException) as exc_info:
            await mock_endpoint(request=request)
        
        assert exc_info.value.status_code == 400
        assert "not supported" in exc_info.value.detail
    
    @pytest.mark.asyncio
    @patch('app.core.decorators.llm_validation.settings')
    @patch('app.core.decorators.llm_validation.LLMService')
    async def test_raises_400_for_unconfigured_provider(self, mock_service, mock_settings):
        """Test that decorator raises 400 for unconfigured provider."""
        mock_service.validate_model_for_provider.side_effect = ValueError(
            "Provider 'groq' not configured (missing API key)"
        )
        
        @validate_llm_params
        async def mock_endpoint(request: MockChatRequest):
            return {}
        
        request = MockChatRequest(message="Hello", provider="groq")
        
        with pytest.raises(HTTPException) as exc_info:
            await mock_endpoint(request=request)
        
        assert exc_info.value.status_code == 400
        assert "not configured" in exc_info.value.detail
    
    @pytest.mark.asyncio
    @patch('app.core.decorators.llm_validation.settings')
    @patch('app.core.decorators.llm_validation.LLMService')
    async def test_raises_500_for_unexpected_errors(self, mock_service, mock_settings):
        """Test that decorator raises 500 for unexpected errors."""
        mock_settings.llm.default.provider = "openai"
        mock_service.validate_model_for_provider.side_effect = Exception("Unexpected error")
        
        @validate_llm_params
        async def mock_endpoint(request: MockChatRequest):
            return {}
        
        request = MockChatRequest(message="Hello")
        
        with pytest.raises(HTTPException) as exc_info:
            await mock_endpoint(request=request)
        
        assert exc_info.value.status_code == 500
        assert "Failed to validate LLM parameters" in exc_info.value.detail
    
    @pytest.mark.asyncio
    async def test_skips_validation_when_no_pydantic_model(self):
        """Test that decorator skips validation when no Pydantic model in args."""
        @validate_llm_params
        async def mock_endpoint(message: str):
            return {"message": message}
        
        # Should not raise, just pass through
        result = await mock_endpoint(message="Hello")
        assert result["message"] == "Hello"


class TestValidateLLMParamsSyncDecorator:
    """Test the synchronous validate_llm_params_sync decorator."""
    
    @patch('app.core.decorators.llm_validation.settings')
    @patch('app.core.decorators.llm_validation.LLMService')
    def test_sync_decorator_validates_provider(self, mock_service, mock_settings):
        """Test that sync decorator validates provider."""
        mock_settings.llm.default.provider = "openai"
        mock_service.validate_model_for_provider.return_value = "gpt-4o-mini"
        
        @validate_llm_params_sync
        def mock_endpoint(request: MockChatRequest):
            return {"provider": request.provider, "model": request.model}
        
        request = MockChatRequest(message="Hello")
        result = mock_endpoint(request=request)
        
        mock_service.validate_model_for_provider.assert_called_once_with("openai", None)
        assert result["provider"] == "openai"
        assert result["model"] == "gpt-4o-mini"
    
    @patch('app.core.decorators.llm_validation.settings')
    @patch('app.core.decorators.llm_validation.LLMService')
    def test_sync_decorator_raises_400_for_invalid_model(self, mock_service, mock_settings):
        """Test that sync decorator raises 400 for invalid model."""
        mock_settings.llm.default.provider = "openai"
        mock_service.validate_model_for_provider.side_effect = ValueError(
            "Model 'gpt-2' is not supported"
        )
        
        @validate_llm_params_sync
        def mock_endpoint(request: MockChatRequest):
            return {}
        
        request = MockChatRequest(message="Hello", model="gpt-2")
        
        with pytest.raises(HTTPException) as exc_info:
            mock_endpoint(request=request)
        
        assert exc_info.value.status_code == 400
        assert "not supported" in exc_info.value.detail
