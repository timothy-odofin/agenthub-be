"""
Unit tests for capability-aware message enhancement in ChatService.

Tests the intelligent conversation flow when users select capabilities.
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock

from app.services.chat_service import ChatService
from app.core.capabilities import SystemCapabilities


@pytest.fixture(autouse=True)
def clear_capabilities():
    """Clear capabilities before and after each test."""
    SystemCapabilities().clear()
    yield
    SystemCapabilities().clear()


@pytest.fixture
def mock_jira_capability():
    """Create a mock Jira capability."""
    capabilities = SystemCapabilities()
    capabilities.add_capability(
        category="jira",
        name="jira",
        enabled=True,
        display_config={
            "title": "Jira Integration",
            "description": "Search, create, and manage Jira issues and projects",
            "icon": "jira",
            "example_prompts": [
                "Search for open bugs in project ABC",
                "Create a new task for implementing feature X",
                "What are my assigned issues?",
                "Add a comment to issue KEY-123"
            ],
            "tags": ["project-management", "issue-tracking", "collaboration"]
        }
    )
    return capabilities


class TestCapabilityMessageEnhancement:
    """Test message enhancement for capability selections."""
    
    def test_enhance_capability_message_with_valid_capability(self, mock_jira_capability):
        """Test enhancement with valid capability metadata."""
        chat_service = ChatService()
        
        message = "I want to use Jira"
        metadata = {
            "capability_id": "jira.jira",
            "is_capability_selection": True
        }
        
        enhanced = chat_service._enhance_capability_message(message, metadata)
        
        # Verify enhancement contains key elements
        assert "Jira Integration" in enhanced
        assert "Search, create, and manage Jira issues" in enhanced
        assert "Search for open bugs in project ABC" in enhanced
        assert "**User's Message:**" in enhanced
        assert "I want to use Jira" in enhanced
        assert "Capability Selection Context" in enhanced
        assert "Your Task" in enhanced
        assert "project-management" in enhanced
    
    def test_enhance_capability_message_missing_capability_id(self):
        """Test enhancement when capability_id is missing."""
        chat_service = ChatService()
        
        message = "I want to use Jira"
        metadata = {
            "is_capability_selection": True
            # Missing capability_id
        }
        
        enhanced = chat_service._enhance_capability_message(message, metadata)
        
        # Should return original message
        assert enhanced == message
    
    def test_enhance_capability_message_nonexistent_capability(self):
        """Test enhancement when capability doesn't exist."""
        chat_service = ChatService()
        
        message = "Test message"
        metadata = {
            "capability_id": "nonexistent.tool",
            "is_capability_selection": True
        }
        
        enhanced = chat_service._enhance_capability_message(message, metadata)
        
        # Should return original message
        assert enhanced == message
    
    def test_enhance_capability_message_with_minimal_capability(self):
        """Test enhancement with capability having minimal metadata."""
        capabilities = SystemCapabilities()
        capabilities.add_capability(
            category="test",
            name="basic_tool",
            enabled=True,
            display_config={
                "title": "Basic Tool",
                "description": "A basic tool"
                # No example_prompts or tags
            }
        )
        
        chat_service = ChatService()
        
        message = "Test"
        metadata = {
            "capability_id": "test.basic_tool",
            "is_capability_selection": True
        }
        
        enhanced = chat_service._enhance_capability_message(message, metadata)
        
        # Should still work with minimal data
        assert "Basic Tool" in enhanced
        assert "A basic tool" in enhanced
        assert "**User's Message:**" in enhanced
        assert "Test" in enhanced
        # Should not have example prompts section
        assert "Available Actions:" not in enhanced
    
    def test_enhance_capability_message_with_empty_message(self, mock_jira_capability):
        """Test enhancement with empty user message."""
        chat_service = ChatService()
        
        message = ""
        metadata = {
            "capability_id": "jira.jira",
            "is_capability_selection": True
        }
        
        enhanced = chat_service._enhance_capability_message(message, metadata)
        
        # Should still enhance even with empty message
        assert "Jira Integration" in enhanced
        assert "**User's Message:**" in enhanced


class TestCapabilitySelectionInChat:
    """Test capability selection handling in chat flow."""
    
    @pytest.mark.asyncio
    async def test_chat_with_capability_selection_metadata(self, mock_jira_capability):
        """Test that chat method enhances message when capability is selected."""
        chat_service = ChatService()
        
        # Mock the agent
        mock_agent = Mock()
        mock_response = Mock()
        mock_response.success = True
        mock_response.content = "I can help you with Jira! What would you like to do?"
        mock_response.session_id = "test-session"
        mock_response.timestamp = Mock()
        mock_response.timestamp.isoformat.return_value = "2026-01-13T00:00:00"
        mock_response.processing_time_ms = 100.0
        mock_response.tools_used = []
        mock_response.errors = []
        mock_response.metadata = {}
        
        mock_agent.execute = AsyncMock(return_value=mock_response)
        chat_service._agent = mock_agent
        
        # Call chat with capability selection metadata
        metadata = {
            "capability_id": "jira.jira",
            "is_capability_selection": True
        }
        
        result = await chat_service.chat(
            message="I want to use Jira",
            user_id="test-user",
            session_id="test-session",
            metadata=metadata
        )
        
        # Verify agent.execute was called with enhanced message
        call_args = mock_agent.execute.call_args
        enhanced_message = call_args[0][0]
        
        assert "Jira Integration" in enhanced_message
        assert "Capability Selection Context" in enhanced_message
        assert result["success"] is True
    
    @pytest.mark.asyncio
    async def test_chat_without_capability_selection(self):
        """Test that regular chat messages are not enhanced."""
        chat_service = ChatService()
        
        # Mock the agent
        mock_agent = Mock()
        mock_response = Mock()
        mock_response.success = True
        mock_response.content = "Regular response"
        mock_response.session_id = "test-session"
        mock_response.timestamp = Mock()
        mock_response.timestamp.isoformat.return_value = "2026-01-13T00:00:00"
        mock_response.processing_time_ms = 100.0
        mock_response.tools_used = []
        mock_response.errors = []
        mock_response.metadata = {}
        
        mock_agent.execute = AsyncMock(return_value=mock_response)
        chat_service._agent = mock_agent
        
        # Call chat WITHOUT capability metadata
        result = await chat_service.chat(
            message="What is the weather?",
            user_id="test-user",
            session_id="test-session",
            metadata=None  # No metadata
        )
        
        # Verify agent.execute was called with original message
        call_args = mock_agent.execute.call_args
        message = call_args[0][0]
        
        assert message == "What is the weather?"
        assert "Capability Selection Context" not in message
        assert result["success"] is True


class TestEnhancementFormat:
    """Test the format and structure of enhanced messages."""
    
    def test_enhancement_includes_all_sections(self, mock_jira_capability):
        """Test that enhancement includes all expected sections."""
        chat_service = ChatService()
        
        message = "Help with Jira"
        metadata = {
            "capability_id": "jira.jira",
            "is_capability_selection": True
        }
        
        enhanced = chat_service._enhance_capability_message(message, metadata)
        
        # Check all expected sections are present
        expected_sections = [
            "## Capability Selection Context",
            "**Capability Description:**",
            "**Available Actions:**",
            "**Related Topics:**",
            "**User's Message:**",
            "## Your Task",
            "**Respond by:**"
        ]
        
        for section in expected_sections:
            assert section in enhanced, f"Missing section: {section}"
    
    def test_enhancement_preserves_markdown_format(self, mock_jira_capability):
        """Test that enhancement uses proper markdown formatting."""
        chat_service = ChatService()
        
        message = "Test"
        metadata = {
            "capability_id": "jira.jira",
            "is_capability_selection": True
        }
        
        enhanced = chat_service._enhance_capability_message(message, metadata)
        
        # Check markdown formatting
        assert "##" in enhanced  # Headers
        assert "**" in enhanced  # Bold text
        assert "\n" in enhanced  # Newlines
        assert "- " in enhanced  # Bullet points (from example prompts)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
