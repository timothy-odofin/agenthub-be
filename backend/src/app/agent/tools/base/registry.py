"""
Registry for agent tools.

Provides a centralized registry for discovering and managing different
categories of agent tools using the decorator pattern.

Implements aggressive caching for tool instances to avoid expensive
initialization (especially GitHub API calls that take 19+ seconds).
"""

from typing import Any, Dict, List, Optional, Set

from langchain.tools import StructuredTool, Tool

from app.core.config.framework.settings import settings
from app.core.utils.logger import get_logger

logger = get_logger(__name__)

# Use module-level globals instead of ClassVar
_tools: Dict[str, List] = {}
_packages: Set[str] = set()

# Global cache for instantiated tools (in-memory, persists across requests)
_tool_cache: Dict[str, List[StructuredTool]] = {}
_cache_enabled: bool = True  # Can be disabled for testing


def is_tool_enabled(category: str, tool_name: str) -> bool:
    """
    Check if a specific tool is enabled based on configuration.

    Args:
        category: The tool category (e.g., 'jira', 'vector')
        tool_name: The specific tool name (e.g., 'create_jira_issue')

    Returns:
        True if tool is enabled, False otherwise
    """
    try:
        # Access tools configuration via settings.tools.tools (nested structure)
        tools_config = getattr(settings, "tools", None)
        if not tools_config:
            logger.debug("No tools configuration found. Defaulting to enabled.")
            return True

        # Handle nested structure - tools.tools
        if hasattr(tools_config, "tools"):
            tools_config = tools_config.tools

        category_config = getattr(tools_config, category, None)
        if not category_config:
            logger.debug(
                f"No configuration for category '{category}'. Defaulting to enabled."
            )
            return True

        # Check master switch first
        if hasattr(category_config, "enabled") and not category_config.enabled:
            return False

        # Then check individual tool setting
        tool_setting = getattr(category_config, tool_name, True)
        return bool(tool_setting)

    except Exception as e:
        logger.warning(
            f"Could not load tool configuration: {e}. Defaulting to enabled."
        )
        return True  # Default to enabled if config unavailable


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
            tool_name = getattr(
                tool_class, "__name__", getattr(tool_class, "name", str(tool_class))
            )
            logger.info(f"Registered tool: {category} -> {tool_name}")

            # Register capability with SystemCapabilities
            cls._register_capability(category, package or category, tool_class)

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
                if (
                    hasattr(tool_class, "_registry_package")
                    and tool_class._registry_package == package
                ):
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
    def get_instantiated_tools(
        cls,
        category: Optional[str] = None,
        config: Optional[Dict[str, Any]] = None,
        use_cache: bool = True,
    ) -> List:
        """
        Get instantiated Tool objects for a category or all categories.
        Filters tools based on configuration settings.

        Implements aggressive caching to avoid expensive tool initialization,
        especially GitHub API calls (19+ seconds) and other external connections.

        Args:
            category: Optional specific category to get tools for
            config: Optional configuration to pass to tool classes
            use_cache: If True, uses cached tools. Set False to force reload.

        Returns:
            List of enabled LangChain Tool objects
        """
        # Generate cache key
        cache_key = f"category:{category or 'all'}"

        # Check cache first (unless explicitly disabled or cache is disabled globally)
        if use_cache and _cache_enabled and cache_key in _tool_cache:
            cached_tools = _tool_cache[cache_key]
            logger.info(
                f"✅ Loaded {len(cached_tools)} tools from cache "
                f"(saved ~20-30s initialization time)"
            )
            return cached_tools

        # Cache miss - perform full tool initialization
        logger.info(f"Cache miss - loading tools from scratch for '{cache_key}'")

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
                # Get the category this tool was registered with
                tool_category = None
                for cat, classes in _tools.items():
                    if tool_class in classes:
                        tool_category = cat
                        break

                if not tool_category:
                    logger.warning(
                        f"Could not determine category for tool {tool_class.__name__}"
                    )
                    continue

                # Create instance with config
                instance = tool_class(config.get(tool_class.__name__, {}))

                # Get tools from instance (if it has get_tools method)
                if hasattr(instance, "get_tools"):
                    class_tools = instance.get_tools()

                    # Filter tools based on configuration
                    for tool in class_tools:
                        tool_name = tool.name
                        if is_tool_enabled(tool_category, tool_name):
                            tools.append(tool)
                        else:
                            logger.debug(f"Tool {tool_name} disabled by configuration")
                else:
                    logger.warning(
                        f"Tool class {tool_class.__name__} has no get_tools method"
                    )

            except Exception as e:
                logger.error(f"Failed to instantiate tool {tool_class.__name__}: {e}")

        # Cache the results
        if _cache_enabled:
            _tool_cache[cache_key] = tools
            logger.info(f"✅ Cached {len(tools)} tools for key '{cache_key}'")

        logger.info(f"Loaded {len(tools)} enabled tools")
        return tools

    @classmethod
    def _register_capability(cls, category: str, name: str, tool_class) -> None:
        """
        Register capability metadata for a tool with SystemCapabilities.

        Extracts tool configuration and display metadata, then registers
        it with the SystemCapabilities singleton. This happens during tool
        registration to avoid double-iteration.

        Args:
            category: Tool category
            name: Tool name
            tool_class: Tool provider class
        """
        try:
            # Import here to avoid circular dependency
            from app.core.capabilities import SystemCapabilities

            # Get tool configuration from settings
            tool_config = cls._get_tool_config(category, name)

            if not tool_config:
                logger.debug(
                    f"No configuration found for {category}.{name}, skipping capability"
                )
                return

            # Extract configuration
            enabled = getattr(tool_config, "enabled", False)
            display_config = {}

            # Try to get display metadata from config
            if hasattr(tool_config, "display"):
                display = tool_config.display
                display_config = {
                    "title": getattr(display, "title", ""),
                    "description": getattr(display, "description", ""),
                    "icon": getattr(display, "icon", "tool"),
                    "example_prompts": list(getattr(display, "example_prompts", [])),
                    "tags": list(getattr(display, "tags", [])),
                }

                if hasattr(display, "color"):
                    display_config["color"] = display.color

            # Register with SystemCapabilities
            SystemCapabilities().add_capability(
                category=category,
                name=name,
                enabled=enabled,
                display_config=display_config,
                tool_class=tool_class,
            )

        except Exception as e:
            logger.error(f"Failed to register capability for {category}.{name}: {e}")
            logger.warning(f"Could not register capability for {category}.{name}: {e}")

    @classmethod
    def clear_tool_cache(cls, category: Optional[str] = None) -> None:
        """
        Clear cached tool instances.

        Useful for development, testing, or when tool configuration changes.

        Args:
            category: Specific category to clear. If None, clears all cached tools.
        """
        global _tool_cache

        if category:
            cache_key = f"category:{category}"
            if cache_key in _tool_cache:
                del _tool_cache[cache_key]
                logger.info(f"Cleared tool cache for category: {category}")
        else:
            _tool_cache.clear()
            logger.info("Cleared all tool caches")

    @classmethod
    def set_cache_enabled(cls, enabled: bool) -> None:
        """
        Enable or disable tool caching globally.

        Useful for testing scenarios where you need fresh tool instances.

        Args:
            enabled: True to enable caching, False to disable
        """
        global _cache_enabled
        _cache_enabled = enabled
        logger.info(f"Tool caching {'enabled' if enabled else 'disabled'}")

    @classmethod
    def get_cache_stats(cls) -> Dict[str, Any]:
        """
        Get statistics about tool cache.

        Returns:
            Dictionary with cache statistics
        """
        return {
            "cache_enabled": _cache_enabled,
            "cached_categories": list(_tool_cache.keys()),
            "total_cached_tools": sum(len(tools) for tools in _tool_cache.values()),
            "cache_size_bytes": sum(
                len(str(tool)) for tools in _tool_cache.values() for tool in tools
            ),
        }

    @classmethod
    def _get_tool_config(cls, category: str, name: str):
        """
        Get tool configuration from settings.

        Args:
            category: Tool category
            name: Tool name

        Returns:
            Tool configuration object or None
        """
        try:
            if not hasattr(settings, "tools") or not hasattr(settings.tools, "tools"):
                return None

            # Get category config (e.g., settings.tools.tools.confluence)
            category_config = getattr(settings.tools.tools, category, None)

            if not category_config:
                return None

            # Check if it's enabled at category level
            if hasattr(category_config, "enabled"):
                return category_config

            # Otherwise try to get nested tool config
            # (for categories with multiple tools)
            tool_config = getattr(category_config, name, None)
            return tool_config

        except Exception as e:
            logger.debug(f"Could not get config for {category}.{name}: {e}")
            return None

    @classmethod
    def clear(cls):
        """Clear all registrations (useful for testing)."""
        logger.warning("CLEARING ALL TOOL REGISTRATIONS!")
        _tools.clear()
        _packages.clear()

        # Also clear capabilities
        try:
            from app.core.capabilities import SystemCapabilities

            SystemCapabilities().clear()
        except Exception as e:
            logger.debug(f"Could not clear capabilities: {e}")

        logger.info("Cleared all tool registrations and capabilities")
