from abc import abstractmethod
from typing import Set, Dict, Any, Optional
from langchain.agents import AgentExecutor
from langchain_core.prompts import ChatPromptTemplate
from app.core.enums import AgentCapability, AgentType, AgentFramework
from app.agent.base.base_agent import BaseAgent
from app.infrastructure.llm.base.base_llm_provider import BaseLLMProvider
from app.agent.tools import ToolRegistry
from app.sessions.repositories.base_session_repository import BaseSessionRepository


class LangChainAgent(BaseAgent):
    
    def __init__(
        self,
        agent_type: AgentType,
        llm_provider: BaseLLMProvider,
        session_repository: Optional[BaseSessionRepository] = None,
        verbose: bool = False,
        config: Optional[Dict[str, Any]] = None
    ):
        super().__init__(agent_type, AgentFramework.LANGCHAIN)
        self.llm_provider = llm_provider
        self.session_repository = session_repository
        self.verbose = verbose
        self.config = config or {}
        
        self.llm = None
        self.tools = []
        self.prompt = None
        self.agent = None
        self.executor = None
    
    async def initialize(self) -> None:
        await self.llm_provider._ensure_initialized()
        
        if hasattr(self.llm_provider, 'client') and self.llm_provider.client is not None:
            self.llm = self.llm_provider.client
        else:
            self.llm = self.llm_provider
        
        self.tools = ToolRegistry.get_instantiated_tools()
        self.prompt = self._create_prompt_template()
        self.agent = self._create_agent_runnable()
        self.executor = AgentExecutor(
            agent=self.agent,
            tools=self.tools,
            verbose=self.verbose
        )
        self._initialized = True
    
    @abstractmethod
    def _create_prompt_template(self) -> ChatPromptTemplate:
        pass
    
    @abstractmethod
    def _create_agent_runnable(self):
        pass
    
    def get_framework_capabilities(self) -> Set[AgentCapability]:
        return {
            AgentCapability.TOOL_CALLING,
            AgentCapability.FUNCTION_CALLING,
            AgentCapability.MEMORY_MANAGEMENT,
            AgentCapability.STREAMING,
            AgentCapability.ASYNC_PROCESSING,
            AgentCapability.MULTI_TURN_CONVERSATION,
            AgentCapability.API_INTEGRATION
        }
