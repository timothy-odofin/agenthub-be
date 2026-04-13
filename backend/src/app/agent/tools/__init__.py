"""
Categorized tool system with automatic registration.

Package Structure:
- database/: Vector stores, SQL, NoSQL tools
- atlassian/: Jira, Confluence, project management tools
- mcp_github/: GitHub integration via MCP (Model Context Protocol) server
- datadog/: Monitoring, logs, metrics, and observability tools
- web/: Search, scraping, API tools
- navigation/: Voice/text-driven route navigation tools
"""

# Import all tool packages to trigger registration
# This ensures that the @ToolRegistry.register decorators are executed
from . import atlassian, database, datadog, mcp_github, navigation, web

# Import registry directly from base.registry (skip the base __init__.py)
from .base.registry import ToolRegistry

# Export the main registry for use by agents
__all__ = [
    "ToolRegistry",
    "database",
    "atlassian",
    "mcp_github",
    "datadog",
    "navigation",
    "web",
]
