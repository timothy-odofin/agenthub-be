"""
Chat service that provides a clean interface for agent interactions.

This service abstracts the agent system and handles:
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
from app.agent import AgentFactory, AgentContext
from app.core.constants import AgentType, AgentFramework
from app.sessions.repositories.session_repository_factory import SessionRepositoryFactory

logger = get_logger(__name__)


class ChatService(metaclass=SingletonMeta):
    
    def __init__(self):
        if hasattr(self, "_initialized"):
            return

        self.agent_verbose = False
        self._agent = None
        self._agent_type = AgentType.REACT
        
        # Default to LangChain, but can be configured
        self._agent_framework = AgentFramework.LANGCHAIN
        # self._agent_framework = AgentFramework.LANGGRAPH  # Uncomment to use LangGraph
        
        self._initialized = True
        logger.info("ChatService initialized")

    @property
    async def agent(self):
        """Lazy load the agent to avoid initialization issues."""
        if self._agent is None:
            try:
                from app.llm.factory.llm_factory import LLMFactory
                from app.core.constants import LLMProvider

                llm = LLMFactory.get_llm(LLMProvider.OPENAI)
                session_repo = SessionRepositoryFactory.get_default_repository()

                self._agent = await AgentFactory.create_agent(
                    agent_type=self._agent_type,
                    framework=self._agent_framework,
                    llm_provider=llm,
                    session_repository=session_repo,
                    verbose=self.agent_verbose
                )
                logger.info("Agent initialized successfully")

            except Exception as e:
                logger.error(f"Failed to initialize agent: {e}", exc_info=True)
                raise

        return self._agent
    
    def set_agent_framework(self, framework: AgentFramework) -> None:
        if self._agent is not None:
            logger.warning(f"Switching agent framework from {self._agent_framework} to {framework}")
        self._agent_framework = framework
        self._agent = None  # Reset agent to force re-initialization

    async def chat(
            self,
            message: str,
            user_id: str,
            session_id: Optional[str] = None,
            protocol: str = "rest"
    ) -> Dict[str, Any]:
        import uuid
        
        start_time = datetime.now()

        try:
            # Auto-generate session_id if not provided
            if session_id is None:
                session_id = str(uuid.uuid4())
                
            logger.info(f"Processing chat message for user {user_id}, session {session_id}")

            agent = await self.agent
            
            context = AgentContext(
                user_id=user_id,
                session_id=session_id,
                metadata={"protocol": protocol}
            )
            
            response = await agent.execute(message, context)
            
            # Convert to legacy format for backward compatibility
            legacy_response = {
                "success": response.success,
                "message": response.content,
                "user_id": user_id,
                "session_id": response.session_id,
                "timestamp": response.timestamp.isoformat(),
                "processing_time_ms": response.processing_time_ms,
                "tools_used": response.tools_used,
                "errors": response.errors,
                "metadata": response.metadata,
                "service": {
                    "name": "ChatService",
                    "version": "2.0.0",
                    "protocol": protocol,
                    "service_processing_time_ms": round((datetime.now() - start_time).total_seconds() * 1000, 2)
                }
            }

            logger.info(
                f"Chat completed for user {user_id} in {legacy_response['service']['service_processing_time_ms']}ms"
            )

            return legacy_response

        except Exception as e:
            logger.error(f"Chat service error for user {user_id}: {e}", exc_info=True)

            return {
                "success": False,
                "message": "I apologize, but I'm experiencing technical difficulties. Please try again.",
                "user_id": user_id,
                "session_id": session_id,
                "timestamp": datetime.now().isoformat(),
                "errors": [str(e)],
                "service": {
                    "name": "ChatService",
                    "version": "2.0.0",
                    "protocol": protocol,
                    "service_processing_time_ms": round((datetime.now() - start_time).total_seconds() * 1000, 2)
                }
            }


    async def chat_simple(self, message: str, user_id: str, session_id: Optional[str] = None) -> str:
        try:
            result = await self.chat(message, user_id, session_id, "rest")
            return result.get("message", "I apologize, but I'm experiencing technical difficulties.")
        except Exception as e:
            logger.error(f"Simple chat error for user {user_id}: {e}", exc_info=True)
            return "I apologize, but I'm experiencing technical difficulties. Please try again."

    def create_session(self, user_id: str, title: Optional[str] = None) -> str:
        try:
            session_title = title or f"Chat session {datetime.now().strftime('%Y-%m-%d %H:%M')}"
            session_repo = SessionRepositoryFactory.get_default_repository()
            session_id = session_repo.create_session(
                user_id=user_id,
                session_data={'title': session_title}
            )

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
            session_repo = SessionRepositoryFactory.get_default_repository()
            messages = await session_repo.get_session_history(user_id, session_id)

            formatted_messages = []
            for msg in messages:
                formatted_messages.append({
                    "role": msg.role,
                    "content": msg.content,
                    "timestamp": msg.timestamp.isoformat() if hasattr(msg, 'timestamp') else None,
                    "id": getattr(msg, 'id', None)
                })

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
        try:
            session_repo = SessionRepositoryFactory.get_default_repository()
            sessions = session_repo.list_paginated_sessions(user_id, page, limit)

            
            formatted_sessions = [
                {
                    "session_id": session.session_id,
                    "title": session.title,
                    "user_id": session.user_id,
                    "created_at": session.created_at.isoformat(),
                    "updated_at": session.updated_at.isoformat(),
                    "metadata": session.metadata
                }
                for session in sessions
            ]

            logger.info(f"Retrieved {len(formatted_sessions)} sessions for user {user_id}")
            return {
                "sessions": formatted_sessions,
                "total": len(sessions),
                "page": page,
                "limit": limit,
                "has_more": len(sessions) == limit
            }

        except Exception as e:
            logger.error(f"Failed to list sessions for user {user_id}: {e}")
            return {
                "sessions": [],
                "total": 0,
                "page": page,
                "limit": limit,
                "has_more": False
            }

    async def get_available_tools(self) -> List[Dict[str, str]]:
        try:
            from app.agent.tools.base.registry import ToolRegistry
            tools = ToolRegistry.get_instantiated_tools()

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

    async def health_check(self) -> Dict[str, Any]:
        try:
            from app.agent.tools.base.registry import ToolRegistry
            tools_count = len(ToolRegistry.get_instantiated_tools())
            
            agent_info = None
            if self._agent:
                agent_info = await self._agent.health_check()

            return {
                "status": "healthy",
                "timestamp": datetime.now().isoformat(),
                "agent_initialized": self._agent is not None,
                "tools_available": tools_count,
                "service_version": "2.0.0",
                "agent_info": agent_info
            }

        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return {
                "status": "unhealthy",
                "timestamp": datetime.now().isoformat(),
                "agent_initialized": False,
                "error": str(e),
                "service_version": "2.0.0"
            }
