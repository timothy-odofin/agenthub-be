"""
Unit tests for Agent Models (AgentContext, AgentResponse, ToolResult).

Tests the data models used for agent communication and state management.
Following Python open-source testing best practices.
"""

import pytest
from datetime import datetime, timedelta
from typing import Dict, Any, List
from unittest.mock import Mock

from app.agent.models.agent_models import AgentContext, AgentResponse, ToolResult
from app.core.enums import AgentStatus


class TestAgentContext:
    """Test suite for AgentContext dataclass."""
    
    def test_minimal_initialization(self):
        """Test AgentContext initialization with only required fields."""
        # Act
        context = AgentContext(user_id="test_user")
        
        # Assert
        assert context.user_id == "test_user"
        assert context.session_id is None
        assert context.request_id is None
        assert context.metadata == {}
        assert context.requires_approval is False
        assert context.approval_callback is None
        assert context.timeout_seconds is None
        assert context.max_iterations == 10
        assert context.tools_allowed is None
        assert context.tools_denied is None
    
    def test_full_initialization(self):
        """Test AgentContext initialization with all fields provided."""
        # Arrange
        approval_callback = Mock()
        metadata = {"key1": "value1", "key2": "value2"}
        tools_allowed = ["tool1", "tool2"]
        tools_denied = ["tool3"]
        
        # Act
        context = AgentContext(
            user_id="test_user",
            session_id="test_session",
            request_id="test_request",
            metadata=metadata,
            requires_approval=True,
            approval_callback=approval_callback,
            timeout_seconds=30,
            max_iterations=15,
            tools_allowed=tools_allowed,
            tools_denied=tools_denied
        )
        
        # Assert
        assert context.user_id == "test_user"
        assert context.session_id == "test_session"
        assert context.request_id == "test_request"
        assert context.metadata == metadata
        assert context.requires_approval is True
        assert context.approval_callback == approval_callback
        assert context.timeout_seconds == 30
        assert context.max_iterations == 15
        assert context.tools_allowed == tools_allowed
        assert context.tools_denied == tools_denied
    
    def test_default_factory_creates_new_dict(self):
        """Test that metadata field creates new dict instances for each object."""
        # Act
        context1 = AgentContext(user_id="user1")
        context2 = AgentContext(user_id="user2")
        
        # Modify one metadata dict
        context1.metadata["key"] = "value"
        
        # Assert
        assert context1.metadata != context2.metadata
        assert "key" not in context2.metadata
        assert context1.metadata == {"key": "value"}
        assert context2.metadata == {}
    
    def test_mutable_lists_are_independent(self):
        """Test that tools_allowed and tools_denied lists are independent."""
        # Act
        tools_list = ["tool1", "tool2"]
        context1 = AgentContext(user_id="user1", tools_allowed=tools_list)
        context2 = AgentContext(user_id="user2", tools_allowed=tools_list.copy())
        
        # Modify one list
        context1.tools_allowed.append("tool3")
        
        # Assert
        assert len(context1.tools_allowed) == 3
        assert len(context2.tools_allowed) == 2
        assert "tool3" in context1.tools_allowed
        assert "tool3" not in context2.tools_allowed
    
    @pytest.mark.parametrize("user_id", ["", "user123", "user@example.com", "user_with_underscores"])
    def test_various_user_id_formats(self, user_id):
        """Test AgentContext with various user ID formats."""
        # Act
        context = AgentContext(user_id=user_id)
        
        # Assert
        assert context.user_id == user_id
    
    @pytest.mark.parametrize("max_iterations", [1, 5, 10, 100, 0])
    def test_max_iterations_values(self, max_iterations):
        """Test AgentContext with different max_iterations values."""
        # Act
        context = AgentContext(user_id="test", max_iterations=max_iterations)
        
        # Assert
        assert context.max_iterations == max_iterations
    
    def test_approval_callback_is_callable(self):
        """Test that approval_callback can be a callable."""
        # Arrange
        def test_callback():
            return "approved"
        
        # Act
        context = AgentContext(
            user_id="test",
            approval_callback=test_callback
        )
        
        # Assert
        assert callable(context.approval_callback)
        assert context.approval_callback() == "approved"


class TestAgentResponse:
    """Test suite for AgentResponse dataclass."""
    
    def test_minimal_initialization(self):
        """Test AgentResponse initialization with only required fields."""
        # Act
        response = AgentResponse(
            content="Test response",
            status=AgentStatus.COMPLETED
        )
        
        # Assert
        assert response.content == "Test response"
        assert response.status == AgentStatus.COMPLETED
        assert response.session_id is None
        assert response.request_id is None
        assert response.metadata == {}
        assert response.tools_used == []
        assert response.processing_time_ms == 0
        assert response.token_usage == {}
        assert response.errors == []
        assert isinstance(response.timestamp, datetime)
    
    def test_full_initialization(self):
        """Test AgentResponse initialization with all fields provided."""
        # Arrange
        metadata = {"model": "gpt-4", "temperature": 0.7}
        tools_used = ["search", "calculator"]
        token_usage = {"prompt_tokens": 100, "completion_tokens": 50}
        errors = ["Warning: Tool timeout"]
        timestamp = datetime(2023, 1, 1, 12, 0, 0)
        
        # Act
        response = AgentResponse(
            content="Full response",
            status=AgentStatus.ERROR,
            session_id="session123",
            request_id="request456",
            metadata=metadata,
            tools_used=tools_used,
            processing_time_ms=1500.5,
            token_usage=token_usage,
            errors=errors,
            timestamp=timestamp
        )
        
        # Assert
        assert response.content == "Full response"
        assert response.status == AgentStatus.ERROR
        assert response.session_id == "session123"
        assert response.request_id == "request456"
        assert response.metadata == metadata
        assert response.tools_used == tools_used
        assert response.processing_time_ms == 1500.5
        assert response.token_usage == token_usage
        assert response.errors == errors
        assert response.timestamp == timestamp
    
    def test_success_property_true_for_completed(self):
        """Test that success property returns True for successful statuses."""
        # Arrange & Act
        successful_statuses = [
            AgentStatus.COMPLETED,
            AgentStatus.IDLE,
            AgentStatus.PROCESSING,
            AgentStatus.WAITING_APPROVAL,
            AgentStatus.WAITING_INPUT
        ]
        
        for status in successful_statuses:
            response = AgentResponse(content="test", status=status)
            # Assert
            assert response.success is True, f"Status {status} should be considered successful"
    
    def test_success_property_false_for_failures(self):
        """Test that success property returns False for failure statuses."""
        # Arrange & Act
        failure_statuses = [AgentStatus.ERROR, AgentStatus.CANCELLED]
        
        for status in failure_statuses:
            response = AgentResponse(content="test", status=status)
            # Assert
            assert response.success is False, f"Status {status} should be considered failure"
    
    def test_timestamp_default_is_recent(self):
        """Test that default timestamp is close to current time."""
        # Arrange
        before_creation = datetime.now()
        
        # Act
        response = AgentResponse(content="test", status=AgentStatus.COMPLETED)
        after_creation = datetime.now()
        
        # Assert
        assert before_creation <= response.timestamp <= after_creation
    
    def test_default_factory_creates_new_collections(self):
        """Test that default factories create new collection instances."""
        # Act
        response1 = AgentResponse(content="test1", status=AgentStatus.COMPLETED)
        response2 = AgentResponse(content="test2", status=AgentStatus.COMPLETED)
        
        # Modify collections in response1
        response1.metadata["key"] = "value"
        response1.tools_used.append("tool1")
        response1.token_usage["tokens"] = 100
        response1.errors.append("error1")
        
        # Assert collections are independent
        assert response1.metadata != response2.metadata
        assert response1.tools_used != response2.tools_used
        assert response1.token_usage != response2.token_usage
        assert response1.errors != response2.errors
        
        # Verify response2 collections are still empty
        assert response2.metadata == {}
        assert response2.tools_used == []
        assert response2.token_usage == {}
        assert response2.errors == []
    
    @pytest.mark.parametrize("status", list(AgentStatus))
    def test_all_agent_statuses(self, status):
        """Test AgentResponse with all possible AgentStatus values."""
        # Act
        response = AgentResponse(content="test", status=status)
        
        # Assert
        assert response.status == status
        # Test success property logic for all statuses
        expected_success = status not in [AgentStatus.ERROR, AgentStatus.CANCELLED]
        assert response.success == expected_success
    
    def test_empty_content_allowed(self):
        """Test that empty content is allowed."""
        # Act
        response = AgentResponse(content="", status=AgentStatus.COMPLETED)
        
        # Assert
        assert response.content == ""
        assert response.success is True


class TestToolResult:
    """Test suite for ToolResult dataclass."""
    
    def test_minimal_initialization(self):
        """Test ToolResult initialization with only required fields."""
        # Act
        result = ToolResult(
            tool_name="test_tool",
            success=True,
            result="Tool output"
        )
        
        # Assert
        assert result.tool_name == "test_tool"
        assert result.success is True
        assert result.result == "Tool output"
        assert result.error_message is None
        assert result.execution_time_ms == 0
        assert result.metadata == {}
    
    def test_full_initialization(self):
        """Test ToolResult initialization with all fields provided."""
        # Arrange
        metadata = {"version": "1.0", "source": "external"}
        
        # Act
        result = ToolResult(
            tool_name="advanced_tool",
            success=False,
            result=None,
            error_message="Tool execution failed",
            execution_time_ms=250.7,
            metadata=metadata
        )
        
        # Assert
        assert result.tool_name == "advanced_tool"
        assert result.success is False
        assert result.result is None
        assert result.error_message == "Tool execution failed"
        assert result.execution_time_ms == 250.7
        assert result.metadata == metadata
    
    def test_success_true_cases(self):
        """Test ToolResult with various successful scenarios."""
        # Test cases: (result_value, description)
        success_cases = [
            ("string result", "string result"),
            ({"key": "value"}, "dictionary result"),
            ([1, 2, 3], "list result"),
            (42, "integer result"),
            (True, "boolean result"),
            (None, "None result (valid for some tools)")
        ]
        
        for result_value, description in success_cases:
            # Act
            tool_result = ToolResult(
                tool_name="test_tool",
                success=True,
                result=result_value
            )
            
            # Assert
            assert tool_result.success is True, f"Failed for {description}"
            assert tool_result.result == result_value, f"Failed for {description}"
            assert tool_result.error_message is None, f"Failed for {description}"
    
    def test_failure_cases(self):
        """Test ToolResult with various failure scenarios."""
        # Arrange
        error_messages = [
            "Connection timeout",
            "Invalid input parameters",
            "Permission denied",
            "Tool not found"
        ]
        
        for error_msg in error_messages:
            # Act
            tool_result = ToolResult(
                tool_name="failing_tool",
                success=False,
                result=None,
                error_message=error_msg
            )
            
            # Assert
            assert tool_result.success is False
            assert tool_result.error_message == error_msg
            assert tool_result.result is None
    
    def test_execution_time_precision(self):
        """Test that execution_time_ms supports decimal precision."""
        # Arrange
        execution_times = [0.1, 1.5, 10.25, 100.001, 1000.999]
        
        for exec_time in execution_times:
            # Act
            result = ToolResult(
                tool_name="timed_tool",
                success=True,
                result="output",
                execution_time_ms=exec_time
            )
            
            # Assert
            assert result.execution_time_ms == exec_time
    
    def test_metadata_independence(self):
        """Test that metadata dictionaries are independent between instances."""
        # Act
        result1 = ToolResult(tool_name="tool1", success=True, result="output1")
        result2 = ToolResult(tool_name="tool2", success=True, result="output2")
        
        # Modify metadata in result1
        result1.metadata["custom"] = "value"
        
        # Assert
        assert result1.metadata != result2.metadata
        assert "custom" in result1.metadata
        assert "custom" not in result2.metadata
        assert result2.metadata == {}
    
    @pytest.mark.parametrize("tool_name", [
        "simple_tool",
        "tool_with_underscores",
        "tool-with-hyphens",
        "ToolWithCamelCase",
        "tool123",
        "tool.with.dots"
    ])
    def test_various_tool_names(self, tool_name):
        """Test ToolResult with various tool name formats."""
        # Act
        result = ToolResult(
            tool_name=tool_name,
            success=True,
            result="test output"
        )
        
        # Assert
        assert result.tool_name == tool_name


class TestAgentModelsIntegration:
    """Integration tests for agent models working together."""
    
    def test_agent_context_to_agent_response_data_flow(self):
        """Test data flow from AgentContext to AgentResponse."""
        # Arrange
        context = AgentContext(
            user_id="integration_user",
            session_id="integration_session",
            request_id="integration_request",
            metadata={"source": "test"}
        )
        
        # Act - Simulate agent processing
        response = AgentResponse(
            content="Processed request successfully",
            status=AgentStatus.COMPLETED,
            session_id=context.session_id,
            request_id=context.request_id,
            metadata=context.metadata.copy()
        )
        
        # Assert
        assert response.session_id == context.session_id
        assert response.request_id == context.request_id
        assert response.metadata == context.metadata
    
    def test_agent_response_with_tool_results(self):
        """Test AgentResponse containing ToolResult information."""
        # Arrange
        tool_results = [
            ToolResult(
                tool_name="search",
                success=True,
                result={"results": ["item1", "item2"]},
                execution_time_ms=150.0
            ),
            ToolResult(
                tool_name="calculator",
                success=True,
                result=42,
                execution_time_ms=50.0
            )
        ]
        
        # Act
        response = AgentResponse(
            content="Used tools to process request",
            status=AgentStatus.COMPLETED,
            tools_used=[tr.tool_name for tr in tool_results],
            processing_time_ms=sum(tr.execution_time_ms for tr in tool_results),
            metadata={
                "tool_results": [
                    {
                        "tool": tr.tool_name,
                        "success": tr.success,
                        "execution_time": tr.execution_time_ms
                    }
                    for tr in tool_results
                ]
            }
        )
        
        # Assert
        assert response.tools_used == ["search", "calculator"]
        assert response.processing_time_ms == 200.0
        assert len(response.metadata["tool_results"]) == 2
        assert response.success is True
    
    def test_error_handling_across_models(self):
        """Test error handling patterns across agent models."""
        # Arrange - Tool failure
        failed_tool = ToolResult(
            tool_name="external_api",
            success=False,
            result=None,
            error_message="API rate limit exceeded",
            execution_time_ms=30.0
        )
        
        # Act - Create response with error
        error_response = AgentResponse(
            content="Unable to complete request due to tool failure",
            status=AgentStatus.ERROR,
            tools_used=[failed_tool.tool_name],
            processing_time_ms=failed_tool.execution_time_ms,
            errors=[failed_tool.error_message]
        )
        
        # Assert
        assert error_response.success is False
        assert error_response.status == AgentStatus.ERROR
        assert "API rate limit exceeded" in error_response.errors
        assert "external_api" in error_response.tools_used


class TestAgentModelsEdgeCases:
    """Test suite for edge cases and boundary conditions."""
    
    def test_agent_context_with_empty_tools_lists(self):
        """Test AgentContext with empty tools lists."""
        # Act
        context = AgentContext(
            user_id="test",
            tools_allowed=[],
            tools_denied=[]
        )
        
        # Assert
        assert context.tools_allowed == []
        assert context.tools_denied == []
    
    def test_agent_response_with_large_processing_time(self):
        """Test AgentResponse with large processing time values."""
        # Act
        response = AgentResponse(
            content="Long running task",
            status=AgentStatus.COMPLETED,
            processing_time_ms=999999.999
        )
        
        # Assert
        assert response.processing_time_ms == 999999.999
    
    def test_tool_result_with_complex_result_objects(self):
        """Test ToolResult with complex nested result objects."""
        # Arrange
        complex_result = {
            "data": [{"id": 1, "items": [1, 2, 3]}, {"id": 2, "items": [4, 5, 6]}],
            "meta": {"total": 6, "pages": 2},
            "nested": {"deep": {"value": "test"}}
        }
        
        # Act
        result = ToolResult(
            tool_name="complex_tool",
            success=True,
            result=complex_result
        )
        
        # Assert
        assert result.result == complex_result
        assert result.result["data"][0]["id"] == 1
        assert result.result["nested"]["deep"]["value"] == "test"
    
    def test_timestamp_precision_and_ordering(self):
        """Test timestamp precision and ordering in AgentResponse."""
        # Act - Create multiple responses quickly
        responses = []
        for i in range(5):
            responses.append(AgentResponse(
                content=f"Response {i}",
                status=AgentStatus.COMPLETED
            ))
        
        # Assert - Timestamps should be in order or very close
        for i in range(1, len(responses)):
            time_diff = (responses[i].timestamp - responses[i-1].timestamp).total_seconds()
            assert time_diff >= 0, "Timestamps should be monotonic or equal"
            assert time_diff < 1.0, "Timestamps should be created within 1 second"
