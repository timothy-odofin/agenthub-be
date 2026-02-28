"""
Core utility modules for the application.

Provides centralized utilities for environment variable management,
property placeholder resolution, user context extraction, and other common functionality.
"""

from .config_converter import (
    dict_to_pydantic_compatible,
    dynamic_config_to_dict,
    extract_config_section,
)
from .env_utils import EnvironmentManager, env, initialize_environment
from .file_utils import (
    FileReadError,
    file_exists,
    get_file_info,
    read_binary_file,
    read_private_key_file,
    read_text_file,
)
from .property_resolver import PropertyResolver, property_resolver
from .user_context import (
    create_audit_context,
    extract_user_display_name,
    extract_user_email,
    extract_user_from_token,
    extract_user_id,
    format_on_behalf_of_context,
)

__all__ = [
    "EnvironmentManager",
    "env",
    "initialize_environment",
    "PropertyResolver",
    "property_resolver",
    "dynamic_config_to_dict",
    "dict_to_pydantic_compatible",
    "extract_config_section",
    "read_text_file",
    "read_binary_file",
    "read_private_key_file",
    "file_exists",
    "get_file_info",
    "FileReadError",
    "extract_user_from_token",
    "extract_user_display_name",
    "extract_user_email",
    "extract_user_id",
    "format_on_behalf_of_context",
    "create_audit_context",
]
