from abc import ABC, abstractmethod
from typing import Set, Dict, Any
from app.core.enums import AgentCapability, AgentType, AgentFramework
from app.agent.models import AgentContext, AgentResponse


class BaseAgent(ABC):
    
    def __init__(self, agent_type: AgentType, framework: AgentFramework):
        self.agent_type = agent_type
        self.framework = framework
        self._initialized = False
    
    @property
    @abstractmethod
    def name(self) -> str:
        pass
    
    @property
    @abstractmethod
    def version(self) -> str:
        pass
    
    @abstractmethod
    async def initialize(self) -> None:
        pass
    
    @abstractmethod
    async def execute(self, query: str, context: AgentContext) -> AgentResponse:
        pass
    
    @abstractmethod
    def get_supported_capabilities(self) -> Set[AgentCapability]:
        pass
    
    @abstractmethod
    def get_configuration_schema(self) -> Dict[str, Any]:
        pass
    
    async def health_check(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "version": self.version,
            "type": self.agent_type.value,
            "framework": self.framework.value,
            "initialized": self._initialized,
            "capabilities": [cap.value for cap in self.get_supported_capabilities()]
        }
    
    def supports_capability(self, capability: AgentCapability) -> bool:
        return capability in self.get_supported_capabilities()
    
    async def shutdown(self) -> None:
        pass
