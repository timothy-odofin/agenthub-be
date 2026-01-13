"""
Integration tests for the complete confirmation workflow.

These tests verify the end-to-end flow of the confirmation system,
including the interaction between tools, service, formatter, and store.
"""

import pytest
from datetime import datetime, timedelta
from time import sleep

from app.core.confirmation import (
    PendingActionsStore,
    ActionPreviewFormatter,
    get_default_formatter,
    ConfirmationService,
)
from app.agent.tools.confirmation.confirmation_tools import (
    prepare_action,
    confirm_action,
    cancel_action,
    list_pending_actions,
)


@pytest.fixture
def integration_store():
    """Create a fresh store for integration tests."""
    return PendingActionsStore(ttl_minutes=1)


@pytest.fixture
def integration_formatter():
    """Create a formatter with default formatters."""
    return get_default_formatter()


@pytest.fixture
def integration_service(integration_store, integration_formatter):
    """Create a confirmation service for integration tests."""
    return ConfirmationService(
        store=integration_store,
        formatter=integration_formatter
    )


class TestJiraIssueCreationWorkflow:
    """
    Integration test for Jira issue creation with confirmation.
    
    Simulates the complete workflow:
    1. Agent prepares action
    2. User reviews preview
    3. User confirms
    4. Action executes
    """
    
    def test_successful_jira_issue_creation(self, integration_service):
        """Test complete workflow for Jira issue creation."""
        jira_response = {"issue_key": "PROJ-123", "status": "created"}
        
        def mock_create_jira_issue(parameters):
            return jira_response
        
        tool_args = {
            "project": "PROJ",
            "summary": "Login page crashes on mobile Safari",
            "description": "Users report crashes when accessing login page",
            "issue_type": "Bug"
        }
        
        prep_result = integration_service.prepare_action(
            user_id="user_alice",
            session_id="session_123",
            integration="jira",
            tool_name="create_jira_issue",
            action_type="create",
            risk_level="medium",
            parameters=tool_args,
            executor_func=mock_create_jira_issue
        )
        
        assert "action_id" in prep_result
        assert "preview" in prep_result
        assert "Create Jira Issue" in prep_result["preview"]
        
        action_id = prep_result["action_id"]
        
        action_details = integration_service.get_action_details(
            action_id=action_id,
            user_id="user_alice"
        )
        assert action_details is not None
        
        confirm_result = integration_service.confirm_action(
            action_id=action_id,
            user_id="user_alice"
        )
        
        assert confirm_result == jira_response
