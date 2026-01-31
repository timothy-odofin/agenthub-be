"""Datadog tools package for monitoring and observability."""

from app.core.utils.dynamic_import import import_providers

# Datadog tools modules configuration: (module_name, class_name)
DATADOG_TOOLS_MODULES = [
    ('datadog_tools', 'DatadogToolsProvider'),
]

# Import Datadog tools using the generic utility
__all__ = import_providers(__name__, DATADOG_TOOLS_MODULES, globals(), suppress_warnings=True)
