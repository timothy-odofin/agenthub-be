"""
Integration test for intelligent field clarification feature.

This test demonstrates how the system responds to user questions about fields
with personalized, contextual answers powered by LLM.
"""

import pytest
from app.schemas.conversational_auth import (
    SignupStep,
    ConversationalSignupRequest,
)


@pytest.mark.asyncio
class TestIntelligentClarification:
    """Test suite for intelligent clarification responses."""
    
    async def test_user_asks_about_email_at_start(self, conversational_auth_service):
        """
        Test: User asks "What do you mean by email address?" at START step.
        
        Expected: System provides intelligent, contextual answer and stays on START.
        """
        request = ConversationalSignupRequest(
            message="What do you mean by email address?",
            session_id="12f1dd13-c686-4da0-815e-df1477eed142",
            current_step=SignupStep.START
        )
        
        response = await conversational_auth_service.process_signup_step(request)
        
        # Should stay on START (no progress)
        assert response.next_step == SignupStep.START
        assert response.success is True
        
        # Message should contain explanation about email
        message_lower = response.message.lower()
        assert "email" in message_lower
        
        # Should ask for email at the end
        assert "?" in response.message
        
        print(f"\n✅ Intelligent Response:\n{response.message}\n")
    
    async def test_user_asks_why_email_needed(self, conversational_auth_service):
        """
        Test: User asks "Why do you need my email?" at EMAIL step.
        
        Expected: System explains purpose of email and stays on EMAIL step.
        """
        # First, create a session by starting signup
        start_request = ConversationalSignupRequest(
            message="yes",
            session_id=None,
            current_step=SignupStep.START
        )
        start_response = await conversational_auth_service.process_signup_step(start_request)
        session_id = start_response.session_id
        
        # Now ask clarifying question
        request = ConversationalSignupRequest(
            message="Why do you need my email?",
            session_id=session_id,
            current_step=SignupStep.EMAIL
        )
        
        response = await conversational_auth_service.process_signup_step(request)
        
        # Should stay on EMAIL (no progress)
        assert response.next_step == SignupStep.EMAIL
        assert response.success is True
        
        # Message should explain why email is needed
        message_lower = response.message.lower()
        assert any(word in message_lower for word in ["login", "account", "identifier", "contact"])
        
        # Should ask for email
        assert "email" in message_lower
        
        print(f"\n✅ Intelligent Response:\n{response.message}\n")
    
    async def test_user_asks_about_password_requirements(self, conversational_auth_service):
        """
        Test: User asks "What makes a password strong?" at PASSWORD step.
        
        Expected: System explains password requirements specifically.
        """
        # Setup: Create session and progress to PASSWORD step
        # (You would need to go through email and username steps first)
        # For this test, we'll simulate being at PASSWORD step
        
        from app.db.repositories.signup_session_repository import signup_session_repository
        import uuid
        
        session_id = str(uuid.uuid4())
        await signup_session_repository.create_session(
            session_id,
            {
                "email": "test@example.com",
                "username": "testuser",
                "current_step": SignupStep.PASSWORD.value
            }
        )
        
        request = ConversationalSignupRequest(
            message="What makes a password strong?",
            session_id=session_id,
            current_step=SignupStep.PASSWORD
        )
        
        response = await conversational_auth_service.process_signup_step(request)
        
        # Should stay on PASSWORD (no progress)
        assert response.next_step == SignupStep.PASSWORD
        assert response.success is True
        
        # Message should explain password strength
        message_lower = response.message.lower()
        assert "password" in message_lower
        assert any(word in message_lower for word in ["strong", "secure", "character", "uppercase", "lowercase", "number"])
        
        print(f"\n✅ Intelligent Response:\n{response.message}\n")
        
        # Cleanup
        await signup_session_repository.delete_session(session_id)
    
    async def test_user_asks_vs_provides_data(self, conversational_auth_service):
        """
        Test: System correctly distinguishes between asking questions vs providing data.
        
        Expected: Questions trigger clarification, data proceeds to next step.
        """
        # Start signup
        start_request = ConversationalSignupRequest(
            message="yes",
            session_id=None,
            current_step=SignupStep.START
        )
        start_response = await conversational_auth_service.process_signup_step(start_request)
        session_id = start_response.session_id
        
        # Test 1: Ask a question (should stay on EMAIL)
        question_request = ConversationalSignupRequest(
            message="What is an email?",
            session_id=session_id,
            current_step=SignupStep.EMAIL
        )
        question_response = await conversational_auth_service.process_signup_step(question_request)
        assert question_response.next_step == SignupStep.EMAIL  # Stays on same step
        print(f"\n✅ Question Response: {question_response.message[:100]}...\n")
        
        # Test 2: Provide data (should move to USERNAME)
        data_request = ConversationalSignupRequest(
            message="test@example.com",
            session_id=session_id,
            current_step=SignupStep.EMAIL
        )
        data_response = await conversational_auth_service.process_signup_step(data_request)
        assert data_response.next_step == SignupStep.USERNAME  # Progresses to next step
        print(f"✅ Data Response: {data_response.message[:100]}...\n")
        
        # Cleanup
        from app.db.repositories.signup_session_repository import signup_session_repository
        await signup_session_repository.delete_session(session_id)


@pytest.fixture
async def conversational_auth_service():
    """Provide an instance of ConversationalAuthService for testing."""
    from app.services.conversational_auth_service import ConversationalAuthService
    return ConversationalAuthService()
