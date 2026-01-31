from typing import Optional, Dict, Any
from app.core.enums import AgentType, AgentFramework
from app.agent.base.base_agent import BaseAgent
from app.agent.base.agent_registry import AgentRegistry
from app.core.utils.logger import get_logger

logger = get_logger(__name__)


class AgentFactory:
    
    @staticmethod
    async def create_agent(
        agent_type: AgentType,
        framework: AgentFramework,
        config: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> BaseAgent:
        if not AgentRegistry.is_registered(agent_type, framework):
            available = AgentRegistry.list_registered_agents()
            raise ValueError(f"Agent type '{agent_type.value}' with framework '{framework.value}' not registered. Available: {available}")
        
        agent_class = AgentRegistry.get_agent_class(agent_type, framework)
        
        try:
            if config:
                agent = agent_class(config=config, **kwargs)
            else:
                agent = agent_class(**kwargs)
            
            await agent.initialize()
            logger.info(f"Created and initialized agent: {agent.name} ({agent_type.value}/{framework.value})")
            return agent
            
        except Exception as e:
            logger.error(f"Failed to create agent {agent_type.value}/{framework.value}: {e}", exc_info=True)
            raise
    
    @staticmethod
    def list_available_agents():
        return [
            {
                "type": agent_type.value,
                "framework": framework.value,
                "class_name": AgentRegistry.get_agent_class(agent_type, framework).__name__
            }
            for agent_type, framework in AgentRegistry.list_registered_agents()
        ]
