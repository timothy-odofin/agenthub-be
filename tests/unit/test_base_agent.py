"""
Unit tests for BaseAgent abstract class.

Tests the abstract base class that defines the interface for all agent implementations.
Tests both the concrete methods and proper abstraction enforcement.
Following Python open-source testing best practices.
"""

import pytest
from unittest.mock import Mock, patch
from typing import Set, Dict, Any
from abc import ABC

from app.agent.base.base_agent import BaseAgent
from app.core.enums import AgentType, AgentFramework, AgentCapability, AgentStatus
from app.agent.models import AgentContext, AgentResponse


class ConcreteAgentImplementation(BaseAgent):
    """Concrete implementation of BaseAgent for testing."""
    
    def __init__(
        self,
        agent_type: AgentType = AgentType.REACT,
        framework: AgentFramework = AgentFramework.LANGCHAIN,
        test_name: str = "Test Agent",
        test_version: str = "1.0.0",
        test_capabilities: Set[AgentCapability] = None
    ):
        super().__init__(agent_type, framework)
        self._test_name = test_name
        self._test_version = test_version
        self._test_capabilities = test_capabilities or {
            AgentCapability.REACT,
            AgentCapability.TOOL_CALLING
        }
        self.execute_called = False
        self.initialize_called = False
        self.shutdown_called = False
    
    @property
    def name(self) -> str:
        return self._test_name
    
    @property
    def version(self) -> str:
        return self._test_version
    
    async def initialize(self) -> None:
        self._initialized = True
        self.initialize_called = True
    
    async def execute(self, query: str, context: AgentContext) -> AgentResponse:
        self.execute_called = True
        return AgentResponse(
            content=f"Processed: {query}",
            status=AgentStatus.COMPLETED,
            session_id=context.session_id,
            request_id=context.request_id
        )
    
    def get_supported_capabilities(self) -> Set[AgentCapability]:
        return self._test_capabilities
    
    def get_configuration_schema(self) -> Dict[str, Any]:
        return {
            "test_param": {
                "type": "string",
                "default": "default_value",
                "description": "Test parameter"
            }
        }
    
    async def shutdown(self) -> None:
        self.shutdown_called = True
        await super().shutdown()


class IncompleteAgentImplementation(BaseAgent):
    """Incomplete implementation for testing abstract method enforcement."""
    
    def __init__(self):
        super().__init__(AgentType.REACT, AgentFramework.LANGCHAIN)
    
    @property
    def name(self) -> str:
        return "Incomplete Agent"
    
    # Missing other abstract methods intentionally


@pytest.fixture
def agent_context():
    """Fixture providing a standard AgentContext for testing."""
    return AgentContext(
        user_id="test_user",
        session_id="test_session",
        request_id="test_request",
        metadata={"test": "data"},
        max_iterations=5
    )


@pytest.fixture
def concrete_agent():
    """Fixture providing a concrete agent instance for testing."""
    return ConcreteAgentImplementation()


class TestBaseAgentInitialization:
    """Test suite for BaseAgent initialization and basic properties."""
    
    def test_initialization_with_required_params(self):
        """Test that BaseAgent initializes correctly with required parameters."""
        # Act
        agent = ConcreteAgentImplementation(
            agent_type=AgentType.PLANNING,
            framework=AgentFramework.LANGGRAPH
        )
        
        # Assert
        assert agent.agent_type == AgentType.PLANNING
        assert agent.framework == AgentFramework.LANGGRAPH
        assert agent._initialized is False
        assert agent.logger is not None
    
    def test_initialization_sets_logger_with_class_name(self):
        """Test that logger is set up with the correct class name."""
        # Arrange & Act
        with patch('app.agent.base.base_agent.get_logger') as mock_get_logger:
            agent = ConcreteAgentImplementation()
            
            # Assert
            mock_get_logger.assert_called_once_with('ConcreteAgentImplementation')
    
    def test_default_initialized_state(self, concrete_agent):
        """Test that agents start in uninitialized state."""
        # Assert
        assert concrete_agent._initialized is False


class TestBaseAgentAbstractMethods:
    """Test suite for abstract method enforcement."""
    
    def test_cannot_instantiate_base_agent_directly(self):
        """Test that BaseAgent cannot be instantiated directly."""
        # Act & Assert
        with pytest.raises(TypeError) as exc_info:
            BaseAgent(AgentType.REACT, AgentFramework.LANGCHAIN)
        
        assert "Can't instantiate abstract class BaseAgent" in str(exc_info.value)
    
    def test_incomplete_implementation_raises_type_error(self):
        """Test that incomplete implementations cannot be instantiated."""
        # Act & Assert
        with pytest.raises(TypeError) as exc_info:
            IncompleteAgentImplementation()
        
        error_message = str(exc_info.value)
        assert "Can't instantiate abstract class" in error_message
        assert "IncompleteAgentImplementation" in error_message
    
    def test_concrete_implementation_can_be_instantiated(self):
        """Test that complete implementations can be instantiated."""
        # Act
        agent = ConcreteAgentImplementation()
        
        # Assert
        assert isinstance(agent, BaseAgent)
        assert isinstance(agent, ConcreteAgentImplementation)


class TestBaseAgentConcreteMethodsReturnTypes:
    """Test suite for concrete methods and their return types."""
    
    @pytest.mark.asyncio
    async def test_health_check_returns_correct_structure(self, concrete_agent):
        """Test that health_check returns the expected dictionary structure."""
        # Act
        health_data = await concrete_agent.health_check()
        
        # Assert
        expected_keys = {
            "name", "version", "type", "framework", 
            "initialized", "capabilities"
        }
        assert set(health_data.keys()) == expected_keys
        
        # Check data types and values
        assert isinstance(health_data["name"], str)
        assert isinstance(health_data["version"], str)
        assert isinstance(health_data["type"], str)
        assert isinstance(health_data["framework"], str)
        assert isinstance(health_data["initialized"], bool)
        assert isinstance(health_data["capabilities"], list)
        
        assert health_data["name"] == "Test Agent"
        assert health_data["version"] == "1.0.0"
        assert health_data["type"] == "react"
        assert health_data["framework"] == "langchain"
        assert health_data["initialized"] is False
    
    @pytest.mark.asyncio
    async def test_health_check_capabilities_format(self, concrete_agent):
        """Test that health_check formats capabilities correctly."""
        # Act
        health_data = await concrete_agent.health_check()
        
        # Assert
        capabilities = health_data["capabilities"]
        expected_capabilities = ["react", "tool_calling"]
        assert sorted(capabilities) == sorted(expected_capabilities)
        
        # Verify all capabilities are strings
        for cap in capabilities:
            assert isinstance(cap, str)
    
    @pytest.mark.asyncio
    async def test_health_check_reflects_initialization_state(self, concrete_agent):
        """Test that health_check reflects the current initialization state."""
        # Initial state
        health_data = await concrete_agent.health_check()
        assert health_data["initialized"] is False
        
        # After initialization
        await concrete_agent.initialize()
        health_data = await concrete_agent.health_check()
        assert health_data["initialized"] is True
    
    def test_supports_capability_true(self, concrete_agent):
        """Test supports_capability returns True for supported capabilities."""
        # Act & Assert
        assert concrete_agent.supports_capability(AgentCapability.REACT) is True
        assert concrete_agent.supports_capability(AgentCapability.TOOL_CALLING) is True
    
    def test_supports_capability_false(self, concrete_agent):
        """Test supports_capability returns False for unsupported capabilities."""
        # Act & Assert
        assert concrete_agent.supports_capability(AgentCapability.PLANNING) is False
        assert concrete_agent.supports_capability(AgentCapability.CODE_GENERATION) is False
    
    @pytest.mark.asyncio
    async def test_shutdown_default_implementation(self, concrete_agent):
        """Test that shutdown method has a default implementation that does nothing."""
        # Act
        await concrete_agent.shutdown()
        
        # Assert - Should not raise any exception
        assert concrete_agent.shutdown_called is True


class TestBaseAgentWithDifferentConfigurations:
    """Test suite for BaseAgent with various configurations."""
    
    @pytest.mark.parametrize("agent_type,framework", [
        (AgentType.REACT, AgentFramework.LANGCHAIN),
        (AgentType.REACT, AgentFramework.LANGGRAPH),
        (AgentType.PLANNING, AgentFramework.LANGCHAIN),
        (AgentType.PLANNING, AgentFramework.LANGGRAPH),
        (AgentType.RESEARCH, AgentFramework.CUSTOM),
        (AgentType.CUSTOM, AgentFramework.CUSTOM),
    ])
    def test_initialization_with_different_enum_values(self, agent_type, framework):
        """Test BaseAgent initialization with different enum combinations."""
        # Act
        agent = ConcreteAgentImplementation(
            agent_type=agent_type,
            framework=framework
        )
        
        # Assert
        assert agent.agent_type == agent_type
        assert agent.framework == framework
    
    @pytest.mark.parametrize("capabilities", [
        set(),  # Empty set
        {AgentCapability.REACT},  # Single capability
        {AgentCapability.REACT, AgentCapability.TOOL_CALLING, AgentCapability.PLANNING},  # Multiple
        {cap for cap in AgentCapability},  # All capabilities
    ])
    @pytest.mark.asyncio
    async def test_health_check_with_different_capabilities(self, capabilities):
        """Test health_check with different capability sets."""
        # Arrange
        agent = ConcreteAgentImplementation(test_capabilities=capabilities)
        
        # Act
        health_data = await agent.health_check()
        
        # Assert
        returned_capabilities = set(health_data["capabilities"])
        expected_capabilities = {cap.value for cap in capabilities}
        assert returned_capabilities == expected_capabilities
    
    def test_custom_name_and_version(self):
        """Test agent with custom name and version."""
        # Arrange
        custom_name = "Custom Test Agent v2"
        custom_version = "2.1.0"
        
        # Act
        agent = ConcreteAgentImplementation(
            test_name=custom_name,
            test_version=custom_version
        )
        
        # Assert
        assert agent.name == custom_name
        assert agent.version == custom_version


class TestBaseAgentErrorHandling:
    """Test suite for BaseAgent error handling and edge cases."""
    
    @pytest.mark.asyncio
    async def test_execute_with_minimal_context(self, concrete_agent):
        """Test execute method with minimal AgentContext."""
        # Arrange
        minimal_context = AgentContext(user_id="user")
        
        # Act
        response = await concrete_agent.execute("test query", minimal_context)
        
        # Assert
        assert isinstance(response, AgentResponse)
        assert response.content == "Processed: test query"
        assert response.status == AgentStatus.COMPLETED
        assert response.session_id is None
        assert response.request_id is None
    
    @pytest.mark.asyncio
    async def test_execute_with_full_context(self, concrete_agent, agent_context):
        """Test execute method with fully populated AgentContext."""
        # Act
        response = await concrete_agent.execute("test query", agent_context)
        
        # Assert
        assert isinstance(response, AgentResponse)
        assert response.content == "Processed: test query"
        assert response.status == AgentStatus.COMPLETED
        assert response.session_id == "test_session"
        assert response.request_id == "test_request"
    
    def test_get_configuration_schema_structure(self, concrete_agent):
        """Test that get_configuration_schema returns proper structure."""
        # Act
        schema = concrete_agent.get_configuration_schema()
        
        # Assert
        assert isinstance(schema, dict)
        assert "test_param" in schema
        
        param_schema = schema["test_param"]
        assert "type" in param_schema
        assert "default" in param_schema
        assert "description" in param_schema
        assert param_schema["type"] == "string"
        assert param_schema["default"] == "default_value"


class TestBaseAgentBehaviorIntegration:
    """Integration tests for BaseAgent behavior across method calls."""
    
    @pytest.mark.asyncio
    async def test_full_agent_lifecycle(self, concrete_agent, agent_context):
        """Test complete agent lifecycle from creation to shutdown."""
        # Initial state
        assert concrete_agent._initialized is False
        assert concrete_agent.initialize_called is False
        
        # Health check before initialization
        health_before = await concrete_agent.health_check()
        assert health_before["initialized"] is False
        
        # Initialize
        await concrete_agent.initialize()
        assert concrete_agent._initialized is True
        assert concrete_agent.initialize_called is True
        
        # Health check after initialization
        health_after = await concrete_agent.health_check()
        assert health_after["initialized"] is True
        
        # Execute query
        response = await concrete_agent.execute("test query", agent_context)
        assert concrete_agent.execute_called is True
        assert response.status == AgentStatus.COMPLETED
        
        # Shutdown
        await concrete_agent.shutdown()
        assert concrete_agent.shutdown_called is True
    
    @pytest.mark.asyncio
    async def test_multiple_execute_calls(self, concrete_agent, agent_context):
        """Test that agent can handle multiple execute calls."""
        # Arrange
        await concrete_agent.initialize()
        
        # Act - Multiple executions
        response1 = await concrete_agent.execute("query 1", agent_context)
        response2 = await concrete_agent.execute("query 2", agent_context)
        response3 = await concrete_agent.execute("query 3", agent_context)
        
        # Assert
        assert response1.content == "Processed: query 1"
        assert response2.content == "Processed: query 2"
        assert response3.content == "Processed: query 3"
        
        # All should be successful
        assert all(r.status == AgentStatus.COMPLETED for r in [response1, response2, response3])
    
    def test_capability_checking_consistency(self, concrete_agent):
        """Test that capability checking is consistent across calls."""
        # Arrange
        test_capabilities = {AgentCapability.REACT, AgentCapability.TOOL_CALLING}
        agent = ConcreteAgentImplementation(test_capabilities=test_capabilities)
        
        # Act & Assert - Multiple checks should be consistent
        for _ in range(3):
            assert agent.supports_capability(AgentCapability.REACT) is True
            assert agent.supports_capability(AgentCapability.TOOL_CALLING) is True
            assert agent.supports_capability(AgentCapability.PLANNING) is False
        
        # Get capabilities should be consistent
        capabilities1 = agent.get_supported_capabilities()
        capabilities2 = agent.get_supported_capabilities()
        assert capabilities1 == capabilities2 == test_capabilities


class TestBaseAgentMockingAndDependencies:
    """Test suite for BaseAgent mocking and dependency handling."""
    
    def test_logger_dependency(self):
        """Test that logger dependency is properly handled."""
        # Arrange & Act
        with patch('app.agent.base.base_agent.get_logger') as mock_get_logger:
            mock_logger = Mock()
            mock_get_logger.return_value = mock_logger
            
            agent = ConcreteAgentImplementation()
            
            # Assert
            assert agent.logger == mock_logger
            mock_get_logger.assert_called_once_with('ConcreteAgentImplementation')
    
    @pytest.mark.asyncio
    async def test_health_check_enum_value_access(self, concrete_agent):
        """Test that health_check properly accesses enum values."""
        # Act
        health_data = await concrete_agent.health_check()
        
        # Assert - Verify enum .value access works correctly
        assert health_data["type"] == concrete_agent.agent_type.value
        assert health_data["framework"] == concrete_agent.framework.value
        
        # Verify capabilities are converted to values
        expected_capability_values = {cap.value for cap in concrete_agent.get_supported_capabilities()}
        actual_capability_values = set(health_data["capabilities"])
        assert actual_capability_values == expected_capability_values
