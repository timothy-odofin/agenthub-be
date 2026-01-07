"""
Unit tests for prompt configuration management.
"""

import pytest
from unittest.mock import MagicMock, patch

from app.core.config.providers.prompt import PromptConfig, PromptConfigError, PromptType


class TestPromptConfig:
    """Test cases for PromptConfig class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.prompt_config = PromptConfig()
    
    @patch('src.app.core.config.providers.prompt.settings')
    def test_default_config_with_settings(self, mock_settings):
        """Test default configuration when settings are available."""
        # Mock settings structure
        mock_default = MagicMock()
        mock_default.provider = "system"
        mock_default.language = "en"
        mock_default.max_tokens = 4096
        mock_default.temperature = 0.7
        
        mock_settings.prompt.default = mock_default
        
        result = self.prompt_config.default_config
        
        expected = {
            'provider': 'system',
            'language': 'en',
            'max_tokens': 4096,
            'temperature': 0.7
        }
        
        assert result == expected
    
    @patch('src.app.core.config.providers.prompt.settings')
    def test_default_config_missing_settings(self, mock_settings):
        """Test default configuration fallback when settings are missing."""
        # Mock missing settings
        del mock_settings.prompt
        
        result = self.prompt_config.default_config
        
        expected = {
            'provider': 'system',
            'language': 'en',
            'max_tokens': 4096,
            'temperature': 0.7
        }
        
        assert result == expected
    
    @patch('src.app.core.config.providers.prompt.settings')
    def test_get_system_prompt_basic(self, mock_settings):
        """Test getting a basic system prompt."""
        # Mock settings structure
        mock_chat = MagicMock()
        mock_chat.default = "You are a helpful AI assistant."
        
        mock_settings.prompt.system.chat = mock_chat
        
        result = self.prompt_config.get_system_prompt("chat.default")
        
        assert result == "You are a helpful AI assistant."
    
    @patch('src.app.core.config.providers.prompt.settings')
    def test_get_system_prompt_with_variables(self, mock_settings):
        """Test getting a system prompt with variable substitution."""
        # Mock settings structure
        mock_chat = MagicMock()
        mock_chat.default = "Hello {name}, welcome to {system}!"
        
        mock_settings.prompt.system.chat = mock_chat
        
        result = self.prompt_config.get_system_prompt(
            "chat.default", 
            name="Alice", 
            system="AgentHub"
        )
        
        assert result == "Hello Alice, welcome to AgentHub!"
    
    @patch('src.app.core.config.providers.prompt.settings')
    def test_get_system_prompt_not_found(self, mock_settings):
        """Test error when system prompt is not found."""
        # Mock settings without the requested prompt
        mock_settings.prompt.system = MagicMock()
        del mock_settings.prompt.system.chat
        
        with pytest.raises(PromptConfigError, match="Prompt type 'chat.default' not found"):
            self.prompt_config.get_system_prompt("chat.default")
    
    @patch('src.app.core.config.providers.prompt.settings')
    def test_get_system_prompt_no_settings(self, mock_settings):
        """Test error when system prompts are not configured."""
        # Mock missing system settings
        del mock_settings.prompt.system
        
        with pytest.raises(PromptConfigError, match="System prompts not configured"):
            self.prompt_config.get_system_prompt("chat.default")
    
    @patch('src.app.core.config.providers.prompt.settings')
    def test_get_custom_prompt_basic(self, mock_settings):
        """Test getting a custom prompt."""
        # Mock settings structure
        mock_custom = MagicMock()
        mock_custom.code_review = "Review the following code for best practices."
        
        mock_settings.prompt.custom = mock_custom
        
        result = self.prompt_config.get_custom_prompt("code_review")
        
        assert result == "Review the following code for best practices."
    
    @patch('src.app.core.config.providers.prompt.settings')
    def test_get_custom_prompt_with_variables(self, mock_settings):
        """Test getting a custom prompt with variable substitution."""
        # Mock settings structure  
        mock_custom = MagicMock()
        mock_custom.meeting_summary = "Summarize the {meeting_type} meeting for {participants}."
        
        mock_settings.prompt.custom = mock_custom
        
        result = self.prompt_config.get_custom_prompt(
            "meeting_summary",
            meeting_type="quarterly review",
            participants="engineering team"
        )
        
        assert result == "Summarize the quarterly review meeting for engineering team."
    
    @patch('src.app.core.config.providers.prompt.settings')
    def test_get_template_variables(self, mock_settings):
        """Test getting template variables."""
        # Mock settings structure
        mock_variables = MagicMock()
        mock_variables.to_dict.return_value = {
            'user_name': 'User',
            'company_name': 'AgentHub',
            'environment': 'production'
        }
        
        mock_settings.prompt.templates.variables = mock_variables
        
        result = self.prompt_config.get_template_variables()
        
        expected = {
            'user_name': 'User',
            'company_name': 'AgentHub',
            'environment': 'production'
        }
        
        assert result == expected
    
    @patch('src.app.core.config.providers.prompt.settings')
    def test_get_template_prompt(self, mock_settings):
        """Test getting a template prompt with variables."""
        # Mock template variables
        mock_variables = MagicMock()
        mock_variables.to_dict.return_value = {
            'user_name': 'DefaultUser',
            'company_name': 'AgentHub'
        }
        
        # Mock template
        mock_templates = MagicMock()
        mock_templates.variables = mock_variables
        mock_templates.personalized_greeting = "Hello {user_name}, welcome to {company_name}!"
        
        mock_settings.prompt.templates = mock_templates
        
        # Test with override
        result = self.prompt_config.get_template_prompt(
            "personalized_greeting",
            user_name="Alice"
        )
        
        assert result == "Hello Alice, welcome to AgentHub!"
    
    @patch('src.app.core.config.providers.prompt.settings')
    def test_get_environment_prompt_development(self, mock_settings):
        """Test getting environment-specific prompt for development."""
        # Mock environment-specific prompt
        mock_env_chat = MagicMock()
        mock_env_chat.default = "[DEV MODE] You are in development environment."
        
        mock_env_system = MagicMock()
        mock_env_system.chat = mock_env_chat
        
        mock_settings.prompt.environments.development.system = mock_env_system
        
        result = self.prompt_config.get_environment_prompt("development", "system.chat.default")
        
        assert result == "[DEV MODE] You are in development environment."
    
    @patch('src.app.core.config.providers.prompt.settings')  
    def test_get_environment_prompt_fallback(self, mock_settings):
        """Test fallback to system prompt when environment-specific not found."""
        # Mock missing environment config but available system prompt
        del mock_settings.prompt.environments.production
        
        mock_chat = MagicMock()
        mock_chat.default = "You are a helpful AI assistant."
        mock_settings.prompt.system.chat = mock_chat
        
        result = self.prompt_config.get_environment_prompt("production", "chat.default")
        
        assert result == "You are a helpful AI assistant."
    
    @patch('src.app.core.config.providers.prompt.settings')
    def test_get_versioned_prompt_basic(self, mock_settings):
        """Test getting a prompt from a specific version."""
        # Mock version configuration
        mock_v1_prompts = MagicMock()
        mock_v1_prompts.chat_default = "system.chat.default"
        
        mock_v1_config = MagicMock()
        mock_v1_config.prompts = mock_v1_prompts
        
        mock_settings.prompt.versions.v1_0 = mock_v1_config
        
        # Mock system prompt
        mock_chat = MagicMock()
        mock_chat.default = "Version 1.0 system prompt."
        mock_settings.prompt.system.chat = mock_chat
        
        result = self.prompt_config.get_versioned_prompt("v1_0", "chat_default")
        
        assert result == "Version 1.0 system prompt."
    
    @patch('src.app.core.config.providers.prompt.settings')
    def test_get_active_version_prompt(self, mock_settings):
        """Test getting prompt from active version."""
        # Mock active version
        mock_v1_prompts = MagicMock()
        mock_v1_prompts.chat_default = "system.chat.default"
        
        mock_v1_config = MagicMock()
        mock_v1_config.active = True
        mock_v1_config.prompts = mock_v1_prompts
        
        mock_settings.prompt.versions.v1_0 = mock_v1_config
        
        # Mock system prompt
        mock_chat = MagicMock()
        mock_chat.default = "Active version prompt."
        mock_settings.prompt.system.chat = mock_chat
        
        result = self.prompt_config.get_active_version_prompt("chat_default")
        
        assert result == "Active version prompt."
    
    @patch('src.app.core.config.providers.prompt.settings')
    def test_get_active_version_prompt_experimental_access(self, mock_settings):
        """Test experimental version access for specific users."""
        # Mock experimental version
        mock_exp_prompts = MagicMock()
        mock_exp_prompts.chat_default = "system.chat.technical"
        
        mock_exp_config = MagicMock()
        mock_exp_config.enabled_for_users = ["admin", "beta_testers"]
        mock_exp_config.prompts = mock_exp_prompts
        
        mock_settings.prompt.versions.experimental = mock_exp_config
        
        # Mock active version (fallback)
        mock_v1_config = MagicMock()
        mock_v1_config.active = True
        mock_settings.prompt.versions.v1_0 = mock_v1_config
        
        # Mock system prompts
        mock_chat = MagicMock()
        mock_chat.technical = "Technical experimental prompt."
        mock_settings.prompt.system.chat = mock_chat
        
        result = self.prompt_config.get_active_version_prompt("chat_default", user_id="admin")
        
        assert result == "Technical experimental prompt."
    
    @patch('src.app.core.config.providers.prompt.settings')
    def test_list_available_prompts_simplified(self, mock_settings):
        """Test listing all available prompts with simplified approach."""
        # Mock that hasattr returns False for non-existent attributes
        mock_settings.prompt = None  # No prompt settings configured
        
        result = self.prompt_config.list_available_prompts()
        
        # When no settings are available, should return empty lists
        expected = {
            'system': [],
            'custom': [],
            'templates': [],
            'versions': []
        }
        
        assert result == expected
    
    def test_get_connection_config(self):
        """Test getting connection configuration."""
        result = self.prompt_config.get_connection_config()
        
        assert result['type'] == 'prompt'
        assert 'default_config' in result
        assert 'available_prompts' in result
    
    def test_prompt_type_enum(self):
        """Test PromptType enum values."""
        assert PromptType.CHAT_DEFAULT.value == "chat.default"
        assert PromptType.REACT_AGENT.value == "agent.react_agent"
        assert PromptType.CODE_REVIEW.value == "code_review"
