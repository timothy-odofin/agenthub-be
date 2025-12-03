"""
Registry for agent tools.

Provides a centralized registry for discovering and managing different
categories of agent tools using the decorator pattern.
"""

from typing import Dict, List, Set, Optional, Any
from app.core.utils.logger import get_logger

logger = get_logger(__name__)

# Use module-level globals instead of ClassVar
_tools: Dict[str, List] = {}
_packages: Set[str] = set()


class ToolRegistry:
    """Registry for tool provider classes organized by categories."""
        
    @classmethod
    def register(cls, category: str, package: Optional[str] = None):
        """
        Decorator to register a tool provider class.
        
        Args:
            category: The category this tool belongs to (e.g., 'vector', 'jira')
            package: Optional package name for organization
            
        Returns:
            The decorator function
        """
        def decorator(tool_class):
            # Initialize category if needed
            if category not in _tools:
                _tools[category] = []
            
            # Add tool to category
            _tools[category].append(tool_class)
            
            # Store package info on the class for easier lookup
            if package:
                _packages.add(package)
                tool_class._registry_package = package
                
            # Get name for logging (handle both functions and classes)
            tool_name = getattr(tool_class, '__name__', getattr(tool_class, 'name', str(tool_class)))
            logger.info(f"Registered tool: {category} -> {tool_name}")
            return tool_class
        return decorator
    
    @classmethod
    def get_tools_by_category(cls, category: str) -> List:
        """
        Get all tools in a specific category.
        
        Args:
            category: The category name
            
        Returns:
            List of tool classes in the category
        """
        return _tools.get(category, [])
    
    @classmethod
    def get_tools_by_package(cls, package: str) -> List:
        """
        Get all tools belonging to a specific package.
        
        Args:
            package: The package name
            
        Returns:
            List of tool classes in the package
        """
        package_tools = []
        for category, tools in _tools.items():
            for tool_class in tools:
                # Check if tool was registered with this package
                if hasattr(tool_class, '_registry_package') and tool_class._registry_package == package:
                    package_tools.append(tool_class)
        return package_tools
    
    @classmethod
    def get_categories(cls) -> List[str]:
        """Get all registered categories."""
        return list(_tools.keys())
    
    @classmethod
    def get_packages(cls) -> List[str]:
        """Get all registered packages."""
        return list(_packages)
    
    @classmethod
    def get_all_tools(cls) -> List:
        """Get all registered tools across all categories."""
        all_tools = []
        for tools in _tools.values():
            all_tools.extend(tools)
        return all_tools
    
    @classmethod
    def get_instantiated_tools(cls, category: Optional[str] = None, config: Optional[Dict[str, Any]] = None) -> List:
        """
        Get instantiated Tool objects for a category or all categories.
        
        Args:
            category: Optional specific category to get tools for
            config: Optional configuration to pass to tool classes
            
        Returns:
            List of LangChain Tool objects
        """
        from langchain.tools import Tool
        
        tools = []
        config = config or {}
        
        # Get tool classes for specific category or all
        if category:
            tool_classes = cls.get_tools_by_category(category)
        else:
            tool_classes = cls.get_all_tools()
        
        # Instantiate each tool class and get its tools
        for tool_class in tool_classes:
            try:
                # Create instance with config
                instance = tool_class(config.get(tool_class.__name__, {}))
                
                # Get tools from instance (if it has get_tools method)
                if hasattr(instance, 'get_tools'):
                    class_tools = instance.get_tools()
                    tools.extend(class_tools)
                else:
                    logger.warning(f"Tool class {tool_class.__name__} has no get_tools method")
                    
            except Exception as e:
                logger.error(f"Failed to instantiate tool {tool_class.__name__}: {e}")
                
        return tools
    
    @classmethod
    def clear(cls):
        """Clear all registrations (useful for testing)."""
        logger.warning("CLEARING ALL TOOL REGISTRATIONS!")
        _tools.clear()
        _packages.clear()
        logger.info("Cleared all tool registrations")
