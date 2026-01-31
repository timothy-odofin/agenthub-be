"""GitHub tools package with GitHub App integration and multi-repository support."""

from app.core.utils.dynamic_import import import_providers

# GitHub tools modules configuration: (module_name, class_name)
GITHUB_TOOLS_MODULES = [
    ('github_tools', 'GitHubToolsProvider'),
]

# Import GitHub tools using the generic utility
__all__ = import_providers(__name__, GITHUB_TOOLS_MODULES, globals(), suppress_warnings=True)
