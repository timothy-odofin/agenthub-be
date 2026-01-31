"""
Unit tests for ChatService.
"""
import pytest
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime

from app.services.chat_service import ChatService
from app.core.core_enums import AgentFramework, AgentType


class MockAgent:
    """Mock agent for testing."""
    
    def __init__(self):
        self.agent_type = AgentType.REACT
        self.framework = AgentFramework.LANGCHAIN
        self.verbose = False
    
    async def execute(self, user_input: str, session_id: str = None, protocol: str = None):
        from app.schemas.chat import AgentMessage
        return AgentMessage(
            content="Mock response to: " + user_input,
            timestamp=datetime.now(),
            session_id=session_id or "test_session",
            metadata={"mocked": True}
        )


@pytest.fixture
def clean_chat_service():
    """Ensure clean ChatService state for each test."""
    # Reset singleton state
    if hasattr(ChatService, '_instances'):
        ChatService._instances = {}
    yield
    # Cleanup after test
    if hasattr(ChatService, '_instances'):
        ChatService._instances = {}


class TestChatService:
    """Test ChatService singleton behavior."""
    
    def test_singleton_behavior(self, clean_chat_service):
        """Test that ChatService behaves as singleton."""
        # Act
        service1 = ChatService()
        service2 = ChatService()
        
        # Assert
        assert service1 is service2

    def test_framework_setting(self, clean_chat_service):
        """Test setting agent framework."""
        # Arrange
        service = ChatService()
        
        # Act
        service.set_agent_framework(AgentFramework.LANGGRAPH)
        
        # Assert
        assert service._agent_framework == AgentFramework.LANGGRAPH

    def test_agent_type_property(self, clean_chat_service):
        """Test agent type property access."""
        # Arrange
        service = ChatService()
        
        # Act & Assert
        assert service._agent_type == AgentType.REACT  # Default value


class TestChatServiceBasicFunctionality:
    """Test basic ChatService functionality."""
    
    def test_create_session_success(self, clean_chat_service):
        """Test successful session creation."""
        # Arrange
        service = ChatService()
        
        # Mock the session repository
        with patch('app.services.chat_service.SessionRepositoryFactory') as mock_factory:
            mock_repo = Mock()
            # Mock as a regular function instead of async
            mock_repo.create_session.return_value = "test_session_123"
            mock_factory.get_default_repository.return_value = mock_repo
            
            # Act
            session_id = service.create_session("user_123")
            
            # Assert
            assert session_id == "test_session_123"
    
    @pytest.mark.asyncio
    async def test_agent_lazy_initialization(self, clean_chat_service):
        """Test successful lazy agent initialization."""
        # Arrange
        service = ChatService()
        mock_agent = MockAgent()
        
        # Mock all dependencies
        with patch('app.services.chat_service.AgentFactory') as mock_agent_factory, \
             patch('app.llm.factory.llm_factory.LLMFactory') as mock_llm_factory, \
             patch('app.services.chat_service.SessionRepositoryFactory') as mock_session_factory:
            
            # Make create_agent return a coroutine that resolves to mock_agent
            async def create_agent_async(*args, **kwargs):
                return mock_agent
            mock_agent_factory.create_agent = create_agent_async
            
            mock_llm_factory.get_llm.return_value = Mock()
            mock_session_factory.get_default_repository.return_value = Mock()
            
            # Act
            agent = await service.agent
            
            # Assert
            assert agent is mock_agent
            assert service._agent is mock_agent
    
    @pytest.mark.asyncio
    async def test_get_available_tools_success(self, clean_chat_service):
        """Test successful tools retrieval."""
        # Arrange
        service = ChatService()
        mock_tools = [
            Mock(name="tool1", description="Tool 1 description"),
            Mock(name="tool2", description="Tool 2 description")
        ]
        # Configure Mock objects to return proper values when attributes are accessed
        mock_tools[0].name = "tool1"
        mock_tools[0].description = "Tool 1 description"
        mock_tools[1].name = "tool2"
        mock_tools[1].description = "Tool 2 description"
        
        # Act - patch the correct import path
        with patch('app.agent.tools.base.registry.ToolRegistry') as mock_registry:
            mock_registry.get_instantiated_tools.return_value = mock_tools
            tools = await service.get_available_tools()
        
        # Assert
        assert len(tools) == 2
        assert tools[0]["name"] == "tool1"
        assert tools[1]["description"] == "Tool 2 description"
    
    @pytest.mark.asyncio
    async def test_health_check_without_agent(self, clean_chat_service):
        """Test health check when agent is not initialized."""
        # Arrange
        service = ChatService()
        
        # Act - patch the correct import path
        with patch('app.agent.tools.base.registry.ToolRegistry') as mock_registry:
            mock_registry.get_instantiated_tools.return_value = []
            health = await service.health_check()
        
        # Assert
        assert health["status"] == "healthy"
        assert health["agent_initialized"] is False
        assert health["tools_available"] == 0
        assert health["agent_info"] is None
