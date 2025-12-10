import asyncio
from datetime import datetime
from typing import Set, Dict, Any, Optional, TypedDict, List
from langgraph.graph import StateGraph
from langgraph.prebuilt import create_react_agent
from langgraph.prebuilt.tool_executor import ToolExecutor
from langchain_core.messages import HumanMessage, AIMessage, BaseMessage

from app.core.enums import AgentCapability, AgentType, AgentStatus, AgentFramework
from app.agent.frameworks.langgraph_agent import LangGraphAgent
from app.agent.models import AgentContext, AgentResponse
from app.agent.base.agent_registry import AgentRegistry
from app.agent.tools import ToolRegistry
from app.core.config.providers.prompt import prompt_config, PromptType


class GraphState(TypedDict):
    messages: List[BaseMessage]
    user_id: str
    session_id: Optional[str]
    intermediate_steps: List[Any]


@AgentRegistry.register(AgentType.REACT, AgentFramework.LANGGRAPH)
class LangGraphReactAgent(LangGraphAgent):
    
    def __init__(self, *args, **kwargs):
        super().__init__(AgentType.REACT, *args, **kwargs)
        self.agent_prompt_type = self.config.get('prompt_type', PromptType.REACT_AGENT.value)
        self.tools = []
        self.tool_executor = None
    
    @property
    def name(self) -> str:
        return "LangGraph ReAct Agent"
    
    @property
    def version(self) -> str:
        return "1.0.0"
    
    def get_supported_capabilities(self) -> Set[AgentCapability]:
        base_capabilities = {
            AgentCapability.REACT,
            AgentCapability.TOOL_CALLING,
            AgentCapability.MULTI_TURN_CONVERSATION,
            AgentCapability.ASYNC_PROCESSING,
            AgentCapability.TIME_TRAVELING,
            AgentCapability.STATE_BRANCHING,
            AgentCapability.WORKFLOW_ORCHESTRATION
        }
        return base_capabilities | self.get_framework_capabilities()
    
    def get_configuration_schema(self) -> Dict[str, Any]:
        return {
            "prompt_type": {
                "type": "string",
                "default": PromptType.REACT_AGENT.value,
                "description": "Prompt template type for the agent"
            },
            "enable_checkpointing": {
                "type": "boolean",
                "default": True,
                "description": "Enable state checkpointing and time travel"
            },
            "max_iterations": {
                "type": "integer",
                "default": 10,
                "description": "Maximum reasoning iterations"
            }
        }
    
    async def initialize(self) -> None:
        # Get tools first
        self.tools = ToolRegistry.get_instantiated_tools()
        self.tool_executor = ToolExecutor(self.tools)
        
        # Initialize LLM
        await super().initialize()
    
    def _create_graph(self) -> StateGraph:
        # Create a React agent using LangGraph's prebuilt function
        # This handles the React loop (Reason, Act, Observe)
        return create_react_agent(
            model=self.llm,
            tools=self.tools,
            state_modifier=self._get_system_prompt(),
            checkpointer=self.memory if self.enable_checkpointing else None
        )
    
    def _get_system_prompt(self) -> str:
        available_tools = [
            f"- {tool.name}: {tool.description}" 
            for tool in self.tools
        ]
        tools_description = "\n".join(available_tools) if available_tools else "No tools available"
        
        return prompt_config.get_system_prompt(
            self.agent_prompt_type,
            available_tools=tools_description
        )
    
    async def execute(self, query: str, context: AgentContext) -> AgentResponse:
        start_time = datetime.now()
        
        response = AgentResponse(
            content="",
            status=AgentStatus.PROCESSING,
            session_id=context.session_id,
            request_id=context.request_id
        )
        
        try:
            # Prepare messages from session history
            messages = []
            if self.session_repository and context.session_id:
                history = await self.session_repository.get_session_history(
                    context.user_id, 
                    context.session_id
                )
                
                for msg in history[-10:]:  # Last 10 messages for context
                    if msg.role == "user":
                        messages.append(HumanMessage(content=msg.content))
                    else:
                        messages.append(AIMessage(content=msg.content))
            
            # Add current user message
            messages.append(HumanMessage(content=query))
            
            # Save user message to session
            if self.session_repository and context.session_id:
                await self.session_repository.add_message(context.session_id, "user", query)
            
            # Prepare graph input
            graph_input = {
                "messages": messages
            }
            
            # Create thread config for checkpointing
            thread_config = None
            if self.enable_checkpointing and context.session_id:
                thread_config = {
                    "configurable": {
                        "thread_id": f"{context.user_id}_{context.session_id}"
                    }
                }
            
            # Execute the graph
            def run_graph():
                if thread_config:
                    return self.compiled_graph.invoke(graph_input, config=thread_config)
                return self.compiled_graph.invoke(graph_input)
            
            # Run in thread pool to avoid blocking
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as executor:
                result = await asyncio.get_event_loop().run_in_executor(
                    executor, run_graph
                )
            
            # Extract response from result
            if result and "messages" in result:
                last_message = result["messages"][-1]
                if hasattr(last_message, 'content'):
                    response.content = last_message.content
                else:
                    response.content = str(last_message)
            else:
                response.content = "I completed the task successfully."
            
            response.status = AgentStatus.COMPLETED
            
            # Extract tools used from intermediate steps if available
            if "intermediate_steps" in result:
                tools_used = []
                for step in result["intermediate_steps"]:
                    if hasattr(step, 'tool') and step.tool:
                        tools_used.append(step.tool)
                response.tools_used = tools_used
            
            # Save assistant response
            if self.session_repository and context.session_id:
                await self.session_repository.add_message(
                    context.session_id, 
                    "assistant", 
                    response.content
                )
            
        except Exception as e:
            response.content = "I apologize, but I encountered an error processing your request."
            response.status = AgentStatus.ERROR
            response.errors.append(str(e))
        
        response.processing_time_ms = (datetime.now() - start_time).total_seconds() * 1000
        return response
    
    async def get_conversation_state(self, thread_id: str) -> Dict[str, Any]:
        if not self.enable_checkpointing or not self.memory:
            return {}
        
        config = {"configurable": {"thread_id": thread_id}}
        state = self.compiled_graph.get_state(config)
        
        return {
            "messages": [msg.dict() if hasattr(msg, 'dict') else str(msg) 
                        for msg in state.values.get("messages", [])],
            "next_steps": state.next,
            "checkpoint_id": state.config.get("checkpoint_id")
        }
