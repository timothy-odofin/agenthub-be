"""
Unit tests for PendingActionsStore.

Tests cover:
- Action storage and retrieval
- TTL expiry behavior
- Thread safety
- User filtering
- Cleanup operations
- Edge cases and error handling
"""

import pytest
from datetime import datetime, timedelta
from time import sleep
from threading import Thread
from typing import List

from src.app.core.confirmation.pending_actions_store import (
    PendingActionsStore,
    PendingAction
)


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
            created_at=now,
            expires_at=expires
        )
        
        assert action.action_id == "action_123"
        assert action.user_id == "user_456"
        assert action.session_id == "session_789"
        assert action.integration == "jira"
        assert action.tool_name == "create_jira_issue"
        assert action.action_type == "create"
        assert action.risk_level == "medium"
        assert action.parameters == {"summary": "Test", "project": "PROJ"}
        assert action.created_at == now
        assert action.expires_at == expires
    
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
            created_at=now,
            expires_at=expires
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
            created_at=now - timedelta(minutes=10),
            expires_at=expires
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
            created_at=now,
            expires_at=expires
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


class TestPendingActionsStore:
    """Tests for PendingActionsStore."""
    
    @pytest.fixture
    def store(self):
        """Create a fresh store for each test."""
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
    
    def test_store_initialization(self, store):
        """Test store initializes with correct TTL."""
        assert store._ttl_minutes == 10
        assert len(store._store) == 0
    
    def test_store_action_success(self, store, sample_action_params):
        """Test storing a new action returns action_id."""
        action_id = store.store_action(**sample_action_params)
        
        assert action_id.startswith("action_")
        assert len(action_id) == 19  # "action_" + 12 hex chars
    
    def test_store_action_creates_entry(self, store, sample_action_params):
        """Test stored action can be retrieved."""
        action_id = store.store_action(**sample_action_params)
        
        action = store.get_action(action_id)
        
        assert action is not None
        assert action.action_id == action_id
        assert action.user_id == sample_action_params["user_id"]
        assert action.integration == sample_action_params["integration"]
        assert action.tool_name == sample_action_params["tool_name"]
        assert action.action_type == sample_action_params["action_type"]
        assert action.risk_level == sample_action_params["risk_level"]
        assert action.parameters == sample_action_params["parameters"]
    
    def test_store_action_sets_timestamps(self, store, sample_action_params):
        """Test stored action has correct timestamps."""
        before = datetime.now()
        action_id = store.store_action(**sample_action_params)
        after = datetime.now()
        
        action = store.get_action(action_id)
        
        assert before <= action.created_at <= after
        assert action.expires_at > action.created_at
        # Check TTL is approximately correct (within 1 second tolerance)
        expected_ttl = timedelta(minutes=10)
        actual_ttl = action.expires_at - action.created_at
        assert abs((actual_ttl - expected_ttl).total_seconds()) < 1
    
    def test_store_multiple_actions(self, store):
        """Test storing multiple actions generates unique IDs."""
        action_id_1 = store.store_action(
            user_id="user_1",
            session_id="session_1",
            integration="jira",
            tool_name="create_jira_issue",
            action_type="create",
            risk_level="low",
            parameters={"summary": "Issue 1"}
        )
        
        action_id_2 = store.store_action(
            user_id="user_2",
            session_id="session_2",
            integration="email",
            tool_name="send_email",
            action_type="send",
            risk_level="high",
            parameters={"to": "test@example.com"}
        )
        
        assert action_id_1 != action_id_2
        assert store.get_action(action_id_1) is not None
        assert store.get_action(action_id_2) is not None
    
    def test_get_action_not_found(self, store):
        """Test getting non-existent action returns None."""
        result = store.get_action("action_nonexistent")
        
        assert result is None
    
    def test_get_action_expired(self, store):
        """Test getting expired action returns None and removes it."""
        # Store action with 0-minute TTL (immediately expired)
        store._ttl_minutes = 0
        action_id = store.store_action(
            user_id="user_123",
            session_id="session_456",
            integration="jira",
            tool_name="create_jira_issue",
            action_type="create",
            risk_level="low",
            parameters={}
        )
        
        # Small delay to ensure expiry
        sleep(0.1)
        
        result = store.get_action(action_id)
        
        assert result is None
        # Verify it was removed from store
        assert action_id not in store._store
    
    def test_delete_action_success(self, store, sample_action_params):
        """Test deleting an existing action."""
        action_id = store.store_action(**sample_action_params)
        
        result = store.delete_action(action_id)
        
        assert result is True
        assert store.get_action(action_id) is None
    
    def test_delete_action_not_found(self, store):
        """Test deleting non-existent action returns False."""
        result = store.delete_action("action_nonexistent")
        
        assert result is False
    
    def test_get_user_actions_single_session(self, store):
        """Test getting actions for a specific user and session."""
        # Store actions for different users and sessions
        action_1 = store.store_action(
            user_id="user_alice",
            session_id="session_1",
            integration="jira",
            tool_name="create_jira_issue",
            action_type="create",
            risk_level="low",
            parameters={"summary": "Alice Issue 1"}
        )
        
        action_2 = store.store_action(
            user_id="user_alice",
            session_id="session_1",
            integration="jira",
            tool_name="add_jira_comment",
            action_type="update",
            risk_level="low",
            parameters={"comment": "Test"}
        )
        
        action_3 = store.store_action(
            user_id="user_alice",
            session_id="session_2",
            integration="email",
            tool_name="send_email",
            action_type="send",
            risk_level="medium",
            parameters={"to": "alice@example.com"}
        )
        
        action_4 = store.store_action(
            user_id="user_bob",
            session_id="session_3",
            integration="jira",
            tool_name="create_jira_issue",
            action_type="create",
            risk_level="high",
            parameters={"summary": "Bob Issue"}
        )
        
        # Get Alice's actions for session_1
        actions = store.get_user_actions("user_alice", session_id="session_1")
        
        assert len(actions) == 2
        action_ids = [a.action_id for a in actions]
        assert action_1 in action_ids
        assert action_2 in action_ids
        assert action_3 not in action_ids
        assert action_4 not in action_ids
    
    def test_get_user_actions_all_sessions(self, store):
        """Test getting all actions for a user across sessions."""
        action_1 = store.store_action(
            user_id="user_alice",
            session_id="session_1",
            integration="jira",
            tool_name="create_jira_issue",
            action_type="create",
            risk_level="low",
            parameters={}
        )
        
        action_2 = store.store_action(
            user_id="user_alice",
            session_id="session_2",
            integration="email",
            tool_name="send_email",
            action_type="send",
            risk_level="medium",
            parameters={}
        )
        
        action_3 = store.store_action(
            user_id="user_bob",
            session_id="session_3",
            integration="jira",
            tool_name="create_jira_issue",
            action_type="create",
            risk_level="high",
            parameters={}
        )
        
        # Get all of Alice's actions
        actions = store.get_user_actions("user_alice")
        
        assert len(actions) == 2
        action_ids = [a.action_id for a in actions]
        assert action_1 in action_ids
        assert action_2 in action_ids
        assert action_3 not in action_ids
    
    def test_get_user_actions_excludes_expired(self, store):
        """Test get_user_actions excludes and cleans up expired actions."""
        # Store active action
        active_action = store.store_action(
            user_id="user_alice",
            session_id="session_1",
            integration="jira",
            tool_name="create_jira_issue",
            action_type="create",
            risk_level="low",
            parameters={}
        )
        
        # Store expired action by manipulating TTL
        store._ttl_minutes = 0
        expired_action = store.store_action(
            user_id="user_alice",
            session_id="session_1",
            integration="email",
            tool_name="send_email",
            action_type="send",
            risk_level="medium",
            parameters={}
        )
        store._ttl_minutes = 10  # Restore TTL
        
        sleep(0.1)  # Ensure expiry
        
        actions = store.get_user_actions("user_alice")
        
        # Only active action should be returned
        assert len(actions) == 1
        assert actions[0].action_id == active_action
        # Expired action should be removed
        assert expired_action not in store._store
    
    def test_cleanup_expired(self, store):
        """Test cleanup_expired removes only expired actions."""
        # Store active action
        store.store_action(
            user_id="user_alice",
            session_id="session_1",
            integration="jira",
            tool_name="create_jira_issue",
            action_type="create",
            risk_level="low",
            parameters={}
        )
        
        # Store expired actions
        store._ttl_minutes = 0
        store.store_action(
            user_id="user_bob",
            session_id="session_2",
            integration="email",
            tool_name="send_email",
            action_type="send",
            risk_level="medium",
            parameters={}
        )
        store.store_action(
            user_id="user_charlie",
            session_id="session_3",
            integration="github",
            tool_name="create_github_issue",
            action_type="create",
            risk_level="high",
            parameters={}
        )
        store._ttl_minutes = 10  # Restore TTL
        
        sleep(0.1)  # Ensure expiry
        
        count = store.cleanup_expired()
        
        assert count == 2
        assert len(store._store) == 1
    
    def test_cleanup_expired_none(self, store):
        """Test cleanup_expired with no expired actions."""
        store.store_action(
            user_id="user_alice",
            session_id="session_1",
            integration="jira",
            tool_name="create_jira_issue",
            action_type="create",
            risk_level="low",
            parameters={}
        )
        
        count = store.cleanup_expired()
        
        assert count == 0
        assert len(store._store) == 1
    
    def test_get_stats_empty_store(self, store):
        """Test get_stats on empty store."""
        stats = store.get_stats()
        
        assert stats["total_actions"] == 0
        assert stats["active_actions"] == 0
        assert stats["expired_actions"] == 0
        assert stats["by_integration"] == {}
        assert stats["by_risk_level"] == {}
    
    def test_get_stats_with_actions(self, store):
        """Test get_stats with multiple actions."""
        store.store_action(
            user_id="user_1",
            session_id="session_1",
            integration="jira",
            tool_name="create_jira_issue",
            action_type="create",
            risk_level="low",
            parameters={}
        )
        
        store.store_action(
            user_id="user_2",
            session_id="session_2",
            integration="jira",
            tool_name="add_jira_comment",
            action_type="update",
            risk_level="medium",
            parameters={}
        )
        
        store.store_action(
            user_id="user_3",
            session_id="session_3",
            integration="email",
            tool_name="send_email",
            action_type="send",
            risk_level="high",
            parameters={}
        )
        
        stats = store.get_stats()
        
        assert stats["total_actions"] == 3
        assert stats["active_actions"] == 3
        assert stats["expired_actions"] == 0
        assert stats["by_integration"] == {"jira": 2, "email": 1}
        assert stats["by_risk_level"] == {"low": 1, "medium": 1, "high": 1}
    
    def test_get_stats_excludes_expired(self, store):
        """Test get_stats counts expired actions separately."""
        # Active action
        store.store_action(
            user_id="user_1",
            session_id="session_1",
            integration="jira",
            tool_name="create_jira_issue",
            action_type="create",
            risk_level="low",
            parameters={}
        )
        
        # Expired action
        store._ttl_minutes = 0
        store.store_action(
            user_id="user_2",
            session_id="session_2",
            integration="email",
            tool_name="send_email",
            action_type="send",
            risk_level="high",
            parameters={}
        )
        store._ttl_minutes = 10
        
        sleep(0.1)
        
        stats = store.get_stats()
        
        assert stats["total_actions"] == 2
        assert stats["active_actions"] == 1
        assert stats["expired_actions"] == 1
        assert stats["by_integration"] == {"jira": 1}
        assert stats["by_risk_level"] == {"low": 1}
    
    def test_clear_all(self, store):
        """Test clear_all removes all actions."""
        store.store_action(
            user_id="user_1",
            session_id="session_1",
            integration="jira",
            tool_name="create_jira_issue",
            action_type="create",
            risk_level="low",
            parameters={}
        )
        
        store.store_action(
            user_id="user_2",
            session_id="session_2",
            integration="email",
            tool_name="send_email",
            action_type="send",
            risk_level="high",
            parameters={}
        )
        
        count = store.clear_all()
        
        assert count == 2
        assert len(store._store) == 0
    
    def test_clear_all_empty_store(self, store):
        """Test clear_all on empty store."""
        count = store.clear_all()
        
        assert count == 0
        assert len(store._store) == 0
    
    def test_thread_safety(self, store):
        """Test concurrent access from multiple threads."""
        action_ids: List[str] = []
        errors: List[Exception] = []
        
        def store_actions():
            try:
                for i in range(10):
                    action_id = store.store_action(
                        user_id=f"user_{i}",
                        session_id=f"session_{i}",
                        integration="jira",
                        tool_name="create_jira_issue",
                        action_type="create",
                        risk_level="low",
                        parameters={"index": i}
                    )
                    action_ids.append(action_id)
            except Exception as e:
                errors.append(e)
        
        # Create multiple threads
        threads = [Thread(target=store_actions) for _ in range(5)]
        
        # Start all threads
        for thread in threads:
            thread.start()
        
        # Wait for completion
        for thread in threads:
            thread.join()
        
        # Verify no errors occurred
        assert len(errors) == 0
        
        # Verify all actions were stored
        assert len(action_ids) == 50
        
        # Verify all action IDs are unique
        assert len(set(action_ids)) == 50
        
        # Verify all actions can be retrieved
        for action_id in action_ids:
            assert store.get_action(action_id) is not None
    
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
    
    def test_different_integrations(self, store):
        """Test storing actions for different integrations."""
        integrations = ["jira", "email", "github", "confluence", "slack"]
        
        for integration in integrations:
            store.store_action(
                user_id="user_123",
                session_id="session_456",
                integration=integration,
                tool_name=f"{integration}_tool",
                action_type="create",
                risk_level="medium",
                parameters={}
            )
        
        stats = store.get_stats()
        
        assert stats["total_actions"] == len(integrations)
        assert set(stats["by_integration"].keys()) == set(integrations)
    
    def test_different_risk_levels(self, store):
        """Test storing actions with different risk levels."""
        risk_levels = ["low", "medium", "high"]
        
        for risk in risk_levels:
            store.store_action(
                user_id="user_123",
                session_id="session_456",
                integration="jira",
                tool_name="create_jira_issue",
                action_type="create",
                risk_level=risk,
                parameters={}
            )
        
        stats = store.get_stats()
        
        assert stats["total_actions"] == len(risk_levels)
        assert set(stats["by_risk_level"].keys()) == set(risk_levels)
