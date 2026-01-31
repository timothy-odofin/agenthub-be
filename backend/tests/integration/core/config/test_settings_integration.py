"""
Integration tests for Settings management system.

These tests verify the end-to-end functionality of the profile-based Settings system
including YAML profile discovery, dynamic configuration, and integration with existing systems.
"""

import os
import tempfile
import pytest
import yaml
import shutil
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
        
        # Create temporary test resources directory
        self.temp_dir = tempfile.mkdtemp()
        self.temp_resources_dir = os.path.join(self.temp_dir, "resources")
        os.makedirs(self.temp_resources_dir, exist_ok=True)
        
        yield
        
        # Cleanup: restore original state and clean up temp files
        Settings._instance = self.original_instance
        Settings._initialized = self.original_initialized
        
        # Clean up temporary files
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def _create_test_profile_file(self, profile_name: str, config_data: dict):
        """Helper method to create test profile files."""
        file_path = os.path.join(self.temp_resources_dir, f"application-{profile_name}.yaml")
        with open(file_path, 'w') as f:
            yaml.dump(config_data, f)
        return file_path
    
    def test_settings_singleton_behavior(self):
        """Test Settings singleton behavior."""
        # Test singleton property
        settings1 = Settings.instance()
        settings2 = Settings.instance()
        
        assert settings1 is settings2
        assert isinstance(settings1, Settings)
    
    def test_profile_discovery_and_loading(self):
        """Test automatic discovery and loading of profile files."""
        # Create test profile files
        llm_config = {
            'provider': 'openai',
            'model': 'gpt-4',
            'temperature': 0.7
        }
        self._create_test_profile_file('llm', llm_config)
        
        vector_config = {
            'provider': 'qdrant',
            'collection_name': 'test_collection'
        }
        self._create_test_profile_file('vector', vector_config)
        
        app_config = {
            'name': 'TestApp',
            'version': '1.0.0'
        }
        self._create_test_profile_file('app', app_config)
        
        # Mock the resources directory discovery
        original_get_resources = Settings._get_resources_directory
        
        def mock_get_resources(self):
            return Path(self.temp_resources_dir)
        
        Settings._get_resources_directory = mock_get_resources
        
        try:
            # Reset and create new settings instance
            Settings.reset()
            settings = Settings.instance()
            
            # Test profile discovery
            profiles = settings.get_profile_names()
            assert 'llm' in profiles
            assert 'vector' in profiles
            assert 'app' in profiles
            
            # Test dot notation access
            assert settings.llm.provider == 'openai'
            assert settings.llm.model == 'gpt-4'
            assert settings.vector.provider == 'qdrant'
            assert settings.app.name == 'TestApp'
            
        finally:
            # Restore original method
            Settings._get_resources_directory = original_get_resources
    
    def test_dot_notation_access_with_profiles(self):
        """Test dot notation access with profile-based configuration."""
        # Create test profile
        test_config = {
            'database': {
                'host': 'localhost',
                'port': 5432,
                'credentials': {
                    'username': 'admin',
                    'password': 'secret'
                }
            },
            'cache': {
                'ttl': 3600,
                'max_size': 1000
            }
        }
        
        config = DynamicConfig(test_config)
        
        # Test nested dot notation
        assert config.database.host == 'localhost'
        assert config.database.port == 5432
        assert config.database.credentials.username == 'admin'
        assert config.cache.ttl == 3600
    
    def test_profile_file_path_tracking(self):
        """Test that Settings tracks the file paths for each profile."""
        # Create test profiles
        self._create_test_profile_file('test1', {'key': 'value1'})
        self._create_test_profile_file('test2', {'key': 'value2'})
        
        # Mock resources directory
        original_get_resources = Settings._get_resources_directory
        Settings._get_resources_directory = lambda self: Path(self.temp_resources_dir)
        
        try:
            Settings.reset()
            settings = Settings.instance()
            
            # Test file path tracking
            test1_path = settings.get_profile_file_path('test1')
            test2_path = settings.get_profile_file_path('test2')
            
            assert test1_path is not None
            assert test2_path is not None
            assert 'application-test1.yaml' in test1_path
            assert 'application-test2.yaml' in test2_path
            
        finally:
            Settings._get_resources_directory = original_get_resources
    
    def test_profile_reload_functionality(self):
        """Test reloading specific profiles."""
        # Create initial profile
        initial_config = {'version': '1.0.0', 'debug': False}
        profile_file = self._create_test_profile_file('testapp', initial_config)
        
        # Mock resources directory
        original_get_resources = Settings._get_resources_directory
        Settings._get_resources_directory = lambda self: Path(self.temp_resources_dir)
        
        try:
            Settings.reset()
            settings = Settings.instance()
            
            # Verify initial values
            assert settings.testapp.version == '1.0.0'
            assert settings.testapp.debug is False
            
            # Update the file
            updated_config = {'version': '2.0.0', 'debug': True, 'new_feature': 'enabled'}
            with open(profile_file, 'w') as f:
                yaml.dump(updated_config, f)
            
            # Reload the specific profile
            settings.reload_profile('testapp')
            
            # Verify updated values
            assert settings.testapp.version == '2.0.0'
            assert settings.testapp.debug is True
            assert settings.testapp.new_feature == 'enabled'
            
        finally:
            Settings._get_resources_directory = original_get_resources
    
    def test_yaml_loader_profile_integration(self):
        """Test YamlLoader integration with profile-based system."""
        # Test loading multiple profile files
        llm_file = self._create_test_profile_file('llm', {
            'provider': 'anthropic',
            'model': 'claude-3'
        })
        
        db_file = self._create_test_profile_file('db', {
            'provider': 'postgresql',
            'host': 'localhost'
        })
        
        # Test loading individual files
        llm_data = YamlLoader.load_file(llm_file)
        db_data = YamlLoader.load_file(db_file)
        
        assert llm_data['provider'] == 'anthropic'
        assert db_data['provider'] == 'postgresql'
        
        # Test merging multiple files
        merged_data = YamlLoader.load_multiple_files(llm_file, db_file, merge=True)
        
        assert 'provider' in merged_data  # Should have the last provider (from db_file)
        assert merged_data['provider'] == 'postgresql'
    
    def test_dynamic_config_with_profiles(self):
        """Test DynamicConfig behavior with profile-like data."""
        profile_data = {
            'api': {
                'version': 'v1',
                'endpoints': {
                    'users': '/api/v1/users',
                    'orders': '/api/v1/orders'
                }
            },
            'features': {
                'user_management': True,
                'analytics': False
            }
        }
        
        config = DynamicConfig(profile_data)
        
        # Test nested access
        assert config.api.version == 'v1'
        assert config.api.endpoints.users == '/api/v1/users'
        assert config.features.user_management is True
        assert config.features.analytics is False
        
        # Test get method
        assert config.get('api.version') == 'v1'
        assert config.get('features.user_management') is True
        assert config.get('nonexistent.key', 'default') == 'default'
    
    def test_settings_section_management(self):
        """Test Settings section management methods."""
        # Create test profiles
        self._create_test_profile_file('auth', {'provider': 'oauth2'})
        self._create_test_profile_file('storage', {'provider': 's3'})
        
        # Mock resources directory
        original_get_resources = Settings._get_resources_directory
        Settings._get_resources_directory = lambda self: Path(self.temp_resources_dir)
        
        try:
            Settings.reset()
            settings = Settings.instance()
            
            # Test section methods
            sections = settings.list_sections()
            assert 'auth' in sections
            assert 'storage' in sections
            
            assert settings.has_section('auth') is True
            assert settings.has_section('storage') is True
            assert settings.has_section('nonexistent') is False
            
            # Test get_section
            auth_section = settings.get_section('auth')
            assert auth_section is not None
            assert auth_section.provider == 'oauth2'
            
        finally:
            Settings._get_resources_directory = original_get_resources
    
    def test_settings_get_value_method(self):
        """Test Settings get_value method with profile paths."""
        # Create test profile
        self._create_test_profile_file('config', {
            'server': {
                'host': 'localhost',
                'port': 8080,
                'ssl': {
                    'enabled': True,
                    'cert_path': '/etc/ssl/cert.pem'
                }
            }
        })
        
        # Mock resources directory
        original_get_resources = Settings._get_resources_directory
        Settings._get_resources_directory = lambda self: Path(self.temp_resources_dir)
        
        try:
            Settings.reset()
            settings = Settings.instance()
            
            # Test get_value method
            assert settings.get_value('config.server.host') == 'localhost'
            assert settings.get_value('config.server.port') == 8080
            assert settings.get_value('config.server.ssl.enabled') is True
            assert settings.get_value('config.nonexistent.key', 'default') == 'default'
            
        finally:
            Settings._get_resources_directory = original_get_resources
    
    def test_integration_with_existing_config_system(self):
        """Test integration with existing configuration system."""
        # Import existing config components
        from app.core.config import config, app_config, database_config, vector_config
        
        # Test existing system still works
        assert config is not None
        assert hasattr(config, 'app')
        assert hasattr(config, 'database')
        assert hasattr(config, 'vector')
        
        # Test new Settings system is available
        settings = Settings.instance()
        assert settings is not None
        assert hasattr(settings, 'list_sections')
        assert hasattr(settings, 'get_value')
        assert hasattr(settings, 'get_profile_names')
        
        # Test both systems coexist
        assert config.app == app_config
        assert config.database == database_config
        assert config.vector == vector_config
    
    def test_real_profile_files_loading(self):
        """Test loading actual profile files if they exist."""
        # Test that real profile files can be loaded
        settings = Settings.instance()
        
        profiles = settings.get_profile_names()
        sections = settings.list_sections()
        
        # Verify basic functionality works
        assert isinstance(profiles, list)
        assert isinstance(sections, list)
        
        # If we have profiles, test basic access
        if profiles:
            print(f"Found profiles: {profiles}")
            
            # Test that each profile creates a corresponding section
            for profile in profiles:
                # Profile names get sanitized, so check sections
                if profile.replace('-', '_') in sections:
                    section = settings.get_section(profile)
                    assert section is not None
    
    def test_error_handling_and_recovery(self):
        """Test error handling in Settings system."""
        # Test with non-existent resources directory
        original_get_resources = Settings._get_resources_directory
        Settings._get_resources_directory = lambda self: Path("/nonexistent/path")
        
        try:
            Settings.reset()
            settings = Settings.instance()
            
            # Should not crash, should initialize with empty profiles
            profiles = settings.get_profile_names()
            assert isinstance(profiles, list)
            
        finally:
            Settings._get_resources_directory = original_get_resources
        
        # Test with malformed YAML in profile
        malformed_profile = self._create_test_profile_file('malformed', {})
        with open(malformed_profile, 'w') as f:
            f.write("invalid: yaml: content: {\n")
        
        # Should handle malformed YAML gracefully
        Settings._get_resources_directory = lambda self: Path(self.temp_resources_dir)
        
        try:
            Settings.reset()
            settings = Settings.instance()
            
            # Should not crash
            profiles = settings.get_profile_names()
            assert isinstance(profiles, list)
            
        finally:
            Settings._get_resources_directory = original_get_resources

    def test_nested_workflow_configurations(self):
        """Test nested workflow configuration loading and access patterns."""
        # Create workflows subdirectory
        workflows_dir = os.path.join(self.temp_resources_dir, "workflows")
        os.makedirs(workflows_dir, exist_ok=True)
        
        # Create workflow configuration files
        signup_config = {
            "signup": {
                "name": "User Signup Workflow",
                "agent": {
                    "type": "langgraph",
                    "implementation": "LangGraphReactAgent",
                    "capabilities": ["user_registration", "email_verification"]
                },
                "steps": {
                    "email_validation": {"enabled": True, "timeout_seconds": 300},
                    "profile_creation": {"enabled": True, "required_fields": ["email", "name"]}
                }
            }
        }
        
        approval_config = {
            "approval": {
                "name": "Document Approval Workflow", 
                "agent": {
                    "type": "langchain",
                    "implementation": "LangChainReactAgent"
                },
                "stages": {
                    "initial_review": {"required_reviewers": 1, "timeout_hours": 48},
                    "manager_approval": {"required_reviewers": 1, "escalation_hours": 72}
                }
            }
        }
        
        # Write workflow files
        signup_file = os.path.join(workflows_dir, "application-signup.yaml")
        approval_file = os.path.join(workflows_dir, "application-approval.yaml")
        
        with open(signup_file, 'w') as f:
            yaml.dump(signup_config, f)
        with open(approval_file, 'w') as f:
            yaml.dump(approval_config, f)
        
        # Mock the resources directory to point to our temp directory
        original_get_resources = Settings._get_resources_directory
        Settings._get_resources_directory = lambda self: self.temp_resources_dir
        
        try:
            # Initialize settings - should discover nested workflows
            settings = Settings()
            
            # Verify nested workflow namespace was created
            assert hasattr(settings, 'workflows'), "Nested 'workflows' attribute should be created"
            
            # Test access patterns: settings.workflows.signup.*
            workflows = settings.workflows
            assert hasattr(workflows, 'signup'), "Should have 'signup' workflow config"
            assert hasattr(workflows, 'approval'), "Should have 'approval' workflow config"
            
            # Test nested access: settings.workflows.signup.agent.type
            signup_workflow = workflows.signup
            assert signup_workflow.signup.name == "User Signup Workflow"
            assert signup_workflow.signup.agent.type == "langgraph"
            assert signup_workflow.signup.agent.implementation == "LangGraphReactAgent"
            
            # Test nested access: settings.workflows.approval.stages
            approval_workflow = workflows.approval  
            assert approval_workflow.approval.name == "Document Approval Workflow"
            assert approval_workflow.approval.agent.type == "langchain"
            assert approval_workflow.approval.stages.initial_review.timeout_hours == 48
            
            # Test list access to capabilities
            capabilities = signup_workflow.signup.agent.capabilities
            assert "user_registration" in capabilities
            assert "email_verification" in capabilities
            
        finally:
            Settings._get_resources_directory = original_get_resources

    def test_mixed_flat_and_nested_configurations(self):
        """Test that flat and nested configurations coexist properly."""
        # Create flat configuration (existing pattern)
        db_config = {
            "database": {
                "host": "localhost",
                "port": 5432,
                "name": "test_db"
            }
        }
        self._create_test_profile_file("db", db_config)
        
        # Create nested configurations
        workflows_dir = os.path.join(self.temp_resources_dir, "workflows")
        os.makedirs(workflows_dir, exist_ok=True)
        
        signup_config = {
            "signup": {
                "enabled": True,
                "timeout": 300
            }
        }
        
        signup_file = os.path.join(workflows_dir, "application-signup.yaml")
        with open(signup_file, 'w') as f:
            yaml.dump(signup_config, f)
        
        # Mock the resources directory
        original_get_resources = Settings._get_resources_directory
        Settings._get_resources_directory = lambda self: self.temp_resources_dir
        
        try:
            settings = Settings()
            
            # Verify flat configuration still works
            assert hasattr(settings, 'db'), "Flat configuration should still work"
            assert settings.db.database.host == "localhost"
            assert settings.db.database.port == 5432
            
            # Verify nested configuration works
            assert hasattr(settings, 'workflows'), "Nested configuration should work"
            assert settings.workflows.signup.signup.enabled is True
            assert settings.workflows.signup.signup.timeout == 300
            
            # Verify both configurations are in profile list
            profiles = settings.get_profile_names()
            assert 'db' in profiles
            assert 'workflows' in profiles
            
        finally:
            Settings._get_resources_directory = original_get_resources
            
    def test_nested_configuration_error_handling(self):
        """Test error handling for malformed nested configurations."""
        # Create workflows subdirectory
        workflows_dir = os.path.join(self.temp_resources_dir, "workflows")
        os.makedirs(workflows_dir, exist_ok=True)
        
        # Create malformed YAML file
        malformed_file = os.path.join(workflows_dir, "application-malformed.yaml")
        with open(malformed_file, 'w') as f:
            f.write("invalid: yaml: content: [\n")  # Malformed YAML
        
        # Create valid workflow config as well
        valid_config = {"test": {"name": "Valid Workflow"}}
        valid_file = os.path.join(workflows_dir, "application-valid.yaml")
        with open(valid_file, 'w') as f:
            yaml.dump(valid_config, f)
        
        # Mock the resources directory
        original_get_resources = Settings._get_resources_directory
        Settings._get_resources_directory = lambda self: self.temp_resources_dir
        
        try:
            # Should handle errors gracefully and still load valid configs
            settings = Settings()
            
            # Should have workflows namespace but only valid config
            if hasattr(settings, 'workflows'):
                assert hasattr(settings.workflows, 'valid'), "Should load valid config"
                assert settings.workflows.valid.test.name == "Valid Workflow"
                
                # Malformed config should not be present
                assert not hasattr(settings.workflows, 'malformed'), "Malformed config should not load"
            
        finally:
            Settings._get_resources_directory = original_get_resources
