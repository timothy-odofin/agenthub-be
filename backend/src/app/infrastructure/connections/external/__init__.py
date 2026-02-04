"""
External service connection managers.
"""

from app.core.utils.dynamic_import import import_providers

# External service connection modules configuration: (module_name, class_name)
EXTERNAL_CONNECTION_MODULES = [
    ('confluence_connection_manager', 'ConfluenceConnectionManager'),
    ('jira_connection_manager', 'JiraConnectionManager'),
    ('s3_connection_manager', 'S3ConnectionManager'),
]

# Import external connection managers using the generic utility
__all__ = import_providers(__name__, EXTERNAL_CONNECTION_MODULES, globals(), suppress_warnings=True)