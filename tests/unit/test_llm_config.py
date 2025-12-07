"""
Unit tests for LLMConfig class.

These tests focus on the LLMConfig logic by mocking the Settings system,
ensuring proper mapping and configuration access without testing the Settings
integration (which has its own integration tests).
"""

import pytest
from unittest.mock import Mock, patch
from typing import Dict, Any

from app.core.config.framework.dynamic_config import DynamicConfig


class TestLLMConfig:
    """Test suite for LLMConfig class."""

    @pytest.fixture
    def mock_settings(self):
        """Create a mock Settings object with comprehensive LLM configuration."""
        mock = Mock()
        
        # Mock main LLM configuration
        mock.llm = DynamicConfig({
            'provider': 'openai',
            'model': 'gpt-4',
            'temperature': 0.1,
            'max_tokens': 4096,
            'timeout': 30,
            'max_retries': 3,
            
            # Provider-specific configs
            'openai': {
                'api_key': 'test-openai-key',
                'base_url': 'https://api.openai.com/v1',
                'model': 'gpt-4-turbo',
                'temperature': 0.2,
                'max_tokens': 8192,
                'timeout': 60
            },
            'groq': {
                'api_key': 'test-groq-key',
                'base_url': 'https://api.groq.com/openai/v1',
                'model': 'llama-3.3-70b-versatile',
                'temperature': 0.7,
                'max_tokens': 4000,
                'timeout': 60
            },
            'anthropic': {
                'api_key': 'test-anthropic-key',
                'base_url': 'https://api.anthropic.com',
                'model': 'claude-3-sonnet-20240229',
                'temperature': 0.3,
                'max_tokens': 4096,
                'timeout': 60
            },
            'huggingface': {
                'api_key': 'test-hf-key',
                'base_url': 'https://api-inference.huggingface.co/models',
                'model': 'meta-llama/Llama-2-7b-chat-hf',
                'temperature': 0.7,
                'max_tokens': 2000,
                'timeout': 120
            },
            'ollama': {
                'base_url': 'http://localhost:11434',
                'model': 'llama3',
                'temperature': 0.8,
                'timeout': 120,
                'keep_alive': '10m'
            },
            'google': {
                'api_key': 'test-google-key',
                'base_url': 'https://generativelanguage.googleapis.com/v1',
                'model': 'gemini-pro',
                'temperature': 0.5,
                'max_tokens': 4000,
                'timeout': 60
            }
        })
        
        return mock

    @pytest.fixture
    def mock_settings_minimal(self):
        """Create a mock Settings object with minimal LLM configuration."""
        mock = Mock()
        
        mock.llm = DynamicConfig({
            'provider': 'groq',
            'model': 'llama-3-8b',
            'temperature': 0.0,
            'max_tokens': 1000,
            'timeout': 10,
            'max_retries': 1,
            
            'groq': {
                'api_key': None,
                'base_url': 'https://api.groq.com/openai/v1',
                'model': 'llama-3-8b',
                'temperature': 0.0,
                'max_tokens': 1000,
                'timeout': 10
            },
            'openai': {
                'api_key': '',
                'base_url': 'https://api.openai.com/v1',
                'model': 'gpt-3.5-turbo',
                'temperature': 0.1,
                'max_tokens': 2048,
                'timeout': 30
            }
        })
        
        return mock

    def test_llm_config_loads_global_configuration(self, mock_settings):
        """Test that LLMConfig correctly loads global LLM configuration from Settings."""
        with patch('app.core.config.application.llm.settings', mock_settings):
            from app.core.config.application.llm import LLMConfig
            LLMConfig._instances = {}
            
            config = LLMConfig()
            main_config = config.llm_config
            
            # Verify global configuration
            assert main_config['default_provider'] == 'openai'
            assert main_config['default_model'] == 'gpt-4'
            assert main_config['temperature'] == 0.1
            assert main_config['max_tokens'] == 4096
            assert main_config['timeout'] == 30
            assert main_config['max_retries'] == 3

    def test_llm_config_loads_openai_configuration(self, mock_settings):
        """Test that LLMConfig correctly loads OpenAI provider configuration."""
        with patch('app.core.config.application.llm.settings', mock_settings):
            from app.core.config.application.llm import LLMConfig
            LLMConfig._instances = {}
            
            config = LLMConfig()
            openai_config = config.openai_config
            
            # Verify OpenAI configuration
            assert openai_config['api_key'] == 'test-openai-key'
            assert openai_config['base_url'] == 'https://api.openai.com/v1'
            assert openai_config['default_model'] == 'gpt-4-turbo'
            assert openai_config['temperature'] == 0.2
            assert openai_config['max_tokens'] == 8192
            assert openai_config['timeout'] == 60

    def test_llm_config_loads_groq_configuration(self, mock_settings):
        """Test that LLMConfig correctly loads Groq provider configuration."""
        with patch('app.core.config.application.llm.settings', mock_settings):
            from app.core.config.application.llm import LLMConfig
            LLMConfig._instances = {}
            
            config = LLMConfig()
            groq_config = config.groq_config
            
            # Verify Groq configuration
            assert groq_config['api_key'] == 'test-groq-key'
            assert groq_config['base_url'] == 'https://api.groq.com/openai/v1'
            assert groq_config['default_model'] == 'llama-3.3-70b-versatile'
            assert groq_config['temperature'] == 0.7
            assert groq_config['max_tokens'] == 4000
            assert groq_config['timeout'] == 60

    def test_llm_config_loads_anthropic_configuration(self, mock_settings):
        """Test that LLMConfig correctly loads Anthropic provider configuration."""
        with patch('app.core.config.application.llm.settings', mock_settings):
            from app.core.config.application.llm import LLMConfig
            LLMConfig._instances = {}
            
            config = LLMConfig()
            anthropic_config = config.anthropic_config
            
            # Verify Anthropic configuration
            assert anthropic_config['api_key'] == 'test-anthropic-key'
            assert anthropic_config['base_url'] == 'https://api.anthropic.com'
            assert anthropic_config['default_model'] == 'claude-3-sonnet-20240229'
            assert anthropic_config['temperature'] == 0.3
            assert anthropic_config['max_tokens'] == 4096
            assert anthropic_config['timeout'] == 60

    def test_llm_config_loads_huggingface_configuration(self, mock_settings):
        """Test that LLMConfig correctly loads HuggingFace provider configuration."""
        with patch('app.core.config.application.llm.settings', mock_settings):
            from app.core.config.application.llm import LLMConfig
            LLMConfig._instances = {}
            
            config = LLMConfig()
            hf_config = config.huggingface_config
            
            # Verify HuggingFace configuration
            assert hf_config['api_key'] == 'test-hf-key'
            assert hf_config['base_url'] == 'https://api-inference.huggingface.co/models'
            assert hf_config['default_model'] == 'meta-llama/Llama-2-7b-chat-hf'
            assert hf_config['temperature'] == 0.7
            assert hf_config['max_tokens'] == 2000
            assert hf_config['timeout'] == 120

    def test_llm_config_loads_ollama_configuration(self, mock_settings):
        """Test that LLMConfig correctly loads Ollama provider configuration."""
        with patch('app.core.config.application.llm.settings', mock_settings):
            from app.core.config.application.llm import LLMConfig
            LLMConfig._instances = {}
            
            config = LLMConfig()
            ollama_config = config.ollama_config
            
            # Verify Ollama configuration
            assert ollama_config['base_url'] == 'http://localhost:11434'
            assert ollama_config['default_model'] == 'llama3'
            assert ollama_config['temperature'] == 0.8
            assert ollama_config['timeout'] == 120
            assert ollama_config['keep_alive'] == '10m'
            # Note: Ollama doesn't have api_key

    def test_llm_config_loads_google_configuration(self, mock_settings):
        """Test that LLMConfig correctly loads Google provider configuration."""
        with patch('app.core.config.application.llm.settings', mock_settings):
            from app.core.config.application.llm import LLMConfig
            LLMConfig._instances = {}
            
            config = LLMConfig()
            google_config = config.google_config
            
            # Verify Google configuration
            assert google_config['api_key'] == 'test-google-key'
            assert google_config['base_url'] == 'https://generativelanguage.googleapis.com/v1'
            assert google_config['default_model'] == 'gemini-pro'
            assert google_config['temperature'] == 0.5
            assert google_config['max_tokens'] == 4000
            assert google_config['timeout'] == 60

    def test_get_provider_config_method(self, mock_settings):
        """Test the get_provider_config convenience method."""
        with patch('app.core.config.application.llm.settings', mock_settings):
            from app.core.config.application.llm import LLMConfig
            LLMConfig._instances = {}
            
            config = LLMConfig()
            
            # Test valid providers
            openai_config = config.get_provider_config('openai')
            assert openai_config['api_key'] == 'test-openai-key'
            assert openai_config['default_model'] == 'gpt-4-turbo'
            
            groq_config = config.get_provider_config('groq')
            assert groq_config['api_key'] == 'test-groq-key'
            
            # Test invalid provider
            invalid_config = config.get_provider_config('invalid_provider')
            assert invalid_config == {}

    def test_get_default_provider_method(self, mock_settings):
        """Test the get_default_provider convenience method."""
        with patch('app.core.config.application.llm.settings', mock_settings):
            from app.core.config.application.llm import LLMConfig
            LLMConfig._instances = {}
            
            config = LLMConfig()
            default_provider = config.get_default_provider()
            assert default_provider == 'openai'

    def test_get_default_model_method(self, mock_settings):
        """Test the get_default_model convenience method."""
        with patch('app.core.config.application.llm.settings', mock_settings):
            from app.core.config.application.llm import LLMConfig
            LLMConfig._instances = {}
            
            config = LLMConfig()
            
            # Test global default model
            global_default = config.get_default_model()
            assert global_default == 'gpt-4'
            
            # Test provider-specific default model
            openai_default = config.get_default_model('openai')
            assert openai_default == 'gpt-4-turbo'
            
            groq_default = config.get_default_model('groq')
            assert groq_default == 'llama-3.3-70b-versatile'
            
            # Test invalid provider
            invalid_default = config.get_default_model('invalid_provider')
            assert invalid_default == ''

    def test_llm_config_singleton_behavior(self, mock_settings):
        """Test that LLMConfig maintains singleton behavior."""
        with patch('app.core.config.application.llm.settings', mock_settings):
            from app.core.config.application.llm import LLMConfig
            LLMConfig._instances = {}
            
            config1 = LLMConfig()
            config2 = LLMConfig()
            
            # Should be the same instance
            assert config1 is config2
            assert id(config1) == id(config2)

    def test_llm_config_with_minimal_settings(self, mock_settings_minimal):
        """Test LLMConfig with minimal/edge case configurations."""
        with patch('app.core.config.application.llm.settings', mock_settings_minimal):
            from app.core.config.application.llm import LLMConfig
            LLMConfig._instances = {}
            
            config = LLMConfig()
            
            # Test minimal global config
            main_config = config.llm_config
            assert main_config['default_provider'] == 'groq'
            assert main_config['default_model'] == 'llama-3-8b'
            assert main_config['temperature'] == 0.0
            assert main_config['max_tokens'] == 1000
            assert main_config['timeout'] == 10
            assert main_config['max_retries'] == 1
            
            # Test provider with None/empty API key
            groq_config = config.groq_config
            assert groq_config['api_key'] is None
            
            openai_config = config.openai_config
            assert openai_config['api_key'] == ''

    def test_llm_config_all_providers_included(self, mock_settings):
        """Test that the main llm_config includes all provider configurations."""
        with patch('app.core.config.application.llm.settings', mock_settings):
            from app.core.config.application.llm import LLMConfig
            LLMConfig._instances = {}
            
            config = LLMConfig()
            main_config = config.llm_config
            
            # Verify all providers are included
            expected_providers = ['groq', 'openai', 'anthropic', 'huggingface', 'ollama', 'google']
            for provider in expected_providers:
                assert provider in main_config
                assert isinstance(main_config[provider], dict)
                
            # Verify global settings are included
            assert 'default_provider' in main_config
            assert 'default_model' in main_config
            assert 'temperature' in main_config
            assert 'max_tokens' in main_config
            assert 'timeout' in main_config
            assert 'max_retries' in main_config

    def test_llm_config_different_provider_defaults(self):
        """Test LLMConfig with different default provider configurations."""
        providers = ['openai', 'groq', 'anthropic', 'google']
        
        for provider in providers:
            mock_settings = Mock()
            mock_settings.llm = DynamicConfig({
                'provider': provider,
                'model': f'{provider}-test-model',
                'temperature': 0.5,
                'max_tokens': 2048,
                'timeout': 45,
                'max_retries': 2,
                
                provider: {
                    'api_key': f'test-{provider}-key',
                    'base_url': f'https://api.{provider}.com',
                    'model': f'{provider}-specific-model',
                    'temperature': 0.3,
                    'max_tokens': 1024,
                    'timeout': 30
                }
            })
            
            with patch('app.core.config.application.llm.settings', mock_settings):
                from app.core.config.application.llm import LLMConfig
                LLMConfig._instances = {}
                
                config = LLMConfig()
                
                assert config.get_default_provider() == provider
                assert config.get_default_model() == f'{provider}-test-model'
                assert config.get_default_model(provider) == f'{provider}-specific-model'

    def test_llm_config_edge_case_values(self):
        """Test LLMConfig with edge case configuration values."""
        mock_settings = Mock()
        mock_settings.llm = DynamicConfig({
            'provider': '',
            'model': None,
            'temperature': 0.0,
            'max_tokens': 0,
            'timeout': 0,
            'max_retries': 0,
            
            'openai': {
                'api_key': '',
                'base_url': '',
                'model': '',
                'temperature': 2.0,  # Max temperature
                'max_tokens': 999999,  # Very large
                'timeout': 1  # Very short
            }
        })
        
        with patch('app.core.config.application.llm.settings', mock_settings):
            from app.core.config.application.llm import LLMConfig
            LLMConfig._instances = {}
            
            config = LLMConfig()
            
            # Should handle edge cases without errors
            main_config = config.llm_config
            assert main_config['default_provider'] == ''
            assert main_config['default_model'] is None
            assert main_config['temperature'] == 0.0
            assert main_config['max_tokens'] == 0
            assert main_config['timeout'] == 0
            assert main_config['max_retries'] == 0
            
            openai_config = config.openai_config
            assert openai_config['temperature'] == 2.0
            assert openai_config['max_tokens'] == 999999
            assert openai_config['timeout'] == 1
