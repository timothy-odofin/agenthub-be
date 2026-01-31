"""
Unit tests for AgentRegistry class.

Tests the agent registration and retrieval system used for managing
different agent implementations with their types and frameworks.
Following Python open-source testing best practices.
"""

import pytest
from unittest.mock import Mock, patch
from typing import Set, Dict, Any

from app.agent.base.agent_registry import AgentRegistry
from app.agent.base.base_agent import BaseAgent
from app.core.enums import AgentType, AgentFramework, AgentCapability, AgentStatus
from app.agent.models import AgentContext, AgentResponse


class MockAgent(BaseAgent):
    """Mock agent implementation for testing purposes."""
    
    def __init__(self, agent_type: AgentType, framework: AgentFramework):
        super().__init__(agent_type, framework)
    
    @property
    def name(self) -> str:
        return "Mock Test Agent"
    
    @property
    def version(self) -> str:
        return "1.0.0"
    
    async def initialize(self) -> None:
        self._initialized = True
    
    async def execute(self, query: str, context: AgentContext) -> AgentResponse:
        return AgentResponse(
            content="Mock response",
            status=AgentStatus.COMPLETED
        )
    
    def get_supported_capabilities(self) -> Set[AgentCapability]:
        return {AgentCapability.REACT, AgentCapability.TOOL_CALLING}
    
    def get_configuration_schema(self) -> Dict[str, Any]:
        return {"test": {"type": "string", "default": "value"}}


class TestAgentRegistry:
    """Test suite for AgentRegistry class."""
    
    def setup_method(self):
        """Set up test fixtures before each test method."""
        # Clear the registry before each test to ensure isolation
        AgentRegistry.clear_registry()
    
    def teardown_method(self):
        """Clean up after each test method."""
        # Clear the registry after each test to prevent test pollution
        AgentRegistry.clear_registry()
    
    def test_register_decorator_functionality(self):
        """Test that the register decorator properly registers agent classes."""
        # Arrange & Act
        @AgentRegistry.register(AgentType.REACT, AgentFramework.LANGCHAIN)
        class TestAgent(MockAgent):
            def __init__(self):
                super().__init__(AgentType.REACT, AgentFramework.LANGCHAIN)
        
        # Assert
        assert AgentRegistry.is_registered(AgentType.REACT, AgentFramework.LANGCHAIN)
        retrieved_class = AgentRegistry.get_agent_class(AgentType.REACT, AgentFramework.LANGCHAIN)
        assert retrieved_class == TestAgent
    
    def test_register_multiple_agents(self):
        """Test registering multiple agents with different type/framework combinations."""
        # Arrange & Act
        @AgentRegistry.register(AgentType.REACT, AgentFramework.LANGCHAIN)
        class LangchainReactAgent(MockAgent):
            def __init__(self):
                super().__init__(AgentType.REACT, AgentFramework.LANGCHAIN)
        
        @AgentRegistry.register(AgentType.REACT, AgentFramework.LANGGRAPH)
        class LanggraphReactAgent(MockAgent):
            def __init__(self):
                super().__init__(AgentType.REACT, AgentFramework.LANGGRAPH)
        
        @AgentRegistry.register(AgentType.PLANNING, AgentFramework.LANGCHAIN)
        class LangchainPlanningAgent(MockAgent):
            def __init__(self):
                super().__init__(AgentType.PLANNING, AgentFramework.LANGCHAIN)
        
        # Assert
        registered_agents = AgentRegistry.list_registered_agents()
        expected_combinations = [
            (AgentType.REACT, AgentFramework.LANGCHAIN),
            (AgentType.REACT, AgentFramework.LANGGRAPH),
            (AgentType.PLANNING, AgentFramework.LANGCHAIN)
        ]
        
        assert len(registered_agents) == 3
        for combination in expected_combinations:
            assert combination in registered_agents
    
    def test_register_override_warning(self):
        """Test that registering the same agent combination logs a warning."""
        # Arrange
        @AgentRegistry.register(AgentType.REACT, AgentFramework.LANGCHAIN)
        class FirstAgent(MockAgent):
            def __init__(self):
                super().__init__(AgentType.REACT, AgentFramework.LANGCHAIN)
        
        # Act & Assert - Should log warning when overriding
        with patch('app.agent.base.agent_registry.logger.warning') as mock_warning:
            @AgentRegistry.register(AgentType.REACT, AgentFramework.LANGCHAIN)
            class SecondAgent(MockAgent):
                def __init__(self):
                    super().__init__(AgentType.REACT, AgentFramework.LANGCHAIN)
            
            mock_warning.assert_called_once()
            assert "Overriding existing agent registration" in mock_warning.call_args[0][0]
        
        # Verify the second agent overwrote the first
        retrieved_class = AgentRegistry.get_agent_class(AgentType.REACT, AgentFramework.LANGCHAIN)
        assert retrieved_class == SecondAgent
    
    def test_get_agent_class_success(self):
        """Test successfully retrieving a registered agent class."""
        # Arrange
        @AgentRegistry.register(AgentType.REACT, AgentFramework.LANGCHAIN)
        class TestAgent(MockAgent):
            def __init__(self):
                super().__init__(AgentType.REACT, AgentFramework.LANGCHAIN)
        
        # Act
        retrieved_class = AgentRegistry.get_agent_class(AgentType.REACT, AgentFramework.LANGCHAIN)
        
        # Assert
        assert retrieved_class == TestAgent
    
    def test_get_agent_class_not_registered_raises_value_error(self):
        """Test that retrieving an unregistered agent raises ValueError."""
        # Act & Assert
        with pytest.raises(ValueError) as exc_info:
            AgentRegistry.get_agent_class(AgentType.REACT, AgentFramework.LANGCHAIN)
        
        error_message = str(exc_info.value)
        assert "No agent registered for type 'react' with framework 'langchain'" in error_message
    
    def test_list_registered_agents_empty(self):
        """Test listing agents when registry is empty."""
        # Act
        registered_agents = AgentRegistry.list_registered_agents()
        
        # Assert
        assert registered_agents == []
    
    def test_list_registered_agents_populated(self):
        """Test listing agents when registry contains multiple agents."""
        # Arrange
        @AgentRegistry.register(AgentType.REACT, AgentFramework.LANGCHAIN)
        class ReactLangchain(MockAgent):
            def __init__(self):
                super().__init__(AgentType.REACT, AgentFramework.LANGCHAIN)
        
        @AgentRegistry.register(AgentType.PLANNING, AgentFramework.LANGGRAPH)
        class PlanningLanggraph(MockAgent):
            def __init__(self):
                super().__init__(AgentType.PLANNING, AgentFramework.LANGGRAPH)
        
        # Act
        registered_agents = AgentRegistry.list_registered_agents()
        
        # Assert
        assert len(registered_agents) == 2
        assert (AgentType.REACT, AgentFramework.LANGCHAIN) in registered_agents
        assert (AgentType.PLANNING, AgentFramework.LANGGRAPH) in registered_agents
    
    def test_get_agents_by_type(self):
        """Test filtering agents by type."""
        # Arrange
        @AgentRegistry.register(AgentType.REACT, AgentFramework.LANGCHAIN)
        class ReactLangchain(MockAgent):
            def __init__(self):
                super().__init__(AgentType.REACT, AgentFramework.LANGCHAIN)
        
        @AgentRegistry.register(AgentType.REACT, AgentFramework.LANGGRAPH)
        class ReactLanggraph(MockAgent):
            def __init__(self):
                super().__init__(AgentType.REACT, AgentFramework.LANGGRAPH)
        
        @AgentRegistry.register(AgentType.PLANNING, AgentFramework.LANGCHAIN)
        class PlanningLangchain(MockAgent):
            def __init__(self):
                super().__init__(AgentType.PLANNING, AgentFramework.LANGCHAIN)
        
        # Act
        react_agents = AgentRegistry.get_agents_by_type(AgentType.REACT)
        
        # Assert
        assert len(react_agents) == 2
        frameworks_and_classes = dict(react_agents)
        assert AgentFramework.LANGCHAIN in frameworks_and_classes
        assert AgentFramework.LANGGRAPH in frameworks_and_classes
        assert frameworks_and_classes[AgentFramework.LANGCHAIN] == ReactLangchain
        assert frameworks_and_classes[AgentFramework.LANGGRAPH] == ReactLanggraph
    
    def test_get_agents_by_type_no_matches(self):
        """Test filtering agents by type when no matches exist."""
        # Arrange
        @AgentRegistry.register(AgentType.REACT, AgentFramework.LANGCHAIN)
        class ReactAgent(MockAgent):
            def __init__(self):
                super().__init__(AgentType.REACT, AgentFramework.LANGCHAIN)
        
        # Act
        planning_agents = AgentRegistry.get_agents_by_type(AgentType.PLANNING)
        
        # Assert
        assert planning_agents == []
    
    def test_get_agents_by_framework(self):
        """Test filtering agents by framework."""
        # Arrange
        @AgentRegistry.register(AgentType.REACT, AgentFramework.LANGCHAIN)
        class ReactLangchain(MockAgent):
            def __init__(self):
                super().__init__(AgentType.REACT, AgentFramework.LANGCHAIN)
        
        @AgentRegistry.register(AgentType.PLANNING, AgentFramework.LANGCHAIN)
        class PlanningLangchain(MockAgent):
            def __init__(self):
                super().__init__(AgentType.PLANNING, AgentFramework.LANGCHAIN)
        
        @AgentRegistry.register(AgentType.REACT, AgentFramework.LANGGRAPH)
        class ReactLanggraph(MockAgent):
            def __init__(self):
                super().__init__(AgentType.REACT, AgentFramework.LANGGRAPH)
        
        # Act
        langchain_agents = AgentRegistry.get_agents_by_framework(AgentFramework.LANGCHAIN)
        
        # Assert
        assert len(langchain_agents) == 2
        types_and_classes = dict(langchain_agents)
        assert AgentType.REACT in types_and_classes
        assert AgentType.PLANNING in types_and_classes
        assert types_and_classes[AgentType.REACT] == ReactLangchain
        assert types_and_classes[AgentType.PLANNING] == PlanningLangchain
    
    def test_get_agents_by_framework_no_matches(self):
        """Test filtering agents by framework when no matches exist."""
        # Arrange
        @AgentRegistry.register(AgentType.REACT, AgentFramework.LANGCHAIN)
        class ReactAgent(MockAgent):
            def __init__(self):
                super().__init__(AgentType.REACT, AgentFramework.LANGCHAIN)
        
        # Act
        langgraph_agents = AgentRegistry.get_agents_by_framework(AgentFramework.LANGGRAPH)
        
        # Assert
        assert langgraph_agents == []
    
    def test_is_registered_true(self):
        """Test is_registered returns True for registered agents."""
        # Arrange
        @AgentRegistry.register(AgentType.REACT, AgentFramework.LANGCHAIN)
        class TestAgent(MockAgent):
            def __init__(self):
                super().__init__(AgentType.REACT, AgentFramework.LANGCHAIN)
        
        # Act & Assert
        assert AgentRegistry.is_registered(AgentType.REACT, AgentFramework.LANGCHAIN) is True
    
    def test_is_registered_false(self):
        """Test is_registered returns False for unregistered agents."""
        # Act & Assert
        assert AgentRegistry.is_registered(AgentType.REACT, AgentFramework.LANGCHAIN) is False
    
    def test_clear_registry(self):
        """Test clearing the registry removes all registered agents."""
        # Arrange
        @AgentRegistry.register(AgentType.REACT, AgentFramework.LANGCHAIN)
        class TestAgent1(MockAgent):
            def __init__(self):
                super().__init__(AgentType.REACT, AgentFramework.LANGCHAIN)
        
        @AgentRegistry.register(AgentType.PLANNING, AgentFramework.LANGGRAPH)
        class TestAgent2(MockAgent):
            def __init__(self):
                super().__init__(AgentType.PLANNING, AgentFramework.LANGGRAPH)
        
        # Verify agents are registered
        assert len(AgentRegistry.list_registered_agents()) == 2
        
        # Act
        AgentRegistry.clear_registry()
        
        # Assert
        assert len(AgentRegistry.list_registered_agents()) == 0
        assert not AgentRegistry.is_registered(AgentType.REACT, AgentFramework.LANGCHAIN)
        assert not AgentRegistry.is_registered(AgentType.PLANNING, AgentFramework.LANGGRAPH)
    
    def test_clear_registry_logs_info(self):
        """Test that clearing registry logs an info message."""
        # Arrange & Act
        with patch('app.agent.base.agent_registry.logger.info') as mock_info:
            AgentRegistry.clear_registry()
            
            # Assert
            mock_info.assert_called_once_with("Agent registry cleared")
    
    @pytest.mark.parametrize("agent_type,framework", [
        (AgentType.REACT, AgentFramework.LANGCHAIN),
        (AgentType.REACT, AgentFramework.LANGGRAPH),
        (AgentType.PLANNING, AgentFramework.LANGCHAIN),
        (AgentType.PLANNING, AgentFramework.LANGGRAPH),
        (AgentType.RESEARCH, AgentFramework.CUSTOM),
    ])
    def test_register_all_enum_combinations(self, agent_type, framework):
        """Test registering agents with various type/framework combinations."""
        # Arrange & Act
        @AgentRegistry.register(agent_type, framework)
        class ParameterizedAgent(MockAgent):
            def __init__(self):
                super().__init__(agent_type, framework)
        
        # Assert
        assert AgentRegistry.is_registered(agent_type, framework)
        retrieved_class = AgentRegistry.get_agent_class(agent_type, framework)
        assert retrieved_class == ParameterizedAgent


class TestAgentRegistryEdgeCases:
    """Test suite for AgentRegistry edge cases and error conditions."""
    
    def setup_method(self):
        """Set up test fixtures before each test method."""
        AgentRegistry.clear_registry()
    
    def teardown_method(self):
        """Clean up after each test method."""
        AgentRegistry.clear_registry()
    
    def test_register_with_invalid_agent_class(self):
        """Test registering a class that doesn't inherit from BaseAgent."""
        # Arrange
        class InvalidAgent:
            pass
        
        # Act - The decorator should still work, but the class won't be a valid agent
        @AgentRegistry.register(AgentType.REACT, AgentFramework.LANGCHAIN)
        class InvalidAgentWithDecorator(InvalidAgent):
            pass
        
        # Assert - Class is registered but won't be a valid BaseAgent
        assert AgentRegistry.is_registered(AgentType.REACT, AgentFramework.LANGCHAIN)
        retrieved_class = AgentRegistry.get_agent_class(AgentType.REACT, AgentFramework.LANGCHAIN)
        assert retrieved_class == InvalidAgentWithDecorator
        assert not issubclass(retrieved_class, BaseAgent)
    
    def test_registry_state_persistence_across_operations(self):
        """Test that registry state persists across multiple operations."""
        # Arrange
        @AgentRegistry.register(AgentType.REACT, AgentFramework.LANGCHAIN)
        class PersistentAgent(MockAgent):
            def __init__(self):
                super().__init__(AgentType.REACT, AgentFramework.LANGCHAIN)
        
        # Act - Perform multiple registry operations
        agents_list_1 = AgentRegistry.list_registered_agents()
        is_registered_1 = AgentRegistry.is_registered(AgentType.REACT, AgentFramework.LANGCHAIN)
        agents_by_type = AgentRegistry.get_agents_by_type(AgentType.REACT)
        agents_by_framework = AgentRegistry.get_agents_by_framework(AgentFramework.LANGCHAIN)
        agents_list_2 = AgentRegistry.list_registered_agents()
        is_registered_2 = AgentRegistry.is_registered(AgentType.REACT, AgentFramework.LANGCHAIN)
        
        # Assert - State should remain consistent
        assert agents_list_1 == agents_list_2
        assert is_registered_1 == is_registered_2 == True
        assert len(agents_by_type) == 1
        assert len(agents_by_framework) == 1
    
    def test_decorator_returns_original_class(self):
        """Test that the register decorator returns the original class unchanged."""
        # Arrange
        class OriginalAgent(MockAgent):
            def __init__(self):
                super().__init__(AgentType.REACT, AgentFramework.LANGCHAIN)
        
        # Act
        decorated_class = AgentRegistry.register(AgentType.REACT, AgentFramework.LANGCHAIN)(OriginalAgent)
        
        # Assert
        assert decorated_class is OriginalAgent
        assert decorated_class.__name__ == OriginalAgent.__name__
        assert AgentRegistry.get_agent_class(AgentType.REACT, AgentFramework.LANGCHAIN) is OriginalAgent
