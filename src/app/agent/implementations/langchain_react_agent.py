import asyncio
from datetime import datetime
from typing import Set, Dict, Any
from langchain_core.prompts import ChatPromptTemplate
from langchain.agents.format_scratchpad.openai_tools import format_to_openai_tool_messages
from langchain.agents.output_parsers.openai_tools import OpenAIToolsAgentOutputParser
from langchain_core.messages import HumanMessage, AIMessage

from app.core.enums import AgentCapability, AgentType, AgentStatus, AgentFramework
from app.agent.frameworks.langchain_agent import LangChainAgent
from app.agent.models import AgentContext, AgentResponse
from app.agent.base.agent_registry import AgentRegistry
from app.core.config.providers.prompt import prompt_config, PromptType


@AgentRegistry.register(AgentType.REACT, AgentFramework.LANGCHAIN)
class LangChainReactAgent(LangChainAgent):
    
    def __init__(self, *args, **kwargs):
        super().__init__(AgentType.REACT, *args, **kwargs)
        self.agent_prompt_type = self.config.get('prompt_type', PromptType.REACT_AGENT.value)
    
    @property
    def name(self) -> str:
        return "LangChain ReAct Agent"
    
    @property
    def version(self) -> str:
        return "1.0.0"
    
    def get_supported_capabilities(self) -> Set[AgentCapability]:
        base_capabilities = {
            AgentCapability.REACT,
            AgentCapability.TOOL_CALLING,
            AgentCapability.MULTI_TURN_CONVERSATION,
            AgentCapability.ASYNC_PROCESSING
        }
        return base_capabilities | self.get_framework_capabilities()
    
    def get_configuration_schema(self) -> Dict[str, Any]:
        return {
            "prompt_type": {
                "type": "string",
                "default": PromptType.REACT_AGENT.value,
                "description": "Prompt template type for the agent"
            },
            "max_iterations": {
                "type": "integer",
                "default": 10,
                "description": "Maximum reasoning iterations"
            },
            "verbose": {
                "type": "boolean",
                "default": False,
                "description": "Enable verbose logging"
            }
        }
    
    def _create_prompt_template(self) -> ChatPromptTemplate:
        available_tools = [
            f"- {tool.name}: {tool.description}" 
            for tool in self.tools
        ]
        tools_description = "\n".join(available_tools) if available_tools else "No tools available"
        
        system_prompt = prompt_config.get_system_prompt(
            self.agent_prompt_type,
            available_tools=tools_description
        )
        
        return ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            ("placeholder", "{chat_history}"),
            ("human", "{input}"),
            ("placeholder", "{agent_scratchpad}")
        ])
    
    def _create_agent_runnable(self):
        llm_with_tools = self.llm.bind_tools(self.tools)
        
        return (
            {
                "input": lambda x: x["input"],
                "agent_scratchpad": lambda x: format_to_openai_tool_messages(x["intermediate_steps"]),
                "chat_history": lambda x: x.get("chat_history", []),
            }
            | self.prompt
            | llm_with_tools
            | OpenAIToolsAgentOutputParser()
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
            chat_history = []
            if self.session_repository and context.session_id:
                messages = await self.session_repository.get_session_history(
                    context.user_id, 
                    context.session_id
                )
                
                for msg in messages[-10:]:
                    if msg.role == "user":
                        chat_history.append(HumanMessage(content=msg.content))
                    else:
                        chat_history.append(AIMessage(content=msg.content))
            
            if self.session_repository and context.session_id:
                await self.session_repository.add_message(context.session_id, "user", query)
            
            def run_agent():
                return self.executor.invoke({
                    "input": query,
                    "chat_history": chat_history
                })
            
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as executor:
                agent_response = await asyncio.get_event_loop().run_in_executor(
                    executor, run_agent
                )
            
            response.content = agent_response.get("output", "")
            response.status = AgentStatus.COMPLETED
            
            if "intermediate_steps" in agent_response:
                for step in agent_response["intermediate_steps"]:
                    if hasattr(step, 'tool') and step.tool:
                        response.tools_used.append(step.tool)
            
            if self.session_repository and context.session_id:
                await self.session_repository.add_message(context.session_id, "assistant", response.content)
            
        except Exception as e:
            response.content = "I apologize, but I encountered an error processing your request."
            response.status = AgentStatus.ERROR
            response.errors.append(str(e))
        
        response.processing_time_ms = (datetime.now() - start_time).total_seconds() * 1000
        return response
