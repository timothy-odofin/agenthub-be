"""
Navigation tools for the agent.

These tools enable the agent to navigate users to specific routes/pages
in the frontend application via voice or text commands.

This demonstrates how to implement intent-based navigation in an AI agent:
1. The user says "go to dashboard" or "take me to signup"
2. The agent recognizes the intent and calls the navigate_to_route tool
3. The tool returns a structured action in the response metadata
4. The frontend reads the action and executes the navigation

Inspired by the novitari-ai-service pattern (NavigateToRouteTool + ApplicationMapService).
"""

from .navigation_tools import NavigationTools

__all__ = ["NavigationTools"]
