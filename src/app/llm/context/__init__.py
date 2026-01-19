"""
Context window management for LLM conversations.
Handles token counting, message truncation, and context optimization.
"""

import time
import tiktoken
from typing import List, Dict, Any, Optional, Tuple
from abc import ABC, abstractmethod
from dataclasses import dataclass
from langchain_core.messages import HumanMessage, AIMessage, BaseMessage

from app.sessions.models.message import ChatMessage
from app.core.utils.single_ton import SingletonMeta
from app.core.utils.logger import get_logger
from app.core.config.framework.settings import settings

logger = get_logger(__name__)


@dataclass
class ContextWindow:
    """Context window configuration."""
    max_tokens: int
    reserved_tokens: int = 500  # Reserve tokens for response
    system_prompt_tokens: int = 100  # Estimate for system prompt
    
    @property
    def available_tokens(self) -> int:
        """Calculate available tokens for history."""
        return self.max_tokens - self.reserved_tokens - self.system_prompt_tokens


class TokenCounter(ABC):
    """Abstract base class for token counting."""
    
    @abstractmethod
    def count_tokens(self, text: str) -> int:
        """Count tokens in text."""
        pass
    
    @abstractmethod
    def count_message_tokens(self, message: BaseMessage) -> int:
        """Count tokens in a message."""
        pass


class TikTokenCounter(TokenCounter):
    """OpenAI tiktoken-based token counter."""
    
    def __init__(self, model: str = "gpt-4"):
        try:
            self.encoding = tiktoken.encoding_for_model(model)
        except KeyError:
            # Fallback to cl100k_base encoding for unknown models
            self.encoding = tiktoken.get_encoding("cl100k_base")
    
    def count_tokens(self, text: str) -> int:
        """Count tokens in text."""
        if not text:
            return 0
        return len(self.encoding.encode(text))
    
    def count_message_tokens(self, message: BaseMessage) -> int:
        """Count tokens in a message including role overhead."""
        content_tokens = self.count_tokens(message.content)
        # Add overhead for message structure (role, metadata, etc.)
        return content_tokens + 4  # Approximate overhead per message


class SimpleTokenCounter(TokenCounter):
    """Simple token counter using word approximation."""
    
    def count_tokens(self, text: str) -> int:
        """Estimate tokens as ~0.75 * word count."""
        if not text:
            return 0
        return int(len(text.split()) * 0.75)
    
    def count_message_tokens(self, message: BaseMessage) -> int:
        """Count tokens in a message."""
        return self.count_tokens(message.content) + 2  # Small overhead


class ContextStrategy(ABC):
    """Abstract strategy for context window management."""
    
    @abstractmethod
    def truncate_messages(
        self, 
        messages: List[ChatMessage], 
        available_tokens: int,
        token_counter: TokenCounter
    ) -> List[BaseMessage]:
        """Truncate messages to fit within available tokens."""
        pass


class RecentMessagesStrategy(ContextStrategy):
    """Keep most recent messages that fit in context window."""
    
    def truncate_messages(
        self, 
        messages: List[ChatMessage], 
        available_tokens: int,
        token_counter: TokenCounter
    ) -> List[BaseMessage]:
        """Keep most recent messages that fit within token limit."""
        if not messages:
            return []
        
        result = []
        current_tokens = 0
        
        # Process messages in reverse order (most recent first)
        for message in reversed(messages):
            # Convert to LangChain message
            if message.role == "user":
                lc_message = HumanMessage(content=message.content)
            else:
                lc_message = AIMessage(content=message.content)
            
            # Count tokens for this message
            message_tokens = token_counter.count_message_tokens(lc_message)
            
            # Check if adding this message would exceed limit
            if current_tokens + message_tokens > available_tokens:
                break
                
            result.insert(0, lc_message)  # Insert at beginning to maintain order
            current_tokens += message_tokens
        
        return result


class SlidingWindowStrategy(ContextStrategy):
    """Sliding window with importance-based message selection."""
    
    def __init__(self, min_recent_messages: int = 5):
        self.min_recent_messages = min_recent_messages
    
    def truncate_messages(
        self, 
        messages: List[ChatMessage], 
        available_tokens: int,
        token_counter: TokenCounter
    ) -> List[BaseMessage]:
        """Keep recent messages + important earlier messages."""
        if not messages:
            return []
        
        # Always keep the most recent messages
        recent_messages = messages[-self.min_recent_messages:]
        earlier_messages = messages[:-self.min_recent_messages] if len(messages) > self.min_recent_messages else []
        
        result = []
        current_tokens = 0
        
        # First, add recent messages
        for message in recent_messages:
            if message.role == "user":
                lc_message = HumanMessage(content=message.content)
            else:
                lc_message = AIMessage(content=message.content)
                
            message_tokens = token_counter.count_message_tokens(lc_message)
            if current_tokens + message_tokens <= available_tokens:
                result.append(lc_message)
                current_tokens += message_tokens
        
        # Then, add important earlier messages if space allows
        for message in reversed(earlier_messages):
            if message.role == "user":
                lc_message = HumanMessage(content=message.content)
            else:
                lc_message = AIMessage(content=message.content)
                
            message_tokens = token_counter.count_message_tokens(lc_message)
            if current_tokens + message_tokens <= available_tokens:
                result.insert(-len(recent_messages), lc_message)
                current_tokens += message_tokens
        
        return result


class SummarizationStrategy(ContextStrategy):
    """Summarize old messages to preserve context while saving tokens."""
    
    def __init__(self, summarization_threshold: int = 20):
        self.summarization_threshold = summarization_threshold
    
    def truncate_messages(
        self, 
        messages: List[ChatMessage], 
        available_tokens: int,
        token_counter: TokenCounter
    ) -> List[BaseMessage]:
        """Summarize old messages and keep recent ones."""
        if not messages:
            return []
        
        # If we have few messages, just use recent strategy
        if len(messages) <= self.summarization_threshold:
            strategy = RecentMessagesStrategy()
            return strategy.truncate_messages(messages, available_tokens, token_counter)
        
        # Split messages into old (to summarize) and recent (to keep)
        split_point = len(messages) - 10  # Keep last 10 messages
        old_messages = messages[:split_point]
        recent_messages = messages[split_point:]
        
        # Create summary of old messages
        summary_content = self._create_summary(old_messages)
        summary_message = AIMessage(content=f"[Previous conversation summary: {summary_content}]")
        summary_tokens = token_counter.count_message_tokens(summary_message)
        
        result = [summary_message]
        current_tokens = summary_tokens
        
        # Add recent messages
        for message in recent_messages:
            if message.role == "user":
                lc_message = HumanMessage(content=message.content)
            else:
                lc_message = AIMessage(content=message.content)
                
            message_tokens = token_counter.count_message_tokens(lc_message)
            if current_tokens + message_tokens <= available_tokens:
                result.append(lc_message)
                current_tokens += message_tokens
        
        return result
    
    def _create_summary(self, messages: List[ChatMessage]) -> str:
        """Create a simple summary of old messages."""
        if not messages:
            return "No previous context."
        
        # Simple extractive summary
        key_points = []
        current_topic = None
        
        for i, message in enumerate(messages):
            # Extract key information (this is simplified)
            content = message.content
            if len(content) > 100:  # Long messages likely contain important info
                key_points.append(f"User discussed: {content[:80]}...")
            elif "?" in content:  # Questions are often important
                key_points.append(f"User asked: {content}")
        
        if not key_points:
            return f"Conversation covered {len(messages)} exchanges about general topics."
        
        return " | ".join(key_points[:5])  # Keep top 5 key points


class ContextWindowManager(metaclass=SingletonMeta):
    """Main context window manager."""
    
    def __init__(self):
        self.token_counters: Dict[str, TokenCounter] = {}
        self.strategies: Dict[str, ContextStrategy] = {
            "recent": RecentMessagesStrategy(),
            "sliding": SlidingWindowStrategy(),
            "summarization": SummarizationStrategy()
        }
        
        # Load model windows from Settings system
        self.model_windows = self._load_model_windows_from_settings()
        
        # Apply strategy configurations from settings
        self._apply_strategy_configurations()
    
    def _load_model_windows_from_settings(self) -> Dict[str, ContextWindow]:
        """Load model window definitions from Settings system."""
        model_windows = {}
        window_settings = settings.context
        try:
            # Access context configuration from Settings system
            if hasattr(window_settings, 'context_window') and hasattr(window_settings.context_window, 'definitions'):
                definitions = window_settings.context_window.definitions
                
                # Convert each model definition to ContextWindow
                for model_name in dir(definitions):
                    if model_name.startswith('_') or model_name in ['get', 'has', 'to_dict', 'update', 'keys', 'values', 'items']:
                        continue
                    
                    model_config = getattr(definitions, model_name, None)
                    if model_config and hasattr(model_config, 'max_tokens'):
                        model_windows[model_name] = ContextWindow(
                            max_tokens=getattr(model_config, 'max_tokens', 4096),
                            reserved_tokens=getattr(model_config, 'reserved_tokens', 500),
                            system_prompt_tokens=getattr(model_config, 'system_prompt_tokens', 100)
                        )
                        
                logger.info(f"Loaded {len(model_windows)} model window definitions from settings")
                
            else:
                logger.warning("No context window definitions found in settings, using minimal fallback")
                # Minimal fallback if no config found
                model_windows["default"] = ContextWindow(max_tokens=4096)
        
        except Exception as e:
            logger.error(f"Error loading model windows from settings: {e}")
            # Emergency fallback
            model_windows["default"] = ContextWindow(max_tokens=4096)
        
        return model_windows
    
    def _apply_strategy_configurations(self):
        """Apply strategy configurations from settings."""
        try:
            if hasattr(settings.context, 'context_window') and hasattr(settings.context.context_window, 'strategies'):
                strategies_config = settings.context.context_window.strategies
                
                # Configure sliding window strategy
                if hasattr(strategies_config, 'sliding') and hasattr(strategies_config.sliding, 'min_recent_messages'):
                    min_recent = getattr(strategies_config.sliding, 'min_recent_messages', 5)
                    self.strategies["sliding"] = SlidingWindowStrategy(min_recent_messages=min_recent)
                
                # Configure summarization strategy
                if hasattr(strategies_config, 'summarization'):
                    threshold = getattr(strategies_config.summarization, 'summarization_threshold', 20)
                    self.strategies["summarization"] = SummarizationStrategy(summarization_threshold=threshold)
                
                logger.debug("Applied strategy configurations from settings")
        
        except Exception as e:
            logger.warning(f"Error applying strategy configurations: {e}, using defaults")
    
    def get_token_counter(self, model: str) -> TokenCounter:
        """Get appropriate token counter for model."""
        if model not in self.token_counters:
            if "gpt" in model.lower() or "claude" in model.lower():
                self.token_counters[model] = TikTokenCounter(model)
            else:
                self.token_counters[model] = SimpleTokenCounter()
        
        return self.token_counters[model]
    
    def get_context_window(self, model: str) -> ContextWindow:
        """Get context window configuration for model."""
        return self.model_windows.get(model, self.model_windows["default"])
    
    def prepare_context(
        self,
        messages: List[ChatMessage],
        model: str = None,
        strategy: str = None,
        custom_max_tokens: Optional[int] = None
    ) -> Tuple[List[BaseMessage], Dict[str, Any]]:
        """
        Prepare messages for LLM context with token management.
        
        Args:
            messages: Chat history messages
            model: LLM model name for token counting
            strategy: Context management strategy
            custom_max_tokens: Override default max tokens
            
        Returns:
            Tuple of (processed_messages, metadata)
        """
        start_time = time.time()
        
        # Get default values from settings
        default_model = getattr(settings.context.context_window, 'default_model', 'gpt-4')
        default_strategy = getattr(settings.context.context_window, 'default_strategy', 'recent')
        max_single_message_tokens = getattr(settings.context.context_window, 'max_single_message_tokens', 2000)
        log_utilization = getattr(settings.context.context_window, 'log_utilization', True)
        emergency_message_limit = getattr(settings.context.context_window, 'emergency_message_limit', 3)
        max_processing_time = getattr(settings.context.context_window, 'max_processing_time', 5.0)
        warn_threshold = getattr(settings.context.context_window, 'warn_threshold', 0.8)
        
        # Use defaults if not specified
        model = model or default_model
        strategy = strategy or default_strategy
        
        # Get components
        token_counter = self.get_token_counter(model)
        context_window = self.get_context_window(model)
        
        # Override max tokens if provided
        if custom_max_tokens:
            context_window = ContextWindow(
                max_tokens=custom_max_tokens,
                reserved_tokens=context_window.reserved_tokens,
                system_prompt_tokens=context_window.system_prompt_tokens
            )
        
        # Get strategy
        context_strategy = self.strategies.get(strategy, self.strategies["recent"])
        
        # Calculate total tokens in original messages
        original_tokens = sum(
            token_counter.count_tokens(msg.content) for msg in messages
        )
        
        # Safety check: truncate extremely long individual messages
        processed_input_messages = []
        for msg in messages:
            content = msg.content
            msg_tokens = token_counter.count_tokens(content)
            
            if msg_tokens > max_single_message_tokens:
                # Truncate the message content
                words = content.split()
                truncated_words = []
                current_tokens = 0
                
                for word in words:
                    word_tokens = token_counter.count_tokens(word)
                    if current_tokens + word_tokens > max_single_message_tokens:
                        break
                    truncated_words.append(word)
                    current_tokens += word_tokens
                
                content = " ".join(truncated_words) + "... [truncated]"
                if log_utilization:
                    logger.warning(
                        f"Truncated oversized message: {msg_tokens} tokens → {current_tokens} tokens"
                    )
            
            # Create a new message with truncated content, preserving original structure
            processed_msg = ChatMessage(
                message_id=msg.message_id,
                session_id=msg.session_id,
                role=msg.role,
                content=content,
                timestamp=msg.timestamp
            )
            processed_input_messages.append(processed_msg)
        
        try:
            # Truncate messages using selected strategy
            processed_messages = context_strategy.truncate_messages(
                processed_input_messages,
                context_window.available_tokens,
                token_counter
            )
            
            # Emergency fallback if strategy fails
            if not processed_messages and messages:
                logger.warning("Context strategy failed, using emergency fallback")
                recent_messages = processed_input_messages[-emergency_message_limit:]
                
                processed_messages = []
                for msg in recent_messages:
                    if msg.role == "user":
                        processed_messages.append(HumanMessage(content=msg.content))
                    else:
                        processed_messages.append(AIMessage(content=msg.content))
        
        except Exception as e:
            logger.error(f"Context preparation failed: {e}")
            # Emergency fallback
            processed_messages = []
            if messages:
                last_msg = processed_input_messages[-1]
                if last_msg.role == "user":
                    processed_messages = [HumanMessage(content=last_msg.content)]
                else:
                    processed_messages = [AIMessage(content=last_msg.content)]
        
        # Calculate final token usage
        final_tokens = sum(
            token_counter.count_message_tokens(msg) for msg in processed_messages
        )
        
        # Processing time check
        processing_time = time.time() - start_time
        if processing_time > max_processing_time:
            logger.warning(
                f"Context preparation took {processing_time:.2f}s, "
                f"exceeded limit of {max_processing_time}s"
            )
        
        # Prepare metadata
        metadata = {
            "original_message_count": len(messages),
            "final_message_count": len(processed_messages),
            "original_tokens": original_tokens,
            "final_tokens": final_tokens,
            "max_tokens": context_window.max_tokens,
            "available_tokens": context_window.available_tokens,
            "token_utilization": final_tokens / context_window.available_tokens if context_window.available_tokens > 0 else 0,
            "strategy_used": strategy,
            "model": model,
            "messages_truncated": len(messages) - len(processed_messages),
            "processing_time": processing_time,
            "tokens_saved": original_tokens - final_tokens,
            "efficiency_ratio": final_tokens / original_tokens if original_tokens > 0 else 1.0
        }
        
        # Log utilization if enabled
        if log_utilization:
            utilization = metadata['token_utilization']
            if utilization >= warn_threshold:
                logger.warning(
                    f"High context utilization: {utilization:.1%} "
                    f"({final_tokens}/{context_window.available_tokens} tokens) "
                    f"with {strategy} strategy for {model}"
                )
            else:
                logger.info(
                    f"Context prepared: {utilization:.1%} utilization "
                    f"({metadata['final_message_count']}/{metadata['original_message_count']} messages, "
                    f"{final_tokens} tokens) using {strategy} strategy"
                )
        
        return processed_messages, metadata


# Export main components
__all__ = [
    "ContextWindowManager",
    "ContextWindow", 
    "ContextStrategy",
    "RecentMessagesStrategy",
    "SlidingWindowStrategy", 
    "SummarizationStrategy",
    "TokenCounter",
    "TikTokenCounter",
    "SimpleTokenCounter"
]
