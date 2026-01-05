"""
Integration tests for Settings management system.

These tests verify the end-to-end functionality of the profile-based Settings system
including YAML loading, dynamic configuration, profile discovery, and
integration with existing configuration components.
"""

import os
import tempfile
import pytest
import yaml
from pathlib import Path

from app.core.config import Settings, DynamicConfig, YamlLoader


class TestSettings:
    """Integration tests for the Settings management system."""
    
    @pytest.fixture(autouse=True)
    def setup_and_teardown(self):
        """Set up and tear down test environment."""
        # Store original state
        self.original_instance = Settings._instance
        self.original_initialized = Settings._initialized
        
        # Reset singleton state for clean testing
        Settings.reset()
        
        # Create temporary test configuration files
        self.temp_dir = tempfile.mkdtemp()
        self.test_config_path = os.path.join(self.temp_dir, "test-defaults.yaml")
        self.test_nested_config_path = os.path.join(self.temp_dir, "test-nested.yaml")
        
        yield
        
        # Cleanup: restore original state and clean up temp files
        Settings._instance = self.original_instance
        Settings._initialized = self.original_initialized
        
        # Clean up temporary files
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def _create_test_config_file(self, config_data: dict, file_path: str = None):
        """Helper method to create test configuration files."""
        if file_path is None:
            file_path = self.test_config_path
            
        with open(file_path, 'w') as f:
            yaml.dump(config_data, f)
        
        return file_path
    
    def test_yaml_loader_basic_functionality(self):
        """Test YamlLoader can load and parse YAML files correctly."""
        # Test data
        test_data = {
            'llm': {
                'provider': 'openai',
                'model': 'gpt-4',
                'temperature': 0.7
            },
            'vector_db': {
                'provider': 'qdrant',
                'collection_name': 'test_collection'
            }
        }
        
        # Create test file
        config_file = self._create_test_config_file(test_data)
        
        # Test loading
        loaded_data = YamlLoader.load_file(config_file)
        
        # Assertions
        assert loaded_data == test_data
        assert loaded_data['llm']['provider'] == 'openai'
        assert loaded_data['vector_db']['collection_name'] == 'test_collection'
    
    def test_yaml_loader_missing_file_handling(self):
        """Test YamlLoader handles missing files gracefully."""
        non_existent_file = os.path.join(self.temp_dir, "does_not_exist.yaml")
        
        # Test with raise_on_missing=True (default)
        with pytest.raises(FileNotFoundError):
            YamlLoader.load_file(non_existent_file)
        
        # Test with raise_on_missing=False
        result = YamlLoader.load_file(non_existent_file, raise_on_missing=False)
        assert result == {}
    
    def test_yaml_loader_multiple_files_merge(self):
        """Test YamlLoader can load and merge multiple files."""
        # Create first config file
        config1_data = {
            'llm': {'provider': 'openai', 'temperature': 0.7},
            'database': {'provider': 'mongodb'}
        }
        config1_path = self._create_test_config_file(config1_data)
        
        # Create second config file  
        config2_data = {
            'llm': {'model': 'gpt-4'},  # Should merge with llm from config1
            'vector_db': {'provider': 'qdrant'}  # New section
        }
        config2_path = self._create_test_config_file(config2_data, self.test_nested_config_path)
        
        # Test merging
        merged_data = YamlLoader.load_multiple_files(config1_path, config2_path, merge=True)
        
        # Assertions
        assert merged_data['llm']['provider'] == 'openai'  # From config1
        assert merged_data['llm']['model'] == 'gpt-4'      # From config2
        assert merged_data['llm']['temperature'] == 0.7    # From config1
        assert merged_data['database']['provider'] == 'mongodb'
        assert merged_data['vector_db']['provider'] == 'qdrant'
    
    def test_dynamic_config_dot_notation_access(self):
        """Test DynamicConfig provides proper dot notation access."""
        test_data = {
            'llm': {
                'provider': 'openai',
                'config': {
                    'temperature': 0.7,
                    'max_tokens': 4096
                }
            },
            'vector_db': {
                'provider': 'qdrant',
                'settings': {
                    'collection_name': 'test_collection'
                }
            },
            'simple_value': 'test'
        }
        
        config = DynamicConfig(test_data)
        
        # Test dot notation access
        assert config.llm.provider == 'openai'
        assert config.llm.config.temperature == 0.7
        assert config.llm.config.max_tokens == 4096
        assert config.vector_db.provider == 'qdrant'
        assert config.vector_db.settings.collection_name == 'test_collection'
        assert config.simple_value == 'test'
    
    def test_dynamic_config_key_sanitization(self):
        """Test DynamicConfig properly sanitizes invalid attribute names."""
        test_data = {
            'llm-provider': 'openai',           # Hyphen should become underscore
            'vector.db': 'qdrant',              # Dot should become underscore
            'class': 'test_class',              # Reserved keyword
            '2_starts_with_number': 'value',    # Starts with number
            'normal_key': 'normal_value'
        }
        
        config = DynamicConfig(test_data)
        
        # Test sanitized access
        assert config.llm_provider == 'openai'
        assert config.vector_db == 'qdrant'
        assert config.class_ == 'test_class'  # Should have underscore suffix
        assert config._2_starts_with_number == 'value'  # Should have underscore prefix
        assert config.normal_key == 'normal_value'
    
    def test_dynamic_config_get_method(self):
        """Test DynamicConfig get method with dot notation paths."""
        test_data = {
            'llm': {
                'provider': 'openai',
                'nested': {
                    'deep': {
                        'value': 'found'
                    }
                }
            }
        }
        
        config = DynamicConfig(test_data)
        
        # Test get method
        assert config.get('llm.provider') == 'openai'
        assert config.get('llm.nested.deep.value') == 'found'
        assert config.get('nonexistent.key', 'default') == 'default'
        assert config.get('llm.nonexistent', None) is None
    
    def test_dynamic_config_has_method(self):
        """Test DynamicConfig has method for checking key existence."""
        test_data = {
            'llm': {
                'provider': 'openai'
            }
        }
        
        config = DynamicConfig(test_data)
        
        # Test has method
        assert config.has('llm') is True
        assert config.has('llm.provider') is True
        assert config.has('nonexistent') is False
        assert config.has('llm.nonexistent') is False
    
    def test_settings_singleton_behavior(self):
        """Test Settings singleton behavior."""
        # Test singleton property
        settings1 = Settings.instance()
        settings2 = Settings.instance()
        
        assert settings1 is settings2
        assert isinstance(settings1, Settings)
    
    def test_defaults_manager_with_test_config(self):
        """Test DefaultConfigManager with a test configuration file."""
        # Create test defaults file
        test_defaults = {
            'llm': {
                'provider': 'test_provider',
                'model': 'test_model',
                'temperature': 0.5
            },
            'vector_db': {
                'provider': 'test_vector_db',
                'collection_name': 'test_collection'
            },
            'database': {
                'provider': 'test_database'
            }
        }
        
        # Save to resources directory temporarily
        resources_dir = Path(__file__).parent.parent.parent / "resources"
        test_defaults_file = resources_dir / "test-application-defaults.yaml"
        
        try:
            with open(test_defaults_file, 'w') as f:
                yaml.dump(test_defaults, f)
            
            # Temporarily modify the defaults manager to use test file
            original_load = DefaultsManager._load_default_configurations
            
            def mock_load_defaults(self):
                try:
                    defaults_data = YamlLoader.load_file(str(test_defaults_file), raise_on_missing=False)
                    self._create_dynamic_attributes(defaults_data)
                except Exception as e:
                    print(f"Error in mock load: {e}")
                    self._create_dynamic_attributes({})
            
            DefaultsManager._load_default_configurations = mock_load_defaults
            
            # Reset and create new instance
            DefaultConfigManager.reset()
            manager = DefaultConfigManager.instance()
            
            # Test dot notation access
            assert manager.llm.provider == 'test_provider'
            assert manager.llm.model == 'test_model'
            assert manager.llm.temperature == 0.5
            assert manager.vector_db.provider == 'test_vector_db'
            assert manager.vector_db.collection_name == 'test_collection'
            assert manager.database.provider == 'test_database'
            
        finally:
            # Cleanup: restore original method and remove test file
            DefaultsManager._load_default_configurations = original_load
            if test_defaults_file.exists():
                test_defaults_file.unlink()
    
    def test_defaults_manager_section_methods(self):
        """Test DefaultConfigManager section management methods."""
        # Create test config
        test_data = {
            'llm': {'provider': 'openai'},
            'vector_db': {'provider': 'qdrant'}
        }
        
        # Mock the defaults manager with test data
        manager = DefaultConfigManager.instance()
        manager._create_dynamic_attributes(test_data)
        
        # Test section methods
        assert manager.has_section('llm') is True
        assert manager.has_section('vector_db') is True
        assert manager.has_section('nonexistent') is False
        
        llm_section = manager.get_section('llm')
        assert llm_section is not None
        assert llm_section.provider == 'openai'
        
        sections = manager.list_sections()
        assert 'llm' in sections
        assert 'vector_db' in sections
    
    def test_defaults_manager_get_value_method(self):
        """Test DefaultConfigManager get_value method with path navigation."""
        test_data = {
            'llm': {
                'provider': 'openai',
                'config': {
                    'temperature': 0.7
                }
            }
        }
        
        manager = DefaultConfigManager.instance()
        manager._create_dynamic_attributes(test_data)
        
        # Test get_value method
        assert manager.get_value('llm.provider') == 'openai'
        assert manager.get_value('llm.config.temperature') == 0.7
        assert manager.get_value('nonexistent.path', 'default') == 'default'
        assert manager.get_value('llm.nonexistent', None) is None
    
    def test_defaults_manager_reload_functionality(self):
        """Test DefaultConfigManager reload functionality."""
        manager = DefaultConfigManager.instance()
        
        # Store original sections
        original_sections = manager.list_sections()
        
        # Test reload (should not crash)
        manager.reload()
        
        # Verify manager is still functional
        reloaded_sections = manager.list_sections()
        assert isinstance(reloaded_sections, list)
    
    def test_integration_with_existing_config_system(self):
        """Test integration with existing configuration system."""
        # Import existing config components
        from app.core.config import config, app_config, database_config, vector_config
        
        # Test existing system still works
        assert config is not None
        assert hasattr(config, 'app')
        assert hasattr(config, 'database')
        assert hasattr(config, 'vector')
        
        # Test new defaults manager is available
        defaults = DefaultConfigManager.instance()
        assert defaults is not None
        assert hasattr(defaults, 'list_sections')
        assert hasattr(defaults, 'get_value')
        
        # Test both systems coexist
        assert config.app == app_config
        assert config.database == database_config
        assert config.vector == vector_config
    
    def test_real_application_defaults_file_loading(self):
        """Test loading the actual application-defaults.yaml file."""
        # Test that the actual defaults file can be loaded
        resources_dir = Path(__file__).parent.parent.parent / "resources"
        defaults_file = resources_dir / "application-defaults.yaml"
        
        if defaults_file.exists():
            # Test loading the real file
            data = YamlLoader.load_file(str(defaults_file))
            
            # Verify expected structure exists
            assert isinstance(data, dict)
            
            # Check for expected top-level sections
            expected_sections = ['llm', 'vector_db', 'embeddings', 'database', 'agent']
            for section in expected_sections:
                if section in data:
                    assert isinstance(data[section], dict)
            
            # Test creating DynamicConfig from real data
            config = DynamicConfig(data)
            
            # Verify dot notation works with real data
            if 'llm' in data and 'provider' in data['llm']:
                assert hasattr(config, 'llm')
                assert hasattr(config.llm, 'provider')
        else:
            pytest.skip("application-defaults.yaml file not found")
    
    def test_error_handling_and_recovery(self):
        """Test error handling and recovery in configuration system."""
        # Test with malformed YAML
        malformed_yaml_path = os.path.join(self.temp_dir, "malformed.yaml")
        with open(malformed_yaml_path, 'w') as f:
            f.write("invalid: yaml: content: {\n")
        
        # Should raise YAMLError
        with pytest.raises(yaml.YAMLError):
            YamlLoader.load_file(malformed_yaml_path)
        
        # Test DynamicConfig with None data
        config = DynamicConfig({})
        assert config.get('any.key', 'default') == 'default'
        assert not config.has('any.key')
        
        # Test DefaultConfigManager with missing file
        DefaultConfigManager.reset()
        manager = DefaultConfigManager.instance()
        
        # Should not crash, should initialize with empty config
        assert manager is not None
        assert isinstance(manager.list_sections(), list)
