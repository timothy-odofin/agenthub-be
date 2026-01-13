"""
Chat service that provides a clean interface for agent interactions.

This service abstracts the agent system and handles:
- Agent lifecycle management
- Configuration management
- Response formatting for different protocols (REST/WebSocket)
- Error handling and logging
- Performance monitoring
- Automatic session title generation
"""

from datetime import datetime
from typing import Dict, Any, Optional, List
import asyncio

from app.core.utils.logger import get_logger
from app.core.utils.single_ton import SingletonMeta
from app.agent import AgentFactory, AgentContext
from app.core.constants import AgentType, AgentFramework
from app.sessions.repositories.session_repository_factory import SessionRepositoryFactory
from app.services.session_title_service import SessionTitleService

logger = get_logger(__name__)


class ChatService(metaclass=SingletonMeta):
    
    def __init__(self):
        if hasattr(self, "_initialized"):
            return

        self.agent_verbose = False
        self.title_service = SessionTitleService()
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
            protocol: str = "rest",
            metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        import uuid
        
        start_time = datetime.now()

        try:
            # Auto-generate session_id if not provided
            if session_id is None:
                session_id = str(uuid.uuid4())
                
            logger.info(f"Processing chat message for user {user_id}, session {session_id}")

            # Check if this is a capability selection
            enhanced_message = message
            if metadata and metadata.get("is_capability_selection"):
                enhanced_message = self._enhance_capability_message(message, metadata)
                logger.info(f"Enhanced message with capability context: {metadata.get('capability_id')}")

            agent = await self.agent
            
            context = AgentContext(
                user_id=user_id,
                session_id=session_id,
                metadata={"protocol": protocol, **(metadata or {})}
            )
            
            response = await agent.execute(enhanced_message, context)
            
            # Trigger auto title generation in background (non-blocking)
            asyncio.create_task(
                self._maybe_generate_title(user_id, response.session_id)
            )
            
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
            # Use new default title instead of timestamp
            session_title = title or self.title_service.get_default_title()
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
    
    def _enhance_capability_message(self, message: str, metadata: Dict[str, Any]) -> str:
        """
        Enhance user message with capability context when they select a capability.
        
        This helps the agent provide a more guided, conversational response by:
        1. Recognizing that the user selected a specific capability
        2. Providing context about what that capability can do
        3. Instructing the agent to offer specific options and examples
        
        Args:
            message: Original user message
            metadata: Request metadata containing capability information
            
        Returns:
            Enhanced message with capability context
        """
        try:
            from app.core.capabilities import SystemCapabilities
            
            capability_id = metadata.get("capability_id")
            if not capability_id:
                return message
            
            # Get full capability details
            capability = SystemCapabilities().get_capability_by_id(capability_id)
            if not capability:
                logger.warning(f"Capability not found: {capability_id}")
                return message
            
            # Build enhanced message with capability context
            enhanced_parts = [
                "## Capability Selection Context",
                f"The user has selected the **{capability['title']}** capability.",
                "",
                f"**Capability Description:** {capability['description']}",
                ""
            ]
            
            # Add example prompts if available
            if capability.get('example_prompts'):
                enhanced_parts.append("**Available Actions:**")
                for prompt in capability['example_prompts']:
                    enhanced_parts.append(f"- {prompt}")
                enhanced_parts.append("")
            
            # Add tags for context
            if capability.get('tags'):
                enhanced_parts.append(f"**Related Topics:** {', '.join(capability['tags'])}")
                enhanced_parts.append("")
            
            # Add the original message
            enhanced_parts.extend([
                f"**User's Message:** {message}",
                "",
                "## Your Task",
                "The user has selected this capability but may not have specified exactly what they want to do yet.",
                "",
                "**Respond by:**",
                "1. Acknowledging their selection warmly",
                "2. Briefly explaining what you can help them with (use the capability description)",
                "3. Offering 3-4 **specific, actionable examples** from the available actions above",
                "4. Asking them what they'd like to do or inviting them to provide more details",
                "",
                "Keep your response conversational, helpful, and focused on guiding them to their goal.",
                "Use the example prompts above as suggestions to help them get started."
            ])
            
            enhanced_message = "\n".join(enhanced_parts)
            
            logger.debug(f"Enhanced capability message for: {capability_id}")
            return enhanced_message
            
        except Exception as e:
            logger.error(f"Failed to enhance capability message: {e}", exc_info=True)
            return message
    
    async def _maybe_generate_title(self, user_id: str, session_id: str):
        """
        Background task to auto-generate session title if conditions are met.
        
        This is called after each message and checks if title should be generated.
        Non-blocking - runs in background without affecting chat response time.
        
        Args:
            user_id: User identifier
            session_id: Session identifier
        """
        try:
            logger.debug(f"_maybe_generate_title called for session {session_id}")
            
            session_repo = SessionRepositoryFactory.get_default_repository()
            
            # Get current session info
            session = session_repo.get_session(user_id, session_id)
            if not session:
                logger.warning(f"Session not found for title generation: {session_id}")
                return
            
            logger.debug(f"Session found with title: '{session.title}'")
            
            # Count user messages in session
            messages = session_repo.get_session_messages(
                user_id=user_id,
                session_id=session_id,
                limit=100  # Get more to count accurately
            )
            
            user_message_count = sum(1 for msg in messages if msg.role == "user")
            
            logger.info(
                f"Title generation check: session={session_id}, user_messages={user_message_count}, "
                f"current_title='{session.title}', enabled={self.title_service.config.enabled}, "
                f"trigger_count={self.title_service.config.trigger_message_count}"
            )
            
            # Check if we should generate title
            should_generate = self.title_service.should_generate_title(user_message_count, session.title)
            
            logger.info(
                f"Should generate title: {should_generate} for session {session_id} "
                f"(user_messages={user_message_count}, current_title='{session.title}')"
            )
            
            if should_generate:
                logger.info(
                    f"Triggering auto title generation for session {session_id}",
                    extra={"user_message_count": user_message_count}
                )
                
                await self.title_service.auto_generate_and_update_title(
                    session_id=session_id,
                    user_id=user_id,
                    session_repository=session_repo
                )
        
        except Exception as e:
            # Don't let title generation errors affect the chat
            logger.error(
                f"Background title generation failed for session {session_id}: {e}",
                exc_info=True
            )
    
    async def update_session_title(
        self,
        user_id: str,
        session_id: str,
        title: str
    ) -> bool:
        """
        Manually update session title.
        
        Args:
            user_id: User identifier
            session_id: Session identifier
            title: New title
            
        Returns:
            True if successful, False otherwise
        """
        try:
            session_repo = SessionRepositoryFactory.get_default_repository()
            session_repo.update_session(
                user_id=user_id,
                session_id=session_id,
                data={"title": title}
            )
            
            logger.info(f"Manually updated title for session {session_id} to '{title}'")
            return True
            
        except Exception as e:
            logger.error(f"Failed to update session title: {e}")
            return False

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
