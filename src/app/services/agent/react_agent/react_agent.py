
import asyncio
from datetime import datetime
from typing import Optional, Dict, Any

from langchain.agents import AgentExecutor
from langchain_core.prompts import ChatPromptTemplate
from langchain.agents.format_scratchpad.openai_tools import format_to_openai_tool_messages
from langchain.agents.output_parsers.openai_tools import OpenAIToolsAgentOutputParser
from langchain_core.messages import HumanMessage, AIMessage

from app.core.utils.single_ton import SingletonMeta
from app.services.agent.tools import ToolRegistry
from app.sessions.repositories.base_session_repository import BaseSessionRepository
from app.sessions.repositories.session_repository_factory import SessionRepositoryFactory
from app.core.config.providers.prompt import prompt_config, PromptType
from app.core.config.framework.settings import settings


class ReactAgent(metaclass=SingletonMeta):
    """
    Production-ready ReAct agent wrapper with session management.
    Handles agent construction, prompt creation, inference, and chat history.
    Uses centralized prompt configuration for consistent behavior across environments.
    """

    def __init__(self, llm, session_repository: Optional[BaseSessionRepository] = None, 
                 verbose: bool = False, agent_type: str = PromptType.REACT_AGENT.value, 
                 environment: Optional[str] = None, user_id: Optional[str] = None):
        if hasattr(self, "_initialized"):
            return 

        # Store the LLM provider for later initialization if needed
        self.llm_provider = llm
        self.llm = None  # Will be set when initialized
        
        self.tools = ToolRegistry.get_instantiated_tools()
        self.verbose = verbose
        
        # Agent configuration
        self.agent_type = agent_type  # react_agent, react_agent_technical, react_agent_business, etc.
        self.environment = environment or getattr(settings, 'app', {}).get('environment', 'production')
        self.user_id = user_id
        
        # Session management
        self.session_repository = session_repository or SessionRepositoryFactory.get_default_repository()

        # Prompt will be generated dynamically from configuration
        self.prompt = None

        # Agent and executor will be created after LLM initialization
        self.agent = None
        self.executor = None
        self._initialized = True
    
    def _get_agent_prompt(self) -> str:
        """
        Get the appropriate agent prompt based on configuration.
        
        Returns:
            Formatted prompt string with available tools
        """
        # Get available tools list for prompt template
        available_tools = [
            f"- {tool.name}: {tool.description}" 
            for tool in self.tools
        ]
        tools_description = "\n".join(available_tools) if available_tools else "No tools currently available"
        
        # Get prompt by name and pass tools to it
        prompt = prompt_config.get_system_prompt(
            self.agent_type,
            available_tools=tools_description
        )
        return prompt
    
    def _create_prompt_template(self) -> ChatPromptTemplate:
        """
        Create the ChatPromptTemplate using the configured prompt.
        
        Returns:
            ChatPromptTemplate with system message from configuration
        """
        system_prompt = self._get_agent_prompt()
        
        return ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            ("placeholder", "{chat_history}"),
            ("human", "{input}"),
            ("placeholder", "{agent_scratchpad}")
        ])

        # Agent and executor will be created after LLM initialization
        self.agent = None
        self.executor = None
        self._initialized = True

    async def _ensure_llm_initialized(self):
        """Ensure the LLM is initialized and agent is created."""
        if self.llm is None:
            # Initialize the LLM provider
            await self.llm_provider._ensure_initialized()
            
            # Extract the LangChain client
            if hasattr(self.llm_provider, 'client') and self.llm_provider.client is not None:
                self.llm = self.llm_provider.client
            else:
                self.llm = self.llm_provider

            # Create the prompt template from configuration
            self.prompt = self._create_prompt_template()

            # Bind tools to the LLM for the modern agent approach
            llm_with_tools = self.llm.bind_tools(self.tools)

            # Create agent with modern approach using messages
            def create_agent_runnable():
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
            
            self.agent = create_agent_runnable()

            self.executor = AgentExecutor(
                agent=self.agent,
                tools=self.tools,
                verbose=self.verbose
            )

    async def run_async(self, query: str, user_id: str, session_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Run a user query through the agent with session management (async version).
        
        Args:
            query: User's question/input
            user_id: ID of the user
            session_id: Optional session ID. If None, creates a new session
            
        Returns:
            Dict containing response, metadata, session info, and any errors
        """
        # Ensure LLM and agent are initialized
        await self._ensure_llm_initialized()
        
        start_time = datetime.now()
        
        # Initialize response structure
        response_data = {
            "success": False,
            "message": "",
            "session_id": session_id,
            "user_id": user_id,
            "query": query,
            "timestamp": start_time.isoformat(),
            "processing_time_ms": 0,
            "tools_used": [],
            "chat_history_loaded": False,
            "errors": [],
            "metadata": {}
        }
        
        try:
            # Step 1: Handle session creation if needed
            if not session_id:
                session_id = await self.session_repository.create_session_async(
                    user_id=user_id,
                    session_data={'title': query[:50] + "..." if len(query) > 50 else query}
                )
                response_data["session_id"] = session_id
            
            # Step 2: Get chat history
            messages = await self.session_repository.get_session_history(user_id, session_id)
            
            # Format chat history for the LangChain agent
            from langchain_core.messages import HumanMessage, AIMessage
            
            chat_history_messages = []
            for msg in messages[-10:]:  # Last 10 messages for context
                if msg.role == "user":
                    chat_history_messages.append(HumanMessage(content=msg.content))
                else:
                    chat_history_messages.append(AIMessage(content=msg.content))
            
            response_data["chat_history_loaded"] = True
            response_data["metadata"]["history_messages_count"] = len(messages)
            response_data["metadata"]["context_messages_used"] = min(10, len(messages))
            
            # Step 3: Save user message
            await self.session_repository.add_message(session_id, "user", query)
            
            # Step 4: Run agent with chat history (sync operation in thread pool)
            def run_agent():
                return self.executor.invoke({
                    "input": query,
                    "chat_history": chat_history_messages
                })
            
            # Run the sync agent in a thread pool to avoid blocking
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as executor:
                agent_response = await asyncio.get_event_loop().run_in_executor(
                    executor, run_agent
                )
            
            output = agent_response.get("output", "")
            response_data["message"] = output
            response_data["success"] = True
            
            # Extract tools used (if available in the response)
            if "intermediate_steps" in agent_response:
                tools_used = []
                for step in agent_response["intermediate_steps"]:
                    if hasattr(step, 'tool') and step.tool:
                        tools_used.append(step.tool)
                response_data["tools_used"] = tools_used
                response_data["metadata"]["tools_count"] = len(tools_used)
            
            # Step 5: Save assistant response
            await self.session_repository.add_message(session_id, "assistant", output)
            
        except Exception as e:
            response_data["errors"].append(str(e))
            response_data["message"] = "I apologize, but I encountered an error processing your request."
            print(f"Error in ReactAgent.run_async: {e}")
        
        # Calculate processing time
        end_time = datetime.now()
        response_data["processing_time_ms"] = round((end_time - start_time).total_seconds() * 1000, 2)
        
        return response_data

    def run(self, query: str, user_id: str, session_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Run a user query through the agent with session management.
        
        Args:
            query: User's question/input
            user_id: ID of the user
            session_id: Optional session ID. If None, creates a new session
            
        Returns:
            Dict containing response, metadata, session info, and any errors
        """
        # Ensure executor is available (should be called after async initialization)
        if self.executor is None:
            raise RuntimeError("Agent not initialized. Use run_async() for proper initialization.")
            
        start_time = datetime.now()
        
        # Initialize response structure
        response_data = {
            "success": False,
            "message": "",
            "session_id": session_id,
            "user_id": user_id,
            "query": query,
            "timestamp": start_time.isoformat(),
            "processing_time_ms": 0,
            "tools_used": [],
            "chat_history_loaded": False,
            "errors": [],
            "metadata": {}
        }
        
        try:
            # Create or get session
            if not session_id:
                session_id = self.session_repository.create_session(
                    user_id=user_id,
                    session_data={'title': query[:50] + "..." if len(query) > 50 else query}
                )
                response_data["session_id"] = session_id
            
            # Get chat history
            chat_history = []
            try:
                loop = asyncio.get_event_loop()
                messages = loop.run_until_complete(
                    self.session_repository.get_session_history(user_id, session_id)
                )
                
                # Format chat history for the prompt
                for msg in messages[-10:]:  # Last 10 messages for context
                    if msg.role == "user":
                        chat_history.append(f"Human: {msg.content}")
                    else:
                        chat_history.append(f"Assistant: {msg.content}")
                
                response_data["chat_history_loaded"] = True
                response_data["metadata"]["history_messages_count"] = len(messages)
                response_data["metadata"]["context_messages_used"] = min(10, len(messages))
            
            except Exception as e:
                error_msg = f"Could not load chat history: {str(e)}"
                response_data["errors"].append(error_msg)
                print(f"Warning: {error_msg}")
            
            # Format chat history
            formatted_history = "\n".join(chat_history) if chat_history else ""
            
            # Save user message
            try:
                loop = asyncio.get_event_loop()
                loop.run_until_complete(
                    self.session_repository.add_message(session_id, "user", query)
                )
            except Exception as e:
                error_msg = f"Could not save user message: {str(e)}"
                response_data["errors"].append(error_msg)
                print(f"Warning: {error_msg}")
            
            # Run agent with chat history
            agent_response = self.executor.invoke({
                "input": query,
                "chat_history": formatted_history
            })
            
            output = agent_response.get("output", "")
            response_data["message"] = output
            response_data["success"] = True
            
            # Extract tools used (if available in the response)
            if "intermediate_steps" in agent_response:
                tools_used = []
                for step in agent_response["intermediate_steps"]:
                    if hasattr(step, 'tool') and step.tool:
                        tools_used.append(step.tool)
                response_data["tools_used"] = tools_used
                response_data["metadata"]["tools_count"] = len(tools_used)
            
            # Save assistant response
            try:
                loop = asyncio.get_event_loop()
                loop.run_until_complete(
                    self.session_repository.add_message(session_id, "assistant", output)
                )
            except Exception as e:
                error_msg = f"Could not save assistant message: {str(e)}"
                response_data["errors"].append(error_msg)
                print(f"Warning: {error_msg}")
            
        except Exception as e:
            error_msg = f"Agent execution failed: {str(e)}"
            response_data["errors"].append(error_msg)
            response_data["message"] = "I apologize, but I encountered an error while processing your request."
        
        finally:
            # Calculate processing time
            end_time = datetime.now()
            processing_time = (end_time - start_time).total_seconds() * 1000
            response_data["processing_time_ms"] = round(processing_time, 2)
        
        return response_data
    
    def run_simple(self, query: str, user_id: str, session_id: Optional[str] = None) -> str:
        """
        Backward compatibility method that returns just the message string.
        
        Args:
            query: User's question/input
            user_id: ID of the user
            session_id: Optional session ID
            
        Returns:
            Just the agent's response message
        """
        result = self.run(query, user_id, session_id)
        return result.get("message", "")
    
    def run_for_websocket(self, query: str, user_id: str, session_id: Optional[str] = None) -> Dict[str, Any]:
        """
        WebSocket-optimized version with streaming indicators and structured response.
        
        Returns response optimized for real-time WebSocket communication.
        """
        result = self.run(query, user_id, session_id)
        
        # Add WebSocket-specific fields
        websocket_response = {
            "type": "agent_response",
            "status": "completed" if result["success"] else "error",
            "session_id": result["session_id"],
            "message": result["message"],
            "timestamp": result["timestamp"],
            "processing_time_ms": result["processing_time_ms"],
            "has_errors": len(result["errors"]) > 0,
            "errors": result["errors"],
            "metadata": {
                "tools_used_count": len(result["tools_used"]),
                "tools_used": result["tools_used"],
                **result["metadata"]
            }
        }
        
        return websocket_response
    
    def create_session(self, user_id: str, title: str = "New Chat") -> str:
        """Create a new chat session."""
        return self.session_repository.create_session(
            user_id=user_id,
            session_data={'title': title}
        )
    
    async def get_session_history(self, user_id: str, session_id: str):
        """Get the chat history for a session."""
        return await self.session_repository.get_session_history(user_id, session_id)
    
    def list_user_sessions(self, user_id: str, page: int = 0, limit: int = 10):
        """List sessions for a user with pagination metadata."""
        sessions = self.session_repository.list_paginated_sessions(user_id, page, limit)
        
        # Convert to the expected format for the chat service
        return {
            "sessions": [
                {
                    "session_id": session.session_id,
                    "title": session.title,
                    "user_id": session.user_id,
                    "created_at": session.created_at.isoformat(),
                    "updated_at": session.updated_at.isoformat(),
                    "metadata": session.metadata
                }
                for session in sessions
            ],
            "total": len(sessions),  # Note: This is just the current page count, not total across all pages
            "page": page,
            "limit": limit,
            "has_more": len(sessions) == limit  # Assumes more if we got a full page
        }
