"""
Conversational authentication service for chatbot-style signup/login flows.
"""

import uuid
import re
from typing import Dict, Optional, Tuple
from app.schemas.conversational_auth import (
    SignupStep,
    ConversationalSignupRequest,
    ConversationalSignupResponse,
)
from app.services.auth_service import auth_service


class ConversationalAuthService:
    """Service for handling conversational authentication flows."""
    
    # Step-by-step prompts
    PROMPTS = {
        SignupStep.START: "👋 Welcome! Let's create your account. What's your email address?",
        SignupStep.EMAIL: "Great! Now choose a username (3-30 characters, letters, numbers, _ or -).",
        SignupStep.USERNAME: "Perfect! Create a strong password (min 8 characters, include uppercase, lowercase, number, and special character).",
        SignupStep.PASSWORD: "Excellent! What's your first name?",
        SignupStep.FIRSTNAME: "Almost there! What's your last name?",
        SignupStep.LASTNAME: "Processing your registration...",
        SignupStep.COMPLETE: "🎉 Welcome aboard! Your account has been created successfully!",
    }
    
    # Validation patterns
    EMAIL_PATTERN = re.compile(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$")
    USERNAME_PATTERN = re.compile(r"^[a-zA-Z0-9_-]{3,30}$")
    PASSWORD_PATTERN = re.compile(
        r"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{8,72}$"
    )
    NAME_PATTERN = re.compile(r"^[a-zA-Z\s'-]{1,50}$")
    
    async def process_signup_step(
        self, request: ConversationalSignupRequest
    ) -> ConversationalSignupResponse:
        """
        Process a single step in the conversational signup flow.
        
        Args:
            request: Conversational signup request with user input
            
        Returns:
            ConversationalSignupResponse with bot message and next step
        """
        # Generate or use existing session ID
        session_id = request.session_id or str(uuid.uuid4())
        
        # Determine current step
        current_step = request.current_step or SignupStep.START
        
        # If START, just return the first prompt
        if current_step == SignupStep.START:
            return ConversationalSignupResponse(
                success=True,
                message=self.PROMPTS[SignupStep.START],
                next_step=SignupStep.EMAIL,
                session_id=session_id,
                is_valid=True,
                progress_percentage=0,
                fields_remaining=5,
            )
        
        # Process based on current step
        if current_step == SignupStep.EMAIL:
            return await self._process_email(request, session_id)
        elif current_step == SignupStep.USERNAME:
            return await self._process_username(request, session_id)
        elif current_step == SignupStep.PASSWORD:
            return await self._process_password(request, session_id)
        elif current_step == SignupStep.FIRSTNAME:
            return await self._process_firstname(request, session_id)
        elif current_step == SignupStep.LASTNAME:
            return await self._process_lastname(request, session_id)
        
        # Should not reach here
        return ConversationalSignupResponse(
            success=False,
            message="❌ Something went wrong. Please start over.",
            next_step=SignupStep.START,
            session_id=session_id,
            is_valid=False,
            validation_error="Invalid step",
            progress_percentage=0,
            fields_remaining=5,
        )
    
    async def _process_email(
        self, request: ConversationalSignupRequest, session_id: str
    ) -> ConversationalSignupResponse:
        """Process email input step."""
        email = request.message.strip()
        
        # Validate email format
        if not self.EMAIL_PATTERN.match(email):
            return ConversationalSignupResponse(
                success=False,
                message="❌ Hmm, that doesn't look like a valid email. Please try again with a valid email address (e.g., john@example.com).",
                next_step=SignupStep.EMAIL,
                session_id=session_id,
                is_valid=False,
                validation_error="Invalid email format",
                progress_percentage=0,
                fields_remaining=5,
            )
        
        # TODO: Check if email already exists (optional for now)
        # You can add database check here later
        
        return ConversationalSignupResponse(
            success=True,
            message=self.PROMPTS[SignupStep.EMAIL],
            next_step=SignupStep.USERNAME,
            session_id=session_id,
            is_valid=True,
            progress_percentage=20,
            fields_remaining=4,
        )
    
    async def _process_username(
        self, request: ConversationalSignupRequest, session_id: str
    ) -> ConversationalSignupResponse:
        """Process username input step."""
        username = request.message.strip()
        
        # Validate username format
        if not self.USERNAME_PATTERN.match(username):
            return ConversationalSignupResponse(
                success=False,
                message="❌ Username must be 3-30 characters and can only contain letters, numbers, underscores, or hyphens. Please try again.",
                next_step=SignupStep.USERNAME,
                session_id=session_id,
                is_valid=False,
                validation_error="Invalid username format",
                progress_percentage=20,
                fields_remaining=4,
            )
        
        # TODO: Check if username already exists (optional for now)
        
        return ConversationalSignupResponse(
            success=True,
            message=self.PROMPTS[SignupStep.USERNAME],
            next_step=SignupStep.PASSWORD,
            session_id=session_id,
            is_valid=True,
            progress_percentage=40,
            fields_remaining=3,
        )
    
    async def _process_password(
        self, request: ConversationalSignupRequest, session_id: str
    ) -> ConversationalSignupResponse:
        """Process password input step."""
        password = request.message.strip()
        
        # Validate password strength
        if not self.PASSWORD_PATTERN.match(password):
            feedback = []
            if len(password) < 8:
                feedback.append("at least 8 characters")
            if not re.search(r"[a-z]", password):
                feedback.append("a lowercase letter")
            if not re.search(r"[A-Z]", password):
                feedback.append("an uppercase letter")
            if not re.search(r"\d", password):
                feedback.append("a number")
            if not re.search(r"[@$!%*?&]", password):
                feedback.append("a special character (@$!%*?&)")
            
            error_msg = f"❌ Password needs: {', '.join(feedback)}. Please try again with a stronger password."
            
            return ConversationalSignupResponse(
                success=False,
                message=error_msg,
                next_step=SignupStep.PASSWORD,
                session_id=session_id,
                is_valid=False,
                validation_error="Weak password",
                progress_percentage=40,
                fields_remaining=3,
            )
        
        return ConversationalSignupResponse(
            success=True,
            message=self.PROMPTS[SignupStep.PASSWORD],
            next_step=SignupStep.FIRSTNAME,
            session_id=session_id,
            is_valid=True,
            progress_percentage=60,
            fields_remaining=2,
        )
    
    async def _process_firstname(
        self, request: ConversationalSignupRequest, session_id: str
    ) -> ConversationalSignupResponse:
        """Process first name input step."""
        firstname = request.message.strip()
        
        # Validate name format
        if not self.NAME_PATTERN.match(firstname) or len(firstname) < 1:
            return ConversationalSignupResponse(
                success=False,
                message="❌ Please enter a valid first name (1-50 characters, letters only).",
                next_step=SignupStep.FIRSTNAME,
                session_id=session_id,
                is_valid=False,
                validation_error="Invalid first name",
                progress_percentage=60,
                fields_remaining=2,
            )
        
        return ConversationalSignupResponse(
            success=True,
            message=self.PROMPTS[SignupStep.FIRSTNAME],
            next_step=SignupStep.LASTNAME,
            session_id=session_id,
            is_valid=True,
            progress_percentage=80,
            fields_remaining=1,
        )
    
    async def _process_lastname(
        self, request: ConversationalSignupRequest, session_id: str
    ) -> ConversationalSignupResponse:
        """Process last name input step and complete signup."""
        lastname = request.message.strip()
        
        # Validate name format
        if not self.NAME_PATTERN.match(lastname) or len(lastname) < 1:
            return ConversationalSignupResponse(
                success=False,
                message="❌ Please enter a valid last name (1-50 characters, letters only).",
                next_step=SignupStep.LASTNAME,
                session_id=session_id,
                is_valid=False,
                validation_error="Invalid last name",
                progress_percentage=80,
                fields_remaining=1,
            )
        
        # All data collected, now create the account
        try:
            signup_result = await auth_service.signup(
                email=request.email,
                username=request.username,
                password=request.password,
                firstname=request.firstname,
                lastname=lastname,
            )
            
            return ConversationalSignupResponse(
                success=True,
                message=f"🎉 Welcome aboard, {request.firstname}! Your account has been created successfully. You can now start using AgentHub!",
                next_step=SignupStep.COMPLETE,
                session_id=session_id,
                is_valid=True,
                user_id=signup_result.get("user_id"),
                access_token=signup_result.get("access_token"),
                refresh_token=signup_result.get("refresh_token"),
                progress_percentage=100,
                fields_remaining=0,
            )
        except Exception as e:
            return ConversationalSignupResponse(
                success=False,
                message=f"❌ Oops! Something went wrong: {str(e)}. Please try again.",
                next_step=SignupStep.START,
                session_id=session_id,
                is_valid=False,
                validation_error=str(e),
                progress_percentage=80,
                fields_remaining=1,
            )


# Singleton instance
conversational_auth_service = ConversationalAuthService()
