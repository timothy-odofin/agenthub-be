"""
Categorized tool system with automatic registration.

Package Structure:
- database/: Vector stores, SQL, NoSQL tools
- atlassian/: Jira, Confluence, project management tools
- github/: GitHub repositories, issues, pull requests tools
- datadog/: Monitoring, logs, metrics, and observability tools
- web/: Search, scraping, API tools
"""

# Import all tool packages to trigger registration
# This ensures that the @ToolRegistry.register decorators are executed
from . import atlassian, database, datadog, github, web

# Import registry directly from base.registry (skip the base __init__.py)
from .base.registry import ToolRegistry

# Export the main registry for use by agents
__all__ = ["ToolRegistry", "database", "atlassian", "github", "datadog", "web"]
