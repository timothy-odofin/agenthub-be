"""
Unit tests for AgentFactory class.

Tests the factory pattern for creating agent instances with proper initialization
and configuration management. Following Python open-source testing best practices.
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock
from typing import Set, Dict, Any

from app.agent.base.agent_factory import AgentFactory
from app.agent.base.agent_registry import AgentRegistry
from app.agent.base.base_agent import BaseAgent
from app.core.enums import AgentType, AgentFramework, AgentCapability, AgentStatus
from app.agent.models import AgentContext, AgentResponse


class MockAgentForFactory(BaseAgent):
    """Mock agent implementation for factory testing."""
    
    def __init__(self, agent_type: AgentType, framework: AgentFramework, config=None, **kwargs):
        super().__init__(agent_type, framework)
        self.config = config or {}
        self.kwargs = kwargs
        self.initialization_called = False
    
    @property
    def name(self) -> str:
        return "Mock Factory Agent"
    
    @property
    def version(self) -> str:
        return "1.0.0"
    
    async def initialize(self) -> None:
        self._initialized = True
        self.initialization_called = True
    
    async def execute(self, query: str, context: AgentContext) -> AgentResponse:
        return AgentResponse(
            content="Factory mock response",
            status=AgentStatus.COMPLETED
        )
    
    def get_supported_capabilities(self) -> Set[AgentCapability]:
        return {AgentCapability.REACT, AgentCapability.TOOL_CALLING}
    
    def get_configuration_schema(self) -> Dict[str, Any]:
        return {"test": {"type": "string", "default": "value"}}


class MockFailingAgent(BaseAgent):
    """Mock agent that fails during initialization for testing error handling."""
    
    def __init__(self, agent_type: AgentType, framework: AgentFramework, **kwargs):
        super().__init__(agent_type, framework)
        if kwargs.get('fail_init'):
            raise ValueError("Initialization failed")
    
    @property
    def name(self) -> str:
        return "Failing Mock Agent"
    
    @property
    def version(self) -> str:
        return "1.0.0"
    
    async def initialize(self) -> None:
        if hasattr(self, 'should_fail_initialize') and self.should_fail_initialize:
            raise RuntimeError("Initialize method failed")
        self._initialized = True
    
    async def execute(self, query: str, context: AgentContext) -> AgentResponse:
        return AgentResponse(content="", status=AgentStatus.ERROR)
    
    def get_supported_capabilities(self) -> Set[AgentCapability]:
        return set()
    
    def get_configuration_schema(self) -> Dict[str, Any]:
        return {}


@pytest.fixture
def clean_registry():
    """Fixture to ensure clean agent registry for each test."""
    AgentRegistry.clear_registry()
    yield
    AgentRegistry.clear_registry()


@pytest.fixture
def registered_agent():
    """Fixture to provide a registered agent for testing."""
    @AgentRegistry.register(AgentType.REACT, AgentFramework.LANGCHAIN)
    class TestAgent(MockAgentForFactory):
        def __init__(self, **kwargs):
            super().__init__(AgentType.REACT, AgentFramework.LANGCHAIN, **kwargs)
    
    return TestAgent


@pytest.fixture
def failing_agent():
    """Fixture to provide a registered failing agent for testing."""
    @AgentRegistry.register(AgentType.PLANNING, AgentFramework.LANGCHAIN)
    class TestFailingAgent(MockFailingAgent):
        def __init__(self, **kwargs):
            super().__init__(AgentType.PLANNING, AgentFramework.LANGCHAIN, **kwargs)
    
    return TestFailingAgent


class TestAgentFactory:
    """Test suite for AgentFactory class."""
    
    @pytest.mark.asyncio
    async def test_create_agent_success_with_config(self, clean_registry, registered_agent):
        """Test successful agent creation with configuration."""
        # Arrange
        config = {"test_param": "test_value"}
        
        # Act
        agent = await AgentFactory.create_agent(
            AgentType.REACT,
            AgentFramework.LANGCHAIN,
            config=config,
            extra_param="extra_value"
        )
        
        # Assert
        assert isinstance(agent, registered_agent)
        assert agent._initialized is True
        assert agent.initialization_called is True
        assert agent.config == config
        assert agent.kwargs["extra_param"] == "extra_value"
    
    @pytest.mark.asyncio
    async def test_create_agent_success_without_config(self, clean_registry, registered_agent):
        """Test successful agent creation without configuration."""
        # Act
        agent = await AgentFactory.create_agent(
            AgentType.REACT,
            AgentFramework.LANGCHAIN
        )
        
        # Assert
        assert isinstance(agent, registered_agent)
        assert agent._initialized is True
        assert agent.initialization_called is True
        assert agent.config == {}
    
    @pytest.mark.asyncio
    async def test_create_agent_success_with_kwargs_only(self, clean_registry, registered_agent):
        """Test successful agent creation with kwargs but no config."""
        # Act
        agent = await AgentFactory.create_agent(
            AgentType.REACT,
            AgentFramework.LANGCHAIN,
            test_kwarg="test_value",
            another_param=42
        )
        
        # Assert
        assert isinstance(agent, registered_agent)
        assert agent._initialized is True
        assert agent.kwargs["test_kwarg"] == "test_value"
        assert agent.kwargs["another_param"] == 42
    
    @pytest.mark.asyncio
    async def test_create_agent_not_registered_raises_value_error(self, clean_registry):
        """Test that creating an unregistered agent raises ValueError."""
        # Act & Assert
        with pytest.raises(ValueError) as exc_info:
            await AgentFactory.create_agent(
                AgentType.REACT,
                AgentFramework.LANGCHAIN
            )
        
        error_message = str(exc_info.value)
        assert "Agent type 'react' with framework 'langchain' not registered" in error_message
        assert "Available:" in error_message
    
    @pytest.mark.asyncio
    async def test_create_agent_initialization_failure(self, clean_registry, failing_agent):
        """Test agent creation when initialization fails."""
        # Arrange - Create a mock class that will fail during __init__
        with patch.object(failing_agent, '__init__', side_effect=ValueError("Init failed")):
            # Act & Assert
            with pytest.raises(ValueError) as exc_info:
                await AgentFactory.create_agent(
                    AgentType.PLANNING,
                    AgentFramework.LANGCHAIN
                )
            
            assert "Init failed" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_create_agent_async_initialize_failure(self, clean_registry):
        """Test agent creation when async initialize method fails."""
        # Arrange
        @AgentRegistry.register(AgentType.RESEARCH, AgentFramework.LANGCHAIN)
        class FailingInitAgent(MockAgentForFactory):
            def __init__(self, **kwargs):
                super().__init__(AgentType.RESEARCH, AgentFramework.LANGCHAIN, **kwargs)
            
            async def initialize(self) -> None:
                raise RuntimeError("Async initialization failed")
        
        # Act & Assert
        with pytest.raises(RuntimeError) as exc_info:
            await AgentFactory.create_agent(
                AgentType.RESEARCH,
                AgentFramework.LANGCHAIN
            )
        
        assert "Async initialization failed" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_create_agent_logs_success(self, clean_registry, registered_agent):
        """Test that successful agent creation is logged."""
        # Arrange & Act
        with patch('app.agent.base.agent_factory.logger.info') as mock_info:
            agent = await AgentFactory.create_agent(
                AgentType.REACT,
                AgentFramework.LANGCHAIN
            )
            
            # Assert
            mock_info.assert_called_once()
            log_message = mock_info.call_args[0][0]
            assert "Created and initialized agent:" in log_message
            assert "Mock Factory Agent" in log_message
            assert "react/langchain" in log_message
    
    @pytest.mark.asyncio
    async def test_create_agent_logs_error_on_failure(self, clean_registry, failing_agent):
        """Test that agent creation failures are logged."""
        # Arrange
        with patch.object(failing_agent, '__init__', side_effect=ValueError("Test error")):
            # Act & Assert
            with patch('app.agent.base.agent_factory.logger.error') as mock_error:
                with pytest.raises(ValueError):
                    await AgentFactory.create_agent(
                        AgentType.PLANNING,
                        AgentFramework.LANGCHAIN
                    )
                
                mock_error.assert_called_once()
                log_message = mock_error.call_args[0][0]
                assert "Failed to create agent planning/langchain:" in log_message
    
    def test_list_available_agents_empty(self, clean_registry):
        """Test listing available agents when registry is empty."""
        # Act
        available_agents = AgentFactory.list_available_agents()
        
        # Assert
        assert available_agents == []
    
    def test_list_available_agents_populated(self, clean_registry):
        """Test listing available agents when registry has agents."""
        # Arrange
        @AgentRegistry.register(AgentType.REACT, AgentFramework.LANGCHAIN)
        class ReactLangchain(MockAgentForFactory):
            def __init__(self, **kwargs):
                super().__init__(AgentType.REACT, AgentFramework.LANGCHAIN, **kwargs)
        
        @AgentRegistry.register(AgentType.PLANNING, AgentFramework.LANGGRAPH)
        class PlanningLanggraph(MockAgentForFactory):
            def __init__(self, **kwargs):
                super().__init__(AgentType.PLANNING, AgentFramework.LANGGRAPH, **kwargs)
        
        # Act
        available_agents = AgentFactory.list_available_agents()
        
        # Assert
        assert len(available_agents) == 2
        
        # Check that the returned format is correct
        agent_types = {agent["type"] for agent in available_agents}
        frameworks = {agent["framework"] for agent in available_agents}
        class_names = {agent["class_name"] for agent in available_agents}
        
        assert agent_types == {"react", "planning"}
        assert frameworks == {"langchain", "langgraph"}
        assert class_names == {"ReactLangchain", "PlanningLanggraph"}
        
        # Check specific entries
        react_agent = next(a for a in available_agents if a["type"] == "react")
        assert react_agent["framework"] == "langchain"
        assert react_agent["class_name"] == "ReactLangchain"
        
        planning_agent = next(a for a in available_agents if a["type"] == "planning")
        assert planning_agent["framework"] == "langgraph"
        assert planning_agent["class_name"] == "PlanningLanggraph"
    
    @pytest.mark.parametrize("agent_type,framework", [
        (AgentType.REACT, AgentFramework.LANGCHAIN),
        (AgentType.REACT, AgentFramework.LANGGRAPH),
        (AgentType.PLANNING, AgentFramework.LANGCHAIN),
        (AgentType.RESEARCH, AgentFramework.CUSTOM),
    ])
    @pytest.mark.asyncio
    async def test_create_agent_various_combinations(
        self, clean_registry, agent_type, framework
    ):
        """Test creating agents with various type/framework combinations."""
        # Arrange
        @AgentRegistry.register(agent_type, framework)
        class ParameterizedAgent(MockAgentForFactory):
            def __init__(self, **kwargs):
                super().__init__(agent_type, framework, **kwargs)
        
        # Act
        agent = await AgentFactory.create_agent(agent_type, framework)
        
        # Assert
        assert isinstance(agent, ParameterizedAgent)
        assert agent.agent_type == agent_type
        assert agent.framework == framework
        assert agent._initialized is True


class TestAgentFactoryIntegration:
    """Integration tests for AgentFactory with real agent registry interactions."""
    
    def setup_method(self):
        """Set up test fixtures before each test method."""
        AgentRegistry.clear_registry()
    
    def teardown_method(self):
        """Clean up after each test method."""
        AgentRegistry.clear_registry()
    
    @pytest.mark.asyncio
    async def test_factory_registry_integration(self):
        """Test that factory properly integrates with registry operations."""
        # Arrange
        @AgentRegistry.register(AgentType.REACT, AgentFramework.LANGCHAIN)
        class IntegrationAgent(MockAgentForFactory):
            def __init__(self, **kwargs):
                super().__init__(AgentType.REACT, AgentFramework.LANGCHAIN, **kwargs)
        
        # Verify registry state
        assert AgentRegistry.is_registered(AgentType.REACT, AgentFramework.LANGCHAIN)
        
        # Act - Create agent through factory
        agent = await AgentFactory.create_agent(
            AgentType.REACT,
            AgentFramework.LANGCHAIN
        )
        
        # Assert
        assert isinstance(agent, IntegrationAgent)
        
        # Verify factory listing reflects registry state
        available_agents = AgentFactory.list_available_agents()
        assert len(available_agents) == 1
        assert available_agents[0]["type"] == "react"
        assert available_agents[0]["framework"] == "langchain"
    
    @pytest.mark.asyncio
    async def test_multiple_agents_creation_and_listing(self):
        """Test creating multiple different agents and listing them."""
        # Arrange - Register multiple agents
        @AgentRegistry.register(AgentType.REACT, AgentFramework.LANGCHAIN)
        class ReactLangchain(MockAgentForFactory):
            def __init__(self, **kwargs):
                super().__init__(AgentType.REACT, AgentFramework.LANGCHAIN, **kwargs)
        
        @AgentRegistry.register(AgentType.REACT, AgentFramework.LANGGRAPH)
        class ReactLanggraph(MockAgentForFactory):
            def __init__(self, **kwargs):
                super().__init__(AgentType.REACT, AgentFramework.LANGGRAPH, **kwargs)
        
        @AgentRegistry.register(AgentType.PLANNING, AgentFramework.LANGCHAIN)
        class PlanningLangchain(MockAgentForFactory):
            def __init__(self, **kwargs):
                super().__init__(AgentType.PLANNING, AgentFramework.LANGCHAIN, **kwargs)
        
        # Act - Create all agents
        react_lc_agent = await AgentFactory.create_agent(
            AgentType.REACT, AgentFramework.LANGCHAIN
        )
        react_lg_agent = await AgentFactory.create_agent(
            AgentType.REACT, AgentFramework.LANGGRAPH
        )
        planning_agent = await AgentFactory.create_agent(
            AgentType.PLANNING, AgentFramework.LANGCHAIN
        )
        
        # Assert agents are created correctly
        assert isinstance(react_lc_agent, ReactLangchain)
        assert isinstance(react_lg_agent, ReactLanggraph)
        assert isinstance(planning_agent, PlanningLangchain)
        
        # Verify listing includes all agents
        available_agents = AgentFactory.list_available_agents()
        assert len(available_agents) == 3
        
        # Check that we have the expected combinations
        combinations = {(a["type"], a["framework"]) for a in available_agents}
        expected_combinations = {
            ("react", "langchain"),
            ("react", "langgraph"),
            ("planning", "langchain")
        }
        assert combinations == expected_combinations


class TestAgentFactoryErrorHandling:
    """Test suite for AgentFactory error handling and edge cases."""
    
    def setup_method(self):
        """Set up test fixtures before each test method."""
        AgentRegistry.clear_registry()
    
    def teardown_method(self):
        """Clean up after each test method."""
        AgentRegistry.clear_registry()
    
    @pytest.mark.asyncio
    async def test_create_agent_with_none_config(self, clean_registry, registered_agent):
        """Test creating agent with explicitly None config."""
        # Act
        agent = await AgentFactory.create_agent(
            AgentType.REACT,
            AgentFramework.LANGCHAIN,
            config=None
        )
        
        # Assert
        assert isinstance(agent, registered_agent)
        assert agent.config == {}
    
    @pytest.mark.asyncio
    async def test_create_agent_preserves_exception_type(self, clean_registry):
        """Test that factory preserves the original exception type on failures."""
        # Arrange
        @AgentRegistry.register(AgentType.CUSTOM, AgentFramework.CUSTOM)
        class CustomErrorAgent(MockAgentForFactory):
            def __init__(self, **kwargs):
                super().__init__(AgentType.CUSTOM, AgentFramework.CUSTOM, **kwargs)
            
            async def initialize(self) -> None:
                raise TypeError("Custom type error")
        
        # Act & Assert
        with pytest.raises(TypeError) as exc_info:
            await AgentFactory.create_agent(
                AgentType.CUSTOM,
                AgentFramework.CUSTOM
            )
        
        assert "Custom type error" in str(exc_info.value)
    
    def test_list_available_agents_handles_registry_exceptions(self):
        """Test that list_available_agents handles registry exceptions gracefully."""
        # Arrange - Mock registry to raise an exception
        with patch.object(AgentRegistry, 'list_registered_agents', side_effect=Exception("Registry error")):
            # Act & Assert - Should not raise exception from factory method
            with pytest.raises(Exception) as exc_info:
                AgentFactory.list_available_agents()
            
            assert "Registry error" in str(exc_info.value)
