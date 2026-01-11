"""
Test for natural, conversational START step responses.

This test validates that the system responds naturally to user questions
without robotic "I'm your AI assistant" introductions.
"""

import pytest
from app.schemas.conversational_auth import (
    SignupStep,
    ConversationalSignupRequest,
)


@pytest.mark.asyncio
class TestNaturalStartResponse:
    """Test suite for natural START step responses."""
    
    async def test_what_do_i_need_question(self, conversational_auth_service):
        """
        Test: User asks "What do I need in order to create an account?"
        
        Expected: Natural answer without "I'm your signup assistant" intro.
        """
        request = ConversationalSignupRequest(
            message="What do I need in other to create an account",
            session_id=None,
            current_step=SignupStep.START
        )
        
        response = await conversational_auth_service.process_signup_step(request)
        
        # Should stay on START (no progress)
        assert response.next_step == SignupStep.START
        assert response.success is True
        
        # Message should NOT contain robotic phrases
        message_lower = response.message.lower()
        
        # Should NOT say "I'm your signup assistant" or "I'm an AI"
        assert "i'm your signup assistant" not in message_lower
        assert "i'm an ai" not in message_lower
        assert "assistant" not in message_lower or "signup assistant" not in message_lower
        
        # Should contain helpful information about requirements
        assert any(word in message_lower for word in ["email", "username", "password", "name"])
        
        # Should end with asking if they want to proceed
        assert "?" in response.message  # Should ask a question
        
        print(f"\n✅ Natural Response to 'What do I need':\n{response.message}\n")
    
    async def test_how_does_it_work_question(self, conversational_auth_service):
        """
        Test: User asks "How does this work?"
        
        Expected: Natural explanation without robot talk.
        """
        request = ConversationalSignupRequest(
            message="How does this work?",
            session_id=None,
            current_step=SignupStep.START
        )
        
        response = await conversational_auth_service.process_signup_step(request)
        
        # Should stay on START
        assert response.next_step == SignupStep.START
        assert response.success is True
        
        # Should be natural and conversational
        message_lower = response.message.lower()
        
        # Should NOT be robotic
        assert "i'm your" not in message_lower or "assistant" not in message_lower
        
        # Should explain the process
        assert len(response.message) > 50  # Should be a substantial explanation
        
        print(f"\n✅ Natural Response to 'How does this work':\n{response.message}\n")
    
    async def test_what_information_needed(self, conversational_auth_service):
        """
        Test: User asks "What information do you need?"
        
        Expected: Direct list of requirements, natural tone.
        """
        request = ConversationalSignupRequest(
            message="What information do you need?",
            session_id=None,
            current_step=SignupStep.START
        )
        
        response = await conversational_auth_service.process_signup_step(request)
        
        # Should stay on START
        assert response.next_step == SignupStep.START
        assert response.success is True
        
        # Should list requirements
        message_lower = response.message.lower()
        
        # Check for key requirements mentioned
        requirements_mentioned = 0
        if "email" in message_lower:
            requirements_mentioned += 1
        if "username" in message_lower:
            requirements_mentioned += 1
        if "password" in message_lower:
            requirements_mentioned += 1
        if "name" in message_lower or "first" in message_lower or "last" in message_lower:
            requirements_mentioned += 1
        
        # Should mention at least 3 out of 5 requirements
        assert requirements_mentioned >= 3
        
        print(f"\n✅ Natural Response to 'What information do you need':\n{response.message}\n")
    
    async def test_comparison_robotic_vs_natural(self, conversational_auth_service):
        """
        Test: Compare responses to ensure they're natural, not robotic.
        
        This validates the improvement from:
        "👋 Hello! I'm your signup assistant..." (ROBOTIC ❌)
        to:
        "To create an account, you'll need..." (NATURAL ✅)
        """
        test_questions = [
            "What do I need in order to create an account?",
            "What information is required?",
            "What do you need from me?",
            "Tell me about the signup process"
        ]
        
        for question in test_questions:
            request = ConversationalSignupRequest(
                message=question,
                session_id=None,
                current_step=SignupStep.START
            )
            
            response = await conversational_auth_service.process_signup_step(request)
            
            # Validate natural response
            message_lower = response.message.lower()
            
            # Red flags for robotic language
            robotic_phrases = [
                "i'm your signup assistant",
                "i'm an ai",
                "i can help you create",
                "hello! i'm your"
            ]
            
            has_robotic_language = any(phrase in message_lower for phrase in robotic_phrases)
            
            if has_robotic_language:
                print(f"\n❌ ROBOTIC LANGUAGE DETECTED in response to: '{question}'")
                print(f"Response: {response.message}\n")
            else:
                print(f"\n✅ NATURAL response to: '{question}'")
                print(f"Response preview: {response.message[:150]}...\n")
            
            # Assert no robotic language
            assert not has_robotic_language, f"Response contains robotic language for question: '{question}'"


@pytest.fixture
async def conversational_auth_service():
    """Provide an instance of ConversationalAuthService for testing."""
    from app.services.conversational_auth_service import ConversationalAuthService
    return ConversationalAuthService()
