"""
Unit tests for LLM API endpoints.

Tests:
- GET /api/v1/llm/providers
- GET /api/v1/llm/providers/{provider_name}
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, Mock
from app.main import app

client = TestClient(app)


class TestListProvidersEndpoint:
    """Test GET /api/v1/llm/providers endpoint."""
    
    @patch('app.api.v1.llm.llm_service')
    def test_list_providers_returns_success(self, mock_llm_service):
        """Test that endpoint returns success response with providers."""
        mock_llm_service.get_available_providers.return_value = [
            {
                "name": "openai",
                "display_name": "OpenAI",
                "model_versions": ["gpt-4", "gpt-5-mini"],
                "default_model": "gpt-5-mini",
                "is_default": True
            },
            {
                "name": "anthropic",
                "display_name": "Anthropic (Claude)",
                "model_versions": ["claude-3-opus", "claude-3-sonnet"],
                "default_model": "claude-3-sonnet",
                "is_default": False
            }
        ]
        
        response = client.get("/api/v1/llm/providers")
        
        assert response.status_code == 200
        data = response.json()
        assert data['success'] is True
        assert data['total'] == 2
        assert len(data['providers']) == 2
        assert data['providers'][0]['name'] == "openai"
        assert data['providers'][1]['name'] == "anthropic"
    
    @patch('app.api.v1.llm.llm_service')
    def test_list_providers_returns_empty_list_when_none_configured(self, mock_llm_service):
        """Test that endpoint returns empty list when no providers configured."""
        mock_llm_service.get_available_providers.return_value = []
        
        response = client.get("/api/v1/llm/providers")
        
        assert response.status_code == 200
        data = response.json()
        assert data['success'] is True
        assert data['total'] == 0
        assert data['providers'] == []
    
    @patch('app.api.v1.llm.llm_service')
    def test_list_providers_handles_service_exception(self, mock_llm_service):
        """Test that endpoint handles service exceptions gracefully."""
        mock_llm_service.get_available_providers.side_effect = Exception("Service error")
        
        response = client.get("/api/v1/llm/providers")
        
        assert response.status_code == 500
        data = response.json()
        assert "error" in data
        assert "Failed to fetch providers" in data['error']['message']


class TestGetProviderEndpoint:
    """Test GET /api/v1/llm/providers/{provider_name} endpoint."""
    
    @patch('app.api.v1.llm.llm_service')
    def test_get_provider_returns_detailed_info(self, mock_llm_service):
        """Test that endpoint returns detailed provider information."""
        mock_llm_service.get_provider_info.return_value = {
            "name": "openai",
            "display_name": "OpenAI",
            "model_versions": ["gpt-4", "gpt-5-mini"],
            "default_model": "gpt-5-mini",
            "is_default": True,
            "base_url": "https://api.openai.com/v1",
            "timeout": 60,
            "max_tokens": 4096
        }
        
        response = client.get("/api/v1/llm/providers/openai")
        
        assert response.status_code == 200
        data = response.json()
        assert data['name'] == "openai"
        assert data['display_name'] == "OpenAI"
        assert data['base_url'] == "https://api.openai.com/v1"
        assert data['timeout'] == 60
        assert data['max_tokens'] == 4096
    
    @patch('app.api.v1.llm.llm_service')
    def test_get_provider_returns_404_for_nonexistent_provider(self, mock_llm_service):
        """Test that endpoint returns 404 for provider that doesn't exist."""
        mock_llm_service.get_provider_info.side_effect = ValueError(
            "Provider 'nonexistent' not found in configuration"
        )
        
        response = client.get("/api/v1/llm/providers/nonexistent")
        
        assert response.status_code == 404
        data = response.json()
        assert "error" in data
        assert "not found in configuration" in data['error']['message']
    
    @patch('app.api.v1.llm.llm_service')
    def test_get_provider_returns_404_for_unconfigured_provider(self, mock_llm_service):
        """Test that endpoint returns 404 for provider without API key."""
        mock_llm_service.get_provider_info.side_effect = ValueError(
            "Provider 'openai' not configured (missing API key)"
        )
        
        response = client.get("/api/v1/llm/providers/openai")
        
        assert response.status_code == 404
        data = response.json()
        assert "error" in data
        assert "not configured" in data['error']['message']
    
    @patch('app.api.v1.llm.llm_service')
    def test_get_provider_handles_service_exception(self, mock_llm_service):
        """Test that endpoint handles unexpected service exceptions."""
        mock_llm_service.get_provider_info.side_effect = Exception("Unexpected error")
        
        response = client.get("/api/v1/llm/providers/openai")
        
        assert response.status_code == 500
        data = response.json()
        assert "error" in data
        assert "Failed to fetch provider" in data['error']['message']
