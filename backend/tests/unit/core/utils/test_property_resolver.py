"""
Comprehensive test suite for PropertyResolver.
Tests Spring Boot-style property placeholder resolution with
environment variables, defaults, type conversion, and caching.
"""

import os
import pytest
from unittest.mock import Mock, patch
from typing import Dict, Any, List

from app.core.utils.property_resolver import PropertyResolver
from app.core.utils.env_utils import EnvironmentManager


class TestPropertyResolverBasicFunctionality:
    """Test basic PropertyResolver functionality."""
    
    def setup_method(self):
        """Setup for each test method."""
        # Clear any existing test environment variables
        test_vars = [key for key in os.environ.keys() if key.startswith('TEST_')]
        for var in test_vars:
            del os.environ[var]
        
        # Create fresh environment manager and resolver
        self.env_manager = EnvironmentManager(load_dotenv=False)
        self.resolver = PropertyResolver(self.env_manager)
    
    def teardown_method(self):
        """Cleanup after each test method."""
        test_vars = [key for key in os.environ.keys() if key.startswith('TEST_')]
        for var in test_vars:
            del os.environ[var]
        
        # Clear caches
        self.resolver.clear_cache()
        self.env_manager.clear_cache()
    
    def test_resolve_simple_placeholder(self):
        """Test resolving simple placeholder with environment variable."""
        os.environ['TEST_VAR'] = 'test_value'
        
        result = self.resolver.resolve_value('${TEST_VAR}')
        
        assert result == 'test_value'
    
    def test_resolve_placeholder_with_default(self):
        """Test resolving placeholder with default value when env var missing."""
        result = self.resolver.resolve_value('${MISSING_VAR:default_value}')
        
        assert result == 'default_value'
    
    def test_resolve_placeholder_with_env_var_overriding_default(self):
        """Test that environment variable overrides default value."""
        os.environ['TEST_VAR'] = 'env_value'
        
        result = self.resolver.resolve_value('${TEST_VAR:default_value}')
        
        assert result == 'env_value'
    
    def test_resolve_placeholder_without_default_missing_var(self):
        """Test resolving placeholder without default when env var missing."""
        result = self.resolver.resolve_value('${MISSING_VAR}')
        
        assert result is None
    
    def test_resolve_non_string_value(self):
        """Test resolving non-string value returns unchanged."""
        assert self.resolver.resolve_value(42) == 42
        assert self.resolver.resolve_value(True) is True
        assert self.resolver.resolve_value([1, 2, 3]) == [1, 2, 3]
        assert self.resolver.resolve_value({'key': 'value'}) == {'key': 'value'}
    
    def test_resolve_string_without_placeholder(self):
        """Test resolving string without placeholder returns unchanged."""
        result = self.resolver.resolve_value('plain string')
        
        assert result == 'plain string'
    
    def test_resolve_partial_placeholder_replacement(self):
        """Test resolving string with partial placeholder replacement."""
        os.environ['TEST_VAR'] = 'value'
        
        result = self.resolver.resolve_value('prefix_${TEST_VAR}_suffix')
        
        assert result == 'prefix_value_suffix'
    
    def test_resolve_multiple_placeholders(self):
        """Test resolving string with multiple placeholders."""
        os.environ['TEST_VAR1'] = 'value1'
        os.environ['TEST_VAR2'] = 'value2'
        
        result = self.resolver.resolve_value('${TEST_VAR1}_middle_${TEST_VAR2}')
        
        assert result == 'value1_middle_value2'


class TestPropertyResolverTypeConversion:
    """Test PropertyResolver type conversion functionality."""
    
    def setup_method(self):
        """Setup for each test method."""
        test_vars = [key for key in os.environ.keys() if key.startswith('TEST_')]
        for var in test_vars:
            del os.environ[var]
        
        self.env_manager = EnvironmentManager(load_dotenv=False)
        self.resolver = PropertyResolver(self.env_manager)
    
    def teardown_method(self):
        """Cleanup after each test method."""
        test_vars = [key for key in os.environ.keys() if key.startswith('TEST_')]
        for var in test_vars:
            del os.environ[var]
        
        self.resolver.clear_cache()
        self.env_manager.clear_cache()
    
    def test_auto_convert_integer(self):
        """Test automatic conversion to integer."""
        os.environ['TEST_INT'] = '42'
        
        result = self.resolver.resolve_value('${TEST_INT}')
        
        assert result == 42
        assert isinstance(result, int)
    
    def test_auto_convert_negative_integer(self):
        """Test automatic conversion to negative integer."""
        os.environ['TEST_NEG_INT'] = '-100'
        
        result = self.resolver.resolve_value('${TEST_NEG_INT}')
        
        assert result == -100
        assert isinstance(result, int)
    
    def test_auto_convert_float(self):
        """Test automatic conversion to float."""
        os.environ['TEST_FLOAT'] = '3.14'
        
        result = self.resolver.resolve_value('${TEST_FLOAT}')
        
        assert result == 3.14
        assert isinstance(result, float)
    
    def test_auto_convert_bool_true(self):
        """Test automatic conversion to boolean true."""
        true_values = ['true', 'True', 'TRUE', 'yes', 'YES', 'on', 'enabled']
        
        for i, value in enumerate(true_values):
            key = f'TEST_BOOL_TRUE_{i}'
            os.environ[key] = value
            result = self.resolver.resolve_value(f'${{{key}}}')
            
            assert result is True
            assert isinstance(result, bool)
            del os.environ[key]
    
    def test_auto_convert_bool_false(self):
        """Test automatic conversion to boolean false."""
        false_values = ['false', 'False', 'FALSE', 'no', 'NO', 'off', 'disabled']
        
        for i, value in enumerate(false_values):
            key = f'TEST_BOOL_FALSE_{i}'
            os.environ[key] = value
            result = self.resolver.resolve_value(f'${{{key}}}')
            
            assert result is False
            assert isinstance(result, bool)
            del os.environ[key]
    
    def test_string_remains_string(self):
        """Test that regular strings remain as strings."""
        os.environ['TEST_STRING'] = 'hello world'
        
        result = self.resolver.resolve_value('${TEST_STRING}')
        
        assert result == 'hello world'
        assert isinstance(result, str)
    
    def test_partial_replacement_stays_string(self):
        """Test that partial replacements remain strings regardless of content."""
        os.environ['TEST_INT'] = '42'
        
        result = self.resolver.resolve_value('value_${TEST_INT}')
        
        assert result == 'value_42'
        assert isinstance(result, str)
    
    def test_default_value_type_conversion(self):
        """Test type conversion of default values."""
        # Integer default
        result = self.resolver.resolve_value('${MISSING_VAR:123}')
        assert result == 123
        assert isinstance(result, int)
        
        # Boolean default
        result = self.resolver.resolve_value('${MISSING_VAR:true}')
        assert result is True
        assert isinstance(result, bool)
        
        # Float default  
        result = self.resolver.resolve_value('${MISSING_VAR:3.14}')
        assert result == 3.14
        assert isinstance(result, float)


class TestPropertyResolverComplexData:
    """Test PropertyResolver with complex data structures."""
    
    def setup_method(self):
        """Setup for each test method."""
        test_vars = [key for key in os.environ.keys() if key.startswith('TEST_')]
        for var in test_vars:
            del os.environ[var]
        
        self.env_manager = EnvironmentManager(load_dotenv=False)
        self.resolver = PropertyResolver(self.env_manager)
        
        # Setup test environment variables
        os.environ['TEST_HOST'] = 'localhost'
        os.environ['TEST_PORT'] = '8080'
        os.environ['TEST_DEBUG'] = 'true'
    
    def teardown_method(self):
        """Cleanup after each test method."""
        test_vars = [key for key in os.environ.keys() if key.startswith('TEST_')]
        for var in test_vars:
            del os.environ[var]
        
        self.resolver.clear_cache()
        self.env_manager.clear_cache()
    
    def test_resolve_dict(self):
        """Test resolving placeholders in dictionary."""
        data = {
            'host': '${TEST_HOST}',
            'port': '${TEST_PORT}',
            'debug': '${TEST_DEBUG}',
            'url': 'http://${TEST_HOST}:${TEST_PORT}'
        }
        
        result = self.resolver.resolve_dict(data)
        
        assert result == {
            'host': 'localhost',
            'port': 8080,
            'debug': True,
            'url': 'http://localhost:8080'
        }
    
    def test_resolve_nested_dict(self):
        """Test resolving placeholders in nested dictionary."""
        data = {
            'server': {
                'host': '${TEST_HOST}',
                'port': '${TEST_PORT}',
                'config': {
                    'debug': '${TEST_DEBUG}',
                    'timeout': '${TEST_TIMEOUT:30}'
                }
            },
            'database': {
                'url': 'jdbc:postgresql://${TEST_HOST}:${DB_PORT:5432}/mydb'
            }
        }
        
        result = self.resolver.resolve_dict(data)
        
        assert result == {
            'server': {
                'host': 'localhost',
                'port': 8080,
                'config': {
                    'debug': True,
                    'timeout': 30
                }
            },
            'database': {
                'url': 'jdbc:postgresql://localhost:5432/mydb'
            }
        }
    
    def test_resolve_list(self):
        """Test resolving placeholders in list."""
        data = [
            '${TEST_HOST}',
            '${TEST_PORT}',
            'static_value',
            '${MISSING_VAR:default}'
        ]
        
        result = self.resolver.resolve_list(data)
        
        assert result == ['localhost', 8080, 'static_value', 'default']
    
    def test_resolve_complex_mixed_structure(self):
        """Test resolving placeholders in complex mixed structure."""
        data = {
            'servers': [
                {
                    'name': 'primary',
                    'host': '${TEST_HOST}',
                    'port': '${TEST_PORT}'
                },
                {
                    'name': 'secondary', 
                    'host': '${BACKUP_HOST:backup.example.com}',
                    'port': '${BACKUP_PORT:9090}'
                }
            ],
            'config': {
                'debug': '${TEST_DEBUG}',
                'features': ['${FEATURE_1:auth}', 'logging', '${FEATURE_2:monitoring}']
            }
        }
        
        result = self.resolver.resolve_dict(data)
        
        expected = {
            'servers': [
                {
                    'name': 'primary',
                    'host': 'localhost',
                    'port': 8080
                },
                {
                    'name': 'secondary',
                    'host': 'backup.example.com',
                    'port': 9090
                }
            ],
            'config': {
                'debug': True,
                'features': ['auth', 'logging', 'monitoring']
            }
        }
        
        assert result == expected


class TestPropertyResolverCaching:
    """Test PropertyResolver caching functionality."""
    
    def setup_method(self):
        """Setup for each test method."""
        test_vars = [key for key in os.environ.keys() if key.startswith('TEST_')]
        for var in test_vars:
            del os.environ[var]
        
        self.env_manager = EnvironmentManager(load_dotenv=False)
        self.resolver = PropertyResolver(self.env_manager)
    
    def teardown_method(self):
        """Cleanup after each test method."""
        test_vars = [key for key in os.environ.keys() if key.startswith('TEST_')]
        for var in test_vars:
            del os.environ[var]
        
        self.resolver.clear_cache()
        self.env_manager.clear_cache()
    
    def test_caching_behavior(self):
        """Test that resolved values are cached."""
        os.environ['TEST_VAR'] = 'cached_value'
        
        # First resolution
        result1 = self.resolver.resolve_value('${TEST_VAR}')
        
        # Check cache
        assert '${TEST_VAR}' in self.resolver._resolution_cache
        assert self.resolver._resolution_cache['${TEST_VAR}'] == 'cached_value'
        
        # Second resolution should use cache
        result2 = self.resolver.resolve_value('${TEST_VAR}')
        
        assert result1 == result2 == 'cached_value'
    
    def test_cache_with_different_placeholders(self):
        """Test caching with different placeholders."""
        os.environ['TEST_VAR1'] = 'value1'
        os.environ['TEST_VAR2'] = 'value2'
        
        self.resolver.resolve_value('${TEST_VAR1}')
        self.resolver.resolve_value('${TEST_VAR2}')
        self.resolver.resolve_value('${TEST_VAR1:default}')  # Different placeholder format
        
        # Should have separate cache entries
        assert '${TEST_VAR1}' in self.resolver._resolution_cache
        assert '${TEST_VAR2}' in self.resolver._resolution_cache
        assert '${TEST_VAR1:default}' in self.resolver._resolution_cache
    
    def test_clear_cache(self):
        """Test clearing the cache."""
        os.environ['TEST_VAR'] = 'value'
        
        # Populate cache
        self.resolver.resolve_value('${TEST_VAR}')
        assert len(self.resolver._resolution_cache) > 0
        
        # Clear cache
        self.resolver.clear_cache()
        assert len(self.resolver._resolution_cache) == 0


class TestPropertyResolverUtilityMethods:
    """Test PropertyResolver utility methods."""
    
    def setup_method(self):
        """Setup for each test method."""
        test_vars = [key for key in os.environ.keys() if key.startswith('TEST_')]
        for var in test_vars:
            del os.environ[var]
        
        self.env_manager = EnvironmentManager(load_dotenv=False)
        self.resolver = PropertyResolver(self.env_manager)
    
    def teardown_method(self):
        """Cleanup after each test method."""
        test_vars = [key for key in os.environ.keys() if key.startswith('TEST_')]
        for var in test_vars:
            del os.environ[var]
        
        self.resolver.clear_cache()
        self.env_manager.clear_cache()
    
    def test_has_placeholders_positive(self):
        """Test has_placeholders with values containing placeholders."""
        assert self.resolver.has_placeholders('${VAR}') is True
        assert self.resolver.has_placeholders('prefix_${VAR}_suffix') is True
        assert self.resolver.has_placeholders('${VAR1}_${VAR2}') is True
        assert self.resolver.has_placeholders('${VAR:default}') is True
    
    def test_has_placeholders_negative(self):
        """Test has_placeholders with values not containing placeholders."""
        assert self.resolver.has_placeholders('plain string') is False
        assert self.resolver.has_placeholders('$VAR') is False  # Not proper format
        assert self.resolver.has_placeholders('${') is False  # Incomplete
        assert self.resolver.has_placeholders('') is False
        assert self.resolver.has_placeholders(42) is False  # Not string
    
    def test_extract_placeholder_variables(self):
        """Test extracting placeholder variable names."""
        # Single variable
        result = self.resolver.extract_placeholder_variables('${VAR_NAME}')
        assert result == ['VAR_NAME']
        
        # Multiple variables
        result = self.resolver.extract_placeholder_variables('${VAR1}_middle_${VAR2}')
        assert result == ['VAR1', 'VAR2']
        
        # Variables with defaults
        result = self.resolver.extract_placeholder_variables('${VAR1:default1}_${VAR2:default2}')
        assert result == ['VAR1', 'VAR2']
        
        # Mixed with and without defaults
        result = self.resolver.extract_placeholder_variables('${VAR1}_${VAR2:default}')
        assert result == ['VAR1', 'VAR2']
        
        # No placeholders
        result = self.resolver.extract_placeholder_variables('plain string')
        assert result == []
    
    def test_extract_all_variables_from_data(self):
        """Test extracting all variables from complex data."""
        data = {
            'simple': '${VAR1}',
            'nested': {
                'value': '${VAR2:default}'
            },
            'list': [
                '${VAR3}',
                {'item': '${VAR4}'}
            ],
            'complex': 'prefix_${VAR5}_${VAR6:def}_suffix'
        }
        
        variables = self.resolver._extract_all_variables(data)
        
        # Should contain all unique variables
        expected = ['VAR1', 'VAR2', 'VAR3', 'VAR4', 'VAR5', 'VAR6']
        assert sorted(variables) == sorted(expected)
    
    def test_validate_required_variables(self):
        """Test validation of required environment variables."""
        # Setup some environment variables
        os.environ['AVAILABLE_VAR'] = 'value'
        
        data = {
            'config': {
                'available': '${AVAILABLE_VAR}',
                'missing_required': '${MISSING_VAR}',
                'has_default': '${MISSING_WITH_DEFAULT:default_value}'
            }
        }
        
        missing = self.resolver.validate_required_variables(data)
        
        # Only MISSING_VAR should be reported as missing (MISSING_WITH_DEFAULT has default)
        assert missing == ['MISSING_VAR']
    
    def test_variable_has_default_in_data(self):
        """Test checking if variable has default value in data."""
        data = {
            'with_default': '${VAR_WITH_DEFAULT:some_default}',
            'without_default': '${VAR_WITHOUT_DEFAULT}',
            'mixed': 'prefix_${VAR_MIXED:default}_suffix'
        }
        
        assert self.resolver._variable_has_default_in_data('VAR_WITH_DEFAULT', data) is True
        assert self.resolver._variable_has_default_in_data('VAR_WITHOUT_DEFAULT', data) is False
        assert self.resolver._variable_has_default_in_data('VAR_MIXED', data) is True
        assert self.resolver._variable_has_default_in_data('NONEXISTENT_VAR', data) is False


class TestPropertyResolverEdgeCases:
    """Test PropertyResolver edge cases and error conditions."""
    
    def setup_method(self):
        """Setup for each test method."""
        test_vars = [key for key in os.environ.keys() if key.startswith('TEST_')]
        for var in test_vars:
            del os.environ[var]
        
        self.env_manager = EnvironmentManager(load_dotenv=False)
        self.resolver = PropertyResolver(self.env_manager)
    
    def teardown_method(self):
        """Cleanup after each test method."""
        test_vars = [key for key in os.environ.keys() if key.startswith('TEST_')]
        for var in test_vars:
            del os.environ[var]
        
        self.resolver.clear_cache()
        self.env_manager.clear_cache()
    
    def test_empty_string_values(self):
        """Test handling of empty string values."""
        os.environ['TEST_EMPTY'] = ''
        
        result = self.resolver.resolve_value('${TEST_EMPTY}')
        
        # Empty string is falsy, so it returns None for missing values
        assert result is None
    
    def test_empty_default_value(self):
        """Test handling of empty default values."""
        result = self.resolver.resolve_value('${MISSING_VAR:}')
        
        assert result == ''
        assert isinstance(result, str)
    
    def test_whitespace_in_variable_names(self):
        """Test handling of whitespace in variable names."""
        os.environ['TEST_VAR'] = 'value'
        
        # Should handle whitespace around variable name
        result = self.resolver.resolve_value('${ TEST_VAR }')
        assert result == 'value'
        
        result = self.resolver.resolve_value('${TEST_VAR :default}')
        assert result == 'value'
    
    def test_nested_placeholders_not_supported(self):
        """Test that nested placeholders are not resolved."""
        os.environ['INNER_VAR'] = 'TEST_VALUE'
        os.environ['TEST_VALUE'] = 'final_value'
        
        # This should resolve to '${TEST_VALUE}', not 'final_value'
        result = self.resolver.resolve_value('${${INNER_VAR}}')
        
        # Should not resolve nested placeholder
        assert 'final_value' not in str(result)
    
    def test_malformed_placeholders(self):
        """Test handling of malformed placeholders."""
        # These should be left as-is
        assert self.resolver.resolve_value('${') == '${'
        assert self.resolver.resolve_value('${}') == '${}'
        assert self.resolver.resolve_value('$VAR') == '$VAR'  # Missing braces
        assert self.resolver.resolve_value('{VAR}') == '{VAR}'  # Missing $
    
    def test_special_characters_in_values(self):
        """Test handling of special characters in resolved values."""
        os.environ['TEST_SPECIAL'] = 'value:with:colons'
        
        result = self.resolver.resolve_value('${TEST_SPECIAL}')
        
        assert result == 'value:with:colons'
    
    def test_custom_environment_manager(self):
        """Test using custom environment manager."""
        mock_env = Mock()
        mock_env.get_string.return_value = 'mocked_value'
        mock_env.has.return_value = True
        
        custom_resolver = PropertyResolver(mock_env)
        result = custom_resolver.resolve_value('${TEST_VAR}')
        
        assert result == 'mocked_value'
        mock_env.get_string.assert_called_with('TEST_VAR', '')


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
