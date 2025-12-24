"""
Test suite for EnvironmentManager utility.

Tests environment variable access, type conversion, validation,
caching, and .env file loading functionality.
"""
import os
import pytest
from unittest.mock import patch, MagicMock
from pathlib import Path
from tempfile import TemporaryDirectory

from app.core.utils.env_utils import EnvironmentManager


class TestEnvironmentManagerInitialization:
    """Test EnvironmentManager initialization."""
    
    def test_default_initialization(self):
        """Test default initialization."""
        manager = EnvironmentManager()
        assert manager._load_dotenv is True
        assert isinstance(manager._cache, dict)
    
    def test_initialization_without_dotenv(self):
        """Test initialization without dotenv loading."""
        manager = EnvironmentManager(load_dotenv=False)
        assert manager._load_dotenv is False
        assert isinstance(manager._cache, dict)
    
    @patch('app.core.utils.env_utils.EnvironmentManager._load_env_file')
    def test_initialization_calls_load_env_file(self, mock_load_env):
        """Test that initialization calls _load_env_file when load_dotenv is True."""
        EnvironmentManager(load_dotenv=True)
        mock_load_env.assert_called_once()
    
    @patch('app.core.utils.env_utils.EnvironmentManager._load_env_file')
    def test_initialization_skips_load_env_file(self, mock_load_env):
        """Test that initialization skips _load_env_file when load_dotenv is False."""
        EnvironmentManager(load_dotenv=False)
        mock_load_env.assert_not_called()


class TestEnvironmentVariableAccess:
    """Test environment variable access methods."""
    
    def setup_method(self):
        """Set up test environment."""
        self.manager = EnvironmentManager(load_dotenv=False)
        self.manager.clear_cache()
    
    def test_get_existing_variable(self):
        """Test getting existing environment variable."""
        with patch.dict(os.environ, {'TEST_VAR': 'test_value'}):
            result = self.manager.get('TEST_VAR')
            assert result == 'test_value'
    
    def test_get_non_existing_variable_with_default(self):
        """Test getting non-existing variable with default."""
        result = self.manager.get('NON_EXISTENT_VAR', default='default_value')
        assert result == 'default_value'
    
    def test_get_non_existing_variable_without_default(self):
        """Test getting non-existing variable without default."""
        result = self.manager.get('NON_EXISTENT_VAR')
        assert result is None
    
    def test_get_required_existing_variable(self):
        """Test getting required existing variable."""
        with patch.dict(os.environ, {'TEST_VAR': 'test_value'}):
            result = self.manager.get('TEST_VAR', required=True)
            assert result == 'test_value'
    
    def test_get_required_non_existing_variable(self):
        """Test getting required non-existing variable raises ValueError."""
        with pytest.raises(ValueError, match="Required environment variable 'NON_EXISTENT_VAR' is not set"):
            self.manager.get('NON_EXISTENT_VAR', required=True)
    
    def test_get_with_type_conversion(self):
        """Test getting variable with type conversion."""
        with patch.dict(os.environ, {'INT_VAR': '42'}):
            # When var_type=int is provided, it should use int conversion
            result = self.manager.get('INT_VAR', var_type=int)
            assert result == 42
            assert isinstance(result, int)


class TestTypeConversionMethods:
    """Test type-specific environment variable methods."""
    
    def setup_method(self):
        """Set up test environment."""
        self.manager = EnvironmentManager(load_dotenv=False)
        self.manager.clear_cache()
    
    def test_get_string(self):
        """Test get_string method."""
        with patch.dict(os.environ, {'STRING_VAR': 'test_string'}):
            result = self.manager.get_string('STRING_VAR')
            assert result == 'test_string'
            assert isinstance(result, str)
    
    def test_get_string_with_default(self):
        """Test get_string with default value."""
        result = self.manager.get_string('NON_EXISTENT_VAR', default='default')
        assert result == 'default'
    
    def test_get_string_empty_returns_empty(self):
        """Test get_string returns empty string for missing variables."""
        result = self.manager.get_string('NON_EXISTENT_VAR')
        assert result == ''
    
    def test_get_int(self):
        """Test get_int method."""
        with patch.dict(os.environ, {'INT_VAR': '123'}):
            result = self.manager.get_int('INT_VAR')
            assert result == 123
            assert isinstance(result, int)
    
    def test_get_int_with_default(self):
        """Test get_int with default value."""
        result = self.manager.get_int('NON_EXISTENT_VAR', default=456)
        assert result == 456
    
    def test_get_int_missing_returns_zero(self):
        """Test get_int returns zero for missing variables."""
        result = self.manager.get_int('NON_EXISTENT_VAR')
        assert result == 0
    
    def test_get_float(self):
        """Test get_float method."""
        with patch.dict(os.environ, {'FLOAT_VAR': '3.14'}):
            result = self.manager.get_float('FLOAT_VAR')
            assert result == 3.14
            assert isinstance(result, float)
    
    def test_get_float_with_default(self):
        """Test get_float with default value."""
        result = self.manager.get_float('NON_EXISTENT_VAR', default=2.71)
        assert result == 2.71
    
    def test_get_float_missing_returns_zero(self):
        """Test get_float returns zero for missing variables."""
        result = self.manager.get_float('NON_EXISTENT_VAR')
        assert result == 0.0
    
    def test_get_bool_true_values(self):
        """Test get_bool with various true values."""
        true_values = ['true', 'True', 'TRUE', '1', 'yes', 'Yes', 'on', 'enabled']
        
        for value in true_values:
            with patch.dict(os.environ, {'BOOL_VAR': value}):
                result = self.manager.get_bool('BOOL_VAR')
                assert result is True, f"Failed for value: {value}"
    
    def test_get_bool_false_values(self):
        """Test get_bool with various false values."""
        false_values = ['false', 'False', 'FALSE', '0', 'no', 'No', 'off', 'disabled', '']
        
        for value in false_values:
            with patch.dict(os.environ, {'BOOL_VAR': value}):
                result = self.manager.get_bool('BOOL_VAR')
                assert result is False, f"Failed for value: {value}"
    
    def test_get_bool_with_default(self):
        """Test get_bool with default value."""
        result = self.manager.get_bool('NON_EXISTENT_VAR', default=True)
        assert result is True
    
    def test_get_bool_missing_returns_false(self):
        """Test get_bool returns False for missing variables."""
        result = self.manager.get_bool('NON_EXISTENT_VAR')
        assert result is False
    
    def test_get_list_default_separator(self):
        """Test get_list with default comma separator."""
        with patch.dict(os.environ, {'LIST_VAR': 'a,b,c,d'}):
            result = self.manager.get_list('LIST_VAR')
            assert result == ['a', 'b', 'c', 'd']
    
    def test_get_list_custom_separator(self):
        """Test get_list with custom separator."""
        with patch.dict(os.environ, {'LIST_VAR': 'a;b;c;d'}):
            result = self.manager.get_list('LIST_VAR', separator=';')
            assert result == ['a', 'b', 'c', 'd']
    
    def test_get_list_with_spaces(self):
        """Test get_list strips whitespace."""
        with patch.dict(os.environ, {'LIST_VAR': ' a , b , c , d '}):
            result = self.manager.get_list('LIST_VAR')
            assert result == ['a', 'b', 'c', 'd']
    
    def test_get_list_with_default(self):
        """Test get_list with default value."""
        result = self.manager.get_list('NON_EXISTENT_VAR', default=['x', 'y'])
        assert result == ['x', 'y']
    
    def test_get_list_missing_returns_empty(self):
        """Test get_list returns empty list for missing variables."""
        result = self.manager.get_list('NON_EXISTENT_VAR')
        assert result == []
    
    def test_get_list_empty_string_returns_empty(self):
        """Test get_list returns empty list for empty string."""
        with patch.dict(os.environ, {'LIST_VAR': ''}):
            result = self.manager.get_list('LIST_VAR')
            assert result == []


class TestValueConversion:
    """Test _convert_value method."""
    
    def setup_method(self):
        """Set up test environment."""
        self.manager = EnvironmentManager(load_dotenv=False)
    
    def test_convert_to_string(self):
        """Test conversion to string."""
        result = self.manager._convert_value('test', str)
        assert result == 'test'
        assert isinstance(result, str)
    
    def test_convert_to_int_success(self):
        """Test successful conversion to int."""
        result = self.manager._convert_value('123', int)
        assert result == 123
        assert isinstance(result, int)
    
    def test_convert_to_int_failure(self):
        """Test failed conversion to int."""
        with pytest.raises(ValueError, match="Cannot convert 'not_a_number' to integer"):
            self.manager._convert_value('not_a_number', int)
    
    def test_convert_to_float_success(self):
        """Test successful conversion to float."""
        result = self.manager._convert_value('3.14', float)
        assert result == 3.14
        assert isinstance(result, float)
    
    def test_convert_to_float_failure(self):
        """Test failed conversion to float."""
        with pytest.raises(ValueError, match="Cannot convert 'not_a_number' to float"):
            self.manager._convert_value('not_a_number', float)
    
    def test_convert_to_bool_success(self):
        """Test successful conversion to bool."""
        result = self.manager._convert_value('true', bool)
        assert result is True
    
    def test_convert_to_list(self):
        """Test conversion to list."""
        result = self.manager._convert_value('a,b,c', list)
        assert result == ['a', 'b', 'c']


class TestBooleanParsing:
    """Test _parse_bool method."""
    
    def setup_method(self):
        """Set up test environment."""
        self.manager = EnvironmentManager(load_dotenv=False)
    
    def test_parse_bool_true_values(self):
        """Test parsing true values."""
        true_values = ['true', 'True', 'TRUE', '1', 'yes', 'on', 'enabled']
        
        for value in true_values:
            result = self.manager._parse_bool(value)
            assert result is True, f"Failed for value: {value}"
    
    def test_parse_bool_false_values(self):
        """Test parsing false values."""
        false_values = ['false', 'False', 'FALSE', '0', 'no', 'off', 'disabled', '']
        
        for value in false_values:
            result = self.manager._parse_bool(value)
            assert result is False, f"Failed for value: {value}"
    
    def test_parse_bool_with_whitespace(self):
        """Test parsing bool values with whitespace."""
        assert self.manager._parse_bool('  true  ') is True
        assert self.manager._parse_bool('  false  ') is False
    
    def test_parse_bool_invalid_value(self):
        """Test parsing invalid bool value raises ValueError."""
        with pytest.raises(ValueError, match="Cannot convert 'maybe' to boolean"):
            self.manager._parse_bool('maybe')


class TestCaching:
    """Test caching functionality."""
    
    def setup_method(self):
        """Set up test environment."""
        self.manager = EnvironmentManager(load_dotenv=False)
        self.manager.clear_cache()
    
    def test_caching_behavior(self):
        """Test that values are cached."""
        with patch.dict(os.environ, {'CACHE_VAR': 'cached_value'}):
            # First call
            result1 = self.manager.get('CACHE_VAR', var_type=str)
            assert result1 == 'cached_value'
            
            # Check cache
            cache_key = 'CACHE_VAR:str'
            assert cache_key in self.manager._cache
            assert self.manager._cache[cache_key] == 'cached_value'
            
            # Second call should use cache
            result2 = self.manager.get('CACHE_VAR', var_type=str)
            assert result2 == 'cached_value'
    
    def test_cache_key_includes_type(self):
        """Test that cache key includes type information."""
        with patch.dict(os.environ, {'TYPE_VAR': '42'}):
            # Get as string (using default values to force type)
            result_str = self.manager.get('TYPE_VAR', default="", var_type=str)
            assert result_str == '42'
            
            # Get as int (using default values to force type)
            result_int = self.manager.get('TYPE_VAR', default=0, var_type=int)
            assert result_int == 42
            
            # Check both are cached separately
            assert 'TYPE_VAR:str' in self.manager._cache
            assert 'TYPE_VAR:int' in self.manager._cache
            assert self.manager._cache['TYPE_VAR:str'] == '42'
            assert self.manager._cache['TYPE_VAR:int'] == 42
    
    def test_clear_cache(self):
        """Test clearing cache."""
        with patch.dict(os.environ, {'CACHE_VAR': 'value'}):
            self.manager.get('CACHE_VAR')
            assert len(self.manager._cache) > 0
            
            self.manager.clear_cache()
            assert len(self.manager._cache) == 0


class TestUtilityMethods:
    """Test utility methods."""
    
    def setup_method(self):
        """Set up test environment."""
        self.manager = EnvironmentManager(load_dotenv=False)
    
    def test_has_existing_variable(self):
        """Test has method with existing variable."""
        with patch.dict(os.environ, {'EXISTS_VAR': 'value'}):
            assert self.manager.has('EXISTS_VAR') is True
    
    def test_has_non_existing_variable(self):
        """Test has method with non-existing variable."""
        assert self.manager.has('NON_EXISTENT_VAR') is False
    
    def test_list_variables_all(self):
        """Test listing all variables."""
        with patch.dict(os.environ, {'TEST_VAR1': 'value1', 'TEST_VAR2': 'value2'}, clear=True):
            variables = self.manager.list_variables()
            assert variables == {'TEST_VAR1': 'value1', 'TEST_VAR2': 'value2'}
    
    def test_list_variables_with_prefix(self):
        """Test listing variables with prefix."""
        env_vars = {
            'APP_DEBUG': 'true',
            'APP_PORT': '8000',
            'DB_HOST': 'localhost',
            'OTHER_VAR': 'value'
        }
        
        with patch.dict(os.environ, env_vars, clear=True):
            app_vars = self.manager.list_variables(prefix='APP_')
            assert app_vars == {'APP_DEBUG': 'true', 'APP_PORT': '8000'}
    
    @patch('app.core.utils.env_utils.EnvironmentManager._load_env_file')
    def test_reload_env(self, mock_load_env):
        """Test reload_env method."""
        # Set up manager with dotenv enabled
        manager = EnvironmentManager(load_dotenv=True)
        mock_load_env.reset_mock()  # Reset after initialization
        
        # Add something to cache
        manager._cache['test'] = 'value'
        
        # Reload
        manager.reload_env()
        
        # Check cache was cleared and _load_env_file was called
        assert len(manager._cache) == 0
        mock_load_env.assert_called_once()
    
    def test_reload_env_without_dotenv(self):
        """Test reload_env method when dotenv is disabled."""
        manager = EnvironmentManager(load_dotenv=False)
        
        # Add something to cache
        manager._cache['test'] = 'value'
        
        # Reload
        manager.reload_env()
        
        # Check cache was cleared
        assert len(manager._cache) == 0


class TestDotenvLoading:
    """Test .env file loading functionality."""
    
    @patch('app.core.utils.env_utils.EnvironmentManager._find_env_file')
    def test_load_env_file_not_found(self, mock_find_env):
        """Test _load_env_file when .env file is not found."""
        mock_find_env.return_value = None
        
        manager = EnvironmentManager(load_dotenv=False)
        # Should not raise an error
        manager._load_env_file()
        
        mock_find_env.assert_called_once()
    
    def test_load_env_file_import_error(self):
        """Test _load_env_file when python-dotenv is not available."""
        manager = EnvironmentManager(load_dotenv=False)
        
        # Mock the import failure
        original_import = __builtins__['__import__']
        
        def mock_import(name, *args, **kwargs):
            if name == 'dotenv':
                raise ImportError("No module named 'dotenv'")
            return original_import(name, *args, **kwargs)
        
        with patch('builtins.__import__', side_effect=mock_import):
            # Should not raise an error, just log a warning
            manager._load_env_file()
    
    def test_load_env_file_general_error(self):
        """Test _load_env_file with general error."""
        manager = EnvironmentManager(load_dotenv=False)
        
        # Mock _find_env_file to return an env file
        with patch.object(manager, '_find_env_file', return_value=Path('.env')):
            # Mock the import to succeed but load_dotenv to fail
            original_import = __builtins__['__import__']
            
            def mock_import(name, *args, **kwargs):
                if name == 'dotenv':
                    mock_module = MagicMock()
                    mock_module.load_dotenv = MagicMock(side_effect=Exception('Test error'))
                    return mock_module
                return original_import(name, *args, **kwargs)
            
            with patch('builtins.__import__', side_effect=mock_import):
                # Should not raise an error, just log a warning
                manager._load_env_file()
    
    def test_find_env_file_current_directory(self):
        """Test _find_env_file finds .env in current directory."""
        manager = EnvironmentManager(load_dotenv=False)
        
        with TemporaryDirectory() as temp_dir:
            env_file = Path(temp_dir) / '.env'
            env_file.touch()
            
            with patch('pathlib.Path.cwd', return_value=Path(temp_dir)):
                result = manager._find_env_file()
                assert result == env_file
    
    def test_find_env_file_parent_directory(self):
        """Test _find_env_file finds .env in parent directory."""
        manager = EnvironmentManager(load_dotenv=False)
        
        with TemporaryDirectory() as temp_dir:
            parent_dir = Path(temp_dir)
            child_dir = parent_dir / 'child'
            child_dir.mkdir()
            
            env_file = parent_dir / '.env'
            env_file.touch()
            
            with patch('pathlib.Path.cwd', return_value=child_dir):
                result = manager._find_env_file()
                assert result == env_file
    
    def test_find_env_file_not_found(self):
        """Test _find_env_file returns None when .env not found."""
        manager = EnvironmentManager(load_dotenv=False)
        
        with TemporaryDirectory() as temp_dir:
            with patch('pathlib.Path.cwd', return_value=Path(temp_dir)):
                result = manager._find_env_file()
                assert result is None


class TestGlobalInstance:
    """Test global env instance."""
    
    def test_global_env_instance_exists(self):
        """Test that global env instance exists and is EnvironmentManager."""
        from app.core.utils.env_utils import env
        assert isinstance(env, EnvironmentManager)
    
    def test_global_env_instance_has_dotenv_enabled(self):
        """Test that global env instance has dotenv loading enabled."""
        from app.core.utils.env_utils import env
        assert env._load_dotenv is True
