import uuid
from abc import abstractmethod
from typing import Set, Dict, Any, Optional
from langgraph.graph import StateGraph
from langgraph.graph.state import CompiledStateGraph
from langgraph.checkpoint.memory import MemorySaver
from app.core.enums import AgentCapability, AgentType, AgentFramework
from app.agent.base.base_agent import BaseAgent
from app.infrastructure.llm.base.base_llm_provider import BaseLLMProvider
from app.sessions.repositories.base_session_repository import BaseSessionRepository


class LangGraphAgent(BaseAgent):
    
    def __init__(
        self,
        agent_type: AgentType,
        llm_provider: BaseLLMProvider,
        session_repository: Optional[BaseSessionRepository] = None,
        enable_checkpointing: bool = True,
        config: Optional[Dict[str, Any]] = None
    ):
        super().__init__(agent_type, AgentFramework.LANGGRAPH)
        self.llm_provider = llm_provider
        self.session_repository = session_repository
        self.enable_checkpointing = enable_checkpointing
        self.config = config or {}
        
        self.llm = None
        self.graph = None
        self.compiled_graph = None
        self.memory = None
    
    async def initialize(self) -> None:
        await self.llm_provider._ensure_initialized()
        
        if hasattr(self.llm_provider, 'client') and self.llm_provider.client is not None:
            self.llm = self.llm_provider.client
        else:
            self.llm = self.llm_provider
        
        if self.enable_checkpointing:
            self.memory = MemorySaver()
        
        self.graph = self._create_graph()
        self.compiled_graph = self._compile_graph()
        self._initialized = True
    
    @abstractmethod
    def _create_graph(self) -> StateGraph:
        pass
    
    def _compile_graph(self) -> CompiledStateGraph:
        if self.enable_checkpointing and self.memory:
            return self.graph.compile(checkpointer=self.memory)
        return self.graph.compile()
    
    async def create_checkpoint(self, thread_id: str) -> str:
        if not self.enable_checkpointing or not self.memory:
            raise ValueError("Checkpointing not enabled for this agent")
        
        config = {"configurable": {"thread_id": thread_id}}
        return config
    
    async def restore_from_checkpoint(self, thread_id: str, checkpoint_id: str) -> Dict[str, Any]:
        if not self.enable_checkpointing or not self.memory:
            raise ValueError("Checkpointing not enabled for this agent")
        
        config = {
            "configurable": {
                "thread_id": thread_id,
                "checkpoint_id": checkpoint_id
            }
        }
        return config
    
    def get_framework_capabilities(self) -> Set[AgentCapability]:
        base_capabilities = {
            AgentCapability.STATE_BRANCHING,
            AgentCapability.CONVERSATION_REPLAY,
            AgentCapability.TIME_TRAVELING,
            AgentCapability.WORKFLOW_ORCHESTRATION,
            AgentCapability.ASYNC_PROCESSING,
            AgentCapability.MEMORY_MANAGEMENT
        }
        
        if self.enable_checkpointing:
            base_capabilities.update({
                AgentCapability.TIME_TRAVELING,
                AgentCapability.STATE_BRANCHING,
                AgentCapability.CONVERSATION_REPLAY
            })
        
        return base_capabilities
    
    async def branch_conversation(self, thread_id: str, from_checkpoint: str) -> str:
        if not self.enable_checkpointing:
            raise ValueError("Branching requires checkpointing to be enabled")
        
        new_thread_id = f"{thread_id}_branch_{uuid.uuid4().hex[:8]}"
        
        # Create new thread with state from checkpoint
        config = await self.restore_from_checkpoint(thread_id, from_checkpoint)
        config["configurable"]["thread_id"] = new_thread_id
        
        return new_thread_id
