"""
Core utility modules for the application.

Provides centralized utilities for environment variable management,
property placeholder resolution, user context extraction, and other common functionality.
"""

from .env_utils import EnvironmentManager, env, initialize_environment
from .property_resolver import PropertyResolver, property_resolver
from .config_converter import (
    dynamic_config_to_dict,
    dict_to_pydantic_compatible,
    extract_config_section
)
from .file_utils import (
    read_text_file,
    read_binary_file, 
    read_private_key_file,
    file_exists,
    get_file_info,
    FileReadError
)
from .user_context import (
    extract_user_from_token,
    extract_user_display_name,
    extract_user_email,
    extract_user_id,
    format_on_behalf_of_context,
    create_audit_context
)

__all__ = [
    'EnvironmentManager',
    'env',
    'initialize_environment',
    'PropertyResolver', 
    'property_resolver',
    'dynamic_config_to_dict',
    'dict_to_pydantic_compatible',
    'extract_config_section',
    'read_text_file',
    'read_binary_file',
    'read_private_key_file', 
    'file_exists',
    'get_file_info',
    'FileReadError',
    'extract_user_from_token',
    'extract_user_display_name',
    'extract_user_email',
    'extract_user_id',
    'format_on_behalf_of_context',
    'create_audit_context'
]