"""
Unit tests for secured chat API endpoints.

Tests verify that chat endpoints properly use JWT authentication
and extract user_id from authenticated user instead of request body.
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime
from fastapi import HTTPException

from app.db.models.user import UserInDB


class TestSecuredChatEndpoints:
    """Test chat endpoints with JWT authentication."""

    @pytest.fixture
    def mock_user(self):
        """Create a mock authenticated user."""
        return UserInDB(
            id="user123",
            username="testuser",
            email="test@example.com",
            firstname="Test",
            lastname="User",
            password_hash="hashed_password",
            is_active=True,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )

    @pytest.fixture
    def mock_chat_service(self):
        """Create a mock chat service."""
        with patch("app.api.v1.chat.chat_service") as mock:
            yield mock

    @pytest.mark.asyncio
    async def test_send_message_with_auth(self, mock_user, mock_chat_service):
        """Test sending message extracts user_id from authenticated user."""
        from app.api.v1.chat import send_message
        from app.schemas.chat import ChatRequest
        
        # Arrange
        request = ChatRequest(
            message="Hello, AI!",
            session_id="session123"
        )
        
        mock_chat_service.chat = AsyncMock(return_value={
            "success": True,
            "message": "Hello! How can I help?",
            "session_id": "session123",
            "user_id": "user123",
            "timestamp": "2026-01-04T12:00:00",
            "processing_time_ms": 150.5,
            "tools_used": [],
            "errors": [],
            "metadata": {}
        })
        
        # Act
        response = await send_message(request, current_user=mock_user)
        
        # Assert
        assert response.success is True
        assert response.message == "Hello! How can I help?"
        assert response.session_id == "session123"
        assert response.user_id == "user123"
        
        # Verify chat service was called with correct user_id from authenticated user
        mock_chat_service.chat.assert_called_once_with(
            message="Hello, AI!",
            user_id="user123",
            session_id="session123",
            protocol="rest"
        )

    @pytest.mark.asyncio
    async def test_send_message_without_session_id(self, mock_user, mock_chat_service):
        """Test sending message without session_id creates new session."""
        from app.api.v1.chat import send_message
        from app.schemas.chat import ChatRequest
        
        # Arrange
        request = ChatRequest(
            message="Start new chat",
            session_id=None
        )
        
        mock_chat_service.chat = AsyncMock(return_value={
            "success": True,
            "message": "New session created",
            "session_id": "new_session_456",
            "user_id": "user123",
            "timestamp": "2026-01-04T12:00:00",
            "processing_time_ms": 100.0,
            "tools_used": [],
            "errors": [],
            "metadata": {}
        })
        
        # Act
        response = await send_message(request, current_user=mock_user)
        
        # Assert
        assert response.success is True
        assert response.session_id == "new_session_456"
        
        # Verify user_id from authenticated user was used
        mock_chat_service.chat.assert_called_once_with(
            message="Start new chat",
            user_id="user123",
            session_id=None,
            protocol="rest"
        )

    @pytest.mark.asyncio
    async def test_create_session_with_auth(self, mock_user, mock_chat_service):
        """Test creating session extracts user_id from authenticated user."""
        from app.api.v1.chat import create_session
        from app.schemas.chat import CreateSessionRequest
        
        # Arrange
        request = CreateSessionRequest(title="My Chat Session")
        
        mock_chat_service.create_session = MagicMock(return_value="session789")
        
        # Act
        response = await create_session(request, current_user=mock_user)
        
        # Assert
        assert response.success is True
        assert response.session_id == "session789"
        assert response.title == "My Chat Session"
        
        # Verify create_session was called with user_id from authenticated user
        mock_chat_service.create_session.assert_called_once_with(
            user_id="user123",
            title="My Chat Session"
        )

    @pytest.mark.asyncio
    async def test_create_session_without_title(self, mock_user, mock_chat_service):
        """Test creating session without title generates default title."""
        from app.api.v1.chat import create_session
        from app.schemas.chat import CreateSessionRequest
        
        # Arrange
        request = CreateSessionRequest(title=None)
        
        mock_chat_service.create_session = MagicMock(return_value="session999")
        
        # Act
        response = await create_session(request, current_user=mock_user)
        
        # Assert
        assert response.success is True
        assert response.session_id == "session999"
        assert "Chat session" in response.title
        
        # Verify user_id from authenticated user was used
        mock_chat_service.create_session.assert_called_once_with(
            user_id="user123",
            title=None
        )

    @pytest.mark.asyncio
    async def test_get_session_history_with_auth(self, mock_user, mock_chat_service):
        """Test getting session history uses authenticated user_id."""
        from app.api.v1.chat import get_session_history
        
        # Arrange
        mock_chat_service.get_session_history = AsyncMock(return_value=[
            {
                "role": "user",
                "content": "Hello",
                "timestamp": "2026-01-04T12:00:00",
                "id": "msg1"
            },
            {
                "role": "assistant",
                "content": "Hi there!",
                "timestamp": "2026-01-04T12:00:01",
                "id": "msg2"
            }
        ])
        
        # Act
        response = await get_session_history(
            session_id="session123",
            current_user=mock_user,
            limit=50
        )
        
        # Assert
        assert response.success is True
        assert response.session_id == "session123"
        assert response.count == 2
        assert len(response.messages) == 2
        assert response.messages[0].role == "user"
        assert response.messages[1].role == "assistant"
        
        # Verify get_session_history was called with user_id from authenticated user
        mock_chat_service.get_session_history.assert_called_once_with(
            user_id="user123",
            session_id="session123",
            limit=50
        )

    @pytest.mark.asyncio
    async def test_get_session_history_with_custom_limit(self, mock_user, mock_chat_service):
        """Test getting session history with custom limit parameter."""
        from app.api.v1.chat import get_session_history
        
        # Arrange
        mock_chat_service.get_session_history = AsyncMock(return_value=[])
        
        # Act
        response = await get_session_history(
            session_id="session456",
            current_user=mock_user,
            limit=10
        )
        
        # Assert
        assert response.success is True
        assert response.count == 0
        
        # Verify custom limit was passed
        mock_chat_service.get_session_history.assert_called_once_with(
            user_id="user123",
            session_id="session456",
            limit=10
        )

    @pytest.mark.asyncio
    async def test_list_user_sessions_with_auth(self, mock_user, mock_chat_service):
        """Test listing sessions uses authenticated user_id."""
        from app.api.v1.chat import list_user_sessions
        
        # Arrange
        mock_chat_service.list_user_sessions = MagicMock(return_value={
            "sessions": [
                {
                    "session_id": "session1",
                    "title": "First Chat",
                    "created_at": "2026-01-01T10:00:00",
                    "last_message_at": "2026-01-01T10:30:00",
                    "message_count": 5
                },
                {
                    "session_id": "session2",
                    "title": "Second Chat",
                    "created_at": "2026-01-02T14:00:00",
                    "last_message_at": "2026-01-02T14:15:00",
                    "message_count": 3
                }
            ],
            "total": 2,
            "has_more": False
        })
        
        # Act
        response = await list_user_sessions(
            current_user=mock_user,
            page=0,
            limit=10
        )
        
        # Assert
        assert response.success is True
        assert response.total == 2
        assert len(response.sessions) == 2
        assert response.sessions[0].session_id == "session1"
        assert response.sessions[1].session_id == "session2"
        assert response.has_more is False
        
        # Verify list_user_sessions was called with user_id from authenticated user
        mock_chat_service.list_user_sessions.assert_called_once_with(
            user_id="user123",
            page=0,
            limit=10
        )

    @pytest.mark.asyncio
    async def test_list_user_sessions_with_pagination(self, mock_user, mock_chat_service):
        """Test listing sessions with pagination parameters."""
        from app.api.v1.chat import list_user_sessions
        
        # Arrange
        mock_chat_service.list_user_sessions = MagicMock(return_value={
            "sessions": [],
            "total": 25,
            "has_more": True
        })
        
        # Act
        response = await list_user_sessions(
            current_user=mock_user,
            page=2,
            limit=5
        )
        
        # Assert
        assert response.success is True
        assert response.page == 2
        assert response.limit == 5
        assert response.total == 25
        assert response.has_more is True
        
        # Verify pagination parameters were passed correctly
        mock_chat_service.list_user_sessions.assert_called_once_with(
            user_id="user123",
            page=2,
            limit=5
        )


class TestChatEndpointsAuthRequired:
    """Test that chat endpoints require authentication."""

    @pytest.mark.asyncio
    async def test_send_message_requires_auth(self):
        """Test that send_message endpoint requires authentication."""
        from app.api.v1.chat import send_message
        from app.schemas.chat import ChatRequest
        
        # This test verifies the endpoint signature requires authentication
        # In practice, FastAPI will raise 401 if get_current_user dependency fails
        
        request = ChatRequest(message="Test", session_id=None)
        
        # Endpoint should have current_user parameter with Depends(get_current_user)
        import inspect
        sig = inspect.signature(send_message)
        
        assert "current_user" in sig.parameters
        assert sig.parameters["current_user"].annotation.__name__ == "UserInDB"

    def test_create_session_requires_auth(self):
        """Test that create_session endpoint requires authentication."""
        from app.api.v1.chat import create_session
        
        import inspect
        sig = inspect.signature(create_session)
        
        assert "current_user" in sig.parameters
        assert sig.parameters["current_user"].annotation.__name__ == "UserInDB"

    @pytest.mark.asyncio
    async def test_get_session_history_requires_auth(self):
        """Test that get_session_history endpoint requires authentication."""
        from app.api.v1.chat import get_session_history
        
        import inspect
        sig = inspect.signature(get_session_history)
        
        assert "current_user" in sig.parameters
        assert sig.parameters["current_user"].annotation.__name__ == "UserInDB"

    def test_list_user_sessions_requires_auth(self):
        """Test that list_user_sessions endpoint requires authentication."""
        from app.api.v1.chat import list_user_sessions
        
        import inspect
        sig = inspect.signature(list_user_sessions)
        
        assert "current_user" in sig.parameters
        assert sig.parameters["current_user"].annotation.__name__ == "UserInDB"


class TestChatSchemasUpdated:
    """Test that chat schemas no longer contain user_id."""

    def test_chat_request_no_user_id(self):
        """Test that ChatRequest schema doesn't have user_id field."""
        from app.schemas.chat import ChatRequest
        
        # Create request without user_id
        request = ChatRequest(
            message="Hello",
            session_id="session123"
        )
        
        assert request.message == "Hello"
        assert request.session_id == "session123"
        assert not hasattr(request, "user_id")

    def test_create_session_request_no_user_id(self):
        """Test that CreateSessionRequest schema doesn't have user_id field."""
        from app.schemas.chat import CreateSessionRequest
        
        # Create request without user_id
        request = CreateSessionRequest(title="My Session")
        
        assert request.title == "My Session"
        assert not hasattr(request, "user_id")

    def test_chat_request_schema_fields(self):
        """Test ChatRequest has only message and session_id fields."""
        from app.schemas.chat import ChatRequest
        
        # Get schema fields
        fields = ChatRequest.model_fields
        
        assert "message" in fields
        assert "session_id" in fields
        assert "user_id" not in fields
        assert len(fields) == 2

    def test_create_session_request_schema_fields(self):
        """Test CreateSessionRequest has only title field."""
        from app.schemas.chat import CreateSessionRequest
        
        # Get schema fields
        fields = CreateSessionRequest.model_fields
        
        assert "title" in fields
        assert "user_id" not in fields
        assert len(fields) == 1
