"""
Unit tests for AppConfig class.

These tests focus on the AppConfig logic by mocking the Settings system,
ensuring proper mapping and error handling without testing the Settings
integration (which has its own integration tests).
"""

import pytest
from unittest.mock import Mock, patch

from app.core.config.framework.dynamic_config import DynamicConfig


class TestAppConfig:
    """Test suite for AppConfig class."""

    @pytest.fixture
    def mock_settings(self):
        """Create a mock Settings object with typical configuration."""
        mock = Mock()
        
        # Mock app configuration
        mock.app = Mock()
        mock.app.environment = "test"
        mock.app.debug = True
        mock.app.name = "TestApp"
        mock.app.version = "1.0.0"
        
        # Mock security configuration
        mock.app.security = Mock()
        mock.app.security.jwt_secret_key = "test-jwt-secret"
        mock.app.security.jwt_algorithm = "HS256"
        mock.app.security.access_token_expire_minutes = 30
        
        # Mock API configuration
        mock.app.api = Mock()
        mock.app.api.host = "localhost"
        mock.app.api.port = 8000
        
        # Mock logging configuration
        mock.app.logging = Mock()
        mock.app.logging.level = "INFO"
        
        # Mock data sources
        mock.data_sources = DynamicConfig({
            'dataSources': [
                {'type': 'file', 'path': '/test/path'},
                {'type': 'confluence', 'space': 'TEST'}
            ]
        })
        
        return mock

    @pytest.fixture
    def mock_settings_no_data_sources(self):
        """Create a mock Settings object without data sources."""
        mock = Mock()
        
        # Same app config as above
        mock.app = Mock()
        mock.app.environment = "test"
        mock.app.debug = False
        mock.app.name = "TestApp"
        mock.app.version = "1.0.0"
        mock.app.security = Mock()
        mock.app.security.jwt_secret_key = "test-secret"
        mock.app.security.jwt_algorithm = "HS256"
        mock.app.security.access_token_expire_minutes = 60
        mock.app.api = Mock()
        mock.app.api.host = "0.0.0.0"
        mock.app.api.port = 9000
        mock.app.logging = Mock()
        mock.app.logging.level = "DEBUG"
        
        # No data sources
        mock.data_sources = None
        
        return mock

    def test_app_config_loads_basic_configuration(self, mock_settings):
        """Test that AppConfig correctly loads basic app configuration from Settings."""
        with patch('app.core.config.application.app.settings', mock_settings):
            # Reset singleton to force new instance
            from app.core.config.application.app import AppConfig
            AppConfig._instances = {}
            
            config = AppConfig()
            
            # Verify app configuration
            assert config.app_env == "test"
            assert config.debug is True
            assert config.app_name == "TestApp"
            assert config.app_version == "1.0.0"

    def test_app_config_loads_security_configuration(self, mock_settings):
        """Test that AppConfig correctly loads security configuration from Settings."""
        with patch('app.core.config.application.app.settings', mock_settings):
            from app.core.config.application.app import AppConfig
            AppConfig._instances = {}
            
            config = AppConfig()
            
            # Verify security configuration
            assert config.jwt_secret_key == "test-jwt-secret"
            assert config.jwt_algorithm == "HS256"
            assert config.access_token_expire_minutes == 30

    def test_app_config_loads_api_configuration(self, mock_settings):
        """Test that AppConfig correctly loads API configuration from Settings."""
        with patch('app.core.config.application.app.settings', mock_settings):
            from app.core.config.application.app import AppConfig
            AppConfig._instances = {}
            
            config = AppConfig()
            
            # Verify API configuration
            assert config.api_host == "localhost"
            assert config.api_port == 8000

    def test_app_config_loads_logging_configuration(self, mock_settings):
        """Test that AppConfig correctly loads logging configuration from Settings."""
        with patch('app.core.config.application.app.settings', mock_settings):
            from app.core.config.application.app import AppConfig
            AppConfig._instances = {}
            
            config = AppConfig()
            
            # Verify logging configuration
            assert config.log_level == "INFO"

    @patch('app.core.config.application.app.dynamic_config_to_dict')
    @patch('app.core.config.application.app.IngestionConfig.model_validate')
    def test_app_config_loads_ingestion_configuration_successfully(
        self, 
        mock_validate, 
        mock_convert, 
        mock_settings,
        capsys
    ):
        """Test that AppConfig correctly loads ingestion configuration when data sources exist."""
        # Setup mocks
        mock_convert.return_value = {
            'dataSources': [
                {'type': 'file', 'path': '/test/path'},
                {'type': 'confluence', 'space': 'TEST'}
            ]
        }
        mock_ingestion_config = Mock()
        mock_ingestion_config.data_sources = {'file': Mock(), 'confluence': Mock()}
        mock_validate.return_value = mock_ingestion_config
        
        with patch('app.core.config.application.app.settings', mock_settings):
            from app.core.config.application.app import AppConfig
            AppConfig._instances = {}
            
            config = AppConfig()
            
            # Verify ingestion config was loaded
            assert config.ingestion_config is not None
            assert config.ingestion_config == mock_ingestion_config
            
            # Verify utility functions were called
            mock_convert.assert_called_once_with(mock_settings.data_sources)
            mock_validate.assert_called_once()
            
            # Check console output
            captured = capsys.readouterr()
            assert "Ingestion config loaded successfully" in captured.out

    def test_app_config_handles_no_data_sources(self, mock_settings_no_data_sources, capsys):
        """Test that AppConfig handles missing data sources gracefully."""
        with patch('app.core.config.application.app.settings', mock_settings_no_data_sources):
            from app.core.config.application.app import AppConfig
            AppConfig._instances = {}
            
            config = AppConfig()
            
            # Verify no ingestion config
            assert config.ingestion_config is None
            
            # Check console output
            captured = capsys.readouterr()
            assert "No data sources found in Settings" in captured.out

    def test_app_config_handles_missing_data_sources_attribute(self, capsys):
        """Test that AppConfig handles completely missing data_sources attribute."""
        mock_settings = Mock()
        mock_settings.app = Mock()
        mock_settings.app.environment = "test"
        mock_settings.app.debug = False
        mock_settings.app.name = "TestApp"
        mock_settings.app.version = "1.0.0"
        mock_settings.app.security = Mock()
        mock_settings.app.security.jwt_secret_key = "secret"
        mock_settings.app.security.jwt_algorithm = "HS256"
        mock_settings.app.security.access_token_expire_minutes = 30
        mock_settings.app.api = Mock()
        mock_settings.app.api.host = "localhost"
        mock_settings.app.api.port = 8000
        mock_settings.app.logging = Mock()
        mock_settings.app.logging.level = "INFO"
        
        # No data_sources attribute at all
        del mock_settings.data_sources
        
        with patch('app.core.config.application.app.settings', mock_settings):
            from app.core.config.application.app import AppConfig
            AppConfig._instances = {}
            
            config = AppConfig()
            
            # Verify no ingestion config
            assert config.ingestion_config is None
            
            # Check console output
            captured = capsys.readouterr()
            assert "No data sources found in Settings" in captured.out

    @patch('app.core.config.application.app.dynamic_config_to_dict')
    @patch('app.core.config.application.app.IngestionConfig.model_validate')
    def test_app_config_handles_ingestion_config_validation_error(
        self, 
        mock_validate, 
        mock_convert, 
        mock_settings,
        capsys
    ):
        """Test that AppConfig handles IngestionConfig validation errors gracefully."""
        # Setup mocks to raise validation error
        mock_convert.return_value = {'invalid': 'data'}
        mock_validate.side_effect = ValueError("Validation failed")
        
        with patch('app.core.config.application.app.settings', mock_settings):
            from app.core.config.application.app import AppConfig
            AppConfig._instances = {}
            
            config = AppConfig()
            
            # Verify ingestion config is None due to error
            assert config.ingestion_config is None
            
            # Check error message in output
            captured = capsys.readouterr()
            assert "Error loading ingestion config from Settings: Validation failed" in captured.out

    @patch('app.core.config.application.app.dynamic_config_to_dict')
    def test_app_config_handles_conversion_error(self, mock_convert, mock_settings, capsys):
        """Test that AppConfig handles dynamic_config_to_dict conversion errors."""
        # Setup mock to raise conversion error
        mock_convert.side_effect = AttributeError("Conversion failed")
        
        with patch('app.core.config.application.app.settings', mock_settings):
            from app.core.config.application.app import AppConfig
            AppConfig._instances = {}
            
            config = AppConfig()
            
            # Verify ingestion config is None due to error
            assert config.ingestion_config is None
            
            # Check error message in output
            captured = capsys.readouterr()
            assert "Error loading ingestion config from Settings: Conversion failed" in captured.out

    def test_app_config_singleton_behavior(self, mock_settings):
        """Test that AppConfig maintains singleton behavior."""
        with patch('app.core.config.application.app.settings', mock_settings):
            from app.core.config.application.app import AppConfig
            AppConfig._instances = {}
            
            config1 = AppConfig()
            config2 = AppConfig()
            
            # Should be the same instance
            assert config1 is config2
            assert id(config1) == id(config2)

    def test_app_config_different_environment_values(self):
        """Test AppConfig with different environment configurations."""
        environments = ["development", "staging", "production"]
        debug_values = [True, False]
        
        for env in environments:
            for debug in debug_values:
                mock_settings = Mock()
                mock_settings.app = Mock()
                mock_settings.app.environment = env
                mock_settings.app.debug = debug
                mock_settings.app.name = "TestApp"
                mock_settings.app.version = "2.0.0"
                mock_settings.app.security = Mock()
                mock_settings.app.security.jwt_secret_key = f"secret-{env}"
                mock_settings.app.security.jwt_algorithm = "HS256"
                mock_settings.app.security.access_token_expire_minutes = 45
                mock_settings.app.api = Mock()
                mock_settings.app.api.host = "0.0.0.0"
                mock_settings.app.api.port = 8080
                mock_settings.app.logging = Mock()
                mock_settings.app.logging.level = "ERROR"
                mock_settings.data_sources = None
                
                with patch('app.core.config.application.app.settings', mock_settings):
                    from app.core.config.application.app import AppConfig
                    AppConfig._instances = {}
                    
                    config = AppConfig()
                    
                    assert config.app_env == env
                    assert config.debug == debug
                    assert config.jwt_secret_key == f"secret-{env}"

    def test_app_config_edge_case_values(self):
        """Test AppConfig with edge case configuration values."""
        mock_settings = Mock()
        mock_settings.app = Mock()
        mock_settings.app.environment = ""
        mock_settings.app.debug = False
        mock_settings.app.name = None
        mock_settings.app.version = "0.0.0"
        mock_settings.app.security = Mock()
        mock_settings.app.security.jwt_secret_key = ""
        mock_settings.app.security.jwt_algorithm = "RS256"
        mock_settings.app.security.access_token_expire_minutes = 0
        mock_settings.app.api = Mock()
        mock_settings.app.api.host = ""
        mock_settings.app.api.port = 0
        mock_settings.app.logging = Mock()
        mock_settings.app.logging.level = None
        mock_settings.data_sources = None
        
        with patch('app.core.config.application.app.settings', mock_settings):
            from app.core.config.application.app import AppConfig
            AppConfig._instances = {}
            
            config = AppConfig()
            
            # Should handle edge cases without errors
            assert config.app_env == ""
            assert config.debug is False
            assert config.app_name is None
            assert config.jwt_secret_key == ""
            assert config.access_token_expire_minutes == 0
            assert config.api_host == ""
            assert config.api_port == 0
            assert config.log_level is None
