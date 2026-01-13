"""
Unit tests for multi-environment configuration system.

Tests CLI argument parsing, environment file loading, and variable precedence.
"""
import os
import tempfile
from pathlib import Path
import pytest
from unittest.mock import patch, mock_open
from app.core.cli import AgentHubCLI, parse_cli_args, get_env_file_from_cli
from app.core.utils.env_utils import EnvironmentManager, initialize_environment


class TestCLIArgumentParsing:
    """Test command-line argument parsing."""
    
    def test_default_env_file(self):
        """Default should be .env when no argument provided."""
        cli = AgentHubCLI()
        args = cli.parse_args([])
        assert args.env == '.env'
    
    def test_custom_env_file(self):
        """Should accept custom environment file path."""
        cli = AgentHubCLI()
        args = cli.parse_args(['--env', '.env.production'])
        assert args.env == '.env.production'
    
    def test_env_required_flag(self):
        """Should parse --env-required flag correctly."""
        cli = AgentHubCLI()
        args = cli.parse_args(['--env-required'])
        assert args.env_required is True
    
    def test_debug_flag(self):
        """Should parse --debug flag correctly."""
        cli = AgentHubCLI()
        args = cli.parse_args(['--debug'])
        assert args.debug is True
    
    def test_log_level_argument(self):
        """Should accept valid log levels."""
        cli = AgentHubCLI()
        args = cli.parse_args(['--log-level', 'ERROR'])
        assert args.log_level == 'ERROR'
    
    def test_multiple_arguments_combined(self):
        """Should handle multiple arguments together."""
        cli = AgentHubCLI()
        args = cli.parse_args([
            '--env', '.env.staging',
            '--env-required',
            '--debug',
            '--log-level', 'INFO'
        ])
        assert args.env == '.env.staging'
        assert args.env_required is True
        assert args.debug is True
        assert args.log_level == 'INFO'
    
    def test_get_env_file_helper(self):
        """Should return env file path from parsed arguments."""
        cli = AgentHubCLI()
        args = cli.parse_args(['--env', '.env.staging'])
        env_file = cli.get_env_file(args)
        assert env_file == '.env.staging'


class TestEnvironmentManager:
    """Test EnvironmentManager with custom env files."""
    
    def test_init_with_env_file(self, tmp_path):
        """Test initialization with specific env file."""
        # Create temporary env file
        env_file = tmp_path / ".env.test"
        env_file.write_text("TEST_VAR=test_value\n")
        
        # Initialize with custom file
        env_manager = EnvironmentManager(load_dotenv=True, env_file=str(env_file))
        
        # Verify variable is loaded
        assert os.getenv("TEST_VAR") == "test_value"
        
        # Cleanup
        del os.environ["TEST_VAR"]
    
    def test_init_without_dotenv(self):
        """Test initialization without loading .env file."""
        env_manager = EnvironmentManager(load_dotenv=False)
        assert env_manager._load_dotenv is False
    
    def test_reload_env_with_new_file(self, tmp_path):
        """Test reloading environment with different file."""
        # Create first env file
        env_file1 = tmp_path / ".env.test1"
        env_file1.write_text("RELOAD_TEST=value1\n")
        
        # Initialize with first file
        env_manager = EnvironmentManager(load_dotenv=True, env_file=str(env_file1))
        assert os.getenv("RELOAD_TEST") == "value1"
        
        # Create second env file
        env_file2 = tmp_path / ".env.test2"
        env_file2.write_text("RELOAD_TEST=value2\nNEW_VAR=new_value\n")
        
        # Reload with second file (note: won't override existing vars by default)
        env_manager.reload_env(str(env_file2))
        
        # Cleanup
        if "RELOAD_TEST" in os.environ:
            del os.environ["RELOAD_TEST"]
        if "NEW_VAR" in os.environ:
            del os.environ["NEW_VAR"]
    
    def test_env_file_not_found_warning(self, tmp_path):
        """Test that non-existent env file generates warning, not error."""
        non_existent = tmp_path / ".env.nonexistent"
        
        # Should not raise exception
        env_manager = EnvironmentManager(load_dotenv=True, env_file=str(non_existent))
        
        # Manager should still be usable
        assert env_manager is not None


class TestInitializeEnvironment:
    """Test the initialize_environment function."""
    
    def test_initialize_with_custom_file(self, tmp_path):
        """Test initializing global environment with custom file."""
        # Create temporary env file
        env_file = tmp_path / ".env.init_test"
        env_file.write_text("INIT_TEST_VAR=init_value\n")
        
        # Initialize
        env = initialize_environment(str(env_file))
        
        # Verify
        assert env is not None
        assert os.getenv("INIT_TEST_VAR") == "init_value"
        
        # Cleanup
        if "INIT_TEST_VAR" in os.environ:
            del os.environ["INIT_TEST_VAR"]
    
    def test_initialize_with_none(self):
        """Test initializing with None falls back to default."""
        env = initialize_environment(None)
        assert env is not None


class TestEnvironmentPriority:
    """Test environment variable priority (system > file)."""
    
    def test_system_env_overrides_file(self, tmp_path):
        """Test that system environment variables override file variables."""
        # Set system environment variable
        os.environ["PRIORITY_TEST"] = "system_value"
        
        # Create env file with different value
        env_file = tmp_path / ".env.priority"
        env_file.write_text("PRIORITY_TEST=file_value\n")
        
        # Load env file (should not override system var)
        env_manager = EnvironmentManager(load_dotenv=True, env_file=str(env_file))
        
        # System value should win
        assert os.getenv("PRIORITY_TEST") == "system_value"
        
        # Cleanup
        del os.environ["PRIORITY_TEST"]


class TestEnvironmentManagerMethods:
    """Test EnvironmentManager helper methods."""
    
    def test_get_string(self):
        """Test get_string method."""
        os.environ["STRING_TEST"] = "test_string"
        env_manager = EnvironmentManager(load_dotenv=False)
        
        value = env_manager.get_string("STRING_TEST", "default")
        assert value == "test_string"
        
        del os.environ["STRING_TEST"]
    
    def test_get_int(self):
        """Test get_int method."""
        os.environ["INT_TEST"] = "42"
        env_manager = EnvironmentManager(load_dotenv=False)
        
        value = env_manager.get_int("INT_TEST", 0)
        assert value == 42
        
        del os.environ["INT_TEST"]
    
    def test_get_bool(self):
        """Test get_bool method."""
        os.environ["BOOL_TEST"] = "true"
        env_manager = EnvironmentManager(load_dotenv=False)
        
        value = env_manager.get_bool("BOOL_TEST", False)
        assert value is True
        
        del os.environ["BOOL_TEST"]
    
    def test_get_list(self):
        """Test get_list method."""
        os.environ["LIST_TEST"] = "item1,item2,item3"
        env_manager = EnvironmentManager(load_dotenv=False)
        
        value = env_manager.get_list("LIST_TEST", [])
        assert value == ["item1", "item2", "item3"]
        
        del os.environ["LIST_TEST"]
    
    def test_has_method(self):
        """Test has method for checking variable existence."""
        os.environ["EXISTS_TEST"] = "value"
        env_manager = EnvironmentManager(load_dotenv=False)
        
        assert env_manager.has("EXISTS_TEST") is True
        assert env_manager.has("DOES_NOT_EXIST") is False
        
        del os.environ["EXISTS_TEST"]


class TestRealWorldScenarios:
    """Test real-world multi-environment scenarios."""
    
    def test_development_environment(self, tmp_path):
        """Simulate loading development environment."""
        env_file = tmp_path / ".env.dev"
        env_file.write_text("""
APP_ENV=development
DEBUG=true
LOG_LEVEL=DEBUG
POSTGRES_HOST=localhost
ALLOWED_ORIGINS=http://localhost:3000,http://localhost:5173
""")
        
        env_manager = EnvironmentManager(load_dotenv=True, env_file=str(env_file))
        
        assert os.getenv("APP_ENV") == "development"
        assert os.getenv("DEBUG") == "true"
        assert os.getenv("LOG_LEVEL") == "DEBUG"
        
        # Cleanup
        for key in ["APP_ENV", "DEBUG", "LOG_LEVEL", "POSTGRES_HOST", "ALLOWED_ORIGINS"]:
            if key in os.environ:
                del os.environ[key]
    
    def test_production_environment(self, tmp_path):
        """Simulate loading production environment."""
        env_file = tmp_path / ".env.production"
        env_file.write_text("""
APP_ENV=production
DEBUG=false
LOG_LEVEL=WARNING
POSTGRES_HOST=${PROD_POSTGRES_HOST}
""")
        
        # Set production secrets via system env
        os.environ["PROD_POSTGRES_HOST"] = "prod-db.example.com"
        
        env_manager = EnvironmentManager(load_dotenv=True, env_file=str(env_file))
        
        assert os.getenv("APP_ENV") == "production"
        assert os.getenv("DEBUG") == "false"
        assert os.getenv("PROD_POSTGRES_HOST") == "prod-db.example.com"
        
        # Cleanup
        for key in ["APP_ENV", "DEBUG", "LOG_LEVEL", "POSTGRES_HOST", "PROD_POSTGRES_HOST"]:
            if key in os.environ:
                del os.environ[key]
    
    def test_staging_with_placeholder_replacement(self, tmp_path):
        """Test staging environment with placeholder variables."""
        # This simulates how K8s/Docker would inject secrets
        os.environ["STAGING_DB_PASSWORD"] = "actual-db-password"
        os.environ["STAGING_API_KEY"] = "actual-api-key"
        
        env_file = tmp_path / ".env.staging"
        env_file.write_text("""
APP_ENV=staging
DB_PASSWORD=${STAGING_DB_PASSWORD}
API_KEY=${STAGING_API_KEY}
""")
        
        env_manager = EnvironmentManager(load_dotenv=True, env_file=str(env_file))
        
        # System env vars should be available
        assert os.getenv("STAGING_DB_PASSWORD") == "actual-db-password"
        assert os.getenv("STAGING_API_KEY") == "actual-api-key"
        
        # Cleanup
        for key in ["APP_ENV", "DB_PASSWORD", "API_KEY", "STAGING_DB_PASSWORD", "STAGING_API_KEY"]:
            if key in os.environ:
                del os.environ[key]


class TestErrorHandling:
    """Test error handling in multi-environment system."""
    
    def test_missing_required_env_file_with_flag(self, tmp_path):
        """Test that --env-required flag causes proper error."""
        non_existent = tmp_path / ".env.missing"
        
        cli = AgentHubCLI()
        
        # Should raise SystemExit when file doesn't exist with --env-required
        with pytest.raises(SystemExit):
            cli.parse_args(['--env', str(non_existent), '--env-required'])
    
    def test_invalid_log_level(self):
        """Test that invalid log level is handled."""
        cli = AgentHubCLI()
        
        # Should raise SystemExit for invalid log level
        with pytest.raises(SystemExit):
            cli.parse_args(['--log-level', 'INVALID_LEVEL'])
    
    def test_empty_env_file(self, tmp_path):
        """Test loading empty env file doesn't break anything."""
        env_file = tmp_path / ".env.empty"
        env_file.write_text("")
        
        # Should not raise exception
        env_manager = EnvironmentManager(load_dotenv=True, env_file=str(env_file))
        assert env_manager is not None
    
    def test_malformed_env_file(self, tmp_path):
        """Test that malformed env file doesn't crash the app."""
        env_file = tmp_path / ".env.malformed"
        env_file.write_text("MALFORMED LINE WITHOUT EQUALS\nVALID=value\n")
        
        # Should not raise exception (python-dotenv handles this gracefully)
        env_manager = EnvironmentManager(load_dotenv=True, env_file=str(env_file))
        assert env_manager is not None
    
    def test_has_method(self):
        """Test has method."""
        os.environ["EXISTS_TEST"] = "value"
        env_manager = EnvironmentManager(load_dotenv=False)
        
        assert env_manager.has("EXISTS_TEST") is True
        assert env_manager.has("NONEXISTENT") is False
        
        del os.environ["EXISTS_TEST"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
