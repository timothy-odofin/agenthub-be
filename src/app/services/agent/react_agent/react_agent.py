
from langchain.agents import create_react_agent, AgentExecutor
from langchain_core.prompts import ChatPromptTemplate
from typing import Optional, Dict, Any, List
import asyncio
from datetime import datetime

from app.core.utils.single_ton import SingletonMeta
from app.services.agent.tools import ToolRegistry
from app.sessions.repositories.session_repository_factory import SessionRepositoryFactory
from app.sessions.repositories.base_session_repository import BaseSessionRepository

class ReactAgent(metaclass=SingletonMeta):
    """
    Production-ready ReAct agent wrapper with session management.
    Handles agent construction, prompt creation, inference, and chat history.
    """

    def __init__(self, llm, session_repository: Optional[BaseSessionRepository] = None, verbose: bool = False):
        if hasattr(self, "_initialized"):
            return  # prevent re-initialization

        self.llm = llm
        self.tools = ToolRegistry.get_instantiated_tools()
        self.verbose = verbose
        
        # Session management
        self.session_repository = session_repository or SessionRepositoryFactory.get_default_repository()

        self.prompt = ChatPromptTemplate.from_messages([
            ("system", "You are a helpful assistant. Use tools when needed. When user provides a question, think step by step. You should also give clarification when necessary."),
            ("placeholder", "{chat_history}"),  # Add chat history placeholder
            ("human", "{input}"),
            ("placeholder", "{agent_scratchpad}")
        ])

        self.agent = create_react_agent(
            llm=self.llm,
            tools=self.tools,
            prompt=self.prompt
        )

        self.executor = AgentExecutor(
            agent=self.agent,
            tools=self.tools,
            verbose=self.verbose
        )
        self._initialized = True

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
        """List sessions for a user."""
        return self.session_repository.list_paginated_sessions(user_id, page, limit)
