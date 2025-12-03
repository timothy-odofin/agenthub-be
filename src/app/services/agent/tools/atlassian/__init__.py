"""Atlassian tools package with Jira and Confluence integrations."""

# Import all tool categories to trigger registration
from . import jira

# Export all categories
__all__ = ['jira']
