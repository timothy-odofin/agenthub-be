"""
Unit tests for PendingActionsStore (Async Redis Implementation).

Tests cover:
- Action storage and retrieval
- TTL expiry behavior
- User filtering
- Cleanup operations
- Edge cases and error handling
"""

import pytest
from datetime import datetime, timedelta
import asyncio

from src.app.core.confirmation.pending_actions_store import (
    PendingActionsStore,
    PendingAction
)
from src.app.services.cache.instances import confirmation_cache


class TestPendingAction:
    """Tests for PendingAction dataclass."""
    
    def test_pending_action_creation(self):
        """Test creating a PendingAction with all fields."""
        now = datetime.now()
        expires = now + timedelta(minutes=10)
        
        action = PendingAction(
            action_id="action_123",
            user_id="user_456",
            session_id="session_789",
            integration="jira",
            tool_name="create_jira_issue",
            action_type="create",
            risk_level="medium",
            parameters={"summary": "Test", "project": "PROJ"},
            created_at=now.isoformat(),
            expires_at=expires.isoformat()
        )
        
        assert action.action_id == "action_123"
        assert action.user_id == "user_456"
        assert action.session_id == "session_789"
        assert action.integration == "jira"
        assert action.tool_name == "create_jira_issue"
        assert action.action_type == "create"
        assert action.risk_level == "medium"
        assert action.parameters == {"summary": "Test", "project": "PROJ"}
        assert isinstance(action.created_at, str)
        assert isinstance(action.expires_at, str)
    
    def test_is_expired_not_expired(self):
        """Test is_expired returns False for future expiry."""
        now = datetime.now()
        expires = now + timedelta(minutes=10)
        
        action = PendingAction(
            action_id="action_123",
            user_id="user_456",
            session_id="session_789",
            integration="jira",
            tool_name="create_jira_issue",
            action_type="create",
            risk_level="low",
            parameters={},
            created_at=now.isoformat(),
            expires_at=expires.isoformat()
        )
        
        assert not action.is_expired()
    
    def test_is_expired_expired(self):
        """Test is_expired returns True for past expiry."""
        now = datetime.now()
        expires = now - timedelta(minutes=1)  # Already expired
        
        action = PendingAction(
            action_id="action_123",
            user_id="user_456",
            session_id="session_789",
            integration="jira",
            tool_name="create_jira_issue",
            action_type="create",
            risk_level="low",
            parameters={},
            created_at=(now - timedelta(minutes=10)).isoformat(),
            expires_at=expires.isoformat()
        )
        
        assert action.is_expired()
    
    def test_to_dict(self):
        """Test converting PendingAction to dictionary."""
        now = datetime.now()
        expires = now + timedelta(minutes=10)
        
        action = PendingAction(
            action_id="action_123",
            user_id="user_456",
            session_id="session_789",
            integration="email",
            tool_name="send_email",
            action_type="send",
            risk_level="high",
            parameters={"to": "test@example.com", "subject": "Test"},
            created_at=now.isoformat(),
            expires_at=expires.isoformat()
        )
        
        data = action.to_dict()
        
        assert data["action_id"] == "action_123"
        assert data["user_id"] == "user_456"
        assert data["integration"] == "email"
        assert data["tool_name"] == "send_email"
        assert data["action_type"] == "send"
        assert data["risk_level"] == "high"
        assert data["parameters"] == {"to": "test@example.com", "subject": "Test"}
        assert isinstance(data["created_at"], str)  # ISO format
        assert isinstance(data["expires_at"], str)  # ISO format


@pytest.mark.asyncio
class TestPendingActionsStore:
    """Tests for PendingActionsStore (async)."""
    
    @pytest.fixture
    async def store(self):
        """Create a fresh store for each test and clear Redis."""
        await confirmation_cache.clear_namespace()
        return PendingActionsStore(ttl_minutes=10)
    
    @pytest.fixture
    def sample_action_params(self):
        """Sample parameters for storing an action."""
        return {
            "user_id": "user_123",
            "session_id": "session_456",
            "integration": "jira",
            "tool_name": "create_jira_issue",
            "action_type": "create",
            "risk_level": "medium",
            "parameters": {
                "summary": "Test Issue",
                "project": "PROJ",
                "description": "This is a test"
            }
        }
    
    async def test_store_initialization(self, store):
        """Test store initializes with correct TTL."""
        assert store._ttl_seconds == 600  # 10 minutes in seconds
    
    async def test_store_action_success(self, store, sample_action_params):
        """Test storing a new action returns action_id."""
        action_id = await store.store_action(**sample_action_params)
        
        assert action_id.startswith("action_")
        assert len(action_id) == 19  # "action_" + 12 hex chars
    
    async def test_store_action_creates_entry(self, store, sample_action_params):
        """Test stored action can be retrieved."""
        action_id = await store.store_action(**sample_action_params)
        
        action = await store.get_action(action_id)
        
        assert action is not None
        assert action.action_id == action_id
        assert action.user_id == sample_action_params["user_id"]
        assert action.integration == sample_action_params["integration"]
        assert action.tool_name == sample_action_params["tool_name"]
        assert action.action_type == sample_action_params["action_type"]
        assert action.risk_level == sample_action_params["risk_level"]
        assert action.parameters == sample_action_params["parameters"]
    
    async def test_store_action_sets_timestamps(self, store, sample_action_params):
        """Test stored action has correct timestamps (ISO strings)."""
        before = datetime.now()
        action_id = await store.store_action(**sample_action_params)
        after = datetime.now()
        
        action = await store.get_action(action_id)
        
        # Parse ISO strings back to datetime
        created_at = datetime.fromisoformat(action.created_at)
        expires_at = datetime.fromisoformat(action.expires_at)
        
        assert before <= created_at <= after
        assert expires_at > created_at
        # Check TTL is approximately correct (within 1 second tolerance)
        expected_ttl = timedelta(minutes=10)
        actual_ttl = expires_at - created_at
        assert abs((actual_ttl - expected_ttl).total_seconds()) < 1
    
    async def test_store_multiple_actions(self, store):
        """Test storing multiple actions generates unique IDs."""
        action_id_1 = await store.store_action(
            user_id="user_1",
            session_id="session_1",
            integration="jira",
            tool_name="create_jira_issue",
            action_type="create",
            risk_level="low",
            parameters={"summary": "Issue 1"}
        )
        
        action_id_2 = await store.store_action(
            user_id="user_2",
            session_id="session_2",
            integration="email",
            tool_name="send_email",
            action_type="send",
            risk_level="high",
            parameters={"to": "test@example.com"}
        )
        
        assert action_id_1 != action_id_2
        assert await store.get_action(action_id_1) is not None
        assert await store.get_action(action_id_2) is not None
    
    async def test_get_action_not_found(self, store):
        """Test getting non-existent action returns None."""
        result = await store.get_action("action_nonexistent")
        
        assert result is None
    
    async def test_get_action_expired(self, store):
        """Test getting expired action returns None and removes it."""
        # Store action with very short TTL
        short_ttl_store = PendingActionsStore(ttl_minutes=0.01)  # ~0.6 seconds
        action_id = await short_ttl_store.store_action(
            user_id="user_123",
            session_id="session_456",
            integration="jira",
            tool_name="create_jira_issue",
            action_type="create",
            risk_level="low",
            parameters={}
        )
        
        # Wait for expiry
        await asyncio.sleep(1)
        
        result = await store.get_action(action_id)
        
        # Should return None (expired or removed by Redis TTL)
        assert result is None
    
    async def test_delete_action_success(self, store, sample_action_params):
        """Test deleting an existing action."""
        action_id = await store.store_action(**sample_action_params)
        
        result = await store.delete_action(action_id)
        
        assert result is True
        assert await store.get_action(action_id) is None
    
    async def test_delete_action_not_found(self, store):
        """Test deleting non-existent action returns False."""
        result = await store.delete_action("action_nonexistent")
        
        assert result is False
    
    async def test_get_user_actions_single_session(self, store):
        """Test getting actions for a specific user and session."""
        # Store actions for different users and sessions
        action_1 = await store.store_action(
            user_id="user_alice",
            session_id="session_1",
            integration="jira",
            tool_name="create_jira_issue",
            action_type="create",
            risk_level="low",
            parameters={"summary": "Alice Issue 1"}
        )
        
        action_2 = await store.store_action(
            user_id="user_alice",
            session_id="session_1",
            integration="jira",
            tool_name="add_jira_comment",
            action_type="update",
            risk_level="low",
            parameters={"comment": "Test"}
        )
        
        action_3 = await store.store_action(
            user_id="user_alice",
            session_id="session_2",
            integration="email",
            tool_name="send_email",
            action_type="send",
            risk_level="medium",
            parameters={"to": "alice@example.com"}
        )
        
        action_4 = await store.store_action(
            user_id="user_bob",
            session_id="session_3",
            integration="jira",
            tool_name="create_jira_issue",
            action_type="create",
            risk_level="high",
            parameters={"summary": "Bob Issue"}
        )
        
        # Get Alice's actions for session_1
        actions = await store.get_user_actions("user_alice", session_id="session_1")
        
        assert len(actions) == 2
        action_ids = [a.action_id for a in actions]
        assert action_1 in action_ids
        assert action_2 in action_ids
        assert action_3 not in action_ids
        assert action_4 not in action_ids
    
    async def test_get_user_actions_all_sessions(self, store):
        """Test getting all actions for a user across sessions."""
        action_1 = await store.store_action(
            user_id="user_alice",
            session_id="session_1",
            integration="jira",
            tool_name="create_jira_issue",
            action_type="create",
            risk_level="low",
            parameters={}
        )
        
        action_2 = await store.store_action(
            user_id="user_alice",
            session_id="session_2",
            integration="email",
            tool_name="send_email",
            action_type="send",
            risk_level="medium",
            parameters={}
        )
        
        action_3 = await store.store_action(
            user_id="user_bob",
            session_id="session_3",
            integration="jira",
            tool_name="create_jira_issue",
            action_type="create",
            risk_level="high",
            parameters={}
        )
        
        # Get all of Alice's actions
        actions = await store.get_user_actions("user_alice")
        
        assert len(actions) == 2
        action_ids = [a.action_id for a in actions]
        assert action_1 in action_ids
        assert action_2 in action_ids
        assert action_3 not in action_ids
    
    async def test_get_user_actions_excludes_expired(self, store):
        """Test get_user_actions excludes expired actions."""
        # Store active action
        active_action = await store.store_action(
            user_id="user_alice",
            session_id="session_1",
            integration="jira",
            tool_name="create_jira_issue",
            action_type="create",
            risk_level="low",
            parameters={}
        )
        
        # Store expired action with very short TTL
        short_ttl_store = PendingActionsStore(ttl_minutes=0.01)
        expired_action = await short_ttl_store.store_action(
            user_id="user_alice",
            session_id="session_1",
            integration="email",
            tool_name="send_email",
            action_type="send",
            risk_level="medium",
            parameters={}
        )
        
        await asyncio.sleep(1)  # Ensure expiry
        
        actions = await store.get_user_actions("user_alice")
        
        # Only active action should be returned
        assert len(actions) == 1
        assert actions[0].action_id == active_action
    
    async def test_cleanup_expired(self, store):
        """Test cleanup_expired returns 0 (Redis TTL handles cleanup)."""
        # Store some actions
        await store.store_action(
            user_id="user_alice",
            session_id="session_1",
            integration="jira",
            tool_name="create_jira_issue",
            action_type="create",
            risk_level="low",
            parameters={}
        )
        
        count = await store.cleanup_expired()
        
        # Redis handles cleanup automatically, so count should be 0
        assert count == 0
    
    async def test_cleanup_expired_none(self, store):
        """Test cleanup_expired with no actions."""
        count = await store.cleanup_expired()
        
        assert count == 0
    
    async def test_get_stats(self, store):
        """Test get_stats returns basic info about Redis backend."""
        stats = await store.get_stats()
        
        assert stats["storage_backend"] == "redis"
        assert stats["cache_namespace"] == "confirmation"
        assert stats["ttl_seconds"] == 600  # 10 minutes
        assert "note" in stats
    
    async def test_clear_all(self, store):
        """Test clear_all removes all actions."""
        await store.store_action(
            user_id="user_1",
            session_id="session_1",
            integration="jira",
            tool_name="create_jira_issue",
            action_type="create",
            risk_level="low",
            parameters={}
        )
        
        await store.store_action(
            user_id="user_2",
            session_id="session_2",
            integration="email",
            tool_name="send_email",
            action_type="send",
            risk_level="high",
            parameters={}
        )
        
        count = await store.clear_all()
        
        # Should have cleared both actions
        assert count >= 2
    
    async def test_clear_all_empty_store(self, store):
        """Test clear_all on empty store."""
        count = await store.clear_all()
        
        assert count == 0
    
    def test_generate_action_id_uniqueness(self):
        """Test action ID generation creates unique IDs."""
        ids = set()
        
        for _ in range(1000):
            action_id = PendingActionsStore._generate_action_id()
            ids.add(action_id)
        
        # All IDs should be unique
        assert len(ids) == 1000
        
        # All IDs should start with "action_"
        for action_id in ids:
            assert action_id.startswith("action_")
    
    async def test_different_integrations(self, store):
        """Test storing actions for different integrations."""
        integrations = ["jira", "email", "github", "confluence", "slack"]
        
        for integration in integrations:
            await store.store_action(
                user_id="user_123",
                session_id="session_456",
                integration=integration,
                tool_name=f"{integration}_tool",
                action_type="create",
                risk_level="medium",
                parameters={}
            )
        
        # Verify all actions stored
        for integration in integrations:
            actions = await store.get_user_actions("user_123")
            assert len(actions) == len(integrations)
    
    async def test_different_risk_levels(self, store):
        """Test storing actions with different risk levels."""
        risk_levels = ["low", "medium", "high"]
        
        for risk in risk_levels:
            await store.store_action(
                user_id="user_123",
                session_id="session_456",
                integration="jira",
                tool_name="create_jira_issue",
                action_type="create",
                risk_level=risk,
                parameters={}
            )
        
        actions = await store.get_user_actions("user_123")
        assert len(actions) == len(risk_levels)
        
        # Verify risk levels
        found_risks = {action.risk_level for action in actions}
        assert found_risks == set(risk_levels)
    
    async def test_from_dict_deserialization(self):
        """Test PendingAction.from_dict deserialization."""
        now = datetime.now()
        expires = now + timedelta(minutes=10)
        
        data = {
            "action_id": "action_123",
            "user_id": "user_456",
            "session_id": "session_789",
            "integration": "jira",
            "tool_name": "create_jira_issue",
            "action_type": "create",
            "risk_level": "medium",
            "parameters": {"summary": "Test"},
            "created_at": now.isoformat(),
            "expires_at": expires.isoformat()
        }
        
        action = PendingAction.from_dict(data)
        
        assert action.action_id == "action_123"
        assert action.user_id == "user_456"
        assert action.integration == "jira"
        assert isinstance(action.created_at, str)
        assert isinstance(action.expires_at, str)
