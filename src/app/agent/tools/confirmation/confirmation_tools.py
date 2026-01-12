"""
Agent tools for the confirmation workflow.

These tools provide the interface between the agent and the confirmation service.
They wrap ConfirmationService methods and handle the interaction with the LLM.
"""

from typing import Any, Callable, Dict, List, Optional, Literal
from langchain_core.tools import tool
from pydantic import BaseModel, Field

from app.core.confirmation import ConfirmationService, get_default_formatter, PendingActionsStore


# Global service instance (will be initialized on first use)
_confirmation_service: Optional[ConfirmationService] = None


def _get_confirmation_service() -> ConfirmationService:
    """
    Get the singleton confirmation service instance.
    
    Returns:
        ConfirmationService: The confirmation service instance
    """
    global _confirmation_service
    if _confirmation_service is None:
        store = PendingActionsStore(ttl_minutes=10)
        formatter = get_default_formatter()
        _confirmation_service = ConfirmationService(store=store, formatter=formatter)
    return _confirmation_service


class PrepareActionInput(BaseModel):
    """Input schema for prepare_action tool."""
    tool_name: str = Field(..., description="Name of the tool being executed (e.g., 'create_jira_issue')")
    tool_args: Dict[str, Any] = Field(..., description="Arguments for the tool (as a dictionary)")
    risk_level: Literal["low", "medium", "high"] = Field(
        "medium",
        description="Risk level of the action: low (safe, easily reversible), medium (moderate impact), high (significant impact)"
    )
    user_id: str = Field(..., description="ID of the user requesting the action")
    session_id: Optional[str] = Field(None, description="Optional session ID for grouping actions")


class ConfirmActionInput(BaseModel):
    """Input schema for confirm_action tool."""
    action_id: str = Field(..., description="ID of the action to confirm (from prepare_action response)")
    user_id: str = Field(..., description="ID of the user confirming the action")


class CancelActionInput(BaseModel):
    """Input schema for cancel_action tool."""
    action_id: str = Field(..., description="ID of the action to cancel")
    user_id: str = Field(..., description="ID of the user canceling the action")


class ListPendingActionsInput(BaseModel):
    """Input schema for list_pending_actions tool."""
    user_id: str = Field(..., description="ID of the user")
    session_id: Optional[str] = Field(None, description="Optional session ID to filter by")


@tool(args_schema=PrepareActionInput)
async def prepare_action(
    tool_name: str,
    tool_args: Dict[str, Any],
    risk_level: Literal["low", "medium", "high"],
    user_id: str,
    session_id: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Prepare an action for confirmation. This stores the action and generates a preview
    for the user to review before execution.
    
    Use this tool BEFORE executing any mutating action that requires user confirmation.
    This includes actions like:
    - Creating Jira issues
    - Adding comments to Jira issues  
    - Sending emails
    - Creating GitHub issues
    - Any other action that modifies external systems
    
    Args:
        tool_name: Name of the tool to execute (e.g., 'create_jira_issue')
        tool_args: Dictionary of arguments for the tool
        risk_level: Risk level of the action (low/medium/high)
        user_id: ID of the user requesting the action
        session_id: Optional session ID for grouping related actions
        
    Returns:
        Dictionary with:
        - action_id: Unique ID for this action (use with confirm_action)
        - preview: Human-readable preview of what will happen
        - expires_at: When this action will expire if not confirmed
        - status: "success" if prepared successfully
        
    Example:
        result = prepare_action(
            tool_name="create_jira_issue",
            tool_args={"project": "PROJ", "summary": "Bug in login", "description": "..."},
            risk_level="medium",
            user_id="user_123",
            session_id="session_456"
        )
        # Returns: {"action_id": "action_abc123", "preview": "...", ...}
    """
    service = _get_confirmation_service()
    
    # Create a mock executor function (actual executor will be provided by the agent framework)
    # For now, we'll store None and the framework can update it later
    def placeholder_executor():
        return {"status": "executed", "message": "Action executed"}
    
    try:
        result = await service.prepare_action(
            user_id=user_id,
            session_id=session_id,
            tool_name=tool_name,
            tool_args=tool_args,
            risk_level=risk_level,
            executor=placeholder_executor,
        )
        
        return {
            "status": "success",
            "action_id": result["action_id"],
            "preview": result["preview"],
            "expires_at": result["expires_at"],
            "message": f"Action prepared. Please review and use confirm_action with action_id='{result['action_id']}' to execute.",
        }
    except ValueError as e:
        return {
            "status": "error",
            "error": str(e),
            "message": f"Failed to prepare action: {str(e)}",
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "message": f"Unexpected error preparing action: {str(e)}",
        }


@tool(args_schema=ConfirmActionInput)
async def confirm_action(
    action_id: str,
    user_id: str,
) -> Dict[str, Any]:
    """
    Confirm and execute a previously prepared action.
    
    Use this tool AFTER the user has reviewed the preview from prepare_action and
    given explicit approval to proceed. This will execute the stored action.
    
    Args:
        action_id: ID of the action to confirm (from prepare_action response)
        user_id: ID of the user confirming (must match the user who prepared it)
        
    Returns:
        Dictionary with:
        - status: "success" if executed, "error" if failed
        - result: The result of the executed action
        - message: Human-readable message about what happened
        
    Example:
        result = confirm_action(
            action_id="action_abc123",
            user_id="user_123"
        )
        # Returns: {"status": "success", "result": {...}, "message": "Action executed successfully"}
    """
    service = _get_confirmation_service()
    
    try:
        result = await service.confirm_action(
            action_id=action_id,
            user_id=user_id,
        )
        
        return {
            "status": "success",
            "result": result["result"],
            "message": f"Action {action_id} executed successfully.",
        }
    except PermissionError as e:
        return {
            "status": "error",
            "error": "permission_denied",
            "message": str(e),
        }
    except ValueError as e:
        return {
            "status": "error",
            "error": "invalid_action",
            "message": str(e),
        }
    except Exception as e:
        return {
            "status": "error",
            "error": "execution_failed",
            "message": f"Failed to execute action: {str(e)}",
        }


@tool(args_schema=CancelActionInput)
async def cancel_action(
    action_id: str,
    user_id: str,
) -> Dict[str, Any]:
    """
    Cancel a previously prepared action without executing it.
    
    Use this tool when the user decides not to proceed with a prepared action,
    or to clean up actions that are no longer needed.
    
    Args:
        action_id: ID of the action to cancel
        user_id: ID of the user canceling (must match the user who prepared it)
        
    Returns:
        Dictionary with:
        - status: "success" if cancelled, "error" if failed
        - message: Human-readable message
        
    Example:
        result = cancel_action(
            action_id="action_abc123",
            user_id="user_123"
        )
        # Returns: {"status": "success", "message": "Action cancelled successfully"}
    """
    service = _get_confirmation_service()
    
    try:
        await service.cancel_action(
            action_id=action_id,
            user_id=user_id,
        )
        
        return {
            "status": "success",
            "message": f"Action {action_id} cancelled successfully.",
        }
    except PermissionError as e:
        return {
            "status": "error",
            "error": "permission_denied",
            "message": str(e),
        }
    except ValueError as e:
        return {
            "status": "error",
            "error": "invalid_action",
            "message": str(e),
        }


@tool(args_schema=ListPendingActionsInput)
async def list_pending_actions(
    user_id: str,
    session_id: Optional[str] = None,
) -> Dict[str, Any]:
    """
    List all pending actions for a user that are awaiting confirmation.
    
    Use this tool to help users see what actions they have prepared but not yet
    confirmed, or to check the status of the confirmation queue.
    
    Args:
        user_id: ID of the user
        session_id: Optional session ID to filter by (only show actions from this session)
        
    Returns:
        Dictionary with:
        - status: "success"
        - actions: List of pending actions with their previews
        - count: Number of pending actions
        
    Example:
        result = list_pending_actions(user_id="user_123")
        # Returns: {
        #     "status": "success",
        #     "count": 2,
        #     "actions": [
        #         {"action_id": "action_123", "tool_name": "create_jira_issue", ...},
        #         {"action_id": "action_456", "tool_name": "send_email", ...}
        #     ]
        # }
    """
    service = _get_confirmation_service()
    
    try:
        actions = await service.list_pending_actions(
            user_id=user_id,
            session_id=session_id,
        )
        
        return {
            "status": "success",
            "count": len(actions),
            "actions": actions,
            "message": f"Found {len(actions)} pending action(s).",
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "message": f"Failed to list pending actions: {str(e)}",
        }
