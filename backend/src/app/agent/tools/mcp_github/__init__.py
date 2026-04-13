"""
MCP GitHub tools package.

Replaces the custom GitHub tools implementation with the standardized
Model Context Protocol (MCP) GitHub server integration. This approach:

1. Uses the official GitHub MCP server for all GitHub API operations
2. Creates StructuredTool wrappers with sync + async support for LangChain agents
3. Eliminates custom connection management, tool factories, and API wrappers
4. Follows the same ToolRegistry pattern as all other tool categories
"""

from app.core.utils.dynamic_import import import_providers

# MCP GitHub tools modules configuration: (module_name, class_name)
MCP_GITHUB_TOOLS_MODULES = [
    ("mcp_github_tools", "MCPGitHubToolsProvider"),
]

# Import MCP GitHub tools using the generic utility
__all__ = import_providers(
    __name__, MCP_GITHUB_TOOLS_MODULES, globals(), suppress_warnings=True
)
