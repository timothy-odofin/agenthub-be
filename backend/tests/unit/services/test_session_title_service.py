"""
Unit tests for Session Title Service.

Tests ChatGPT-style automatic title generation with multiple strategies.
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from datetime import datetime

from app.services.session_title_service import (
    SessionTitleService,
    LLMTitleGenerationStrategy,
    ExtractiveTitleGenerationStrategy,
    TimestampTitleGenerationStrategy
)


def create_test_message(role: str, content: str, message_id: str = "test-msg", session_id: str = "test-session"):
    """Helper function to create test ChatMessage objects."""
    return ChatMessage(
        message_id=message_id,
        session_id=session_id,
        role=role,
        content=content,
        timestamp=datetime.now()
    )
from app.sessions.models import ChatMessage


class TestLLMTitleGenerationStrategy:
    """Test LLM-based title generation strategy."""
    
    @pytest.mark.asyncio
    async def test_generate_title_success(self):
        """Test successful title generation using LLM."""
        # Arrange
        messages = [
            create_test_message(role="user", content="How do I reset my password?"),
            create_test_message(role="assistant", content="I can help you reset your password..."),
            create_test_message(role="user", content="Where is the reset button?"),
        ]
        
        strategy = LLMTitleGenerationStrategy()
        
        # Mock LLM response
        mock_response = Mock()
        mock_response.content = "Password Reset Assistance"
        
        with patch.object(strategy, '_build_title_generation_prompt', return_value="mock prompt"):
            with patch('app.llm.factory.llm_factory.LLMFactory.get_llm') as mock_get_llm:
                mock_llm = AsyncMock()
                mock_llm._ensure_initialized = AsyncMock()
                mock_llm.generate = AsyncMock(return_value=mock_response)
                mock_get_llm.return_value = mock_llm
                
                # Act
                title = await strategy.generate_title(messages)
        
        # Assert
        assert title == "Password Reset Assistance"
        assert len(title.split()) <= 7  # Max words
    
    @pytest.mark.asyncio
    async def test_generate_title_with_quotes(self):
        """Test title generation strips quotes added by LLM."""
        messages = [
            create_test_message(role="user", content="Help with Jira")
        ]
        
        strategy = LLMTitleGenerationStrategy()
        
        mock_response = Mock()
        mock_response.content = '"Jira Integration Help"'  # LLM added quotes
        
        with patch('app.llm.factory.llm_factory.LLMFactory.get_llm') as mock_get_llm:
            mock_llm = AsyncMock()
            mock_llm._ensure_initialized = AsyncMock()
            mock_llm.generate = AsyncMock(return_value=mock_response)
            mock_get_llm.return_value = mock_llm
            
            title = await strategy.generate_title(messages)
        
        assert title == "Jira Integration Help"
        assert '"' not in title
    
    @pytest.mark.asyncio
    async def test_generate_title_too_many_words(self):
        """Test title generation truncates if too many words."""
        messages = [
            create_test_message(role="user", content="Tell me about something")
        ]
        
        strategy = LLMTitleGenerationStrategy()
        
        mock_response = Mock()
        mock_response.content = "This Is A Very Long Title With Too Many Words In It"
        
        with patch('app.llm.factory.llm_factory.LLMFactory.get_llm') as mock_get_llm:
            mock_llm = AsyncMock()
            mock_llm._ensure_initialized = AsyncMock()
            mock_llm.generate = AsyncMock(return_value=mock_response)
            mock_get_llm.return_value = mock_llm
            
            title = await strategy.generate_title(messages)
        
        # Should be truncated to max_title_words (7 by default)
        assert len(title.split()) <= 7
    
    @pytest.mark.asyncio
    async def test_generate_title_empty_messages(self):
        """Test title generation with empty messages returns default."""
        strategy = LLMTitleGenerationStrategy()
        
        title = await strategy.generate_title([])
        
        assert title == "New Chat"  # Default from config
    
    @pytest.mark.asyncio
    async def test_generate_title_llm_failure_fallback(self):
        """Test fallback to extractive strategy when LLM fails."""
        messages = [
            create_test_message(role="user", content="How to fix my computer?")
        ]
        
        strategy = LLMTitleGenerationStrategy()
        
        with patch('app.llm.factory.llm_factory.LLMFactory.get_llm') as mock_get_llm:
            mock_llm = AsyncMock()
            mock_llm._ensure_initialized = AsyncMock()
            mock_llm.generate = AsyncMock(side_effect=Exception("LLM error"))
            mock_get_llm.return_value = mock_llm
            
            title = await strategy.generate_title(messages)
        
        # Should fallback to extractive method
        assert title is not None
        assert len(title) > 0
    
    def test_clean_title_removes_trailing_punctuation(self):
        """Test _clean_title removes trailing punctuation."""
        strategy = LLMTitleGenerationStrategy()
        
        assert strategy._clean_title("Help With Jira.") == "Help With Jira"
        assert strategy._clean_title("Password Reset Question?") == "Password Reset Question"
        assert strategy._clean_title("Test This Now!") == "Test This Now"
    
    def test_clean_title_capitalizes_first_letter(self):
        """Test _clean_title capitalizes first letter."""
        strategy = LLMTitleGenerationStrategy()
        
        assert strategy._clean_title("help with jira") == "Help with jira"


class TestExtractiveTitleGenerationStrategy:
    """Test extractive (non-LLM) title generation strategy."""
    
    @pytest.mark.asyncio
    async def test_generate_title_from_first_message(self):
        """Test extractive title from first user message."""
        messages = [
            create_test_message(role="user", content="How do I reset my password?"),
            create_test_message(role="assistant", content="I can help..."),
        ]
        
        strategy = ExtractiveTitleGenerationStrategy()
        title = await strategy.generate_title(messages)
        
        assert "How do I reset my" in title or "How do I reset my password" in title
        assert len(title) <= 50  # Max length from config
    
    @pytest.mark.asyncio
    async def test_generate_title_truncates_long_message(self):
        """Test extractive title truncates long messages."""
        long_message = "This is a very long message that contains many words and should be truncated to fit within the maximum title length configured in the system settings"
        
        messages = [
            create_test_message(role="user", content=long_message)
        ]
        
        strategy = ExtractiveTitleGenerationStrategy()
        title = await strategy.generate_title(messages)
        
        assert len(title) <= 50  # Max length
        assert title.endswith("...")  # Truncation indicator
    
    @pytest.mark.asyncio
    async def test_generate_title_empty_messages(self):
        """Test extractive title with empty messages."""
        strategy = ExtractiveTitleGenerationStrategy()
        
        title = await strategy.generate_title([])
        
        assert title == "New Chat"  # Fallback from config
    
    @pytest.mark.asyncio
    async def test_generate_title_only_assistant_messages(self):
        """Test extractive title when only assistant messages exist."""
        messages = [
            create_test_message(role="assistant", content="Hello! How can I help?")
        ]
        
        strategy = ExtractiveTitleGenerationStrategy()
        title = await strategy.generate_title(messages)
        
        # Should return default since no user message
        assert title == "New Chat"


class TestTimestampTitleGenerationStrategy:
    """Test timestamp-based title generation (legacy)."""
    
    @pytest.mark.asyncio
    async def test_generate_timestamp_title(self):
        """Test timestamp title generation."""
        messages = [
            create_test_message(role="user", content="Hello")
        ]
        
        strategy = TimestampTitleGenerationStrategy()
        title = await strategy.generate_title(messages)
        
        assert "Chat session" in title
        assert "20" in title  # Year prefix
        assert "-" in title  # Date separator


class TestSessionTitleService:
    """Test session title service with strategy pattern."""
    
    def test_should_generate_title_after_trigger_count(self):
        """Test title generation triggered after configured message count."""
        service = SessionTitleService()
        
        # Should not generate before trigger count
        assert not service.should_generate_title(1, "New Chat")
        assert not service.should_generate_title(2, "New Chat")
        
        # Should generate at trigger count
        assert service.should_generate_title(3, "New Chat")
    
    def test_should_not_regenerate_custom_title(self):
        """Test title generation skipped if custom title exists."""
        service = SessionTitleService()
        
        # Should not regenerate custom titles
        assert not service.should_generate_title(3, "My Custom Title")
        assert not service.should_generate_title(5, "Important Discussion")
    
    def test_should_regenerate_default_titles(self):
        """Test title generation works for default/fallback titles."""
        service = SessionTitleService()
        
        # Should regenerate default titles
        assert service.should_generate_title(3, "New Chat")
        assert service.should_generate_title(3, "Untitled Conversation")
        assert service.should_generate_title(3, "Chat session 2026-01-11 15:30")
    
    def test_should_not_generate_if_disabled(self):
        """Test title generation disabled when config says so."""
        service = SessionTitleService()
        
        with patch.object(service.config, 'enabled', False):
            assert not service.should_generate_title(3, "New Chat")
    
    @pytest.mark.asyncio
    async def test_generate_title_from_messages_success(self):
        """Test successful title generation from messages."""
        messages = [
            create_test_message(role="user", content="Help with Jira")
        ]
        
        mock_strategy = AsyncMock()
        mock_strategy.generate_title = AsyncMock(return_value="Jira Help")
        
        service = SessionTitleService(strategy=mock_strategy)
        title = await service.generate_title_from_messages(messages)
        
        assert title == "Jira Help"
        mock_strategy.generate_title.assert_called_once_with(messages)
    
    @pytest.mark.asyncio
    async def test_generate_title_with_fallback_strategy(self):
        """Test fallback strategy used when primary fails."""
        messages = [
            create_test_message(role="user", content="Help")
        ]
        
        mock_primary = AsyncMock()
        mock_primary.generate_title = AsyncMock(side_effect=Exception("Primary failed"))
        
        mock_fallback = AsyncMock()
        mock_fallback.generate_title = AsyncMock(return_value="Fallback Title")
        
        service = SessionTitleService(strategy=mock_primary)
        title = await service.generate_title_from_messages(messages, fallback_strategy=mock_fallback)
        
        assert title == "Fallback Title"
        mock_fallback.generate_title.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_auto_generate_and_update_title(self):
        """Test complete auto-generation and update flow."""
        session_id = "test-session-123"
        user_id = "user-456"
        
        messages = [
            create_test_message(role="user", content="Help with Jira"),
            create_test_message(role="assistant", content="Sure!"),
            create_test_message(role="user", content="How to create ticket?"),
        ]
        
        mock_repo = Mock()
        mock_repo.get_session_messages = Mock(return_value=messages)
        mock_repo.update_session = Mock()
        
        mock_strategy = AsyncMock()
        mock_strategy.generate_title = AsyncMock(return_value="Jira Ticket Creation")
        
        service = SessionTitleService(strategy=mock_strategy)
        
        title = await service.auto_generate_and_update_title(
            session_id=session_id,
            user_id=user_id,
            session_repository=mock_repo
        )
        
        assert title == "Jira Ticket Creation"
        mock_repo.get_session_messages.assert_called_once()
        mock_repo.update_session.assert_called_once_with(
            user_id=user_id,
            session_id=session_id,
            data={"title": "Jira Ticket Creation"}
        )
    
    @pytest.mark.asyncio
    async def test_auto_generate_handles_no_messages(self):
        """Test auto-generation handles case with no messages gracefully."""
        mock_repo = Mock()
        mock_repo.get_session_messages = Mock(return_value=[])
        
        service = SessionTitleService()
        
        title = await service.auto_generate_and_update_title(
            session_id="test-123",
            user_id="user-456",
            session_repository=mock_repo
        )
        
        assert title is None
    
    def test_get_default_title(self):
        """Test getting default title from configuration."""
        service = SessionTitleService()
        
        default_title = service.get_default_title()
        
        assert default_title == "New Chat"
    
    def test_set_strategy(self):
        """Test changing strategy dynamically."""
        service = SessionTitleService()
        
        new_strategy = TimestampTitleGenerationStrategy()
        service.set_strategy(new_strategy)
        
        assert service.strategy == new_strategy


class TestTitleGenerationIntegration:
    """Integration tests for complete title generation flow."""
    
    @pytest.mark.asyncio
    async def test_full_workflow_llm_to_extractive_fallback(self):
        """Test complete workflow with LLM failure and extractive fallback."""
        messages = [
            create_test_message(role="user", content="How to reset password?"),
            create_test_message(role="assistant", content="I can help with that."),
        ]
        
        # LLM strategy that will fail
        llm_strategy = LLMTitleGenerationStrategy()
        
        with patch('app.llm.factory.llm_factory.LLMFactory.get_llm') as mock_get_llm:
            mock_llm = AsyncMock()
            mock_llm._ensure_initialized = AsyncMock()
            mock_llm.generate = AsyncMock(side_effect=Exception("LLM unavailable"))
            mock_get_llm.return_value = mock_llm
            
            # Should fallback to extractive
            title = await llm_strategy.generate_title(messages)
        
        # Should get a valid title from fallback
        assert title is not None
        assert len(title) > 0
        assert title != "New Chat"  # Should extract from content
    
    @pytest.mark.asyncio
    async def test_strategy_pattern_flexibility(self):
        """Test that different strategies can be swapped easily."""
        messages = [
            create_test_message(role="user", content="Test message")
        ]
        
        service = SessionTitleService()
        
        # Test with LLM strategy
        llm_strategy = LLMTitleGenerationStrategy()
        service.set_strategy(llm_strategy)
        
        # Test with extractive strategy
        extractive_strategy = ExtractiveTitleGenerationStrategy()
        service.set_strategy(extractive_strategy)
        title = await service.generate_title_from_messages(messages)
        
        assert "Test message" in title or title == "Untitled Conversation"
        
        # Test with timestamp strategy
        timestamp_strategy = TimestampTitleGenerationStrategy()
        service.set_strategy(timestamp_strategy)
        title = await service.generate_title_from_messages(messages)
        
        assert "Chat session" in title
