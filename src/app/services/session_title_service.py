"""
Session title generation service.

Implements ChatGPT-style automatic title generation from conversation context.
Uses Strategy pattern for different title generation approaches.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from datetime import datetime
import asyncio
import re

from app.core.utils.logger import get_logger
from app.core.config import settings
from app.llm.factory.llm_factory import LLMFactory
from app.sessions.models import ChatMessage

logger = get_logger(__name__)


class TitleGenerationStrategy(ABC):
    """Abstract base class for title generation strategies."""
    
    @abstractmethod
    async def generate_title(self, messages: List[ChatMessage]) -> str:
        """
        Generate a title from conversation messages.
        
        Args:
            messages: List of chat messages
            
        Returns:
            Generated title string
        """
        pass


class LLMTitleGenerationStrategy(TitleGenerationStrategy):
    """Generate titles using LLM to understand conversation context."""
    
    def __init__(self, llm_provider: Optional[str] = None):
        """
        Initialize LLM title generation strategy.
        
        Args:
            llm_provider: Optional LLM provider name (defaults to configured provider)
        """
        self.llm_provider = llm_provider
        self.config = settings.app.session.auto_title
        
    async def generate_title(self, messages: List[ChatMessage]) -> str:
        """Generate title using LLM analysis of conversation."""
        try:
            if not messages:
                return self.config.default_title
            
            # Get LLM instance
            llm = LLMFactory.get_llm(self.llm_provider)
            await llm._ensure_initialized()
            
            # Build conversation context
            conversation_text = self._format_messages_for_prompt(messages)
            
            # Create title generation prompt
            prompt = self._build_title_generation_prompt(conversation_text)
            
            # Generate title with low temperature for consistency
            response = await llm.generate(
                prompt,
                temperature=self.config.temperature
            )
            
            # Clean and validate title
            title = self._clean_title(response.content)
            
            logger.info(
                f"Generated title using LLM",
                extra={
                    "title": title,
                    "message_count": len(messages),
                    "llm_provider": self.llm_provider or "default"
                }
            )
            
            return title
            
        except Exception as e:
            logger.error(f"LLM title generation failed: {e}", exc_info=True)
            # Fallback to extractive strategy
            fallback_strategy = ExtractiveTitleGenerationStrategy()
            return await fallback_strategy.generate_title(messages)
    
    def _format_messages_for_prompt(self, messages: List[ChatMessage]) -> str:
        """Format messages for LLM prompt."""
        formatted = []
        for msg in messages[:self.config.max_messages_for_context]:
            role = "User" if msg.role == "user" else "Assistant"
            # Truncate long messages
            content = msg.content[:200] + "..." if len(msg.content) > 200 else msg.content
            formatted.append(f"{role}: {content}")
        
        return "\n".join(formatted)
    
    def _build_title_generation_prompt(self, conversation_text: str) -> str:
        """Build prompt for LLM title generation."""
        min_words = self.config.min_title_words
        max_words = self.config.max_title_words
        
        return f"""Generate a concise, descriptive title for this conversation.

Requirements:
- {min_words}-{max_words} words maximum
- Capture the main topic or intent
- No quotes or punctuation at the end
- Clear and professional
- In English

Conversation:
{conversation_text}

Generate only the title (no explanations, no quotes):"""
    
    def _clean_title(self, raw_title: str) -> str:
        """Clean and validate generated title."""
        # Remove quotes if LLM added them
        title = raw_title.strip().strip('"').strip("'")
        
        # Remove trailing punctuation except necessary ones
        title = re.sub(r'[.!?;:]+$', '', title)
        
        # Capitalize first letter
        if title:
            title = title[0].upper() + title[1:]
        
        # Enforce word limit
        words = title.split()
        if len(words) > self.config.max_title_words:
            title = " ".join(words[:self.config.max_title_words])
        
        # Enforce character limit
        if len(title) > self.config.max_title_length:
            title = title[:self.config.max_title_length].rsplit(' ', 1)[0]
        
        # Validate minimum requirements
        if len(words) < self.config.min_title_words or not title:
            return self.config.fallback_title
        
        return title


class ExtractiveTitleGenerationStrategy(TitleGenerationStrategy):
    """Generate titles using extractive methods (fallback, no LLM needed)."""
    
    def __init__(self):
        self.config = settings.app.session.auto_title
    
    async def generate_title(self, messages: List[ChatMessage]) -> str:
        """Generate title by extracting key phrases from first user message."""
        try:
            if not messages:
                return self.config.default_title
            
            # Get first user message
            first_user_message = next(
                (msg for msg in messages if msg.role == "user"),
                None
            )
            
            if not first_user_message:
                return self.config.default_title
            
            # Extract title from first message
            content = first_user_message.content
            
            # Clean and truncate
            title = self._extract_title_from_content(content)
            
            logger.info(
                f"Generated title using extractive method",
                extra={"title": title, "message_count": len(messages)}
            )
            
            return title
            
        except Exception as e:
            logger.error(f"Extractive title generation failed: {e}", exc_info=True)
            return self.config.fallback_title
    
    def _extract_title_from_content(self, content: str) -> str:
        """Extract title from message content."""
        # Remove extra whitespace
        content = " ".join(content.split())
        
        # Take first sentence or question
        sentences = re.split(r'[.!?]', content)
        first_sentence = sentences[0].strip() if sentences else content
        
        # Convert to title case
        words = first_sentence.split()
        
        # Limit words
        if len(words) > self.config.max_title_words:
            words = words[:self.config.max_title_words]
        
        title = " ".join(words)
        
        # Enforce character limit
        if len(title) > self.config.max_title_length:
            title = title[:self.config.max_title_length].rsplit(' ', 1)[0]
        
        # Add ellipsis if truncated
        if len(words) > self.config.max_title_words or len(content) > self.config.max_title_length:
            title += "..."
        
        return title if title else self.config.fallback_title


class TimestampTitleGenerationStrategy(TitleGenerationStrategy):
    """Generate titles using timestamps (legacy fallback)."""
    
    async def generate_title(self, messages: List[ChatMessage]) -> str:
        """Generate timestamp-based title."""
        return f"Chat session {datetime.now().strftime('%Y-%m-%d %H:%M')}"


class SessionTitleService:
    """
    Service for managing session title generation.
    
    Implements ChatGPT-style automatic title generation with:
    - Deferred generation (after N messages)
    - Background/async processing
    - Multiple fallback strategies
    - Configuration-driven behavior
    """
    
    def __init__(self, strategy: Optional[TitleGenerationStrategy] = None):
        """
        Initialize session title service.
        
        Args:
            strategy: Optional title generation strategy (defaults to LLM strategy)
        """
        self.strategy = strategy or LLMTitleGenerationStrategy()
        self.config = settings.app.session.auto_title
    
    def should_generate_title(self, message_count: int, current_title: Optional[str] = None) -> bool:
        """
        Determine if title should be auto-generated.
        
        Args:
            message_count: Number of user messages in session
            current_title: Current session title
            
        Returns:
            True if title should be generated
        """
        if not self.config.enabled:
            logger.debug(f"Title generation disabled in config")
            return False
        
        # Don't regenerate if title was manually set (not default/fallback)
        if current_title and current_title not in [
            self.config.default_title,
            self.config.fallback_title
        ] and not current_title.startswith("Chat session") and not current_title.startswith("New Chat"):
            logger.debug(
                f"Title already set ('{current_title}'), skipping auto-generation"
            )
            return False
        
        # Generate after configured message count
        should_generate = message_count == self.config.trigger_message_count
        
        logger.debug(
            f"should_generate_title: message_count={message_count}, "
            f"trigger_count={self.config.trigger_message_count}, "
            f"current_title='{current_title}', result={should_generate}"
        )
        
        return should_generate
    
    async def generate_title_from_messages(
        self,
        messages: List[ChatMessage],
        fallback_strategy: Optional[TitleGenerationStrategy] = None
    ) -> str:
        """
        Generate title from conversation messages.
        
        Args:
            messages: List of chat messages
            fallback_strategy: Optional fallback strategy if primary fails
            
        Returns:
            Generated title
        """
        try:
            title = await self.strategy.generate_title(messages)
            return title
            
        except Exception as e:
            logger.error(f"Title generation failed with primary strategy: {e}")
            
            # Try fallback strategy
            if fallback_strategy:
                try:
                    return await fallback_strategy.generate_title(messages)
                except Exception as fallback_error:
                    logger.error(f"Fallback title generation failed: {fallback_error}")
            
            return self.config.fallback_title
    
    async def auto_generate_and_update_title(
        self,
        session_id: str,
        user_id: str,
        session_repository
    ) -> Optional[str]:
        """
        Auto-generate title and update session (background task).
        
        Args:
            session_id: Session identifier
            user_id: User identifier
            session_repository: Session repository instance
            
        Returns:
            Generated title or None if generation failed
        """
        try:
            # Get session messages
            messages = await self._get_session_messages(
                session_id,
                user_id,
                session_repository
            )
            
            if not messages:
                logger.warning(f"No messages found for session {session_id}")
                return None
            
            # Generate title
            title = await self.generate_title_from_messages(
                messages,
                fallback_strategy=ExtractiveTitleGenerationStrategy()
            )
            
            # Update session with new title
            await self._update_session_title(
                session_id,
                user_id,
                title,
                session_repository
            )
            
            logger.info(
                f"Auto-generated and updated session title",
                extra={
                    "session_id": session_id,
                    "title": title,
                    "message_count": len(messages)
                }
            )
            
            return title
            
        except Exception as e:
            logger.error(
                f"Auto title generation and update failed for session {session_id}: {e}",
                exc_info=True
            )
            return None
    
    async def _get_session_messages(
        self,
        session_id: str,
        user_id: str,
        session_repository
    ) -> List[ChatMessage]:
        """Retrieve session messages for title generation."""
        try:
            # Limit to first N messages for context
            messages = session_repository.get_session_messages(
                user_id=user_id,
                session_id=session_id,
                limit=self.config.max_messages_for_context
            )
            return messages
            
        except Exception as e:
            logger.error(f"Failed to retrieve messages for session {session_id}: {e}")
            return []
    
    async def _update_session_title(
        self,
        session_id: str,
        user_id: str,
        title: str,
        session_repository
    ):
        """Update session with generated title."""
        try:
            session_repository.update_session(
                user_id=user_id,
                session_id=session_id,
                data={"title": title}
            )
            
        except Exception as e:
            logger.error(f"Failed to update title for session {session_id}: {e}")
            raise
    
    def get_default_title(self) -> str:
        """Get default title for new sessions."""
        return self.config.default_title
    
    def set_strategy(self, strategy: TitleGenerationStrategy):
        """Set title generation strategy (for testing/configuration)."""
        self.strategy = strategy
