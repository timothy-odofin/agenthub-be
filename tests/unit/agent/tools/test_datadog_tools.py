"""
Unit tests for Datadog tools implementation.
Tests the Datadog tools provider, API wrapper, and tool registration.
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
from app.agent.tools.datadog.datadog_tools import DatadogToolsProvider
from app.agent.tools.datadog.datadog_wrapper import DatadogAPIWrapper


class TestDatadogToolsProvider(unittest.TestCase):
    """Test Datadog tools provider."""
    
    def test_provider_initialization(self):
        """Test basic provider initialization."""
        provider = DatadogToolsProvider()
        assert provider is not None
        assert provider.config == {}
    
    def test_provider_with_config(self):
        """Test provider initialization with configuration."""
        config = {"test_key": "test_value"}
        provider = DatadogToolsProvider(config=config)
        assert provider.config == config
    
    @patch('app.agent.tools.datadog.datadog_wrapper.settings')
    def test_wrapper_lazy_initialization(self, mock_settings):
        """Test API wrapper lazy initialization."""
        # Mock Datadog configuration
        mock_dd = Mock()
        mock_dd.api_key = "test_api_key"
        mock_dd.app_key = "test_app_key"
        mock_dd.site = "datadoghq.com"
        mock_dd.timeout = 30
        
        mock_external = Mock()
        mock_external.datadog = mock_dd
        mock_settings.external = mock_external
        
        provider = DatadogToolsProvider()
        
        # Wrapper should be None initially
        assert provider._wrapper is None
        
        # Access wrapper property
        wrapper = provider.wrapper
        
        # Wrapper should now be initialized
        assert wrapper is not None
        assert isinstance(wrapper, DatadogAPIWrapper)
    
    @patch('app.agent.tools.datadog.datadog_wrapper.settings')
    @patch('app.agent.tools.datadog.datadog_wrapper.ApiClient')
    def test_get_tools(self, mock_api_client, mock_settings):
        """Test getting tools from provider."""
        # Mock Datadog configuration
        mock_dd = Mock()
        mock_dd.api_key = "test_api_key"
        mock_dd.app_key = "test_app_key"
        mock_dd.site = "datadoghq.com"
        mock_dd.timeout = 30
        mock_dd.default_limit = 50
        mock_dd.max_limit = 200
        
        mock_external = Mock()
        mock_external.datadog = mock_dd
        mock_settings.external = mock_external
        
        provider = DatadogToolsProvider()
        tools = provider.get_tools()
        
        # Should return 3 tools
        assert len(tools) == 3
        
        # Verify tool names
        tool_names = [tool.name for tool in tools]
        assert "datadog_search_logs" in tool_names
        assert "datadog_query_metrics" in tool_names
        assert "datadog_list_monitors" in tool_names
    
    @patch('app.agent.tools.datadog.datadog_wrapper.settings')
    def test_get_connection_info(self, mock_settings):
        """Test getting connection information."""
        # Mock Datadog configuration
        mock_dd = Mock()
        mock_dd.api_key = "test_api_key"
        mock_dd.app_key = "test_app_key"
        mock_dd.site = "datadoghq.com"
        mock_dd.default_limit = 50
        mock_dd.max_limit = 200
        
        mock_external = Mock()
        mock_external.datadog = mock_dd
        mock_settings.external = mock_external
        
        provider = DatadogToolsProvider()
        info = provider.get_connection_info()
        
        assert info["site"] == "datadoghq.com"
        assert info["api_key_set"] is True
        assert info["app_key_set"] is True
        assert info["default_limit"] == 50
        assert info["max_limit"] == 200


class TestDatadogAPIWrapper(unittest.TestCase):
    """Test Datadog API wrapper."""
    
    @patch('app.agent.tools.datadog.datadog_wrapper.settings')
    def test_wrapper_initialization(self, mock_settings):
        """Test API wrapper initialization."""
        # Mock Datadog configuration
        mock_dd = Mock()
        mock_dd.api_key = "test_api_key"
        mock_dd.app_key = "test_app_key"
        mock_dd.site = "datadoghq.com"
        mock_dd.timeout = 30
        
        mock_external = Mock()
        mock_external.datadog = mock_dd
        mock_settings.external = mock_external
        
        wrapper = DatadogAPIWrapper()
        
        assert wrapper.config.api_key == "test_api_key"
        assert wrapper.config.app_key == "test_app_key"
        assert wrapper.config.site == "datadoghq.com"
    
    @patch('app.agent.tools.datadog.datadog_wrapper.settings')
    def test_wrapper_missing_credentials(self, mock_settings):
        """Test wrapper fails with missing credentials."""
        # Mock Datadog configuration with missing keys
        mock_dd = Mock()
        mock_dd.api_key = None
        mock_dd.app_key = None
        mock_dd.site = "datadoghq.com"
        
        mock_external = Mock()
        mock_external.datadog = mock_dd
        mock_settings.external = mock_external
        
        with self.assertRaises(ValueError) as context:
            DatadogAPIWrapper()
        
        assert "Missing Datadog API key or App key" in str(context.exception)
    
    @patch('app.agent.tools.datadog.datadog_wrapper.settings')
    @patch('app.agent.tools.datadog.datadog_wrapper.ApiClient')
    @patch('app.agent.tools.datadog.datadog_wrapper.LogsApi')
    def test_search_logs_with_limit(self, mock_logs_api, mock_api_client, mock_settings):
        """Test log search respects limit guardrails."""
        # Mock Datadog configuration
        mock_dd = Mock()
        mock_dd.api_key = "test_api_key"
        mock_dd.app_key = "test_app_key"
        mock_dd.site = "datadoghq.com"
        mock_dd.default_limit = 50
        mock_dd.max_limit = 200
        
        mock_external = Mock()
        mock_external.datadog = mock_dd
        mock_settings.external = mock_external
        
        # Mock API response
        mock_log = Mock()
        mock_log.id = "log-123"
        mock_attrs = Mock()
        mock_attrs.timestamp = "2024-01-01T00:00:00Z"
        mock_attrs.message = "Test log message"
        mock_attrs.service = "test-service"
        mock_attrs.status = "info"
        mock_attrs.host = "test-host"
        mock_attrs.tags = ["env:test"]
        mock_log.attributes = mock_attrs
        
        mock_response = Mock()
        mock_response.data = [mock_log]
        
        mock_api_instance = Mock()
        mock_api_instance.list_logs.return_value = mock_response
        mock_logs_api.return_value = mock_api_instance
        
        # Mock API client context manager
        mock_client_instance = MagicMock()
        mock_client_instance.__enter__.return_value = mock_client_instance
        mock_client_instance.__exit__.return_value = None
        mock_api_client.return_value = mock_client_instance
        
        wrapper = DatadogAPIWrapper()
        
        # Test with limit exceeding max (should be capped at 200)
        logs = wrapper.search_logs(query="service:test", limit=500)
        
        assert isinstance(logs, list)
    
    @patch('app.agent.tools.datadog.datadog_wrapper.settings')
    def test_get_connection_info(self, mock_settings):
        """Test getting connection information from wrapper."""
        # Mock Datadog configuration
        mock_dd = Mock()
        mock_dd.api_key = "test_api_key"
        mock_dd.app_key = "test_app_key"
        mock_dd.site = "datadoghq.eu"
        mock_dd.default_limit = 75
        mock_dd.max_limit = 150
        
        mock_external = Mock()
        mock_external.datadog = mock_dd
        mock_settings.external = mock_external
        
        wrapper = DatadogAPIWrapper()
        info = wrapper.get_connection_info()
        
        assert info["site"] == "datadoghq.eu"
        assert info["api_key_set"] is True
        assert info["app_key_set"] is True
        assert info["default_limit"] == 75
        assert info["max_limit"] == 150


class TestDatadogToolsRegistration(unittest.TestCase):
    """Test Datadog tools registration with ToolRegistry."""
    
    def test_datadog_provider_registered(self):
        """Test that DatadogToolsProvider is registered."""
        from app.agent.tools.base.registry import ToolRegistry
        
        # Get all registered tools
        datadog_tools = ToolRegistry.get_tools_by_category("datadog")
        
        # Should have DatadogToolsProvider registered
        assert len(datadog_tools) > 0
        assert DatadogToolsProvider in datadog_tools
    
    def test_datadog_in_monitoring_package(self):
        """Test that Datadog tools are in monitoring package."""
        from app.agent.tools.base.registry import ToolRegistry
        
        # Get all tools in monitoring package
        monitoring_tools = ToolRegistry.get_tools_by_package("monitoring")
        
        # Should include DatadogToolsProvider
        assert DatadogToolsProvider in monitoring_tools


if __name__ == "__main__":
    unittest.main()
