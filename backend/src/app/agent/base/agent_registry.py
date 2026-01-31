from typing import Dict, List, Type, Tuple
from app.core.enums import AgentType, AgentFramework
from app.agent.base.base_agent import BaseAgent
from app.core.utils.logger import get_logger

logger = get_logger(__name__)

_agents: Dict[Tuple[AgentType, AgentFramework], Type[BaseAgent]] = {}


class AgentRegistry:
    
    @classmethod
    def register(cls, agent_type: AgentType, framework: AgentFramework):
        def decorator(agent_class: Type[BaseAgent]):
            key = (agent_type, framework)
            if key in _agents:
                logger.warning(f"Overriding existing agent registration: {key}")
            
            _agents[key] = agent_class
            logger.info(f"Registered agent: {agent_type.value} ({framework.value}) -> {agent_class.__name__}")
            return agent_class
        return decorator
    
    @classmethod
    def get_agent_class(cls, agent_type: AgentType, framework: AgentFramework) -> Type[BaseAgent]:
        key = (agent_type, framework)
        if key not in _agents:
            raise ValueError(f"No agent registered for type '{agent_type.value}' with framework '{framework.value}'")
        return _agents[key]
    
    @classmethod
    def list_registered_agents(cls) -> List[Tuple[AgentType, AgentFramework]]:
        return list(_agents.keys())
    
    @classmethod
    def get_agents_by_type(cls, agent_type: AgentType) -> List[Tuple[AgentFramework, Type[BaseAgent]]]:
        return [(framework, agent_class) for (atype, framework), agent_class in _agents.items() 
                if atype == agent_type]
    
    @classmethod
    def get_agents_by_framework(cls, framework: AgentFramework) -> List[Tuple[AgentType, Type[BaseAgent]]]:
        return [(atype, agent_class) for (atype, fw), agent_class in _agents.items() 
                if fw == framework]
    
    @classmethod
    def is_registered(cls, agent_type: AgentType, framework: AgentFramework) -> bool:
        return (agent_type, framework) in _agents
    
    @classmethod
    def clear_registry(cls) -> None:
        _agents.clear()
        logger.info("Agent registry cleared")
