"""
Unit tests for the ToolRegistry system.

Tests the registration, discovery, and configuration-based filtering of agent tools.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from langchain.tools import Tool, StructuredTool
from pydantic import BaseModel, Field

from app.agent.tools.base.registry import ToolRegistry, is_tool_enabled, _tools, _packages


class MockToolInput(BaseModel):
    """Mock input schema for testing."""
    query: str = Field(description="Test query")


class MockTool1:
    """Mock tool class for testing registration."""
    
    def __init__(self, config=None):
        self.config = config or {}
    
    def get_tools(self):
        return [
            Tool(
                name="mock_tool_1",
                description="Mock tool 1 for testing",
                func=lambda x: "mock result 1"
            ),
            Tool(
                name="mock_tool_2", 
                description="Mock tool 2 for testing",
                func=lambda x: "mock result 2"
            )
        ]


class MockTool2:
    """Another mock tool class for testing."""
    
    def __init__(self, config=None):
        self.config = config or {}
    
    def get_tools(self):
        return [
            StructuredTool(
                name="structured_mock_tool",
                description="Structured mock tool",
                func=lambda x: "structured result",
                args_schema=MockToolInput
            )
        ]


class MockToolWithoutGetTools:
    """Mock tool class without get_tools method."""
    
    def __init__(self, config=None):
        self.config = config or {}


class MockToolWithException:
    """Mock tool class that raises exception during initialization."""
    
    def __init__(self, config=None):
        raise ValueError("Initialization failed")


@pytest.fixture(autouse=True)
def clear_registry():
    """Clear the registry before and after each test."""
    ToolRegistry.clear()
    yield
    ToolRegistry.clear()


@pytest.fixture
def mock_settings():
    """Mock settings with tool configuration."""
    # Create a simple object that behaves like our settings
    class MockConfig:
        def __init__(self, **kwargs):
            for key, value in kwargs.items():
                setattr(self, key, value)
    
    # Create category configurations
    jira_config = MockConfig(
        enabled=True,
        create_jira_issue=True,
        search_jira_issues=False,
        mock_tool_1=True,
        mock_tool_2=False
    )
    
    vector_config = MockConfig(
        enabled=True,
        retrieve_information=True,
        structured_mock_tool=True
    )
    
    disabled_config = MockConfig(
        enabled=False,
        some_tool=True
    )
    
    # Create tools configuration
    tools_config = MockConfig(
        jira=jira_config,
        vector=vector_config,
        disabled_category=disabled_config
    )
    
    # Create main settings object
    settings = MockConfig(tools=tools_config)
    
    return settings


class TestToolRegistryBasics:
    """Test basic registry functionality."""
    
    def test_register_decorator_adds_tool_to_category(self):
        """Test that the register decorator adds tools to the correct category."""
        @ToolRegistry.register("test_category", "test_package")
        class TestTool:
            pass
        
        assert "test_category" in _tools
        assert TestTool in _tools["test_category"]
        assert hasattr(TestTool, '_registry_package')
        assert TestTool._registry_package == "test_package"
        assert "test_package" in _packages
    
    def test_register_decorator_without_package(self):
        """Test registration without package specification."""
        @ToolRegistry.register("no_package_category")
        class TestToolNoPackage:
            pass
        
        assert "no_package_category" in _tools
        assert TestToolNoPackage in _tools["no_package_category"]
        assert not hasattr(TestToolNoPackage, '_registry_package')
    
    def test_get_tools_by_category(self):
        """Test retrieving tools by category."""
        @ToolRegistry.register("category1")
        class Tool1:
            pass
        
        @ToolRegistry.register("category1")
        class Tool2:
            pass
        
        @ToolRegistry.register("category2")
        class Tool3:
            pass
        
        category1_tools = ToolRegistry.get_tools_by_category("category1")
        category2_tools = ToolRegistry.get_tools_by_category("category2")
        empty_tools = ToolRegistry.get_tools_by_category("nonexistent")
        
        assert len(category1_tools) == 2
        assert Tool1 in category1_tools
        assert Tool2 in category1_tools
        assert len(category2_tools) == 1
        assert Tool3 in category2_tools
        assert len(empty_tools) == 0
    
    def test_get_tools_by_package(self):
        """Test retrieving tools by package."""
        @ToolRegistry.register("category1", "package1")
        class Tool1:
            pass
        
        @ToolRegistry.register("category1", "package1") 
        class Tool2:
            pass
        
        @ToolRegistry.register("category2", "package2")
        class Tool3:
            pass
        
        package1_tools = ToolRegistry.get_tools_by_package("package1")
        package2_tools = ToolRegistry.get_tools_by_package("package2")
        empty_tools = ToolRegistry.get_tools_by_package("nonexistent")
        
        assert len(package1_tools) == 2
        assert Tool1 in package1_tools
        assert Tool2 in package1_tools
        assert len(package2_tools) == 1
        assert Tool3 in package2_tools
        assert len(empty_tools) == 0
    
    def test_get_categories(self):
        """Test getting all registered categories."""
        @ToolRegistry.register("cat1")
        class Tool1:
            pass
        
        @ToolRegistry.register("cat2")
        class Tool2:
            pass
        
        categories = ToolRegistry.get_categories()
        assert "cat1" in categories
        assert "cat2" in categories
        assert len(categories) == 2
    
    def test_get_packages(self):
        """Test getting all registered packages."""
        @ToolRegistry.register("cat1", "pkg1")
        class Tool1:
            pass
        
        @ToolRegistry.register("cat2", "pkg2") 
        class Tool2:
            pass
        
        packages = ToolRegistry.get_packages()
        assert "pkg1" in packages
        assert "pkg2" in packages
        assert len(packages) == 2
    
    def test_get_all_tools(self):
        """Test getting all registered tools across categories."""
        @ToolRegistry.register("cat1")
        class Tool1:
            pass
        
        @ToolRegistry.register("cat2")
        class Tool2:
            pass
        
        all_tools = ToolRegistry.get_all_tools()
        assert len(all_tools) == 2
        assert Tool1 in all_tools
        assert Tool2 in all_tools
    
    def test_clear_registry(self):
        """Test clearing the registry."""
        @ToolRegistry.register("category", "package")
        class TestTool:
            pass
        
        assert len(_tools) > 0
        assert len(_packages) > 0
        
        ToolRegistry.clear()
        
        assert len(_tools) == 0
        assert len(_packages) == 0


class TestToolConfiguration:
    """Test configuration-based tool filtering."""
    
    @patch('app.agent.tools.base.registry.settings')
    def test_is_tool_enabled_with_enabled_category(self, mock_settings_obj, mock_settings):
        """Test tool enabled when category is enabled and tool is enabled."""
        # Replace the settings object with our mock
        for attr_name, attr_value in vars(mock_settings).items():
            setattr(mock_settings_obj, attr_name, attr_value)
        
        result = is_tool_enabled("jira", "create_jira_issue")
        assert result is True
    
    @patch('app.agent.tools.base.registry.settings')
    def test_is_tool_enabled_with_disabled_individual_tool(self, mock_settings_obj, mock_settings):
        """Test tool disabled when individually disabled."""
        for attr_name, attr_value in vars(mock_settings).items():
            setattr(mock_settings_obj, attr_name, attr_value)
        
        result = is_tool_enabled("jira", "search_jira_issues")
        assert result is False
    
    @patch('app.agent.tools.base.registry.settings')
    def test_is_tool_enabled_with_disabled_category(self, mock_settings_obj, mock_settings):
        """Test tool disabled when category is disabled."""
        for attr_name, attr_value in vars(mock_settings).items():
            setattr(mock_settings_obj, attr_name, attr_value)
        
        result = is_tool_enabled("disabled_category", "some_tool")
        assert result is False
    
    @patch('app.agent.tools.base.registry.settings')
    def test_is_tool_enabled_with_nonexistent_category(self, mock_settings_obj, mock_settings):
        """Test tool defaults to enabled for nonexistent category."""
        for attr_name, attr_value in vars(mock_settings).items():
            setattr(mock_settings_obj, attr_name, attr_value)
        
        result = is_tool_enabled("nonexistent_category", "some_tool")
        assert result is True
    
    @patch('app.agent.tools.base.registry.settings')
    def test_is_tool_enabled_with_nonexistent_tool(self, mock_settings_obj, mock_settings):
        """Test tool defaults to enabled when not explicitly configured."""
        for attr_name, attr_value in vars(mock_settings).items():
            setattr(mock_settings_obj, attr_name, attr_value)
        
        result = is_tool_enabled("jira", "nonexistent_tool")
        assert result is True
    
    @patch('app.agent.tools.base.registry.settings')
    def test_is_tool_enabled_without_tools_config(self, mock_settings_obj):
        """Test tool defaults to enabled when no tools config exists."""
        # Don't set tools attribute
        result = is_tool_enabled("any_category", "any_tool")
        assert result is True
    
    @patch('app.agent.tools.base.registry.settings', side_effect=Exception("Settings error"))
    def test_is_tool_enabled_with_exception(self, mock_settings_obj):
        """Test tool defaults to enabled when configuration loading fails."""
        result = is_tool_enabled("any_category", "any_tool")
        assert result is True


class TestToolInstantiation:
    """Test tool instantiation with configuration filtering."""
    
    @patch('app.agent.tools.base.registry.settings')
    def test_get_instantiated_tools_all_categories(self, mock_settings_obj, mock_settings):
        """Test getting instantiated tools from all categories."""
        for attr_name, attr_value in vars(mock_settings).items():
            setattr(mock_settings_obj, attr_name, attr_value)
        
        # Register mock tools
        @ToolRegistry.register("jira")
        class TestJiraTool(MockTool1):
            pass
        
        @ToolRegistry.register("vector")
        class TestVectorTool(MockTool2):
            pass
        
        tools = ToolRegistry.get_instantiated_tools()
        
        # Should get tools based on configuration
        tool_names = [tool.name for tool in tools]
        assert "mock_tool_1" in tool_names  # jira.mock_tool_1 = True
        assert "mock_tool_2" not in tool_names  # jira.mock_tool_2 = False
        assert "structured_mock_tool" in tool_names  # vector.structured_mock_tool = True
    
    @patch('app.agent.tools.base.registry.settings')
    def test_get_instantiated_tools_specific_category(self, mock_settings_obj, mock_settings):
        """Test getting instantiated tools from specific category."""
        for attr_name, attr_value in vars(mock_settings).items():
            setattr(mock_settings_obj, attr_name, attr_value)
        
        @ToolRegistry.register("jira")
        class TestJiraTool(MockTool1):
            pass
        
        @ToolRegistry.register("vector") 
        class TestVectorTool(MockTool2):
            pass
        
        jira_tools = ToolRegistry.get_instantiated_tools(category="jira")
        
        tool_names = [tool.name for tool in jira_tools]
        assert "mock_tool_1" in tool_names
        assert "structured_mock_tool" not in tool_names  # Not from jira category
    
    @patch('app.agent.tools.base.registry.settings')
    def test_get_instantiated_tools_with_config(self, mock_settings_obj, mock_settings):
        """Test passing configuration to tool classes."""
        for attr_name, attr_value in vars(mock_settings).items():
            setattr(mock_settings_obj, attr_name, attr_value)
        
        @ToolRegistry.register("jira")
        class TestToolWithConfig(MockTool1):
            def __init__(self, config=None):
                super().__init__(config)
                self.test_config = config
        
        config = {"TestToolWithConfig": {"test_param": "test_value"}}
        tools = ToolRegistry.get_instantiated_tools(config=config)
        
        # Verify tools were created (configuration passed correctly)
        assert len(tools) > 0
    
    @patch('app.agent.tools.base.registry.settings')
    def test_get_instantiated_tools_handles_tool_without_get_tools(self, mock_settings_obj, mock_settings):
        """Test handling of tool class without get_tools method."""
        for attr_name, attr_value in vars(mock_settings).items():
            setattr(mock_settings_obj, attr_name, attr_value)
        
        @ToolRegistry.register("test")
        class BadTool(MockToolWithoutGetTools):
            pass
        
        tools = ToolRegistry.get_instantiated_tools()
        
        # Should handle gracefully and not crash
        assert isinstance(tools, list)
    
    @patch('app.agent.tools.base.registry.settings')
    def test_get_instantiated_tools_handles_initialization_exception(self, mock_settings_obj, mock_settings):
        """Test handling of tool class that fails during initialization."""
        for attr_name, attr_value in vars(mock_settings).items():
            setattr(mock_settings_obj, attr_name, attr_value)
        
        @ToolRegistry.register("test")
        class FailingTool(MockToolWithException):
            pass
        
        tools = ToolRegistry.get_instantiated_tools()
        
        # Should handle gracefully and not crash
        assert isinstance(tools, list)


class TestToolRegistryIntegration:
    """Integration tests for the complete tool registry workflow."""
    
    @patch('app.agent.tools.base.registry.settings')
    def test_complete_workflow(self, mock_settings_obj, mock_settings):
        """Test complete workflow from registration to filtered instantiation."""
        for attr_name, attr_value in vars(mock_settings).items():
            setattr(mock_settings_obj, attr_name, attr_value)
        
        # Register tools
        @ToolRegistry.register("jira", "atlassian")
        class JiraTestTool(MockTool1):
            pass
        
        @ToolRegistry.register("vector", "database")
        class VectorTestTool(MockTool2):
            pass
        
        # Verify registration
        assert len(ToolRegistry.get_categories()) == 2
        assert len(ToolRegistry.get_packages()) == 2
        assert "jira" in ToolRegistry.get_categories()
        assert "vector" in ToolRegistry.get_categories()
        assert "atlassian" in ToolRegistry.get_packages()
        assert "database" in ToolRegistry.get_packages()
        
        # Get tools with configuration filtering
        all_tools = ToolRegistry.get_instantiated_tools()
        jira_tools = ToolRegistry.get_instantiated_tools(category="jira")
        vector_tools = ToolRegistry.get_instantiated_tools(category="vector")
        
        # Verify filtering based on configuration
        all_tool_names = [tool.name for tool in all_tools]
        jira_tool_names = [tool.name for tool in jira_tools]
        vector_tool_names = [tool.name for tool in vector_tools]
        
        # Based on mock settings:
        # jira.mock_tool_1 = True, jira.mock_tool_2 = False
        # vector.structured_mock_tool = True
        assert "mock_tool_1" in all_tool_names
        assert "mock_tool_2" not in all_tool_names
        assert "structured_mock_tool" in all_tool_names
        
        assert "mock_tool_1" in jira_tool_names
        assert "mock_tool_2" not in jira_tool_names
        assert "structured_mock_tool" not in jira_tool_names
        
        assert "structured_mock_tool" in vector_tool_names
        assert "mock_tool_1" not in vector_tool_names
    
    @patch('app.agent.tools.base.registry.settings')
    def test_disabled_category_filters_all_tools(self, mock_settings_obj, mock_settings):
        """Test that disabling a category filters out all its tools."""
        for attr_name, attr_value in vars(mock_settings).items():
            setattr(mock_settings_obj, attr_name, attr_value)
        
        @ToolRegistry.register("disabled_category")
        class DisabledTool(MockTool1):
            pass
        
        tools = ToolRegistry.get_instantiated_tools()
        
        # No tools should be returned from disabled_category
        tool_names = [tool.name for tool in tools]
        # Note: Since disabled_category.enabled = False, no tools should be returned
        # But let's be more specific about which tools we expect
        disabled_category_tools = ToolRegistry.get_instantiated_tools(category="disabled_category")
        assert len(disabled_category_tools) == 0
