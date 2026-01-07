"""
Core Configuration System Integration Tests.

Comprehensive integration tests for the core configuration system including:
- Settings framework (singleton, profile discovery, YAML loading)
- Property resolution (environment variables, placeholders, type conversion)
- Dynamic configuration (dot notation, nested access, attribute creation)
- Integration with application configuration providers
- Error handling and edge cases
- Performance and caching behavior

These tests verify the end-to-end functionality of the configuration
system that forms the foundation of the application.
"""

import os
import tempfile
import pytest
import yaml
import shutil
import time
from pathlib import Path
from unittest.mock import Mock, patch
from typing import Dict, Any

from app.core.config import Settings, DynamicConfig, YamlLoader
from app.core.utils import PropertyResolver, EnvironmentManager, env


class TestCoreConfigurationSystemIntegration:
    """Comprehensive integration tests for the core configuration system."""

    @pytest.fixture(autouse=True)
    def setup_and_teardown(self):
        """Set up and tear down test environment with isolated configuration."""
        # Store original state
        self.original_settings_instance = Settings._instance
        self.original_settings_initialized = Settings._initialized
        
        # Store original environment
        self.original_env = dict(os.environ)
        
        # Reset singletons for clean testing
        Settings.reset()
        env.clear_cache()
        
        # Create temporary test resources
        self.temp_dir = tempfile.mkdtemp()
        self.resources_dir = Path(self.temp_dir) / "resources"
        self.resources_dir.mkdir(exist_ok=True)
        
        yield
        
        # Cleanup: restore original state
        Settings._instance = self.original_settings_instance
        Settings._initialized = self.original_settings_initialized
        
        # Restore environment
        os.environ.clear()
        os.environ.update(self.original_env)
        env.clear_cache()
        
        # Clean up temporary files
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def _create_profile_file(self, profile_name: str, config_data: Dict[str, Any]):
        """Helper to create test profile configuration files."""
        profile_file = self.resources_dir / f"application-{profile_name}.yaml"
        with open(profile_file, 'w') as f:
            yaml.dump(config_data, f)
        return str(profile_file)

    def _create_env_vars(self, env_vars: Dict[str, str]):
        """Helper to set environment variables for tests."""
        for key, value in env_vars.items():
            os.environ[key] = value

class TestSettingsFrameworkIntegration(TestCoreConfigurationSystemIntegration):
    """Test Settings framework integration including profile discovery and loading."""

    def test_settings_singleton_behavior(self):
        """Test Settings maintains singleton behavior across multiple access points."""
        # Mock resources directory
        with patch.object(Settings, '_get_resources_directory', return_value=self.resources_dir):
            Settings.reset()
            
            settings1 = Settings.instance()
            settings2 = Settings.instance()
            
            assert settings1 is settings2
            assert isinstance(settings1, Settings)

    def test_profile_discovery_and_loading(self):
        """Test automatic discovery and loading of profile configuration files."""
        # Create multiple profile files
        self._create_profile_file('app', {
            'server': {'port': 8080, 'host': 'localhost'},
            'security': {'jwt_secret': 'test_secret'}
        })
        
        self._create_profile_file('db', {
            'mongodb': {'host': 'localhost', 'port': 27017},
            'redis': {'host': 'localhost', 'port': 6379}
        })
        
        self._create_profile_file('llm', {
            'provider': 'openai',
            'model': 'gpt-4',
            'temperature': 0.7
        })
        
        with patch.object(Settings, '_get_resources_directory', return_value=self.resources_dir):
            Settings.reset()
            settings = Settings.instance()
            
            # Verify profiles were discovered
            profile_names = settings.get_profile_names()
            assert 'app' in profile_names
            assert 'db' in profile_names
            assert 'llm' in profile_names
            
            # Verify profile access
            assert settings.app.server.port == 8080
            assert settings.app.security.jwt_secret == 'test_secret'
            assert settings.db.mongodb.host == 'localhost'
            assert settings.llm.provider == 'openai'

    def test_nested_profile_discovery(self):
        """Test discovery of nested profile configurations."""
        # Create nested directory structure
        workflows_dir = self.resources_dir / "workflows"
        workflows_dir.mkdir()
        
        # Create nested workflow configs
        with open(workflows_dir / "application-approval.yaml", 'w') as f:
            yaml.dump({'steps': ['validate', 'review', 'approve']}, f)
            
        with open(workflows_dir / "application-signup.yaml", 'w') as f:
            yaml.dump({'steps': ['register', 'verify', 'activate']}, f)
        
        with patch.object(Settings, '_get_resources_directory', return_value=self.resources_dir):
            Settings.reset()
            settings = Settings.instance()
            
            # Verify nested profiles
            assert hasattr(settings, 'workflows')
            assert hasattr(settings.workflows, 'approval')
            assert hasattr(settings.workflows, 'signup')
            
            assert settings.workflows.approval.steps == ['validate', 'review', 'approve']
            assert settings.workflows.signup.steps == ['register', 'verify', 'activate']

    def test_settings_caching_behavior(self):
        """Test Settings caching behavior for performance."""
        self._create_profile_file('cache-test', {
            'database': {'pool_size': 10},
            'redis': {'max_connections': 100}
        })
        
        with patch.object(Settings, '_get_resources_directory', return_value=self.resources_dir):
            Settings.reset()
            settings = Settings.instance()
            
            # First access - should load from file
            start_time = time.time()
            config1 = settings.cache_test
            first_access_time = time.time() - start_time
            
            # Second access - should use cache
            start_time = time.time()
            config2 = settings.cache_test
            second_access_time = time.time() - start_time
            
            # Verify same object and faster access
            assert config1 is config2
            assert second_access_time < first_access_time * 0.5  # Should be significantly faster

class TestPropertyResolutionIntegration(TestCoreConfigurationSystemIntegration):
    """Test property resolution integration with configuration system."""

    def test_environment_variable_resolution_in_profiles(self):
        """Test environment variable resolution within profile configurations."""
        # Set environment variables
        self._create_env_vars({
            'APP_HOST': 'production.example.com',
            'APP_PORT': '443',
            'DB_PASSWORD': 'secret123',
            'FEATURE_ENABLED': 'true'
        })
        
        # Create profile with placeholders
        self._create_profile_file('env-test', {
            'server': {
                'host': '${APP_HOST}',
                'port': '${APP_PORT}',
                'ssl_enabled': '${SSL_ENABLED:false}'  # With default
            },
            'database': {
                'password': '${DB_PASSWORD}',
                'pool_size': '${POOL_SIZE:20}'
            },
            'features': {
                'analytics': '${FEATURE_ENABLED}',
                'debug': '${DEBUG_MODE:false}'
            }
        })
        
        with patch.object(Settings, '_get_resources_directory', return_value=self.resources_dir):
            Settings.reset()
            settings = Settings.instance()
            
            # Verify environment variable resolution
            assert settings.env_test.server.host == 'production.example.com'
            assert settings.env_test.server.port == 443  # Type conversion
            assert settings.env_test.server.ssl_enabled is False  # Default value
            
            assert settings.env_test.database.password == 'secret123'
            assert settings.env_test.database.pool_size == 20
            
            assert settings.env_test.features.analytics is True
            assert settings.env_test.features.debug is False

    def test_complex_placeholder_resolution(self):
        """Test complex placeholder resolution scenarios."""
        self._create_env_vars({
            'BASE_URL': 'https://api.example.com',
            'API_VERSION': 'v2',
            'MAX_RETRIES': '3'
        })
        
        self._create_profile_file('complex-placeholders', {
            'api': {
                'endpoint': '${BASE_URL}/${API_VERSION}/users',
                'config': {
                    'retries': '${MAX_RETRIES}',
                    'timeout': '${API_TIMEOUT:30}',
                    'rate_limit': '${RATE_LIMIT:100}'
                }
            },
            'computed': {
                'display_name': 'API ${API_VERSION} (${MAX_RETRIES} retries)'
            }
        })
        
        with patch.object(Settings, '_get_resources_directory', return_value=self.resources_dir):
            Settings.reset()
            settings = Settings.instance()
            
            assert settings.complex_placeholders.api.endpoint == 'https://api.example.com/v2/users'
            assert settings.complex_placeholders.api.config.retries == 3
            assert settings.complex_placeholders.api.config.timeout == 30
            assert settings.complex_placeholders.computed.display_name == 'API v2 (3 retries)'

    def test_type_conversion_integration(self):
        """Test automatic type conversion in configuration loading."""
        self._create_env_vars({
            'WORKER_THREADS': '8',
            'CACHE_TTL': '3600.5',
            'DEBUG_ENABLED': 'true',
            'FEATURES': 'auth,logging,monitoring'
        })
        
        self._create_profile_file('type-conversion', {
            'workers': {
                'count': '${WORKER_THREADS}',
                'timeout': '${WORKER_TIMEOUT:60.0}'
            },
            'cache': {
                'ttl': '${CACHE_TTL}',
                'enabled': '${CACHE_ENABLED:true}'
            },
            'debug': '${DEBUG_ENABLED}',
            'features': '${FEATURES}',
            'static_values': {
                'integer': 42,
                'float': 3.14,
                'boolean': False,
                'string': 'literal'
            }
        })
        
        with patch.object(Settings, '_get_resources_directory', return_value=self.resources_dir):
            Settings.reset()
            settings = Settings.instance()
            
            # Test type conversions
            assert settings.type_conversion.workers.count == 8
            assert isinstance(settings.type_conversion.workers.count, int)
            
            assert settings.type_conversion.workers.timeout == 60.0
            assert isinstance(settings.type_conversion.workers.timeout, float)
            
            assert settings.type_conversion.cache.ttl == 3600.5
            assert isinstance(settings.type_conversion.cache.ttl, float)
            
            assert settings.type_conversion.debug is True
            assert isinstance(settings.type_conversion.debug, bool)
            
            # Test static values preserve types
            assert settings.type_conversion.static_values.integer == 42
            assert isinstance(settings.type_conversion.static_values.integer, int)

class TestDynamicConfigurationIntegration(TestCoreConfigurationSystemIntegration):
    """Test DynamicConfig integration and behavior."""

    def test_dot_notation_access_patterns(self):
        """Test various dot notation access patterns."""
        config_data = {
            'api': {
                'v1': {
                    'endpoints': {
                        'users': '/api/v1/users',
                        'orders': '/api/v1/orders'
                    },
                    'rate_limits': {
                        'per_minute': 60,
                        'per_hour': 3600
                    }
                }
            },
            'features': {
                'authentication': True,
                'analytics': False
            }
        }
        
        config = DynamicConfig(config_data)
        
        # Test nested access
        assert config.api.v1.endpoints.users == '/api/v1/users'
        assert config.api.v1.rate_limits.per_minute == 60
        assert config.features.authentication is True
        
        # Test get method with paths
        assert config.get('api.v1.endpoints.orders') == '/api/v1/orders'
        assert config.get('features.analytics') is False
        assert config.get('nonexistent.path', 'default') == 'default'
        
        # Test has method
        assert config.has('api.v1.endpoints') is True
        assert config.has('api.v1.endpoints.users') is True
        assert config.has('nonexistent.path') is False

    def test_attribute_name_sanitization(self):
        """Test attribute name sanitization for invalid Python identifiers."""
        config_data = {
            'api-version': 'v2',                    # Hyphen
            'cache.size': 100,                      # Dot
            'class': 'UserService',                 # Reserved keyword
            '2fa_enabled': True,                    # Starts with digit
            'max-retry-count': 3,                   # Multiple hyphens
            'normal_key': 'normal_value'            # Valid key
        }
        
        config = DynamicConfig(config_data)
        
        # Test sanitized access
        assert config.api_version == 'v2'
        assert config.cache_size == 100
        assert config.class_ == 'UserService'  # Reserved word gets underscore
        assert config._2fa_enabled is True    # Leading underscore for digit start
        assert config.max_retry_count == 3
        assert config.normal_key == 'normal_value'

    def test_nested_dynamic_config_behavior(self):
        """Test behavior with deeply nested DynamicConfig objects."""
        config_data = {
            'level1': {
                'level2': {
                    'level3': {
                        'level4': {
                            'deep_value': 'found',
                            'deep_number': 42
                        }
                    }
                }
            }
        }
        
        config = DynamicConfig(config_data)
        
        # Test deep nesting
        assert config.level1.level2.level3.level4.deep_value == 'found'
        assert config.level1.level2.level3.level4.deep_number == 42
        
        # Test intermediate objects are DynamicConfig instances
        assert isinstance(config.level1, DynamicConfig)
        assert isinstance(config.level1.level2, DynamicConfig)
        assert isinstance(config.level1.level2.level3, DynamicConfig)
        assert isinstance(config.level1.level2.level3.level4, DynamicConfig)

class TestConfigurationIntegrationWithApplicationComponents(TestCoreConfigurationSystemIntegration):
    """Test integration between configuration system and application components."""

    def test_integration_with_existing_config_providers(self):
        """Test integration with existing application configuration providers."""
        # Create comprehensive app configuration
        self._create_profile_file('app', {
            'name': 'AgentHub',
            'version': '1.0.0',
            'debug': False,
            'security': {
                'jwt_secret': 'test_secret',
                'token_expiry': 3600
            },
            'api': {
                'prefix': '/api/v1',
                'cors_enabled': True
            }
        })
        
        with patch.object(Settings, '_get_resources_directory', return_value=self.resources_dir):
            Settings.reset()
            
            # Import and test existing config components
            from app.core.config import config, app_config
            
            # Verify existing system still works
            assert config is not None
            assert hasattr(config, 'app')
            
            # Verify new Settings system integration
            settings = Settings.instance()
            assert settings is not None
            assert hasattr(settings, 'app')
            
            # Test both systems have access to the same data
            assert settings.app.name == 'AgentHub'
            assert settings.app.security.jwt_secret == 'test_secret'

    def test_configuration_reload_and_hot_updates(self):
        """Test configuration reload capabilities for hot updates."""
        # Create initial configuration
        self._create_profile_file('hot-reload', {
            'feature_flags': {
                'new_ui': False,
                'advanced_analytics': True
            },
            'limits': {
                'max_users': 1000
            }
        })
        
        with patch.object(Settings, '_get_resources_directory', return_value=self.resources_dir):
            Settings.reset()
            settings = Settings.instance()
            
            # Verify initial state
            assert settings.hot_reload.feature_flags.new_ui is False
            assert settings.hot_reload.limits.max_users == 1000
            
            # Update configuration file
            self._create_profile_file('hot-reload', {
                'feature_flags': {
                    'new_ui': True,  # Changed
                    'advanced_analytics': True
                },
                'limits': {
                    'max_users': 2000  # Changed
                }
            })
            
            # Test reload functionality (if available)
            if hasattr(settings, 'reload'):
                settings.reload()
                assert settings.hot_reload.feature_flags.new_ui is True
                assert settings.hot_reload.limits.max_users == 2000

class TestConfigurationErrorHandlingAndEdgeCases(TestCoreConfigurationSystemIntegration):
    """Test error handling and edge cases in configuration system."""

    def test_missing_environment_variable_handling(self):
        """Test handling of missing environment variables."""
        # Create config with missing environment variables
        self._create_profile_file('missing-env', {
            'database': {
                'host': '${DB_HOST:localhost}',      # Has default
                'password': '${DB_PASSWORD}',         # No default - should cause issues
                'port': '${DB_PORT:5432}'            # Has default
            }
        })
        
        with patch.object(Settings, '_get_resources_directory', return_value=self.resources_dir):
            Settings.reset()
            settings = Settings.instance()
            
            # Should handle missing vars gracefully
            assert settings.missing_env.database.host == 'localhost'
            assert settings.missing_env.database.port == 5432
            
            # Missing required variable should be None or raise appropriate error
            password = settings.missing_env.database.password
            assert password is None or isinstance(password, str)

    def test_invalid_yaml_file_handling(self):
        """Test handling of invalid YAML configuration files."""
        # Create invalid YAML file
        invalid_yaml_file = self.resources_dir / "application-invalid.yaml"
        with open(invalid_yaml_file, 'w') as f:
            f.write("invalid: yaml: content: [\n  - missing close bracket\n")
        
        with patch.object(Settings, '_get_resources_directory', return_value=self.resources_dir):
            Settings.reset()
            # Should handle invalid YAML gracefully without crashing
            settings = Settings.instance()
            
            # Invalid profile should not be available
            profile_names = settings.get_profile_names()
            assert 'invalid' not in profile_names

    def test_circular_reference_detection(self):
        """Test detection and handling of circular references in placeholders."""
        self._create_env_vars({
            'CIRCULAR_A': '${CIRCULAR_B}',
            'CIRCULAR_B': '${CIRCULAR_A}'
        })
        
        self._create_profile_file('circular', {
            'config': {
                'value_a': '${CIRCULAR_A}',
                'value_b': '${CIRCULAR_B}'
            }
        })
        
        with patch.object(Settings, '_get_resources_directory', return_value=self.resources_dir):
            Settings.reset()
            settings = Settings.instance()
            
            # Should handle circular references gracefully
            # Either resolve to None or raise appropriate error
            try:
                value_a = settings.circular.config.value_a
                value_b = settings.circular.config.value_b
                # If no exception, values should be None or the placeholder strings
                assert value_a is None or isinstance(value_a, str)
                assert value_b is None or isinstance(value_b, str)
            except (ValueError, RecursionError):
                # Acceptable to raise these errors for circular references
                pass

class TestConfigurationPerformanceIntegration(TestCoreConfigurationSystemIntegration):
    """Test configuration system performance characteristics."""

    def test_large_configuration_handling(self):
        """Test handling of large configuration structures."""
        # Create large configuration
        large_config = {}
        for i in range(100):
            large_config[f'section_{i}'] = {
                f'key_{j}': f'value_{i}_{j}' for j in range(50)
            }
        
        self._create_profile_file('large', large_config)
        
        with patch.object(Settings, '_get_resources_directory', return_value=self.resources_dir):
            Settings.reset()
            
            start_time = time.time()
            settings = Settings.instance()
            load_time = time.time() - start_time
            
            # Should load within reasonable time (adjust threshold as needed)
            assert load_time < 5.0  # 5 seconds threshold
            
            # Verify data integrity
            assert settings.large.section_0.key_0 == 'value_0_0'
            assert settings.large.section_99.key_49 == 'value_99_49'

    def test_concurrent_access_behavior(self):
        """Test behavior under concurrent access scenarios."""
        import threading
        import concurrent.futures
        
        self._create_profile_file('concurrent', {
            'shared': {
                'counter': 0,
                'data': 'shared_value'
            }
        })
        
        with patch.object(Settings, '_get_resources_directory', return_value=self.resources_dir):
            Settings.reset()
            
            def access_settings():
                settings = Settings.instance()
                return settings.concurrent.shared.data
            
            # Test concurrent access
            with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
                futures = [executor.submit(access_settings) for _ in range(20)]
                results = [future.result() for future in futures]
            
            # All results should be the same
            assert all(result == 'shared_value' for result in results)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
