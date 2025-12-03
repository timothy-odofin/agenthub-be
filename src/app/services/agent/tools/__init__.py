"""
Categorized tool system with automatic registration using manual imports.

Package Structure:
- database/: Vector stores, SQL, NoSQL tools
- atlassian/: Jira, Confluence, project management tools  
- web/: Search, scraping, API tools
"""

# Import registry directly from base.registry (skip the base __init__.py)
from .base.registry import ToolRegistry

# Import all tool packages to trigger registration
from . import database
from . import atlassian  
# from . import web  # Commented out until web tools are implemented

# Export the main registry for use by agents
__all__ = [
    'ToolRegistry',
    'database',
    'atlassian'
]