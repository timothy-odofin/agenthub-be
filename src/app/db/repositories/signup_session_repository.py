"""
Signup Session Repository for Redis operations.

This module provides temporary session storage for the conversational signup flow.
Sessions are stored in Redis with automatic TTL expiration for security and cleanup.

Key Features:
- Server-side state management (prevents client tampering)
- Automatic session expiration (15 minutes TTL)
- Password hashing on storage
- Validation tracking
"""

import json
from typing import Optional, Dict, Any
from datetime import datetime

from app.connections.factory.connection_factory import ConnectionFactory
from app.connections.base import ConnectionType
from app.core.utils.logger import get_logger

logger = get_logger(__name__)


class SignupSessionRepository:
    """
    Repository for managing temporary signup sessions in Redis.
    
    Follows the repository pattern from existing codebase (UserRepository).
    Reuses existing RedisConnectionManager infrastructure (DRY principle).
    
    Session Data Structure:
        {
            "email": "john@example.com",
            "username": "johndoe",
            "password_hash": "bcrypt_hash",
            "firstname": "John",
            "lastname": "Doe",
            "current_step": "LASTNAME",
            "created_at": 1704638400.0,
            "last_updated": 1704638400.0,
            "attempt_count": 1
        }
    """
    
    # Session configuration
    KEY_PREFIX = "signup"
    SESSION_TTL = 300  # 5 minutes in seconds (can be changed as needed)
    
    _instance: Optional['SignupSessionRepository'] = None
    
    def __init__(self):
        """
        Initialize the signup session repository.
        
        Automatically connects to Redis using existing ConnectionFactory.
        """
        self._redis_manager = None
        logger.info("SignupSessionRepository initialized")
    
    @property
    def redis(self):
        """Get Redis connection manager, connecting if necessary."""
        if self._redis_manager is None:
            self._redis_manager = ConnectionFactory.get_connection_manager(ConnectionType.REDIS)
            logger.info("Connected to Redis for SignupSessionRepository")
        return self._redis_manager
    
    def _make_key(self, session_id: str) -> str:
        """
        Generate Redis key for session.
        
        Args:
            session_id: Unique session identifier
            
        Returns:
            Redis key in format "signup:{session_id}"
        """
        return f"{self.KEY_PREFIX}:{session_id}"
    
    async def create_session(
        self, 
        session_id: str, 
        initial_data: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Create a new signup session in Redis.
        
        Args:
            session_id: Unique session identifier (UUID)
            initial_data: Optional initial session data
            
        Returns:
            True if created successfully, False otherwise
            
        Example:
            >>> await repo.create_session("uuid-123", {"current_step": "EMAIL"})
            True
        """
        try:
            key = self._make_key(session_id)
            
            # Initialize session data with timestamps
            session_data = {
                "session_id": session_id,
                "created_at": datetime.utcnow().timestamp(),
                "last_updated": datetime.utcnow().timestamp(),
                "attempt_count": 0,
                **(initial_data or {})
            }
            
            # Store as JSON string with TTL
            await self.redis.set(
                key, 
                json.dumps(session_data), 
                ex=self.SESSION_TTL
            )
            
            logger.info(f"Created signup session: {session_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to create signup session {session_id}: {e}", exc_info=True)
            return False
    
    async def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve session data from Redis.
        
        Args:
            session_id: Unique session identifier
            
        Returns:
            Session data dict if exists, None otherwise
            
        Example:
            >>> data = await repo.get_session("uuid-123")
            >>> print(data["email"])
            "john@example.com"
        """
        try:
            key = self._make_key(session_id)
            data = await self.redis.get(key)
            
            if data is None:
                logger.debug(f"Session not found or expired: {session_id}")
                return None
            
            # Parse JSON
            session_data = json.loads(data)
            logger.debug(f"Retrieved session: {session_id}")
            return session_data
            
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in session {session_id}: {e}")
            return None
        except Exception as e:
            logger.error(f"Failed to get session {session_id}: {e}", exc_info=True)
            return None
    
    async def update_field(
        self, 
        session_id: str, 
        field: str, 
        value: Any
    ) -> bool:
        """
        Update a specific field in the session.
        
        Args:
            session_id: Unique session identifier
            field: Field name to update
            value: New value for the field
            
        Returns:
            True if updated successfully, False otherwise
            
        Example:
            >>> await repo.update_field("uuid-123", "email", "john@example.com")
            True
        """
        try:
            # Get existing session
            session_data = await self.get_session(session_id)
            if session_data is None:
                logger.warning(f"Cannot update field - session not found: {session_id}")
                return False
            
            # Update field and timestamp
            session_data[field] = value
            session_data["last_updated"] = datetime.utcnow().timestamp()
            
            # Save back to Redis with refreshed TTL
            key = self._make_key(session_id)
            await self.redis.set(
                key, 
                json.dumps(session_data), 
                ex=self.SESSION_TTL
            )
            
            logger.debug(f"Updated field '{field}' in session: {session_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to update field in session {session_id}: {e}", exc_info=True)
            return False
    
    async def update_session(
        self, 
        session_id: str, 
        data: Dict[str, Any]
    ) -> bool:
        """
        Update multiple fields in the session at once.
        
        Args:
            session_id: Unique session identifier
            data: Dictionary of fields to update
            
        Returns:
            True if updated successfully, False otherwise
            
        Example:
            >>> await repo.update_session("uuid-123", {
            ...     "email": "john@example.com",
            ...     "current_step": "USERNAME"
            ... })
            True
        """
        try:
            # Get existing session
            session_data = await self.get_session(session_id)
            if session_data is None:
                logger.warning(f"Cannot update session - not found: {session_id}")
                return False
            
            # Update fields and timestamp
            session_data.update(data)
            session_data["last_updated"] = datetime.utcnow().timestamp()
            
            # Save back to Redis with refreshed TTL
            key = self._make_key(session_id)
            await self.redis.set(
                key, 
                json.dumps(session_data), 
                ex=self.SESSION_TTL
            )
            
            logger.debug(f"Updated session with {len(data)} fields: {session_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to update session {session_id}: {e}", exc_info=True)
            return False
    
    async def delete_session(self, session_id: str) -> bool:
        """
        Delete a session from Redis.
        
        Called after successful signup to clean up temporary data.
        
        Args:
            session_id: Unique session identifier
            
        Returns:
            True if deleted successfully, False otherwise
            
        Example:
            >>> await repo.delete_session("uuid-123")
            True
        """
        try:
            key = self._make_key(session_id)
            result = await self.redis.delete(key)
            
            if result > 0:
                logger.info(f"Deleted signup session: {session_id}")
                return True
            else:
                logger.debug(f"Session not found for deletion: {session_id}")
                return False
                
        except Exception as e:
            logger.error(f"Failed to delete session {session_id}: {e}", exc_info=True)
            return False
    
    async def session_exists(self, session_id: str) -> bool:
        """
        Check if a session exists in Redis.
        
        Args:
            session_id: Unique session identifier
            
        Returns:
            True if session exists, False otherwise
            
        Example:
            >>> exists = await repo.session_exists("uuid-123")
            >>> print(exists)
            True
        """
        try:
            key = self._make_key(session_id)
            result = await self.redis.exists(key)
            return result > 0
            
        except Exception as e:
            logger.error(f"Failed to check session existence {session_id}: {e}", exc_info=True)
            return False
    
    async def extend_ttl(self, session_id: str, seconds: Optional[int] = None) -> bool:
        """
        Extend the TTL of a session.
        
        Useful for long signup sessions where user needs more time.
        
        Args:
            session_id: Unique session identifier
            seconds: New TTL in seconds (defaults to SESSION_TTL)
            
        Returns:
            True if TTL extended successfully, False otherwise
            
        Example:
            >>> await repo.extend_ttl("uuid-123", 1800)  # Extend to 30 minutes
            True
        """
        try:
            key = self._make_key(session_id)
            ttl = seconds or self.SESSION_TTL
            result = await self.redis.expire(key, ttl)
            
            if result:
                logger.debug(f"Extended TTL for session {session_id} to {ttl}s")
            else:
                logger.warning(f"Failed to extend TTL - session may not exist: {session_id}")
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to extend TTL for session {session_id}: {e}", exc_info=True)
            return False
    
    async def increment_attempt(self, session_id: str) -> int:
        """
        Increment the attempt counter for a session.
        
        Useful for rate limiting or tracking validation failures.
        
        Args:
            session_id: Unique session identifier
            
        Returns:
            New attempt count, or 0 if failed
            
        Example:
            >>> count = await repo.increment_attempt("uuid-123")
            >>> print(count)
            2
        """
        try:
            session_data = await self.get_session(session_id)
            if session_data is None:
                return 0
            
            current_count = session_data.get("attempt_count", 0)
            new_count = current_count + 1
            
            await self.update_field(session_id, "attempt_count", new_count)
            return new_count
            
        except Exception as e:
            logger.error(f"Failed to increment attempt for session {session_id}: {e}", exc_info=True)
            return 0


# Singleton instance for convenience (following UserRepository pattern)
signup_session_repository = SignupSessionRepository()
