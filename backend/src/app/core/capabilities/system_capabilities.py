"""
System capabilities singleton.

Maintains a registry of agent capabilities derived from enabled tools.
Capabilities are populated during tool registration and served to clients
to show what the agent can do.
"""

from typing import List, Dict, Any, Optional
from app.core.utils.single_ton import SingletonMeta
from app.core.utils.logger import get_logger

logger = get_logger(__name__)


class SystemCapabilities(metaclass=SingletonMeta):
    """
    Singleton class that stores agent capabilities based on registered tools.
    
    Capabilities represent what the agent can do, derived from enabled tools.
    This provides a dynamic, configuration-driven capability list for clients.
    
    Usage:
        # Register capability during tool registration
        SystemCapabilities().add_capability(
            category="confluence",
            name="confluence",
            enabled=True,
            display_config={
                "title": "Search Confluence",
                "description": "Search company wiki and documentation",
                "example_prompts": ["Find documentation about..."]
            }
        )
        
        # Retrieve all capabilities
        capabilities = SystemCapabilities().get_capabilities()
    """
    
    def __init__(self):
        """Initialize the capabilities store."""
        if hasattr(self, '_initialized'):
            return
        
        self._initialized = True
        self.data: List[Dict[str, Any]] = []
        logger.debug("SystemCapabilities singleton initialized")
    
    def add_capability(
        self,
        category: str,
        name: str,
        enabled: bool,
        display_config: Optional[Dict[str, Any]] = None,
        tool_class: Optional[Any] = None
    ) -> None:
        """
        Add a single capability to the registry.
        
        Called during tool registration to build capabilities from tools.
        Only adds capability if the tool is enabled.
        
        Args:
            category: Tool category (e.g., "confluence", "github")
            name: Tool name
            enabled: Whether the tool is enabled in configuration
            display_config: Display metadata from tool configuration
            tool_class: Optional tool class reference
        """
        if not enabled:
            logger.debug(f"Skipping capability for disabled tool: {category}.{name}")
            return
        
        display_config = display_config or {}
        
        # Build capability object
        capability = {
            "id": f"{category}.{name}",
            "category": category,
            "name": name,
            "title": display_config.get('title', self._generate_title(name)),
            "description": display_config.get('description', ''),
            "icon": display_config.get('icon', 'tool'),
            "example_prompts": display_config.get('example_prompts', []),
            "tags": display_config.get('tags', []),
        }
        
        # Add optional metadata
        if 'color' in display_config:
            capability['color'] = display_config['color']
        
        self.data.append(capability)
        logger.info(f"Added capability: {capability['id']} - {capability['title']}")
    
    def get_capabilities(self, category: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get all registered capabilities or filter by category.
        
        Args:
            category: Optional category filter
            
        Returns:
            List of capability dictionaries
        """
        if not category:
            return self.data.copy()
        
        return [cap for cap in self.data if cap['category'] == category]
    
    def get_capability_by_id(self, capability_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a specific capability by ID.
        
        Args:
            capability_id: Capability ID (format: "category.name")
            
        Returns:
            Capability dictionary or None
        """
        for cap in self.data:
            if cap['id'] == capability_id:
                return cap.copy()
        return None
    
    def get_categories(self) -> List[str]:
        """
        Get list of all capability categories.
        
        Returns:
            List of unique category names
        """
        return list(set(cap['category'] for cap in self.data))
    
    def clear(self) -> None:
        """
        Clear all capabilities.
        
        Useful for testing or reinitialization.
        """
        logger.warning("Clearing all capabilities")
        self.data.clear()
    
    def refresh_from_tools(self) -> None:
        """
        Refresh capabilities from tool registry.
        
        This will clear existing capabilities and rebuild from current
        tool registry state. Useful if tools are dynamically enabled/disabled.
        """
        logger.info("Refreshing capabilities from tool registry")
        self.clear()
        
        # Import here to avoid circular dependency
        from app.agent.tools.base.registry import ToolRegistry
        
        # Rebuild capabilities from registry
        # Note: This requires tools to be re-registered or have their
        # configurations re-read
        logger.warning(
            "refresh_from_tools() requires tool re-registration. "
            "Consider restarting application for configuration changes."
        )
    
    @staticmethod
    def _generate_title(name: str) -> str:
        """
        Generate a user-friendly title from tool name.
        
        Args:
            name: Tool name (e.g., "read_python_docs")
            
        Returns:
            Title (e.g., "Read Python Docs")
        """
        # Replace underscores with spaces and title case
        return ' '.join(word.capitalize() for word in name.replace('_', ' ').split())
    
    def __repr__(self) -> str:
        """String representation."""
        return f"SystemCapabilities(capabilities={len(self.data)})"
