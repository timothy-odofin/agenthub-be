"""
Unit tests for SystemCapabilities singleton.

Tests capability registration, retrieval, and singleton behavior.
"""

import pytest
from app.core.capabilities import SystemCapabilities
from app.core.utils.single_ton import SingletonMeta


@pytest.fixture(autouse=True)
def clear_capabilities():
    """Clear capabilities before and after each test."""
    SystemCapabilities().clear()
    yield
    SystemCapabilities().clear()


class TestSystemCapabilitiesBasics:
    """Test basic SystemCapabilities functionality."""
    
    def test_singleton_pattern(self):
        """Test that SystemCapabilities is a singleton."""
        cap1 = SystemCapabilities()
        cap2 = SystemCapabilities()
        
        assert cap1 is cap2
        assert id(cap1) == id(cap2)
    
    def test_initialization(self):
        """Test initialization creates empty data list."""
        capabilities = SystemCapabilities()
        
        assert hasattr(capabilities, 'data')
        assert isinstance(capabilities.data, list)
        assert len(capabilities.data) == 0
    
    def test_multiple_initialization_preserves_data(self):
        """Test that re-instantiation preserves existing data."""
        cap1 = SystemCapabilities()
        cap1.data.append({"id": "test", "title": "Test"})
        
        cap2 = SystemCapabilities()
        assert cap2.data == cap1.data
        assert len(cap2.data) == 1


class TestAddCapability:
    """Test adding capabilities."""
    
    def test_add_enabled_capability(self):
        """Test adding an enabled capability."""
        capabilities = SystemCapabilities()
        
        capabilities.add_capability(
            category="test",
            name="test_tool",
            enabled=True,
            display_config={
                "title": "Test Tool",
                "description": "A test tool",
                "icon": "test-icon",
                "example_prompts": ["Test prompt 1", "Test prompt 2"]
            }
        )
        
        assert len(capabilities.data) == 1
        cap = capabilities.data[0]
        assert cap['id'] == "test.test_tool"
        assert cap['category'] == "test"
        assert cap['name'] == "test_tool"
        assert cap['title'] == "Test Tool"
        assert cap['description'] == "A test tool"
        assert cap['icon'] == "test-icon"
        assert len(cap['example_prompts']) == 2
    
    def test_add_disabled_capability_skipped(self):
        """Test that disabled capabilities are not added."""
        capabilities = SystemCapabilities()
        
        capabilities.add_capability(
            category="test",
            name="disabled_tool",
            enabled=False,
            display_config={"title": "Disabled Tool"}
        )
        
        assert len(capabilities.data) == 0
    
    def test_add_capability_without_display_config(self):
        """Test adding capability without display config uses defaults."""
        capabilities = SystemCapabilities()
        
        capabilities.add_capability(
            category="test",
            name="basic_tool",
            enabled=True
        )
        
        assert len(capabilities.data) == 1
        cap = capabilities.data[0]
        assert cap['title'] == "Basic Tool"  # Auto-generated from name
        assert cap['description'] == ""
        assert cap['icon'] == "tool"
        assert cap['example_prompts'] == []
    
    def test_add_multiple_capabilities(self):
        """Test adding multiple capabilities."""
        capabilities = SystemCapabilities()
        
        for i in range(3):
            capabilities.add_capability(
                category=f"cat{i}",
                name=f"tool{i}",
                enabled=True,
                display_config={"title": f"Tool {i}"}
            )
        
        assert len(capabilities.data) == 3
        assert capabilities.data[0]['title'] == "Tool 0"
        assert capabilities.data[1]['title'] == "Tool 1"
        assert capabilities.data[2]['title'] == "Tool 2"
    
    def test_add_capability_with_optional_color(self):
        """Test adding capability with optional color field."""
        capabilities = SystemCapabilities()
        
        capabilities.add_capability(
            category="test",
            name="colored_tool",
            enabled=True,
            display_config={
                "title": "Colored Tool",
                "color": "#FF5733"
            }
        )
        
        assert len(capabilities.data) == 1
        cap = capabilities.data[0]
        assert 'color' in cap
        assert cap['color'] == "#FF5733"


class TestGetCapabilities:
    """Test retrieving capabilities."""
    
    def test_get_all_capabilities(self):
        """Test getting all capabilities."""
        capabilities = SystemCapabilities()
        
        # Add test capabilities
        capabilities.add_capability("cat1", "tool1", True, {"title": "Tool 1"})
        capabilities.add_capability("cat2", "tool2", True, {"title": "Tool 2"})
        
        all_caps = capabilities.get_capabilities()
        
        assert len(all_caps) == 2
        assert all_caps[0]['title'] == "Tool 1"
        assert all_caps[1]['title'] == "Tool 2"
    
    def test_get_capabilities_returns_copy(self):
        """Test that get_capabilities returns a copy of data."""
        capabilities = SystemCapabilities()
        capabilities.add_capability("test", "tool", True, {"title": "Test"})
        
        caps = capabilities.get_capabilities()
        caps.append({"id": "fake", "title": "Fake"})
        
        # Original data should be unchanged
        assert len(capabilities.data) == 1
        assert len(caps) == 2
    
    def test_get_capabilities_by_category(self):
        """Test filtering capabilities by category."""
        capabilities = SystemCapabilities()
        
        capabilities.add_capability("jira", "tool1", True, {"title": "Jira Tool"})
        capabilities.add_capability("confluence", "tool2", True, {"title": "Conf Tool"})
        capabilities.add_capability("jira", "tool3", True, {"title": "Jira Tool 2"})
        
        jira_caps = capabilities.get_capabilities(category="jira")
        confluence_caps = capabilities.get_capabilities(category="confluence")
        
        assert len(jira_caps) == 2
        assert len(confluence_caps) == 1
        assert jira_caps[0]['category'] == "jira"
        assert confluence_caps[0]['category'] == "confluence"
    
    def test_get_capabilities_nonexistent_category(self):
        """Test getting capabilities for nonexistent category returns empty list."""
        capabilities = SystemCapabilities()
        capabilities.add_capability("test", "tool", True, {"title": "Test"})
        
        result = capabilities.get_capabilities(category="nonexistent")
        
        assert isinstance(result, list)
        assert len(result) == 0


class TestGetCapabilityById:
    """Test getting specific capability by ID."""
    
    def test_get_existing_capability(self):
        """Test getting an existing capability by ID."""
        capabilities = SystemCapabilities()
        capabilities.add_capability("test", "tool", True, {"title": "Test Tool"})
        
        cap = capabilities.get_capability_by_id("test.tool")
        
        assert cap is not None
        assert cap['id'] == "test.tool"
        assert cap['title'] == "Test Tool"
    
    def test_get_nonexistent_capability(self):
        """Test getting nonexistent capability returns None."""
        capabilities = SystemCapabilities()
        capabilities.add_capability("test", "tool", True, {"title": "Test"})
        
        cap = capabilities.get_capability_by_id("nonexistent.id")
        
        assert cap is None
    
    def test_get_capability_returns_copy(self):
        """Test that get_capability_by_id returns a copy."""
        capabilities = SystemCapabilities()
        capabilities.add_capability("test", "tool", True, {"title": "Test"})
        
        cap = capabilities.get_capability_by_id("test.tool")
        cap['title'] = "Modified"
        
        # Original should be unchanged
        original = capabilities.get_capability_by_id("test.tool")
        assert original['title'] == "Test"


class TestGetCategories:
    """Test getting list of categories."""
    
    def test_get_categories_empty(self):
        """Test getting categories when no capabilities exist."""
        capabilities = SystemCapabilities()
        
        categories = capabilities.get_categories()
        
        assert isinstance(categories, list)
        assert len(categories) == 0
    
    def test_get_categories_single(self):
        """Test getting categories with single category."""
        capabilities = SystemCapabilities()
        capabilities.add_capability("test", "tool", True, {"title": "Test"})
        
        categories = capabilities.get_categories()
        
        assert len(categories) == 1
        assert "test" in categories
    
    def test_get_categories_multiple_unique(self):
        """Test getting unique categories."""
        capabilities = SystemCapabilities()
        capabilities.add_capability("cat1", "tool1", True, {"title": "Test 1"})
        capabilities.add_capability("cat2", "tool2", True, {"title": "Test 2"})
        capabilities.add_capability("cat1", "tool3", True, {"title": "Test 3"})
        
        categories = capabilities.get_categories()
        
        assert len(categories) == 2
        assert "cat1" in categories
        assert "cat2" in categories


class TestClearCapabilities:
    """Test clearing capabilities."""
    
    def test_clear_removes_all(self):
        """Test that clear removes all capabilities."""
        capabilities = SystemCapabilities()
        
        for i in range(5):
            capabilities.add_capability(f"cat{i}", f"tool{i}", True, {"title": f"Test {i}"})
        
        assert len(capabilities.data) == 5
        
        capabilities.clear()
        
        assert len(capabilities.data) == 0
    
    def test_clear_on_empty_list(self):
        """Test that clear works on empty list."""
        capabilities = SystemCapabilities()
        assert len(capabilities.data) == 0
        
        capabilities.clear()  # Should not raise
        
        assert len(capabilities.data) == 0


class TestGenerateTitle:
    """Test title generation helper."""
    
    def test_generate_title_simple(self):
        """Test generating title from simple name."""
        result = SystemCapabilities._generate_title("test_tool")
        assert result == "Test Tool"
    
    def test_generate_title_multiple_underscores(self):
        """Test generating title with multiple underscores."""
        result = SystemCapabilities._generate_title("read_python_docs")
        assert result == "Read Python Docs"
    
    def test_generate_title_single_word(self):
        """Test generating title from single word."""
        result = SystemCapabilities._generate_title("jira")
        assert result == "Jira"
    
    def test_generate_title_with_numbers(self):
        """Test generating title with numbers."""
        result = SystemCapabilities._generate_title("tool_v2_alpha")
        assert result == "Tool V2 Alpha"


class TestRepr:
    """Test string representation."""
    
    def test_repr_empty(self):
        """Test repr with no capabilities."""
        capabilities = SystemCapabilities()
        
        repr_str = repr(capabilities)
        
        assert "SystemCapabilities" in repr_str
        assert "capabilities=0" in repr_str
    
    def test_repr_with_capabilities(self):
        """Test repr with capabilities."""
        capabilities = SystemCapabilities()
        capabilities.add_capability("test", "tool1", True, {"title": "Test 1"})
        capabilities.add_capability("test", "tool2", True, {"title": "Test 2"})
        
        repr_str = repr(capabilities)
        
        assert "SystemCapabilities" in repr_str
        assert "capabilities=2" in repr_str


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
