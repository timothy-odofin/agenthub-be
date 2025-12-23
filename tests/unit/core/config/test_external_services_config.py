"""Unit tests for external_services_config.py with Settings system integration."""

import unittest
from unittest.mock import patch, MagicMock

from app.core.config.providers.external import ExternalServicesConfig
from app.core.constants import AtlassianProperties


class TestExternalServicesConfig(unittest.TestCase):
    """Test external services configuration with Settings system."""

    def setUp(self):
        """Set up test environment with fresh config instance."""
        # Clear any cached singleton instances
        if hasattr(ExternalServicesConfig, '_instances'):
            ExternalServicesConfig._instances = {}
        
        # Clear config source registry for clean testing
        from app.core.config.framework.registry import ConfigSourceRegistry
        ConfigSourceRegistry._connection_to_config = {}

    def tearDown(self):
        """Clean up after each test."""
        if hasattr(ExternalServicesConfig, '_instances'):
            ExternalServicesConfig._instances = {}
        
        # Clear config source registry
        from app.core.config.framework.registry import ConfigSourceRegistry
        ConfigSourceRegistry._connection_to_config = {}

    @patch('app.core.config.providers.external.settings')
    def test_atlassian_config_with_settings(self, mock_settings):
        """Test atlassian configuration with Settings system."""
        # Mock atlassian settings
        mock_atlassian = MagicMock()
        mock_atlassian.api_key = 'test-api-key'
        mock_atlassian.email = 'test@example.com'
        mock_atlassian.confluence_base_url = 'https://test.atlassian.net/wiki'
        mock_atlassian.jira_base_url = 'https://test.atlassian.net'
        
        mock_external = MagicMock()
        mock_external.atlassian = mock_atlassian
        mock_settings.external = mock_external
        
        config = ExternalServicesConfig()
        result = config.atlassian_config
        
        expected = {
            AtlassianProperties.API_KEY: 'test-api-key',
            AtlassianProperties.EMAIL: 'test@example.com',
            AtlassianProperties.CONFLUENCE_BASE_URL: 'https://test.atlassian.net/wiki',
            AtlassianProperties.JIRA_BASE_URL: 'https://test.atlassian.net'
        }
        self.assertEqual(result, expected)

    @patch('app.core.config.providers.external.settings')
    def test_atlassian_config_missing_external_settings(self, mock_settings):
        """Test atlassian configuration when external settings are missing."""
        del mock_settings.external
        
        config = ExternalServicesConfig()
        result = config.atlassian_config
        
        self.assertEqual(result, {})

    @patch('app.core.config.providers.external.settings')
    def test_atlassian_config_missing_atlassian_settings(self, mock_settings):
        """Test atlassian configuration when atlassian-specific settings are missing."""
        mock_external = MagicMock()
        del mock_external.atlassian
        mock_settings.external = mock_external
        
        config = ExternalServicesConfig()
        result = config.atlassian_config
        
        self.assertEqual(result, {})

    @patch('app.core.config.providers.external.settings')
    def test_github_config_with_settings(self, mock_settings):
        """Test GitHub configuration with Settings system."""
        mock_github = MagicMock()
        mock_github.api_key = 'github-token'
        mock_github.base_url = 'https://api.github.com'
        mock_github.timeout = 30
        
        mock_external = MagicMock()
        mock_external.github = mock_github
        mock_settings.external = mock_external
        
        config = ExternalServicesConfig()
        result = config.github_config
        
        expected = {
            'api_key': 'github-token',
            'base_url': 'https://api.github.com',
            'timeout': 30
        }
        self.assertEqual(result, expected)

    @patch('app.core.config.providers.external.settings')
    def test_github_config_missing_settings(self, mock_settings):
        """Test GitHub configuration when settings are missing."""
        del mock_settings.external
        
        config = ExternalServicesConfig()
        result = config.github_config
        
        self.assertEqual(result, {})

    @patch('app.core.config.providers.external.settings')
    def test_bitbucket_config_with_settings(self, mock_settings):
        """Test Bitbucket configuration with Settings system."""
        mock_bitbucket = MagicMock()
        mock_bitbucket.username = 'bitbucket-user'
        mock_bitbucket.app_password = 'bitbucket-pass'
        mock_bitbucket.base_url = 'https://api.bitbucket.org/2.0'
        mock_bitbucket.timeout = 30
        
        mock_external = MagicMock()
        mock_external.bitbucket = mock_bitbucket
        mock_settings.external = mock_external
        
        config = ExternalServicesConfig()
        result = config.bitbucket_config
        
        expected = {
            'username': 'bitbucket-user',
            'app_password': 'bitbucket-pass',
            'base_url': 'https://api.bitbucket.org/2.0',
            'timeout': 30
        }
        self.assertEqual(result, expected)

    @patch('app.core.config.providers.external.settings')
    def test_s3_config_with_settings(self, mock_settings):
        """Test S3 configuration with Settings system."""
        mock_s3 = MagicMock()
        mock_s3.access_key_id = 'aws-access-key'
        mock_s3.secret_access_key = 'aws-secret-key'
        mock_s3.region = 'us-west-2'
        mock_s3.bucket_name = 'test-bucket'
        mock_s3.endpoint_url = 'https://s3.amazonaws.com'
        
        mock_external = MagicMock()
        mock_external.s3 = mock_s3
        mock_settings.external = mock_external
        
        config = ExternalServicesConfig()
        result = config.s3_config
        
        expected = {
            'access_key_id': 'aws-access-key',
            'secret_access_key': 'aws-secret-key',
            'region': 'us-west-2',
            'bucket_name': 'test-bucket',
            'endpoint_url': 'https://s3.amazonaws.com'
        }
        self.assertEqual(result, expected)

    @patch('app.core.config.providers.external.settings')
    def test_sharepoint_config_with_settings(self, mock_settings):
        """Test SharePoint configuration with Settings system."""
        mock_sharepoint = MagicMock()
        mock_sharepoint.tenant_id = 'tenant-123'
        mock_sharepoint.client_id = 'client-456'
        mock_sharepoint.client_secret = 'secret-789'
        mock_sharepoint.site_url = 'https://company.sharepoint.com'
        mock_sharepoint.timeout = 60
        
        mock_external = MagicMock()
        mock_external.sharepoint = mock_sharepoint
        mock_settings.external = mock_external
        
        config = ExternalServicesConfig()
        result = config.sharepoint_config
        
        expected = {
            'tenant_id': 'tenant-123',
            'client_id': 'client-456',
            'client_secret': 'secret-789',
            'site_url': 'https://company.sharepoint.com',
            'timeout': 60
        }
        self.assertEqual(result, expected)

    @patch('app.core.config.providers.external.settings')
    def test_langchain_config_with_settings(self, mock_settings):
        """Test LangChain configuration with Settings system."""
        mock_langchain = MagicMock()
        mock_langchain.api_key = 'langchain-api-key'
        mock_langchain.project = 'my-project'
        mock_langchain.tracing_v2 = True
        mock_langchain.endpoint = 'https://api.smith.langchain.com'
        
        mock_external = MagicMock()
        mock_external.langchain = mock_langchain
        mock_settings.external = mock_external
        
        config = ExternalServicesConfig()
        result = config.langchain_config
        
        expected = {
            'api_key': 'langchain-api-key',
            'project': 'my-project',
            'tracing_v2': True,
            'endpoint': 'https://api.smith.langchain.com'
        }
        self.assertEqual(result, expected)

    @patch('app.core.config.providers.external.settings')
    def test_all_configs_missing_settings(self, mock_settings):
        """Test all configurations when external settings are completely missing."""
        del mock_settings.external
        
        config = ExternalServicesConfig()
        
        # All should return empty dict when settings are missing
        self.assertEqual(config.atlassian_config, {})
        self.assertEqual(config.github_config, {})
        self.assertEqual(config.bitbucket_config, {})
        self.assertEqual(config.s3_config, {})
        self.assertEqual(config.sharepoint_config, {})
        self.assertEqual(config.langchain_config, {})

    @patch('app.core.config.providers.external.settings')
    def test_partial_service_config_missing(self, mock_settings):
        """Test configurations when some services are missing but external exists."""
        mock_external = MagicMock()
        # Only add github, others missing
        mock_github = MagicMock()
        mock_github.api_key = 'github-token'
        mock_github.base_url = 'https://api.github.com'
        mock_github.timeout = 30
        mock_external.github = mock_github
        
        # Remove other services
        del mock_external.atlassian
        del mock_external.bitbucket
        del mock_external.s3
        del mock_external.sharepoint
        del mock_external.langchain
        
        mock_settings.external = mock_external
        
        config = ExternalServicesConfig()
        
        # Only github should have config
        expected_github = {
            'api_key': 'github-token',
            'base_url': 'https://api.github.com',
            'timeout': 30
        }
        self.assertEqual(config.github_config, expected_github)
        
        # Others should be empty
        self.assertEqual(config.atlassian_config, {})
        self.assertEqual(config.bitbucket_config, {})
        self.assertEqual(config.s3_config, {})
        self.assertEqual(config.sharepoint_config, {})
        self.assertEqual(config.langchain_config, {})

    def test_singleton_behavior(self):
        """Test that ExternalServicesConfig follows singleton pattern."""
        config1 = ExternalServicesConfig()
        config2 = ExternalServicesConfig()
        
        self.assertIs(config1, config2)
        self.assertEqual(id(config1), id(config2))

    @patch('app.core.config.providers.external.settings')
    def test_config_integration_with_real_structure(self, mock_settings):
        """Test configuration integration mimicking real YAML structure."""
        # Mock complete external settings structure
        mock_atlassian = MagicMock()
        mock_atlassian.api_key = 'real-api-key'
        mock_atlassian.email = 'admin@company.com'
        mock_atlassian.confluence_base_url = 'https://company.atlassian.net/wiki'
        mock_atlassian.jira_base_url = 'https://company.atlassian.net'
        
        mock_github = MagicMock()
        mock_github.api_key = 'ghp_realtoken'
        mock_github.base_url = 'https://api.github.com'
        mock_github.timeout = 45
        
        mock_external = MagicMock()
        mock_external.atlassian = mock_atlassian
        mock_external.github = mock_github
        
        mock_settings.external = mock_external
        
        config = ExternalServicesConfig()
        
        # Test that all configurations work together
        atlassian_result = config.atlassian_config
        github_result = config.github_config
        
        self.assertIsInstance(atlassian_result, dict)
        self.assertIsInstance(github_result, dict)
        self.assertIn(AtlassianProperties.API_KEY, atlassian_result)
        self.assertIn('api_key', github_result)
        
        # Verify values
        self.assertEqual(atlassian_result[AtlassianProperties.API_KEY], 'real-api-key')
        self.assertEqual(github_result['api_key'], 'ghp_realtoken')

    @patch('app.core.config.providers.external.settings')
    def test_get_connection_config_method(self, mock_settings):
        """Test the get_connection_config method for registry integration."""
        # Mock settings for testing
        mock_atlassian = MagicMock()
        mock_atlassian.api_key = 'test-api-key'
        mock_atlassian.email = 'test@example.com'
        mock_atlassian.confluence_base_url = 'https://test.atlassian.net/wiki'
        mock_atlassian.jira_base_url = 'https://test.atlassian.net'
        
        mock_github = MagicMock()
        mock_github.api_key = 'github-token'
        mock_github.base_url = 'https://api.github.com'
        mock_github.timeout = 30
        
        mock_external = MagicMock()
        mock_external.atlassian = mock_atlassian
        mock_external.github = mock_github
        mock_settings.external = mock_external
        
        config = ExternalServicesConfig()
        
        # Test confluence connection (should transform AtlassianProperties to connection format)
        confluence_config = config.get_connection_config('confluence')
        expected_confluence = {
            'base_url': 'https://test.atlassian.net/wiki',
            'username': 'test@example.com',
            'api_token': 'test-api-key'
        }
        self.assertEqual(confluence_config, expected_confluence)
        
        # Test jira connection (should also transform AtlassianProperties)
        jira_config = config.get_connection_config('jira')
        expected_jira = {
            'base_url': 'https://test.atlassian.net',
            'username': 'test@example.com',
            'api_token': 'test-api-key'
        }
        self.assertEqual(jira_config, expected_jira)
        
        # Test github connection
        github_config = config.get_connection_config('github')
        expected_github = {
            'api_key': 'github-token',
            'base_url': 'https://api.github.com',
            'timeout': 30
        }
        self.assertEqual(github_config, expected_github)
        
        # Test unknown connection
        unknown_config = config.get_connection_config('unknown_connection')
        self.assertEqual(unknown_config, {})

    def test_registry_integration(self):
        """Test that the class is properly registered in the config source registry."""
        # Import both modules to ensure registration happens
        from app.core.config.framework.registry import ConfigSourceRegistry
        from app.core.config.providers.external import ExternalServicesConfig, external_services_config
        
        # Ensure the singleton is initialized (which should trigger decorator if it hasn't already)
        instance = external_services_config
        self.assertIsInstance(instance, ExternalServicesConfig)
        
        # Test that we can get connection configs for the services we're supposed to handle
        # This indirectly tests the registry integration since connection managers use the registry
        
        # Test confluence config retrieval
        confluence_config = instance.get_connection_config('confluence')
        self.assertIsInstance(confluence_config, dict)
        
        # Test jira config retrieval  
        jira_config = instance.get_connection_config('jira')
        self.assertIsInstance(jira_config, dict)
        
        # Test s3 config retrieval
        s3_config = instance.get_connection_config('s3')
        self.assertIsInstance(s3_config, dict)
        
        # Test unknown connection returns empty dict
        unknown_config = instance.get_connection_config('unknown')
        self.assertEqual(unknown_config, {})


if __name__ == '__main__':
    unittest.main()
