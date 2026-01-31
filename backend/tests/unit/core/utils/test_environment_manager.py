"""
Comprehensive test suite for EnvironmentManager.
Tests environment variable access, type conversion, caching,
validation, and dotenv file loading functionality.
"""

import os
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock
from typing import List, Dict

import pytest

from app.core.utils.env_utils import EnvironmentManager


class TestEnvironmentManagerBasicFunctionality:
    """Test basic EnvironmentManager functionality."""
    
    def setup_method(self):
        """Setup for each test method."""
        # Clear any existing test environment variables
        test_vars = [key for key in os.environ.keys() if key.startswith('TEST_')]
        for var in test_vars:
            del os.environ[var]
    
    def teardown_method(self):
        """Cleanup after each test method."""
        # Clear any test environment variables
        test_vars = [key for key in os.environ.keys() if key.startswith('TEST_')]
        for var in test_vars:
            del os.environ[var]
    
    def test_basic_initialization(self):
        """Test basic EnvironmentManager initialization."""
        manager = EnvironmentManager(load_dotenv=False)
        
        assert manager._cache == {}
        assert not manager._load_dotenv
    
    def test_initialization_with_dotenv(self):
        """Test EnvironmentManager initialization with dotenv loading."""
        # Mock to avoid actual dotenv import issues in test environment
        with patch('app.core.utils.env_utils.EnvironmentManager._load_env_file') as mock_load:
            manager = EnvironmentManager(load_dotenv=True)
            
            assert manager._load_dotenv
            mock_load.assert_called_once()
    
    def test_get_existing_string_variable(self):
        """Test getting existing string environment variable."""
        os.environ['TEST_STRING'] = 'hello world'
        
        manager = EnvironmentManager(load_dotenv=False)
        result = manager.get('TEST_STRING')
        
        assert result == 'hello world'
        assert isinstance(result, str)
    
    def test_get_nonexistent_variable_with_default(self):
        """Test getting nonexistent variable with default value."""
        manager = EnvironmentManager(load_dotenv=False)
        result = manager.get('TEST_NONEXISTENT', default='default_value')
        
        assert result == 'default_value'
        assert isinstance(result, str)
    
    def test_get_nonexistent_variable_without_default(self):
        """Test getting nonexistent variable without default."""
        manager = EnvironmentManager(load_dotenv=False)
        result = manager.get('TEST_NONEXISTENT')
        
        assert result is None
    
    def test_get_required_variable_exists(self):
        """Test getting required variable that exists."""
        os.environ['TEST_REQUIRED'] = 'exists'
        
        manager = EnvironmentManager(load_dotenv=False)
        result = manager.get('TEST_REQUIRED', required=True)
        
        assert result == 'exists'
    
    def test_get_required_variable_missing(self):
        """Test getting required variable that doesn't exist."""
        manager = EnvironmentManager(load_dotenv=False)
        
        with pytest.raises(ValueError, match="Required environment variable 'TEST_MISSING' is not set"):
            manager.get('TEST_MISSING', required=True)


class TestEnvironmentManagerTypeConversion:
    """Test EnvironmentManager type conversion functionality."""
    
    def setup_method(self):
        """Setup for each test method."""
        # Clear any existing test environment variables
        test_vars = [key for key in os.environ.keys() if key.startswith('TEST_')]
        for var in test_vars:
            del os.environ[var]
    
    def teardown_method(self):
        """Cleanup after each test method."""
        test_vars = [key for key in os.environ.keys() if key.startswith('TEST_')]
        for var in test_vars:
            del os.environ[var]
    
    def test_convert_to_int(self):
        """Test converting environment variable to int."""
        os.environ['TEST_INT'] = '42'
        
        manager = EnvironmentManager(load_dotenv=False)
        result = manager.get('TEST_INT', var_type=int)
        
        assert result == 42
        assert isinstance(result, int)
    
    def test_convert_to_float(self):
        """Test converting environment variable to float."""
        os.environ['TEST_FLOAT'] = '3.14'
        
        manager = EnvironmentManager(load_dotenv=False)
        result = manager.get('TEST_FLOAT', var_type=float)
        
        assert result == 3.14
        assert isinstance(result, float)
    
    def test_convert_to_bool_true_values(self):
        """Test converting various true values to bool."""
        true_values = ['true', 'True', 'TRUE', '1', 'yes', 'Yes', 'on', 'ON']
        manager = EnvironmentManager(load_dotenv=False)
        
        for i, value in enumerate(true_values):
            key = f'TEST_BOOL_TRUE_{i}'
            os.environ[key] = value
            result = manager.get(key, var_type=bool)
            
            assert result is True
            assert isinstance(result, bool)
            del os.environ[key]  # Cleanup
    
    def test_convert_to_bool_false_values(self):
        """Test converting various false values to bool."""
        false_values = ['false', 'False', 'FALSE', '0', 'no', 'No', 'off', 'OFF', '']
        manager = EnvironmentManager(load_dotenv=False)
        
        for i, value in enumerate(false_values):
            key = f'TEST_BOOL_FALSE_{i}'
            os.environ[key] = value
            result = manager.get(key, var_type=bool)
            
            assert result is False
            assert isinstance(result, bool)
            del os.environ[key]  # Cleanup
    
    def test_convert_to_list(self):
        """Test converting environment variable to list."""
        os.environ['TEST_LIST'] = 'item1,item2,item3'
        
        manager = EnvironmentManager(load_dotenv=False)
        result = manager.get('TEST_LIST', var_type=list)
        
        assert result == ['item1', 'item2', 'item3']
        assert isinstance(result, list)
    
    def test_convert_to_list_with_custom_separator(self):
        """Test converting environment variable to list with custom separator."""
        os.environ['TEST_LIST_CUSTOM'] = 'item1;item2;item3'
        
        manager = EnvironmentManager(load_dotenv=False)
        # This tests the _convert_value method's handling of lists
        result = manager._convert_value('item1;item2;item3', list)
        
        # Default separator is comma, so this should be treated as one item
        assert result == ['item1;item2;item3']
        assert isinstance(result, list)
    
    def test_type_inference_from_default_int(self):
        """Test type inference from default value (int)."""
        manager = EnvironmentManager(load_dotenv=False)
        
        # Variable doesn't exist, should return default with correct type
        result = manager.get('TEST_NONEXISTENT_INT', default=42)
        
        assert result == 42
        assert isinstance(result, int)
    
    def test_type_inference_from_default_with_conversion(self):
        """Test type inference from default value with string conversion."""
        os.environ['TEST_INFER_INT'] = '100'
        
        manager = EnvironmentManager(load_dotenv=False)
        result = manager.get('TEST_INFER_INT', default=42)
        
        assert result == 100
        assert isinstance(result, int)
    
    def test_explicit_type_overrides_default_type(self):
        """Test that explicit var_type overrides default value type."""
        os.environ['TEST_OVERRIDE'] = '3.14'
        
        manager = EnvironmentManager(load_dotenv=False)
        result = manager.get('TEST_OVERRIDE', default=42, var_type=float)
        
        assert result == 3.14
        assert isinstance(result, float)
    
    def test_conversion_error_handling(self):
        """Test handling of type conversion errors."""
        os.environ['TEST_BAD_INT'] = 'not_a_number'
        
        manager = EnvironmentManager(load_dotenv=False)
        
        with pytest.raises(ValueError, match="Cannot convert"):
            manager.get('TEST_BAD_INT', var_type=int)


class TestEnvironmentManagerCaching:
    """Test EnvironmentManager caching functionality."""
    
    def setup_method(self):
        """Setup for each test method."""
        test_vars = [key for key in os.environ.keys() if key.startswith('TEST_')]
        for var in test_vars:
            del os.environ[var]
    
    def teardown_method(self):
        """Cleanup after each test method."""
        test_vars = [key for key in os.environ.keys() if key.startswith('TEST_')]
        for var in test_vars:
            del os.environ[var]
    
    def test_caching_basic_functionality(self):
        """Test that values are cached properly."""
        os.environ['TEST_CACHE'] = 'cached_value'
        
        manager = EnvironmentManager(load_dotenv=False)
        
        # First call
        result1 = manager.get('TEST_CACHE')
        
        # Check cache was populated
        cache_key = 'TEST_CACHE:str'
        assert cache_key in manager._cache
        assert manager._cache[cache_key] == 'cached_value'
        
        # Second call should use cache
        result2 = manager.get('TEST_CACHE')
        
        assert result1 == result2 == 'cached_value'
    
    def test_caching_with_type_conversion(self):
        """Test caching with type conversion."""
        os.environ['TEST_CACHE_INT'] = '42'
        
        manager = EnvironmentManager(load_dotenv=False)
        
        # Call with int conversion
        result1 = manager.get('TEST_CACHE_INT', var_type=int)
        
        # Check specific cache key
        cache_key = 'TEST_CACHE_INT:int'
        assert cache_key in manager._cache
        assert manager._cache[cache_key] == 42
        
        # Second call should use cache
        result2 = manager.get('TEST_CACHE_INT', var_type=int)
        
        assert result1 == result2 == 42
        assert isinstance(result1, int)
    
    def test_cache_keys_differentiate_types(self):
        """Test that cache keys differentiate between types."""
        os.environ['TEST_CACHE_MULTI'] = '42'
        
        manager = EnvironmentManager(load_dotenv=False)
        
        # Get as string
        str_result = manager.get('TEST_CACHE_MULTI', var_type=str)
        # Get as int
        int_result = manager.get('TEST_CACHE_MULTI', var_type=int)
        
        # Should have different cache entries
        assert 'TEST_CACHE_MULTI:str' in manager._cache
        assert 'TEST_CACHE_MULTI:int' in manager._cache
        
        assert manager._cache['TEST_CACHE_MULTI:str'] == '42'
        assert manager._cache['TEST_CACHE_MULTI:int'] == 42
        
        assert str_result == '42'
        assert int_result == 42
    
    def test_clear_cache(self):
        """Test clearing the cache."""
        os.environ['TEST_CLEAR'] = 'value'
        
        manager = EnvironmentManager(load_dotenv=False)
        
        # Populate cache
        manager.get('TEST_CLEAR')
        assert len(manager._cache) > 0
        
        # Clear cache
        manager.clear_cache()
        assert len(manager._cache) == 0
    
    def test_cache_with_defaults(self):
        """Test caching behavior with default values."""
        manager = EnvironmentManager(load_dotenv=False)
        
        # Variable doesn't exist, should return and cache default
        result = manager.get('TEST_CACHE_DEFAULT', default='default_val')
        
        # Cache key should reflect the inferred type
        cache_key = 'TEST_CACHE_DEFAULT:str'
        assert cache_key in manager._cache
        assert manager._cache[cache_key] == 'default_val'
        assert result == 'default_val'


class TestEnvironmentManagerEdgeCases:
    """Test edge cases and error conditions."""
    
    def setup_method(self):
        """Setup for each test method."""
        test_vars = [key for key in os.environ.keys() if key.startswith('TEST_')]
        for var in test_vars:
            del os.environ[var]
    
    def teardown_method(self):
        """Cleanup after each test method."""
        test_vars = [key for key in os.environ.keys() if key.startswith('TEST_')]
        for var in test_vars:
            del os.environ[var]
    
    def test_empty_string_handling(self):
        """Test handling of empty string environment variables."""
        os.environ['TEST_EMPTY'] = ''
        
        manager = EnvironmentManager(load_dotenv=False)
        result = manager.get('TEST_EMPTY')
        
        assert result == ''
        assert isinstance(result, str)
    
    def test_whitespace_handling(self):
        """Test handling of whitespace in environment variables."""
        os.environ['TEST_WHITESPACE'] = '  value with spaces  '
        
        manager = EnvironmentManager(load_dotenv=False)
        result = manager.get('TEST_WHITESPACE')
        
        # Should preserve whitespace by default
        assert result == '  value with spaces  '
    
    def test_none_default_with_type(self):
        """Test None default value with explicit type."""
        manager = EnvironmentManager(load_dotenv=False)
        result = manager.get('TEST_NONE_DEFAULT', default=None, var_type=int)
        
        assert result is None
    
    def test_complex_type_conversion(self):
        """Test conversion to complex types that might not be supported."""
        os.environ['TEST_COMPLEX'] = 'test_value'
        
        manager = EnvironmentManager(load_dotenv=False)
        
        # Test with a type that doesn't have obvious string conversion
        class CustomType:
            def __init__(self, value):
                self.value = value
        
        # The implementation tries target_type(value), so CustomType('test_value') should work
        # Let's test with a type that would actually fail
        with pytest.raises(ValueError, match="Cannot convert"):
            manager.get('TEST_COMPLEX', var_type=dict)  # dict('test_value') should fail


class TestEnvironmentManagerDotenvIntegration:
    """Test .env file loading functionality."""
    
    def test_dotenv_loading_disabled(self):
        """Test that dotenv loading can be disabled."""
        with patch('app.core.utils.env_utils.EnvironmentManager._load_env_file') as mock_load:
            manager = EnvironmentManager(load_dotenv=False)
            
            assert not manager._load_dotenv
            mock_load.assert_not_called()
    
    def test_find_env_file_in_current_directory(self):
        """Test finding .env file in current directory."""
        manager = EnvironmentManager(load_dotenv=False)
        
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create a .env file
            env_file = Path(temp_dir) / '.env'
            env_file.write_text('TEST_VAR=test_value')
            
            # Change to temp directory
            original_cwd = Path.cwd()
            try:
                os.chdir(temp_dir)
                found_path = manager._find_env_file()
                # Compare resolved paths to handle symlinks like /private/var vs /var
                assert found_path is not None
                assert found_path.resolve() == env_file.resolve()
                assert found_path.exists()
            finally:
                os.chdir(original_cwd)
    
    def test_find_env_file_not_found(self):
        """Test when .env file is not found."""
        manager = EnvironmentManager(load_dotenv=False)
        
        with tempfile.TemporaryDirectory() as temp_dir:
            original_cwd = Path.cwd()
            try:
                os.chdir(temp_dir)  # Empty directory
                found_path = manager._find_env_file()
                assert found_path is None
            finally:
                os.chdir(original_cwd)
    
    def test_get_logger_method(self):
        """Test the _get_logger method."""
        manager = EnvironmentManager(load_dotenv=False)
        logger = manager._get_logger()
        
        assert logger is not None
        assert logger.name == 'app.core.utils.env_utils'


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
