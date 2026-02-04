"""
Pending Actions Store - Generic storage for actions awaiting user confirmation.

˘ses Redis-backed cache for persistent, scalable storage with TTL support.

Design Principles:
- Integration-agnostic: Works with Jira, Email, GitHub, or any future tool
- Type-safe: Uses dataclasses for clear structure
- Thread-safe: Redis provides atomic operations
- Self-cleaning: Automatic TTL expiration via Redis
- Scalable: Supports distributed deployments
"""

import uuid
from datetime import datetime, timedelta
from typing import Dict, Optional, Any, List
from dataclasses import dataclass, asdict

from app.core.utils.logger import get_logger
from app.infrastructure.cache.instances import confirmation_cache

logger = get_logger(__name__)


@dataclass
class PendingAction:
    """
    Represents an action awaiting user confirmation.
    
    This is integration-agnostic - works for any tool type.
    """
    action_id: str
    user_id: str
    session_id: str
    integration: str  # jira, email, github, confluence, etc.
    tool_name: str  # create_jira_issue, send_email, etc.
    action_type: str  # create, update, delete, send, etc.
    risk_level: str  # low, medium, high
    parameters: Dict[str, Any]
    created_at: str  # ISO format string for JSON serialization
    expires_at: str  # ISO format string for JSON serialization
    
    def is_expired(self) -> bool:
        """Check if action has expired."""
        expires = datetime.fromisoformat(self.expires_at)
        return datetime.now() > expires
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary (already has ISO format timestamps)."""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'PendingAction':
        """Create PendingAction from dictionary."""
        return cls(**data)


class PendingActionsStore:
    """
    Redis-backed store for pending actions using confirmation_cache.
    
    Thread-safe implementation with automatic TTL expiration via Redis.
    Supports distributed deployments with persistence across restarts.
    
    Usage:
        store = PendingActionsStore(ttl_minutes=10)
        action_id = await store.store_action(user_id, session_id, "jira", ...)
        action = await store.get_action(action_id)
        await store.delete_action(action_id)
    """
    
    # Index for user actions: stores action_ids by user
    USER_INDEX_PREFIX = "user_actions"
    
    def __init__(self, ttl_minutes: int = 10):
        """
        Initialize the store.
        
        Args:
            ttl_minutes: Time-to-live for pending actions in minutes.
                        After this time, actions are automatically expired by Redis.
        """
        self._ttl_seconds = ttl_minutes * 60
        logger.info(f"PendingActionsStore initialized with TTL={ttl_minutes} minutes (using confirmation_cache)")
    
    async def store_action(
        self,
        user_id: str,
        session_id: str,
        integration: str,
        tool_name: str,
        action_type: str,
        risk_level: str,
        parameters: Dict[str, Any]
    ) -> str:
        """
        Store a new pending action in Redis.
        
        Args:
            user_id: ID of the user requesting the action
            session_id: Current session ID
            integration: Integration name (jira, email, github, etc.)
            tool_name: Specific tool name (create_jira_issue, send_email, etc.)
            action_type: Type of action (create, update, delete, send, etc.)
            risk_level: Risk level (low, medium, high)
            parameters: Tool-specific parameters as a dictionary
            
        Returns:
            Unique action_id for later confirmation or cancellation
        """
        action_id = self._generate_action_id()
        now = datetime.now()
        expires_at = now + timedelta(seconds=self._ttl_seconds)
        
        action = PendingAction(
            action_id=action_id,
            user_id=user_id,
            session_id=session_id,
            integration=integration,
            tool_name=tool_name,
            action_type=action_type,
            risk_level=risk_level,
            parameters=parameters,
            created_at=now.isoformat(),
            expires_at=expires_at.isoformat()
        )
        
        # Store action data with user index for efficient user-based queries
        await confirmation_cache.set(
            action_id,
            action.to_dict(),
            ttl=self._ttl_seconds,
            indexes={self.USER_INDEX_PREFIX: user_id}
        )
        
        logger.info(
            f"Stored pending action: {action_id} | "
            f"User: {user_id} | Tool: {tool_name} | Risk: {risk_level}"
        )
        
        return action_id
    
    async def get_action(self, action_id: str) -> Optional[PendingAction]:
        """
        Retrieve a pending action by ID from Redis.
        
        Args:
            action_id: The unique action identifier
            
        Returns:
            PendingAction if found and not expired, None otherwise
        """
        action_data = await confirmation_cache.get(action_id)
        
        if action_data is None:
            logger.warning(f"Action not found: {action_id}")
            return None
        
        action = PendingAction.from_dict(action_data)
        
        if action.is_expired():
            logger.warning(f"Action expired: {action_id}")
            # Redis TTL should handle cleanup, but delete manually to be safe
            await confirmation_cache.delete(action_id)
            return None
        
        return action
    
    async def delete_action(self, action_id: str) -> bool:
        """
        Delete a pending action (used after confirmation or cancellation).
        
        Args:
            action_id: The unique action identifier
            
        Returns:
            True if action was deleted, False if not found
        """
        result = await confirmation_cache.delete(action_id)
        
        if result:
            logger.info(f"Deleted pending action: {action_id}")
        else:
            logger.warning(f"Attempted to delete non-existent action: {action_id}")
        
        return result
    
    async def get_user_actions(
        self,
        user_id: str,
        session_id: Optional[str] = None
    ) -> List[PendingAction]:
        """
        Get all pending actions for a user, optionally filtered by session.
        
        Args:
            user_id: The user ID
            session_id: Optional session ID to filter by
            
        Returns:
            List of pending actions (excludes expired actions)
        """
        action_data_list = await confirmation_cache.get_by_index(self.USER_INDEX_PREFIX, user_id)
        
        actions = []
        for action_data in action_data_list:
            action = PendingAction.from_dict(action_data)
            
            # Skip expired actions
            if action.is_expired():
                # Clean up expired action
                await confirmation_cache.delete(action.action_id)
                continue
            
            # Filter by session if provided
            if session_id is None or action.session_id == session_id:
                actions.append(action)
        
        return actions
    
    async def cleanup_expired(self) -> int:
        """
        Remove all expired actions from the store.
        
        Redis TTL handles most cleanup automatically, but this method
        can be used to force cleanup of any remaining expired actions.
        
        Returns:
            Number of actions removed
        """
        # Get all action keys (this is expensive, use sparingly)
        # In production, rely on Redis TTL for cleanup
        logger.info("Cleanup called - Redis TTL handles automatic expiration")
        return 0
    
    async def get_stats(self) -> Dict[str, Any]:
        """
        Get statistics about the store.
        
        Useful for monitoring and debugging.
        
        Returns:
            Dictionary with store statistics
        """
        # Note: Getting comprehensive stats from Redis is expensive
        # This is a simplified implementation
        logger.info("Getting store statistics (limited in Redis implementation)")
        
        return {
            "storage_backend": "redis",
            "cache_namespace": "confirmation",
            "ttl_seconds": self._ttl_seconds,
            "note": "Detailed stats require scanning all keys (expensive operation)"
        }
    
    async def clear_all(self) -> int:
        """
        Clear all pending actions.
        
        WARNING: This removes ALL actions in the confirmation namespace.
        Use with caution. Primarily for testing purposes.
        
        Returns:
            Number of actions removed
        """
        # Clear the entire confirmation namespace
        count = await confirmation_cache.clear_namespace()
        
        logger.warning(f"Cleared all pending actions: {count} removed")
        return count
    
    @staticmethod
    def _generate_action_id() -> str:
        """Generate a unique action ID."""
        return f"action_{uuid.uuid4().hex[:12]}"
