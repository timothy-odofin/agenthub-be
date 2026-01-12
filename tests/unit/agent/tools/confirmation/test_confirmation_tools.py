"""
Tests for confirmation agent tools.

Tests the agent-facing tools that wrap the confirmation service.
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock

from src.app.agent.tools.confirmation.confirmation_tools import (
    prepare_action,
    confirm_action,
    cancel_action,
    list_pending_actions,
    _get_confirmation_service,
)


@pytest.fixture(autouse=True)
def reset_service():
    """Reset the global service instance before each test."""
    import src.app.agent.tools.confirmation.confirmation_tools as tools_module
    tools_module._confirmation_service = None
    yield
    tools_module._confirmation_service = None


@pytest.fixture
def mock_service():
    """Create a mock confirmation service."""
    service = Mock()
    return service


@pytest.fixture
def sample_tool_args():
    """Sample tool arguments for Jira issue creation."""
    return {
        "project": "PROJ",
        "summary": "Test Issue",
        "description": "This is a test issue",
        "issue_type": "Bug",
    }


class TestGetConfirmationService:
    """Tests for the _get_confirmation_service singleton."""
    
    def test_creates_service_on_first_call(self):
        """Test that service is created on first call."""
        service = _get_confirmation_service()
        assert service is not None
        assert hasattr(service, 'prepare_action')
    
    def test_returns_same_instance(self):
        """Test that same instance is returned on multiple calls."""
        service1 = _get_confirmation_service()
        service2 = _get_confirmation_service()
        assert service1 is service2


class TestPrepareActionTool:
    """Tests for prepare_action tool."""
    
    def test_successful_prepare(self, sample_tool_args):
        """Test successful action preparation."""
        # Mock the service to return a successful result
        with patch('src.app.agent.tools.confirmation.confirmation_tools._get_confirmation_service') as mock_get_service:
            mock_service = Mock()
            mock_service.prepare_action.return_value = {
                "action_id": "action_123",
                "preview": "Will create Jira issue in PROJ",
                "expires_at": "2024-01-01T12:00:00",
            }
            mock_get_service.return_value = mock_service
            
            result = prepare_action.invoke({
                "tool_name": "create_jira_issue",
                "tool_args": sample_tool_args,
                "risk_level": "medium",
                "user_id": "user_123",
                "session_id": "session_456",
            })
            
            assert result["status"] == "success"
            assert result["action_id"] == "action_123"
            assert "preview" in result
            assert "expires_at" in result
            assert "confirm_action" in result["message"]
    
    def test_prepare_without_session_id(self, sample_tool_args):
        """Test prepare without session ID."""
        with patch('src.app.agent.tools.confirmation.confirmation_tools._get_confirmation_service') as mock_get_service:
            mock_service = Mock()
            mock_service.prepare_action.return_value = {
                "action_id": "action_123",
                "preview": "Will create Jira issue",
                "expires_at": "2024-01-01T12:00:00",
            }
            mock_get_service.return_value = mock_service
            
            result = prepare_action.invoke({
                "tool_name": "create_jira_issue",
                "tool_args": sample_tool_args,
                "risk_level": "low",
                "user_id": "user_123",
            })
            
            assert result["status"] == "success"
            # Verify service was called with None for session_id
            call_args = mock_service.prepare_action.call_args
            assert call_args[1]["session_id"] is None
    
    def test_prepare_with_different_risk_levels(self, sample_tool_args):
        """Test prepare with different risk levels."""
        with patch('src.app.agent.tools.confirmation.confirmation_tools._get_confirmation_service') as mock_get_service:
            mock_service = Mock()
            mock_service.prepare_action.return_value = {
                "action_id": "action_123",
                "preview": "Preview",
                "expires_at": "2024-01-01T12:00:00",
            }
            mock_get_service.return_value = mock_service
            
            for risk_level in ["low", "medium", "high"]:
                result = prepare_action.invoke({
                    "tool_name": "create_jira_issue",
                    "tool_args": sample_tool_args,
                    "risk_level": risk_level,
                    "user_id": "user_123",
                })
                
                assert result["status"] == "success"
                call_args = mock_service.prepare_action.call_args
                assert call_args[1]["risk_level"] == risk_level
    
    def test_prepare_value_error(self, sample_tool_args):
        """Test prepare with ValueError from service."""
        with patch('src.app.agent.tools.confirmation.confirmation_tools._get_confirmation_service') as mock_get_service:
            mock_service = Mock()
            mock_service.prepare_action.side_effect = ValueError("Invalid tool_args")
            mock_get_service.return_value = mock_service
            
            result = prepare_action.invoke({
                "tool_name": "create_jira_issue",
                "tool_args": sample_tool_args,
                "risk_level": "medium",
                "user_id": "user_123",
            })
            
            assert result["status"] == "error"
            assert "Invalid tool_args" in result["message"]
    
    def test_prepare_unexpected_error(self, sample_tool_args):
        """Test prepare with unexpected error from service."""
        with patch('src.app.agent.tools.confirmation.confirmation_tools._get_confirmation_service') as mock_get_service:
            mock_service = Mock()
            mock_service.prepare_action.side_effect = RuntimeError("Unexpected error")
            mock_get_service.return_value = mock_service
            
            result = prepare_action.invoke({
                "tool_name": "create_jira_issue",
                "tool_args": sample_tool_args,
                "risk_level": "medium",
                "user_id": "user_123",
            })
            
            assert result["status"] == "error"
            assert "Unexpected error" in result["message"]


class TestConfirmActionTool:
    """Tests for confirm_action tool."""
    
    def test_successful_confirm(self):
        """Test successful action confirmation."""
        with patch('src.app.agent.tools.confirmation.confirmation_tools._get_confirmation_service') as mock_get_service:
            mock_service = Mock()
            mock_service.confirm_action.return_value = {
                "result": {"issue_key": "PROJ-123", "status": "created"},
            }
            mock_get_service.return_value = mock_service
            
            result = confirm_action.invoke({
                "action_id": "action_123",
                "user_id": "user_123",
            })
            
            assert result["status"] == "success"
            assert "result" in result
            assert result["result"]["issue_key"] == "PROJ-123"
            assert "executed successfully" in result["message"]
    
    def test_confirm_permission_error(self):
        """Test confirm with permission error."""
        with patch('src.app.agent.tools.confirmation.confirmation_tools._get_confirmation_service') as mock_get_service:
            mock_service = Mock()
            mock_service.confirm_action.side_effect = PermissionError("User mismatch")
            mock_get_service.return_value = mock_service
            
            result = confirm_action.invoke({
                "action_id": "action_123",
                "user_id": "user_456",
            })
            
            assert result["status"] == "error"
            assert result["error"] == "permission_denied"
            assert "User mismatch" in result["message"]
    
    def test_confirm_value_error(self):
        """Test confirm with value error (action not found or expired)."""
        with patch('src.app.agent.tools.confirmation.confirmation_tools._get_confirmation_service') as mock_get_service:
            mock_service = Mock()
            mock_service.confirm_action.side_effect = ValueError("Action not found")
            mock_get_service.return_value = mock_service
            
            result = confirm_action.invoke({
                "action_id": "action_nonexistent",
                "user_id": "user_123",
            })
            
            assert result["status"] == "error"
            assert result["error"] == "invalid_action"
            assert "Action not found" in result["message"]
    
    def test_confirm_execution_error(self):
        """Test confirm with execution error."""
        with patch('src.app.agent.tools.confirmation.confirmation_tools._get_confirmation_service') as mock_get_service:
            mock_service = Mock()
            mock_service.confirm_action.side_effect = RuntimeError("Execution failed")
            mock_get_service.return_value = mock_service
            
            result = confirm_action.invoke({
                "action_id": "action_123",
                "user_id": "user_123",
            })
            
            assert result["status"] == "error"
            assert result["error"] == "execution_failed"
            assert "Execution failed" in result["message"]


class TestCancelActionTool:
    """Tests for cancel_action tool."""
    
    def test_successful_cancel(self):
        """Test successful action cancellation."""
        with patch('src.app.agent.tools.confirmation.confirmation_tools._get_confirmation_service') as mock_get_service:
            mock_service = Mock()
            mock_service.cancel_action.return_value = None
            mock_get_service.return_value = mock_service
            
            result = cancel_action.invoke({
                "action_id": "action_123",
                "user_id": "user_123",
            })
            
            assert result["status"] == "success"
            assert "cancelled successfully" in result["message"]
            assert "action_123" in result["message"]
    
    def test_cancel_permission_error(self):
        """Test cancel with permission error."""
        with patch('src.app.agent.tools.confirmation.confirmation_tools._get_confirmation_service') as mock_get_service:
            mock_service = Mock()
            mock_service.cancel_action.side_effect = PermissionError("User mismatch")
            mock_get_service.return_value = mock_service
            
            result = cancel_action.invoke({
                "action_id": "action_123",
                "user_id": "user_456",
            })
            
            assert result["status"] == "error"
            assert result["error"] == "permission_denied"
            assert "User mismatch" in result["message"]
    
    def test_cancel_value_error(self):
        """Test cancel with value error (action not found)."""
        with patch('src.app.agent.tools.confirmation.confirmation_tools._get_confirmation_service') as mock_get_service:
            mock_service = Mock()
            mock_service.cancel_action.side_effect = ValueError("Action not found")
            mock_get_service.return_value = mock_service
            
            result = cancel_action.invoke({
                "action_id": "action_nonexistent",
                "user_id": "user_123",
            })
            
            assert result["status"] == "error"
            assert result["error"] == "invalid_action"
            assert "Action not found" in result["message"]


class TestListPendingActionsTool:
    """Tests for list_pending_actions tool."""
    
    def test_list_with_actions(self):
        """Test list with pending actions."""
        with patch('src.app.agent.tools.confirmation.confirmation_tools._get_confirmation_service') as mock_get_service:
            mock_service = Mock()
            mock_service.list_pending_actions.return_value = [
                {
                    "action_id": "action_123",
                    "tool_name": "create_jira_issue",
                    "preview": "Will create issue in PROJ",
                },
                {
                    "action_id": "action_456",
                    "tool_name": "send_email",
                    "preview": "Will send email to user@example.com",
                },
            ]
            mock_get_service.return_value = mock_service
            
            result = list_pending_actions.invoke({
                "user_id": "user_123",
            })
            
            assert result["status"] == "success"
            assert result["count"] == 2
            assert len(result["actions"]) == 2
            assert "2 pending action(s)" in result["message"]
    
    def test_list_empty(self):
        """Test list with no pending actions."""
        with patch('src.app.agent.tools.confirmation.confirmation_tools._get_confirmation_service') as mock_get_service:
            mock_service = Mock()
            mock_service.list_pending_actions.return_value = []
            mock_get_service.return_value = mock_service
            
            result = list_pending_actions.invoke({
                "user_id": "user_123",
            })
            
            assert result["status"] == "success"
            assert result["count"] == 0
            assert len(result["actions"]) == 0
    
    def test_list_with_session_filter(self):
        """Test list with session ID filter."""
        with patch('src.app.agent.tools.confirmation.confirmation_tools._get_confirmation_service') as mock_get_service:
            mock_service = Mock()
            mock_service.list_pending_actions.return_value = [
                {
                    "action_id": "action_123",
                    "tool_name": "create_jira_issue",
                },
            ]
            mock_get_service.return_value = mock_service
            
            result = list_pending_actions.invoke({
                "user_id": "user_123",
                "session_id": "session_456",
            })
            
            assert result["status"] == "success"
            # Verify service was called with session_id
            call_args = mock_service.list_pending_actions.call_args
            assert call_args[1]["session_id"] == "session_456"
    
    def test_list_error(self):
        """Test list with error from service."""
        with patch('src.app.agent.tools.confirmation.confirmation_tools._get_confirmation_service') as mock_get_service:
            mock_service = Mock()
            mock_service.list_pending_actions.side_effect = RuntimeError("Database error")
            mock_get_service.return_value = mock_service
            
            result = list_pending_actions.invoke({
                "user_id": "user_123",
            })
            
            assert result["status"] == "error"
            assert "Database error" in result["message"]


class TestToolIntegration:
    """Integration tests for tool workflow."""
    
    def test_prepare_confirm_workflow(self):
        """Test complete prepare -> confirm workflow."""
        with patch('src.app.agent.tools.confirmation.confirmation_tools._get_confirmation_service') as mock_get_service:
            mock_service = Mock()
            
            # Mock prepare
            mock_service.prepare_action.return_value = {
                "action_id": "action_123",
                "preview": "Will create Jira issue",
                "expires_at": "2024-01-01T12:00:00",
            }
            
            # Mock confirm
            mock_service.confirm_action.return_value = {
                "result": {"issue_key": "PROJ-123"},
            }
            
            mock_get_service.return_value = mock_service
            
            # Step 1: Prepare
            prep_result = prepare_action.invoke({
                "tool_name": "create_jira_issue",
                "tool_args": {"project": "PROJ", "summary": "Test"},
                "risk_level": "medium",
                "user_id": "user_123",
            })
            
            assert prep_result["status"] == "success"
            action_id = prep_result["action_id"]
            
            # Step 2: Confirm
            confirm_result = confirm_action.invoke({
                "action_id": action_id,
                "user_id": "user_123",
            })
            
            assert confirm_result["status"] == "success"
            assert confirm_result["result"]["issue_key"] == "PROJ-123"
    
    def test_prepare_cancel_workflow(self):
        """Test complete prepare -> cancel workflow."""
        with patch('src.app.agent.tools.confirmation.confirmation_tools._get_confirmation_service') as mock_get_service:
            mock_service = Mock()
            
            # Mock prepare
            mock_service.prepare_action.return_value = {
                "action_id": "action_123",
                "preview": "Will create Jira issue",
                "expires_at": "2024-01-01T12:00:00",
            }
            
            # Mock cancel
            mock_service.cancel_action.return_value = None
            
            mock_get_service.return_value = mock_service
            
            # Step 1: Prepare
            prep_result = prepare_action.invoke({
                "tool_name": "create_jira_issue",
                "tool_args": {"project": "PROJ", "summary": "Test"},
                "risk_level": "medium",
                "user_id": "user_123",
            })
            
            assert prep_result["status"] == "success"
            action_id = prep_result["action_id"]
            
            # Step 2: Cancel
            cancel_result = cancel_action.invoke({
                "action_id": action_id,
                "user_id": "user_123",
            })
            
            assert cancel_result["status"] == "success"
            assert "cancelled" in cancel_result["message"]
