"""
Pending Actions Store - Generic storage for actions awaiting user confirmation.

Uses Redis-backed cache for persistent, scalable storage with TTL support.

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
from dataclasses import dataclass, asdict, field

from app.core.utils.logger import get_logger
from app.services.cache.instances import confirmation_cache

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
    
    Usage:
        store = PendingActionsStore(ttl_minutes=10)
        action_id = store.store_action(user_id, session_id, "jira", ...)
        action = store.get_action(action_id)
        store.delete_action(action_id)
    """
    
    def __init__(self, ttl_minutes: int = 10):
        """
        Initialize the store.
        
        Args:
            ttl_minutes: Time-to-live for pending actions in minutes.
                        After this time, actions are automatically expired.
        """
        self._store: Dict[str, PendingAction] = {}
        self._lock = Lock()
        self._ttl_minutes = ttl_minutes
        logger.info(f"PendingActionsStore initialized with TTL={ttl_minutes} minutes")
    
    def store_action(
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
        Store a new pending action.
        
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
        expires_at = now + timedelta(minutes=self._ttl_minutes)
        
        action = PendingAction(
            action_id=action_id,
            user_id=user_id,
            session_id=session_id,
            integration=integration,
            tool_name=tool_name,
            action_type=action_type,
            risk_level=risk_level,
            parameters=parameters,
            created_at=now,
            expires_at=expires_at
        )
        
        with self._lock:
            self._store[action_id] = action
        
        logger.info(
            f"Stored pending action: {action_id} | "
            f"User: {user_id} | Tool: {tool_name} | Risk: {risk_level}"
        )
        
        return action_id
    
    def get_action(self, action_id: str) -> Optional[PendingAction]:
        """
        Retrieve a pending action by ID.
        
        Args:
            action_id: The unique action identifier
            
        Returns:
            PendingAction if found and not expired, None otherwise
        """
        with self._lock:
            action = self._store.get(action_id)
            
            if action is None:
                logger.warning(f"Action not found: {action_id}")
                return None
            
            if action.is_expired():
                logger.warning(f"Action expired: {action_id}")
                # Clean up expired action
                del self._store[action_id]
                return None
            
            return action
    
    def delete_action(self, action_id: str) -> bool:
        """
        Delete a pending action (used after confirmation or cancellation).
        
        Args:
            action_id: The unique action identifier
            
        Returns:
            True if action was deleted, False if not found
        """
        with self._lock:
            if action_id in self._store:
                del self._store[action_id]
                logger.info(f"Deleted pending action: {action_id}")
                return True
            
            logger.warning(f"Attempted to delete non-existent action: {action_id}")
            return False
    
    def get_user_actions(
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
        with self._lock:
            actions = []
            expired_ids = []
            
            for action_id, action in self._store.items():
                if action.is_expired():
                    expired_ids.append(action_id)
                    continue
                
                if action.user_id == user_id:
                    if session_id is None or action.session_id == session_id:
                        actions.append(action)
            
            # Clean up expired actions
            for expired_id in expired_ids:
                del self._store[expired_id]
                logger.debug(f"Cleaned up expired action: {expired_id}")
        
        return actions
    
    def cleanup_expired(self) -> int:
        """
        Remove all expired actions from the store.
        
        This can be called periodically by a background task.
        
        Returns:
            Number of actions removed
        """
        with self._lock:
            expired_ids = [
                action_id
                for action_id, action in self._store.items()
                if action.is_expired()
            ]
            
            for action_id in expired_ids:
                del self._store[action_id]
        
        if expired_ids:
            logger.info(f"Cleaned up {len(expired_ids)} expired actions")
        
        return len(expired_ids)
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get statistics about the store.
        
        Useful for monitoring and debugging.
        
        Returns:
            Dictionary with store statistics
        """
        with self._lock:
            total = len(self._store)
            expired = sum(1 for action in self._store.values() if action.is_expired())
            active = total - expired
            
            by_integration = {}
            by_risk = {}
            
            for action in self._store.values():
                if not action.is_expired():
                    by_integration[action.integration] = by_integration.get(action.integration, 0) + 1
                    by_risk[action.risk_level] = by_risk.get(action.risk_level, 0) + 1
        
        return {
            "total_actions": total,
            "active_actions": active,
            "expired_actions": expired,
            "by_integration": by_integration,
            "by_risk_level": by_risk
        }
    
    def clear_all(self) -> int:
        """
        Clear all pending actions.
        
        WARNING: This removes ALL actions. Use with caution.
        Primarily for testing purposes.
        
        Returns:
            Number of actions removed
        """
        with self._lock:
            count = len(self._store)
            self._store.clear()
        
        logger.warning(f"Cleared all pending actions: {count} removed")
        return count
    
    @staticmethod
    def _generate_action_id() -> str:
        """Generate a unique action ID."""
        return f"action_{uuid.uuid4().hex[:12]}"
