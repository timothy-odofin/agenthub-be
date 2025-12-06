"""
Chat service that provides a clean interface for agent interactions.

This service abstracts the ReactAgent and handles:
- Agent lifecycle management
- Configuration management
- Response formatting for different protocols (REST/WebSocket)
- Error handling and logging
- Performance monitoring
"""

from datetime import datetime
from typing import Dict, Any, Optional, List

from app.core.utils.logger import get_logger
from app.core.utils.single_ton import SingletonMeta
from app.services.agent.react_agent.react_agent import ReactAgent
from app.sessions.repositories.session_repository_factory import SessionRepositoryFactory

logger = get_logger(__name__)


class ChatService(metaclass=SingletonMeta):
    """
    Service layer for chat/agent interactions.
    
    Provides a clean interface between API layers and the ReactAgent,
    handles configuration, error management, and response formatting.
    """

    def __init__(self):
        """Initialize the chat service."""
        if hasattr(self, "_initialized"):
            return

        # Hardcode settings for now - replace with proper config later
        self.agent_verbose = False  # Can be made configurable later
        self._agent = None
        self._initialized = True
        logger.info("ChatService initialized")

    @property
    def agent(self) -> ReactAgent:
        """Lazy load the ReactAgent to avoid initialization issues."""
        if self._agent is None:
            try:
                # Import LLM here to avoid circular imports
                from app.llm.factory.llm_factory import LLMFactory
                from app.core.constants import LLMProvider

                # Get LLM from factory
                llm = LLMFactory.get_llm(LLMProvider.OPENAI)
                
                # Check if already initialized, if not we need to initialize it
                if not llm._initialized:
                    # We can't use asyncio.run() here because we're already in an event loop
                    # So we'll defer initialization until first use
                    pass
                    
                session_repo = SessionRepositoryFactory.get_default_repository()

                self._agent = ReactAgent(
                    llm=llm,
                    session_repository=session_repo,
                    verbose=self.agent_verbose
                )
                logger.info("ReactAgent initialized successfully")

            except Exception as e:
                logger.error(f"Failed to initialize ReactAgent: {e}")
                raise

        return self._agent

    async def chat(
            self,
            message: str,
            user_id: str,
            session_id: Optional[str] = None,
            protocol: str = "rest"
    ) -> Dict[str, Any]:
        """
        Send a message to the agent and get a response.
        
        Args:
            message: User's message/query
            user_id: ID of the user
            session_id: Optional session ID
            protocol: Response format ("rest", "websocket")
            
        Returns:
            Formatted response based on protocol
        """
        start_time = datetime.now()

        try:
            logger.info(f"Processing chat message for user {user_id}, session {session_id}")

            # Get response from agent (use async version for proper initialization)
            if protocol == "websocket":
                response = await self.agent.run_for_websocket_async(message, user_id, session_id)
            else:
                response = await self.agent.run_async(message, user_id, session_id)

            # Add service-level metadata
            response["service"] = {
                "name": "ChatService",
                "version": "1.0.0",
                "protocol": protocol,
                "service_processing_time_ms": round((datetime.now() - start_time).total_seconds() * 1000, 2)
            }

            logger.info(
                f"Chat completed for user {user_id} in {response['service']['service_processing_time_ms']}ms"
            )

            return response

        except Exception as e:
            logger.error(f"Chat service error for user {user_id}: {e}")

            # Return error response in appropriate format
            error_response = {
                "success": False,
                "message": "I apologize, but I'm experiencing technical difficulties. Please try again.",
                "user_id": user_id,
                "session_id": session_id,
                "timestamp": datetime.now().isoformat(),
                "errors": [str(e)],
                "service": {
                    "name": "ChatService",
                    "version": "1.0.0",
                    "protocol": protocol,
                    "service_processing_time_ms": round((datetime.now() - start_time).total_seconds() * 1000, 2)
                }
            }

            if protocol == "websocket":
                error_response.update({
                    "type": "agent_response",
                    "status": "error",
                    "has_errors": True
                })

            return error_response

    def chat_simple(self, message: str, user_id: str, session_id: Optional[str] = None) -> str:
        """
        Simple chat interface that returns just the message string.
        Useful for simple REST endpoints or backward compatibility.
        
        Args:
            message: User's message
            user_id: ID of the user
            session_id: Optional session ID
            
        Returns:
            Agent's response message as string
        """
        try:
            return self.agent.run_simple(message, user_id, session_id)
        except Exception as e:
            logger.error(f"Simple chat error for user {user_id}: {e}")
            return "I apologize, but I'm experiencing technical difficulties. Please try again."

    def create_session(self, user_id: str, title: Optional[str] = None) -> str:
        """
        Create a new chat session.
        
        Args:
            user_id: ID of the user
            title: Optional session title
            
        Returns:
            New session ID
        """
        try:
            session_title = title or f"Chat session {datetime.now().strftime('%Y-%m-%d %H:%M')}"
            session_id = self.agent.create_session(user_id, session_title)

            logger.info(f"Created new session {session_id} for user {user_id}")
            return session_id

        except Exception as e:
            logger.error(f"Failed to create session for user {user_id}: {e}")
            raise

    async def get_session_history(
            self,
            user_id: str,
            session_id: str,
            limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Get chat history for a session.
        
        Args:
            user_id: ID of the user
            session_id: Session ID
            limit: Optional limit on number of messages
            
        Returns:
            List of messages in the session
        """
        try:
            messages = await self.agent.get_session_history(user_id, session_id)

            # Format messages for API response
            formatted_messages = []
            for msg in messages:
                formatted_messages.append({
                    "role": msg.role,
                    "content": msg.content,
                    "timestamp": msg.timestamp.isoformat() if hasattr(msg, 'timestamp') else None,
                    "id": getattr(msg, 'id', None)
                })

            # Apply limit if specified
            if limit:
                formatted_messages = formatted_messages[-limit:]

            logger.info(f"Retrieved {len(formatted_messages)} messages for session {session_id}")
            return formatted_messages

        except Exception as e:
            logger.error(f"Failed to get session history {session_id} for user {user_id}: {e}")
            return []

    def list_user_sessions(
            self,
            user_id: str,
            page: int = 0,
            limit: int = 10
    ) -> Dict[str, Any]:
        """
        List chat sessions for a user.
        
        Args:
            user_id: ID of the user
            page: Page number (0-based)
            limit: Number of sessions per page
            
        Returns:
            Paginated list of sessions
        """
        try:
            sessions = self.agent.list_user_sessions(user_id, page, limit)

            logger.info(f"Retrieved {len(sessions.get('sessions', []))} sessions for user {user_id}")
            return sessions

        except Exception as e:
            logger.error(f"Failed to list sessions for user {user_id}: {e}")
            return {
                "sessions": [],
                "total": 0,
                "page": page,
                "limit": limit,
                "has_more": False
            }

    def get_available_tools(self) -> List[Dict[str, str]]:
        """
        Get information about available tools.
        
        Returns:
            List of available tools with their descriptions
        """
        try:
            tools = self.agent.tools

            tool_info = []
            for tool in tools:
                tool_info.append({
                    "name": tool.name,
                    "description": tool.description
                })

            logger.info(f"Retrieved information for {len(tool_info)} available tools")
            return tool_info

        except Exception as e:
            logger.error(f"Failed to get available tools: {e}")
            return []

    def health_check(self) -> Dict[str, Any]:
        """
        Check the health status of the chat service.
        
        Returns:
            Health status information
        """
        try:
            # Try to access the agent (this will initialize it if needed)
            tools_count = len(self.agent.tools)

            return {
                "status": "healthy",
                "timestamp": datetime.now().isoformat(),
                "agent_initialized": self._agent is not None,
                "tools_available": tools_count,
                "service_version": "1.0.0"
            }

        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return {
                "status": "unhealthy",
                "timestamp": datetime.now().isoformat(),
                "agent_initialized": False,
                "error": str(e),
                "service_version": "1.0.0"
            }
