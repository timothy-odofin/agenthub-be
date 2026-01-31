"""
Unit tests for ActionPreviewFormatter.

Tests cover:
- Generic formatting
- Custom formatter registration
- Built-in formatters (Jira, Email, GitHub)
- Edge cases and error handling
"""

import pytest
from datetime import datetime, timedelta

from src.app.core.confirmation.action_preview_formatter import (
    ActionPreviewFormatter,
    format_jira_issue_creation,
    format_jira_comment,
    format_email,
    format_github_issue_creation,
    get_default_formatter
)
from src.app.core.confirmation.pending_actions_store import PendingAction


class TestActionPreviewFormatter:
    """Tests for ActionPreviewFormatter class."""
    
    @pytest.fixture
    def formatter(self):
        """Create a fresh formatter for each test."""
        return ActionPreviewFormatter()
    
    @pytest.fixture
    def sample_action(self):
        """Create a sample pending action."""
        now = datetime.now()
        return PendingAction(
            action_id="action_test123",
            user_id="user_456",
            session_id="session_789",
            integration="jira",
            tool_name="create_jira_issue",
            action_type="create",
            risk_level="medium",
            parameters={
                "summary": "Test Issue",
                "project": "PROJ",
                "description": "This is a test issue"
            },
            created_at=now,
            expires_at=now + timedelta(minutes=10)
        )
    
    def test_formatter_initialization(self, formatter):
        """Test formatter initializes with empty registry."""
        assert formatter._custom_formatters == {}
    
    def test_register_custom_formatter(self, formatter):
        """Test registering a custom formatter."""
        def custom_format(params):
            return "Custom preview"
        
        formatter.register_formatter("jira", "create_issue", custom_format)
        
        assert "jira" in formatter._custom_formatters
        assert "create_issue" in formatter._custom_formatters["jira"]
        assert formatter._custom_formatters["jira"]["create_issue"] == custom_format
    
    def test_register_multiple_formatters(self, formatter):
        """Test registering multiple formatters for different integrations."""
        def jira_format(params):
            return "Jira preview"
        
        def email_format(params):
            return "Email preview"
        
        formatter.register_formatter("jira", "create_issue", jira_format)
        formatter.register_formatter("email", "send_email", email_format)
        
        assert len(formatter._custom_formatters) == 2
        assert "jira" in formatter._custom_formatters
        assert "email" in formatter._custom_formatters
    
    def test_format_with_custom_formatter(self, formatter, sample_action):
        """Test formatting uses custom formatter when registered."""
        def custom_format(params):
            return f"Custom: {params['summary']}"
        
        formatter.register_formatter("jira", "create_jira_issue", custom_format)
        
        result = formatter.format(sample_action)
        
        assert result == "Custom: Test Issue"
    
    def test_format_falls_back_to_generic(self, formatter, sample_action):
        """Test formatting falls back to generic when no custom formatter."""
        result = formatter.format(sample_action)
        
        # Should contain generic preview elements
        assert "Action Confirmation Required" in result
        assert "Test Issue" in result
        assert "PROJ" in result
        assert "create" in result.lower()
        assert "medium" in result.lower()
    
    def test_format_generic_includes_all_parameters(self, formatter):
        """Test generic formatter includes all parameters."""
        now = datetime.now()
        action = PendingAction(
            action_id="action_123",
            user_id="user_456",
            session_id="session_789",
            integration="custom",
            tool_name="custom_tool",
            action_type="create",
            risk_level="low",
            parameters={
                "param1": "value1",
                "param2": "value2",
                "param3": "value3"
            },
            created_at=now,
            expires_at=now + timedelta(minutes=10)
        )
        
        result = formatter.format(action)
        
        assert "param1" in result.lower() or "Param1" in result
        assert "value1" in result
        assert "param2" in result.lower() or "Param2" in result
        assert "value2" in result
        assert "param3" in result.lower() or "Param3" in result
        assert "value3" in result
    
    def test_humanize_tool_name(self, formatter):
        """Test tool name humanization."""
        assert formatter._humanize_tool_name("create_jira_issue") == "Create Jira Issue"
        assert formatter._humanize_tool_name("send_email") == "Send Email"
        assert formatter._humanize_tool_name("add_comment") == "Add Comment"
        assert formatter._humanize_tool_name("simple") == "Simple"
    
    def test_humanize_key(self, formatter):
        """Test parameter key humanization."""
        assert formatter._humanize_key("project_key") == "Project Key"
        assert formatter._humanize_key("issue_type") == "Issue Type"
        assert formatter._humanize_key("summary") == "Summary"
        assert formatter._humanize_key("simple") == "Simple"
    
    def test_format_value_string(self, formatter):
        """Test formatting string values."""
        result = formatter._format_value("test string")
        assert result == "test string"
    
    def test_format_value_dict(self, formatter):
        """Test formatting dict values."""
        result = formatter._format_value({"key1": "val1", "key2": "val2"})
        assert "key1: val1" in result
        assert "key2: val2" in result
    
    def test_format_value_list(self, formatter):
        """Test formatting list values."""
        result = formatter._format_value(["item1", "item2", "item3"])
        assert "item1" in result
        assert "item2" in result
        assert "item3" in result
    
    def test_format_value_truncation(self, formatter):
        """Test value truncation for long strings."""
        long_string = "a" * 250
        result = formatter._format_value(long_string, max_length=100)
        
        assert len(result) <= 100
        assert result.endswith("...")
    
    def test_format_risk_level(self, formatter):
        """Test risk level formatting with emojis."""
        assert "Low" in formatter._format_risk_level("low")
        assert "🟢" in formatter._format_risk_level("low")
        
        assert "Medium" in formatter._format_risk_level("medium")
        assert "🟡" in formatter._format_risk_level("medium")
        
        assert "High" in formatter._format_risk_level("high")
        assert "🔴" in formatter._format_risk_level("high")
    
    def test_format_risk_level_unknown(self, formatter):
        """Test risk level formatting with unknown value."""
        result = formatter._format_risk_level("critical")
        assert "Critical" in result
        assert "⚪️" in result
    
    def test_format_timestamp(self, formatter):
        """Test timestamp formatting."""
        dt = datetime(2026, 1, 11, 15, 30, 45)
        result = formatter._format_timestamp(dt)
        
        assert "2026-01-11" in result
        assert "15:30:45" in result
        assert "UTC" in result
    
    def test_custom_formatter_error_fallback(self, formatter, sample_action):
        """Test fallback to generic when custom formatter raises error."""
        def broken_formatter(params):
            raise ValueError("Intentional error")
        
        formatter.register_formatter("jira", "create_jira_issue", broken_formatter)
        
        result = formatter.format(sample_action)
        
        # Should fall back to generic format
        assert "Action Confirmation Required" in result
        assert "Test Issue" in result


class TestBuiltInFormatters:
    """Tests for built-in custom formatters."""
    
    def test_format_jira_issue_creation_basic(self):
        """Test basic Jira issue creation formatting."""
        params = {
            "summary": "Fix bug in login",
            "project": "PROJ",
            "issue_type": "Bug",
            "description": "User cannot login with SSO"
        }
        
        result = format_jira_issue_creation(params)
        
        assert "Create Jira Issue" in result
        assert "Fix bug in login" in result
        assert "PROJ" in result
        assert "Bug" in result
        assert "User cannot login with SSO" in result
    
    def test_format_jira_issue_creation_with_assignee(self):
        """Test Jira issue formatting with assignee."""
        params = {
            "summary": "Add new feature",
            "project": "FEAT",
            "assignee": "john.doe",
            "priority": "High"
        }
        
        result = format_jira_issue_creation(params)
        
        assert "john.doe" in result
        assert "High" in result
    
    def test_format_jira_issue_creation_truncates_description(self):
        """Test long descriptions are truncated."""
        params = {
            "summary": "Test",
            "project": "TEST",
            "description": "a" * 200
        }
        
        result = format_jira_issue_creation(params)
        
        assert "..." in result
        assert result.count("a") < 200
    
    def test_format_jira_comment_basic(self):
        """Test basic Jira comment formatting."""
        params = {
            "issue_key": "PROJ-123",
            "comment": "This looks good to me"
        }
        
        result = format_jira_comment(params)
        
        assert "Add Jira Comment" in result
        assert "PROJ-123" in result
        assert "This looks good to me" in result
    
    def test_format_jira_comment_with_body_key(self):
        """Test Jira comment formatting with 'body' key."""
        params = {
            "issue_key": "PROJ-456",
            "body": "Alternative comment text"
        }
        
        result = format_jira_comment(params)
        
        assert "PROJ-456" in result
        assert "Alternative comment text" in result
    
    def test_format_jira_comment_truncates_long_comment(self):
        """Test long comments are truncated."""
        params = {
            "issue_key": "PROJ-789",
            "comment": "x" * 250
        }
        
        result = format_jira_comment(params)
        
        assert "..." in result
        assert result.count("x") < 250
    
    def test_format_email_basic(self):
        """Test basic email formatting."""
        params = {
            "to": "user@example.com",
            "subject": "Meeting Tomorrow",
            "body": "Don't forget our meeting at 2pm"
        }
        
        result = format_email(params)
        
        assert "Send Email" in result
        assert "user@example.com" in result
        assert "Meeting Tomorrow" in result
        assert "Don't forget our meeting at 2pm" in result
    
    def test_format_email_with_cc(self):
        """Test email formatting with CC."""
        params = {
            "to": "user1@example.com",
            "cc": "user2@example.com",
            "subject": "Update",
            "body": "Here's the update"
        }
        
        result = format_email(params)
        
        assert "user1@example.com" in result
        assert "user2@example.com" in result
        assert "CC" in result
    
    def test_format_email_with_attachments(self):
        """Test email formatting with attachments."""
        params = {
            "to": "user@example.com",
            "subject": "Files",
            "body": "See attached",
            "attachments": ["file1.pdf", "file2.docx"]
        }
        
        result = format_email(params)
        
        assert "Attachments" in result
        assert "file1.pdf" in result
        assert "file2.docx" in result
    
    def test_format_email_truncates_long_body(self):
        """Test long email bodies are truncated."""
        params = {
            "to": "user@example.com",
            "subject": "Long message",
            "body": "y" * 200
        }
        
        result = format_email(params)
        
        assert "..." in result
        assert result.count("y") < 200
    
    def test_format_email_with_recipients_key(self):
        """Test email formatting with 'recipients' key."""
        params = {
            "recipients": "team@example.com",
            "subject": "Team Update",
            "message": "Updates for the team"
        }
        
        result = format_email(params)
        
        assert "team@example.com" in result
        assert "Updates for the team" in result
    
    def test_format_github_issue_creation_basic(self):
        """Test basic GitHub issue creation formatting."""
        params = {
            "title": "Add dark mode",
            "repo": "myorg/myrepo",
            "body": "Users have requested dark mode support"
        }
        
        result = format_github_issue_creation(params)
        
        assert "Create GitHub Issue" in result
        assert "Add dark mode" in result
        assert "myorg/myrepo" in result
        assert "Users have requested dark mode support" in result
    
    def test_format_github_issue_with_labels(self):
        """Test GitHub issue formatting with labels."""
        params = {
            "title": "Bug fix",
            "repo": "org/repo",
            "labels": ["bug", "high-priority"]
        }
        
        result = format_github_issue_creation(params)
        
        assert "bug" in result
        assert "high-priority" in result
        assert "Labels" in result
    
    def test_format_github_issue_with_assignees(self):
        """Test GitHub issue formatting with assignees."""
        params = {
            "title": "New feature",
            "repo": "org/repo",
            "assignees": ["alice", "bob"]
        }
        
        result = format_github_issue_creation(params)
        
        assert "alice" in result
        assert "bob" in result
        assert "Assignees" in result
    
    def test_format_github_issue_truncates_description(self):
        """Test long GitHub issue descriptions are truncated."""
        params = {
            "title": "Test",
            "repo": "test/test",
            "body": "z" * 200
        }
        
        result = format_github_issue_creation(params)
        
        assert "..." in result
        assert result.count("z") < 200
    
    def test_format_github_issue_with_repository_key(self):
        """Test GitHub issue formatting with 'repository' key."""
        params = {
            "title": "Issue",
            "repository": "owner/project",
            "description": "Issue description"
        }
        
        result = format_github_issue_creation(params)
        
        assert "owner/project" in result
        assert "Issue description" in result


class TestGetDefaultFormatter:
    """Tests for get_default_formatter function."""
    
    def test_get_default_formatter_returns_formatter(self):
        """Test get_default_formatter returns a formatter instance."""
        formatter = get_default_formatter()
        
        assert isinstance(formatter, ActionPreviewFormatter)
    
    def test_default_formatter_has_jira_formatters(self):
        """Test default formatter has Jira formatters registered."""
        formatter = get_default_formatter()
        
        assert "jira" in formatter._custom_formatters
        assert "create_jira_issue" in formatter._custom_formatters["jira"]
        assert "add_jira_comment" in formatter._custom_formatters["jira"]
    
    def test_default_formatter_has_email_formatter(self):
        """Test default formatter has email formatter registered."""
        formatter = get_default_formatter()
        
        assert "email" in formatter._custom_formatters
        assert "send_email" in formatter._custom_formatters["email"]
    
    def test_default_formatter_has_github_formatters(self):
        """Test default formatter has GitHub formatters registered."""
        formatter = get_default_formatter()
        
        assert "github" in formatter._custom_formatters
        assert "create_github_issue" in formatter._custom_formatters["github"]
    
    def test_default_formatter_works_with_jira_action(self):
        """Test default formatter works with Jira action."""
        formatter = get_default_formatter()
        
        now = datetime.now()
        action = PendingAction(
            action_id="action_123",
            user_id="user_456",
            session_id="session_789",
            integration="jira",
            tool_name="create_jira_issue",
            action_type="create",
            risk_level="medium",
            parameters={
                "summary": "Test Issue",
                "project": "PROJ"
            },
            created_at=now,
            expires_at=now + timedelta(minutes=10)
        )
        
        result = formatter.format(action)
        
        # Should use custom Jira formatter
        assert "Create Jira Issue" in result
        assert "Test Issue" in result
        assert "PROJ" in result
    
    def test_default_formatter_works_with_unknown_action(self):
        """Test default formatter falls back to generic for unknown actions."""
        formatter = get_default_formatter()
        
        now = datetime.now()
        action = PendingAction(
            action_id="action_123",
            user_id="user_456",
            session_id="session_789",
            integration="unknown",
            tool_name="unknown_tool",
            action_type="create",
            risk_level="low",
            parameters={"key": "value"},
            created_at=now,
            expires_at=now + timedelta(minutes=10)
        )
        
        result = formatter.format(action)
        
        # Should use generic formatter
        assert "Action Confirmation Required" in result
        assert "Unknown Tool" in result
