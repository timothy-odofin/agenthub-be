"""
Unit tests for Settings enhancements (to_dict and get_section methods).
"""
import unittest
from unittest.mock import patch, MagicMock
from app.core.config.framework.settings import Settings


class TestSettingsEnhancements(unittest.TestCase):
    """Test cases for Settings enhancements."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Reset Settings singleton before each test
        Settings.reset()
    
    def tearDown(self):
        """Clean up after tests."""
        Settings.reset()
    
    @patch('app.core.config.framework.settings.YamlLoader.load_file')
    @patch('app.core.config.framework.settings.Settings._get_resources_directory')
    def test_to_dict_converts_all_profiles(self, mock_get_resources_dir, mock_load_file):
        """Test that to_dict() converts all profile configurations to standard dicts."""
        # Mock resources directory
        mock_resources_dir = MagicMock()
        mock_resources_dir.exists.return_value = True
        mock_resources_dir.glob.return_value = []
        mock_resources_dir.iterdir.return_value = []
        mock_get_resources_dir.return_value = mock_resources_dir
        
        # Mock YAML loading - simulate loading profiles
        def mock_load_side_effect(file_path, raise_on_missing=False):
            if 'app' in str(file_path):
                return {
                    'name': 'test-app',
                    'environment': 'development',
                    'debug': True,
                    'security': {
                        'jwt_secret_key': 'secret123',
                        'jwt_algorithm': 'HS256'
                    }
                }
            elif 'db' in str(file_path):
                return {
                    'postgres': {
                        'host': 'localhost',
                        'port': 5432,
                        'database': 'testdb'
                    },
                    'redis': {
                        'host': 'localhost',
                        'port': 6379
                    }
                }
            return {}
        
        mock_load_file.side_effect = mock_load_side_effect
        
        # Create Settings instance
        settings = Settings.instance()
        
        # Manually set up profile configurations for testing
        from app.core.config.framework.dynamic_config import DynamicConfig
        settings.app = DynamicConfig({
            'name': 'test-app',
            'environment': 'development',
            'debug': True,
            'security': DynamicConfig({
                'jwt_secret_key': 'secret123',
                'jwt_algorithm': 'HS256'
            })
        })
        settings.db = DynamicConfig({
            'postgres': DynamicConfig({
                'host': 'localhost',
                'port': 5432,
                'database': 'testdb'
            }),
            'redis': DynamicConfig({
                'host': 'localhost',
                'port': 6379
            })
        })
        settings._configured_profiles = ['app', 'db']
        
        # Test to_dict()
        config_dict = settings.to_dict()
        
        # Verify it returns a standard dictionary
        self.assertIsInstance(config_dict, dict)
        
        # Verify all profiles are present
        self.assertIn('app', config_dict)
        self.assertIn('db', config_dict)
        
        # Verify nested structures are converted to dicts
        self.assertIsInstance(config_dict['app'], dict)
        self.assertIsInstance(config_dict['app']['security'], dict)
        self.assertIsInstance(config_dict['db'], dict)
        self.assertIsInstance(config_dict['db']['postgres'], dict)
        
        # Verify values are preserved
        self.assertEqual(config_dict['app']['name'], 'test-app')
        self.assertEqual(config_dict['app']['security']['jwt_secret_key'], 'secret123')
        self.assertEqual(config_dict['db']['postgres']['host'], 'localhost')
        self.assertEqual(config_dict['db']['redis']['port'], 6379)
    
    @patch('app.core.config.framework.settings.YamlLoader.load_file')
    @patch('app.core.config.framework.settings.Settings._get_resources_directory')
    def test_get_section_retrieves_nested_values(self, mock_get_resources_dir, mock_load_file):
        """Test that get_section() retrieves nested configuration values."""
        # Setup mocks
        mock_resources_dir = MagicMock()
        mock_resources_dir.exists.return_value = True
        mock_resources_dir.glob.return_value = []
        mock_resources_dir.iterdir.return_value = []
        mock_get_resources_dir.return_value = mock_resources_dir
        mock_load_file.return_value = {}
        
        # Create Settings instance
        settings = Settings.instance()
        
        # Manually set up configuration
        from app.core.config.framework.dynamic_config import DynamicConfig
        settings.app = DynamicConfig({
            'name': 'test-app',
            'security': DynamicConfig({
                'jwt_secret_key': 'secret123',
                'access_token_expire_minutes': 30
            })
        })
        settings.db = DynamicConfig({
            'redis': DynamicConfig({
                'host': 'localhost',
                'port': 6379
            })
        })
        settings._configured_profiles = ['app', 'db']
        
        # Test get_section() with various paths
        
        # Get entire profile
        app_config = settings.get_section('app')
        self.assertIsNotNone(app_config)
        
        # Get nested section
        security_config = settings.get_section('app.security')
        self.assertIsNotNone(security_config)
        
        # Get specific value
        jwt_secret = settings.get_section('app.security.jwt_secret_key')
        self.assertEqual(jwt_secret, 'secret123')
        
        # Get from different profile
        redis_host = settings.get_section('db.redis.host')
        self.assertEqual(redis_host, 'localhost')
        
        # Test default value for missing path
        missing_value = settings.get_section('app.missing.path', default='default_value')
        self.assertEqual(missing_value, 'default_value')
        
        # Test default value for missing profile
        missing_profile = settings.get_section('nonexistent.profile', default=None)
        self.assertIsNone(missing_profile)
    
    @patch('app.core.config.framework.settings.YamlLoader.load_file')
    @patch('app.core.config.framework.settings.Settings._get_resources_directory')
    def test_get_section_with_defaults(self, mock_get_resources_dir, mock_load_file):
        """Test that get_section() returns default values properly."""
        # Setup mocks
        mock_resources_dir = MagicMock()
        mock_resources_dir.exists.return_value = True
        mock_resources_dir.glob.return_value = []
        mock_resources_dir.iterdir.return_value = []
        mock_get_resources_dir.return_value = mock_resources_dir
        mock_load_file.return_value = {}
        
        # Create Settings instance
        settings = Settings.instance()
        
        # Test with empty configuration
        settings._configured_profiles = []
        
        # Should return default for missing profile
        result = settings.get_section('app.name', default='default-app')
        self.assertEqual(result, 'default-app')
        
        # Should return None as default when not specified
        result = settings.get_section('app.name')
        self.assertIsNone(result)
        
        # Should return complex default values
        default_config = {'host': 'localhost', 'port': 5432}
        result = settings.get_section('db.postgres', default=default_config)
        self.assertEqual(result, default_config)


if __name__ == '__main__':
    unittest.main()
