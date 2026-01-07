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
from app.core.config import settings
from app.llm.factory import get_llm
import logging

logger = logging.getLogger(__name__)


class ConversationalAuthService:
    """Service for handling conversational authentication flows."""
    
    def __init__(self):
        """Initialize with prompts from configuration and LLM instance."""
        # Load prompts from application-prompt.yaml
        self.prompts = settings.prompt.conversational_auth.prompts
        self.extraction_config = settings.prompt.conversational_auth.extraction.universal
        self.validation_errors = settings.prompt.conversational_auth.validation_errors
        
        # Get LLM instance from factory
        self.llm = get_llm()
        
        logger.info("ConversationalAuthService initialized with prompts from configuration")
    
    # Validation patterns
    EMAIL_PATTERN = re.compile(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$")
    USERNAME_PATTERN = re.compile(r"^[a-zA-Z0-9_-]{3,30}$")
    PASSWORD_PATTERN = re.compile(
        r"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{8,72}$"
    )
    NAME_PATTERN = re.compile(r"^[a-zA-Z\s'-]{1,50}$")
    
    async def _extract_field_from_message(
        self, 
        message: str, 
        field_type: str
    ) -> str:
        """
        Use LLM to extract field value from natural language message.
        
        This uses the universal extraction prompt from configuration,
        following the KISS and DRY principles.
        
        Args:
            message: User's natural language input
            field_type: Type of field to extract (e.g., "email address", "username")
            
        Returns:
            Extracted field value
            
        Examples:
            >>> await _extract_field_from_message("My email is john@example.com", "email address")
            "john@example.com"
            
            >>> await _extract_field_from_message("You can call me johndoe", "username")
            "johndoe"
        """
        try:
            # Build prompt from configuration
            system_prompt = self.extraction_config.system
            user_prompt = self.extraction_config.user_template.format(
                field_type=field_type,
                user_message=message
            )
            
            # Call LLM for extraction
            response = await self.llm.ainvoke([
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ])
            
            # Extract and clean the value
            extracted = response.content.strip()
            
            # Remove any quotes that LLM might have added
            if extracted.startswith('"') and extracted.endswith('"'):
                extracted = extracted[1:-1]
            if extracted.startswith("'") and extracted.endswith("'"):
                extracted = extracted[1:-1]
            
            logger.debug(f"Extracted {field_type}: '{extracted}' from message: '{message}'")
            return extracted
            
        except Exception as e:
            logger.error(f"Error extracting {field_type}: {e}")
            # Fallback: return original message if extraction fails
            return message.strip()

    
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
        
        # If START, just return the first prompt from config
        if current_step == SignupStep.START:
            return ConversationalSignupResponse(
                success=True,
                message=self.prompts.start,
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
        """Process email input step with LLM extraction."""
        # Step 1: Extract email from natural language using LLM
        extracted_email = await self._extract_field_from_message(
            request.message, 
            field_type="email address"
        )
        
        # Step 2: Validate email format
        if not self.EMAIL_PATTERN.match(extracted_email):
            return ConversationalSignupResponse(
                success=False,
                message=self.validation_errors.email_invalid,
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
            message=self.prompts.email_success,
            next_step=SignupStep.USERNAME,
            session_id=session_id,
            is_valid=True,
            progress_percentage=20,
            fields_remaining=4,
        )
    
    async def _process_username(
        self, request: ConversationalSignupRequest, session_id: str
    ) -> ConversationalSignupResponse:
        """Process username input step with LLM extraction."""
        # Step 1: Extract username from natural language using LLM
        extracted_username = await self._extract_field_from_message(
            request.message, 
            field_type="username"
        )
        
        # Step 2: Validate username format
        if not self.USERNAME_PATTERN.match(extracted_username):
            return ConversationalSignupResponse(
                success=False,
                message=self.validation_errors.username_invalid,
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
            message=self.prompts.username_success,
            next_step=SignupStep.PASSWORD,
            session_id=session_id,
            is_valid=True,
            progress_percentage=40,
            fields_remaining=3,
        )
    
    async def _process_password(
        self, request: ConversationalSignupRequest, session_id: str
    ) -> ConversationalSignupResponse:
        """Process password input step with LLM extraction."""
        # Step 1: Extract password from natural language using LLM
        extracted_password = await self._extract_field_from_message(
            request.message, 
            field_type="password"
        )
        
        # Step 2: Validate password strength
        if not self.PASSWORD_PATTERN.match(extracted_password):
            feedback = []
            if len(extracted_password) < 8:
                feedback.append("at least 8 characters")
            if not re.search(r"[a-z]", extracted_password):
                feedback.append("a lowercase letter")
            if not re.search(r"[A-Z]", extracted_password):
                feedback.append("an uppercase letter")
            if not re.search(r"\d", extracted_password):
                feedback.append("a number")
            if not re.search(r"[@$!%*?&]", extracted_password):
                feedback.append("a special character (@$!%*?&)")
            
            requirements = ", ".join(feedback)
            error_msg = self.validation_errors.password_weak.format(requirements=requirements)
            
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
            message=self.prompts.password_success,
            next_step=SignupStep.FIRSTNAME,
            session_id=session_id,
            is_valid=True,
            progress_percentage=60,
            fields_remaining=2,
        )
    
    async def _process_firstname(
        self, request: ConversationalSignupRequest, session_id: str
    ) -> ConversationalSignupResponse:
        """Process first name input step with LLM extraction."""
        # Step 1: Extract first name from natural language using LLM
        extracted_firstname = await self._extract_field_from_message(
            request.message, 
            field_type="first name"
        )
        
        # Step 2: Validate name format
        if not self.NAME_PATTERN.match(extracted_firstname) or len(extracted_firstname) < 1:
            return ConversationalSignupResponse(
                success=False,
                message=self.validation_errors.firstname_invalid,
                next_step=SignupStep.FIRSTNAME,
                session_id=session_id,
                is_valid=False,
                validation_error="Invalid first name",
                progress_percentage=60,
                fields_remaining=2,
            )
        
        return ConversationalSignupResponse(
            success=True,
            message=self.prompts.firstname_success,
            next_step=SignupStep.LASTNAME,
            session_id=session_id,
            is_valid=True,
            progress_percentage=80,
            fields_remaining=1,
        )
    
    async def _process_lastname(
        self, request: ConversationalSignupRequest, session_id: str
    ) -> ConversationalSignupResponse:
        """Process last name input step and complete signup with LLM extraction."""
        # Step 1: Extract last name from natural language using LLM
        extracted_lastname = await self._extract_field_from_message(
            request.message, 
            field_type="last name"
        )
        
        # Step 2: Validate name format
        if not self.NAME_PATTERN.match(extracted_lastname) or len(extracted_lastname) < 1:
            return ConversationalSignupResponse(
                success=False,
                message=self.validation_errors.lastname_invalid,
                next_step=SignupStep.LASTNAME,
                session_id=session_id,
                is_valid=False,
                validation_error="Invalid last name",
                progress_percentage=80,
                fields_remaining=1,
            )
        
        # Step 3: All data collected, now create the account
        try:
            signup_result = await auth_service.signup(
                email=request.email,
                username=request.username,
                password=request.password,
                firstname=request.firstname,
                lastname=extracted_lastname,
            )
            
            # Format completion message with user's first name
            completion_message = self.prompts.complete.format(firstname=request.firstname)
            
            return ConversationalSignupResponse(
                success=True,
                message=completion_message,
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
            logger.error(f"Signup error: {e}")
            error_message = self.validation_errors.signup_error.format(error=str(e))
            return ConversationalSignupResponse(
                success=False,
                message=error_message,
                next_step=SignupStep.START,
                session_id=session_id,
                is_valid=False,
                validation_error=str(e),
                progress_percentage=80,
                fields_remaining=1,
            )


# Singleton instance
conversational_auth_service = ConversationalAuthService()
