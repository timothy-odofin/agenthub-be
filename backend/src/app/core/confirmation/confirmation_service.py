"""
Confirmation Service - Orchestrates the two-phase confirmation workflow.

Coordinates between PendingActionsStore and ActionPreviewFormatter to manage
the prepare → confirm → execute flow.

Design Principles:
- Single Responsibility: Only orchestrates confirmation workflow
- Dependency Injection: Store and formatter are injected
- Fail-safe: Validates all preconditions before execution
"""

from typing import Dict, Any, Optional, Callable
from datetime import datetime

from app.core.utils.logger import get_logger
from app.core.confirmation.pending_actions_store import PendingActionsStore, PendingAction
from app.core.confirmation.action_preview_formatter import ActionPreviewFormatter

logger = get_logger(__name__)


class ConfirmationService:
    """
    Service for managing the action confirmation workflow.
    
    Provides a clean API for:
    1. Preparing actions (storing and generating previews)
    2. Confirming actions (validating and executing)
    3. Canceling actions
    4. Listing pending actions
    
    Usage:
        service = ConfirmationService(store, formatter)
        
        # Prepare action
        preview = service.prepare_action(
            user_id="user_123",
            session_id="session_456",
            integration="jira",
            tool_name="create_jira_issue",
            action_type="create",
            risk_level="medium",
            parameters={...},
            executor_func=actual_tool_function
        )
        
        # User reviews preview, then confirms
        result = service.confirm_action(action_id, user_id)
    """
    
    def __init__(
        self,
        store: PendingActionsStore,
        formatter: ActionPreviewFormatter
    ):
        """
        Initialize the service with dependencies.
        
        Args:
            store: Storage for pending actions
            formatter: Formatter for action previews
        """
        self._store = store
        self._formatter = formatter
        self._executors: Dict[str, Callable] = {}  # Map action_id -> executor_func
        logger.info("ConfirmationService initialized")
    
    async def prepare_action(
        self,
        user_id: str,
        session_id: str,
        integration: str,
        tool_name: str,
        action_type: str,
        risk_level: str,
        parameters: Dict[str, Any],
        executor_func: Callable
    ) -> Dict[str, Any]:
        """
        Prepare an action for confirmation.
        
        Stores the action and generates a preview for user review.
        
        Args:
            user_id: ID of the user requesting the action
            session_id: Current session ID
            integration: Integration name (jira, email, github, etc.)
            tool_name: Specific tool name (create_jira_issue, send_email, etc.)
            action_type: Type of action (create, update, delete, send, etc.)
            risk_level: Risk level (low, medium, high)
            parameters: Tool-specific parameters
            executor_func: Function to call when action is confirmed
            
        Returns:
            Dictionary with action_id and preview
            {
                "action_id": "action_abc123",
                "preview": "Human-readable preview...",
                "status": "pending_confirmation",
                "expires_at": "2026-01-11T18:00:00"
            }
        """
        # Store the action
        action_id = await self._store.store_action(
            user_id=user_id,
            session_id=session_id,
            integration=integration,
            tool_name=tool_name,
            action_type=action_type,
            risk_level=risk_level,
            parameters=parameters
        )
        
        # Store the executor function
        self._executors[action_id] = executor_func
        
        # Get the stored action to generate preview
        action = await self._store.get_action(action_id)
        if not action:
            logger.error(f"Action {action_id} not found after storing")
            raise ValueError(f"Failed to store action {action_id}")
        
        # Generate preview
        preview = self._formatter.format(action)
        
        logger.info(
            f"Prepared action {action_id} for user {user_id} | "
            f"Tool: {tool_name} | Risk: {risk_level}"
        )
        
        return {
            "action_id": action_id,
            "preview": preview,
            "status": "pending_confirmation",
            "expires_at": action.expires_at,  # Already in ISO format
            "risk_level": risk_level,
            "integration": integration,
            "tool_name": tool_name
        }
    
    async def confirm_action(
        self,
        action_id: str,
        user_id: str
    ) -> Dict[str, Any]:
        """
        Confirm and execute a pending action.
        
        Validates ownership and expiry, then executes the stored action.
        
        Args:
            action_id: The action ID to confirm
            user_id: ID of the user confirming (must match action owner)
            
        Returns:
            Dictionary with execution result
            {
                "status": "confirmed",
                "action_id": "action_abc123",
                "result": <executor function result>,
                "executed_at": "2026-01-11T17:45:00"
            }
            
        Raises:
            ValueError: If action not found, expired, or user mismatch
        """
        # Retrieve the action
        action = await self._store.get_action(action_id)
        
        if not action:
            logger.warning(f"Confirm failed: Action {action_id} not found or expired")
            raise ValueError(f"Action {action_id} not found or has expired")
        
        # Validate ownership
        if action.user_id != user_id:
            logger.warning(
                f"Confirm failed: User {user_id} attempted to confirm "
                f"action {action_id} owned by {action.user_id}"
            )
            raise ValueError(f"You are not authorized to confirm action {action_id}")
        
        # Get the executor function
        executor_func = self._executors.get(action_id)
        if not executor_func:
            logger.error(f"Executor function not found for action {action_id}")
            raise ValueError(f"Executor function not available for action {action_id}")
        
        # Execute the action
        try:
            logger.info(
                f"Executing action {action_id} | User: {user_id} | "
                f"Tool: {action.tool_name}"
            )
            
            result = executor_func(action.parameters)
            
            logger.info(f"Action {action_id} executed successfully")
            
            # Clean up
            await self._store.delete_action(action_id)
            del self._executors[action_id]
            
            return {
                "status": "confirmed",
                "action_id": action_id,
                "result": result,
                "executed_at": datetime.now().isoformat(),
                "integration": action.integration,
                "tool_name": action.tool_name
            }
            
        except Exception as e:
            logger.error(
                f"Action {action_id} execution failed: {e}",
                exc_info=True
            )
            
            # Keep action in store for potential retry
            return {
                "status": "failed",
                "action_id": action_id,
                "error": str(e),
                "error_type": type(e).__name__,
                "failed_at": datetime.now().isoformat()
            }
    
    async def cancel_action(
        self,
        action_id: str,
        user_id: str
    ) -> Dict[str, Any]:
        """
        Cancel a pending action.
        
        Args:
            action_id: The action ID to cancel
            user_id: ID of the user canceling (must match action owner)
            
        Returns:
            Dictionary with cancellation status
            {
                "status": "canceled",
                "action_id": "action_abc123",
                "canceled_at": "2026-01-11T17:45:00"
            }
            
        Raises:
            ValueError: If action not found or user mismatch
        """
        # Retrieve the action
        action = await self._store.get_action(action_id)
        
        if not action:
            logger.warning(f"Cancel failed: Action {action_id} not found or expired")
            raise ValueError(f"Action {action_id} not found or has expired")
        
        # Validate ownership
        if action.user_id != user_id:
            logger.warning(
                f"Cancel failed: User {user_id} attempted to cancel "
                f"action {action_id} owned by {action.user_id}"
            )
            raise ValueError(f"You are not authorized to cancel action {action_id}")
        
        # Delete the action
        await self._store.delete_action(action_id)
        
        # Clean up executor
        if action_id in self._executors:
            del self._executors[action_id]
        
        logger.info(f"Action {action_id} canceled by user {user_id}")
        
        return {
            "status": "canceled",
            "action_id": action_id,
            "canceled_at": datetime.now().isoformat(),
            "integration": action.integration,
            "tool_name": action.tool_name
        }
    
    async def list_pending_actions(
        self,
        user_id: str,
        session_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        List all pending actions for a user.
        
        Args:
            user_id: The user ID
            session_id: Optional session ID to filter by
            
        Returns:
            Dictionary with list of pending actions
            {
                "user_id": "user_123",
                "total": 3,
                "actions": [
                    {
                        "action_id": "action_abc",
                        "preview": "...",
                        "risk_level": "medium",
                        ...
                    },
                    ...
                ]
            }
        """
        actions = await self._store.get_user_actions(user_id, session_id)
        
        actions_data = []
        for action in actions:
            preview = self._formatter.format(action)
            actions_data.append({
                "action_id": action.action_id,
                "preview": preview,
                "integration": action.integration,
                "tool_name": action.tool_name,
                "action_type": action.action_type,
                "risk_level": action.risk_level,
                "created_at": action.created_at,  # Already in ISO format
                "expires_at": action.expires_at,  # Already in ISO format
                "session_id": action.session_id
            })
        
        logger.info(
            f"Listed {len(actions)} pending actions for user {user_id}" +
            (f" in session {session_id}" if session_id else "")
        )
        
        return {
            "user_id": user_id,
            "session_id": session_id,
            "total": len(actions_data),
            "actions": actions_data
        }
    
    async def get_action_details(
        self,
        action_id: str,
        user_id: str
    ) -> Dict[str, Any]:
        """
        Get detailed information about a specific pending action.
        
        Args:
            action_id: The action ID
            user_id: The user ID (must match action owner)
            
        Returns:
            Dictionary with action details including preview
            
        Raises:
            ValueError: If action not found or user mismatch
        """
        action = await self._store.get_action(action_id)
        
        if not action:
            logger.warning(f"Get details failed: Action {action_id} not found or expired")
            raise ValueError(f"Action {action_id} not found or has expired")
        
        if action.user_id != user_id:
            logger.warning(
                f"Get details failed: User {user_id} attempted to access "
                f"action {action_id} owned by {action.user_id}"
            )
            raise ValueError(f"You are not authorized to view action {action_id}")
        
        preview = self._formatter.format(action)
        
        return {
            "action_id": action.action_id,
            "preview": preview,
            "integration": action.integration,
            "tool_name": action.tool_name,
            "action_type": action.action_type,
            "risk_level": action.risk_level,
            "parameters": action.parameters,
            "created_at": action.created_at,  # Already in ISO format
            "expires_at": action.expires_at,  # Already in ISO format
            "session_id": action.session_id,
            "status": "pending_confirmation"
        }
    
    async def cleanup_expired_actions(self) -> int:
        """
        Clean up expired actions and their executors.
        
        This can be called periodically by a background task.
        
        Returns:
            Number of actions cleaned up
        """
        # Cleanup expired actions in Redis (TTL handles this automatically)
        removed_count = await self._store.cleanup_expired()
        
        # Note: With Redis backend, we cannot efficiently iterate all action IDs
        # to clean up orphaned executors. Executors will be cleaned up when accessed.
        # This is acceptable since executors are in-memory and lightweight.
        
        logger.info(f"Cleaned up {removed_count} expired actions from Redis")
        
        return removed_count
    
    async def get_stats(self) -> Dict[str, Any]:
        """
        Get statistics about the confirmation service.
        
        Returns:
            Dictionary with service statistics
        """
        store_stats = await self._store.get_stats()
        
        return {
            **store_stats,
            "pending_executors": len(self._executors)
        }
