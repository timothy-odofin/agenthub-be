"""Atlassian tools package with Jira and Confluence integrations."""

from app.core.utils.dynamic_import import import_providers

# Atlassian tools modules configuration: (module_name, class_name)
ATLASSIAN_TOOLS_MODULES = [
    ('jira', 'JiraTools'),
    ('confluence', 'ConfluenceTools'),
]

# Import atlassian tools using the generic utility
__all__ = import_providers(__name__, ATLASSIAN_TOOLS_MODULES, globals(), suppress_warnings=True)
