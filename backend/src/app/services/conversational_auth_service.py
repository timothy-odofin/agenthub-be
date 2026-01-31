"""
Conversational authentication service for chatbot-style signup/login flows with Redis session storage.
"""

import uuid
import re
from typing import Dict, Optional, Tuple, Callable, Awaitable
from app.schemas.conversational_auth import (
    SignupStep,
    ConversationalSignupRequest,
    ConversationalSignupResponse,
)
from app.services.auth_service import auth_service
from app.db.repositories.user_repository import user_repository
from app.db.repositories.signup_session_repository import signup_session_repository
from app.core.config import settings
from app.llm.factory import LLMFactory
from app.core.constants import LLMProvider
from app.core.security.password_handler import PasswordManager
import logging

logger = logging.getLogger(__name__)


class ConversationalAuthService:
    """Service for handling conversational authentication flows with Redis session management."""
    
    def __init__(self):
        """Initialize with prompts from configuration, LLM instance, and Redis repository."""
        # Load prompts from workflows/application-signup.yaml (not application-prompt.yaml)
        self.prompts = settings.workflows.signup.conversational_auth.prompts
        self.extraction_config = settings.workflows.signup.conversational_auth.extraction.universal
        self.intent_config = settings.workflows.signup.conversational_auth.intent_classification
        self.clarifications = settings.workflows.signup.conversational_auth.clarifications
        self.validation_errors = settings.workflows.signup.conversational_auth.validation_errors
        
        # Get LLM instance from factory (same as chat_service pattern)
        self.llm = LLMFactory.get_llm(LLMProvider.OPENAI)
        
        # Password manager for hashing
        self.password_manager = PasswordManager()
        
        # Registry Design Pattern: Map SignupStep enum to handler functions
        self._step_handlers: Dict[SignupStep, Callable[[ConversationalSignupRequest, str], Awaitable[ConversationalSignupResponse]]] = {
            SignupStep.EMAIL: self._process_email,
            SignupStep.USERNAME: self._process_username,
            SignupStep.PASSWORD: self._process_password,
            SignupStep.FIRSTNAME: self._process_firstname,
            SignupStep.LASTNAME: self._process_lastname,
        }
        
        logger.info("ConversationalAuthService initialized with Redis session storage")
    
    # Validation patterns
    EMAIL_PATTERN = re.compile(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$")
    USERNAME_PATTERN = re.compile(r"^[a-zA-Z0-9_-]{3,30}$")
    # Simplified password: min 8 chars, at least 1 uppercase, 1 lowercase, 1 number
    PASSWORD_PATTERN = re.compile(r"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d).{8,72}$")
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
            
            # Combine prompts for LLM
            full_prompt = f"{system_prompt}\n\n{user_prompt}"
            
            # Ensure LLM is initialized before using it
            await self.llm._ensure_initialized()
            
            # Call LLM for extraction using the generate method
            response = await self.llm.generate(full_prompt)
            
            # Extract and clean the value
            extracted = response.content.strip()
            
            # Remove any quotes that LLM might have added
            if extracted.startswith('"') and extracted.endswith('"'):
                extracted = extracted[1:-1]
            if extracted.startswith("'") and extracted.endswith("'"):
                extracted = extracted[1:-1]
            
            logger.info(f"LLM Extraction - Field: {field_type}, Input: '{message}', Extracted: '{extracted}'")
            return extracted
            
        except Exception as e:
            logger.error(f"Error extracting {field_type}: {e}")
            # Fallback: return original message if extraction fails
            return message.strip()
    
    async def _classify_intent(
        self,
        message: str,
        field_type: str
    ) -> str:
        """
        Classify user's intent: PROVIDES_DATA, ASKS_CLARIFICATION, or CONFUSED.
        
        Args:
            message: User's natural language input
            field_type: Expected field type (e.g., "email address")
            
        Returns:
            One of: "PROVIDES_DATA", "ASKS_CLARIFICATION", "CONFUSED"
        """
        try:
            # Build prompt from configuration (field intent classification)
            system_prompt = self.intent_config.field.system
            user_prompt = self.intent_config.field.user_template.format(
                field_type=field_type,
                user_message=message
            )
            
            # Combine prompts for LLM
            full_prompt = f"{system_prompt}\n\n{user_prompt}"
            
            # Ensure LLM is initialized
            await self.llm._ensure_initialized()
            
            # Call LLM for intent classification
            response = await self.llm.generate(full_prompt)
            intent = response.content.strip().upper()
            
            # Validate intent
            valid_intents = ["PROVIDES_DATA", "ASKS_CLARIFICATION", "CONFUSED"]
            if intent not in valid_intents:
                logger.warning(f"Invalid intent returned: {intent}, defaulting to PROVIDES_DATA")
                return "PROVIDES_DATA"
            
            logger.info(f"Intent Classification - Field: {field_type}, Input: '{message}', Intent: {intent}")
            return intent
            
        except Exception as e:
            logger.error(f"Error classifying intent: {e}")
            # Fallback: assume user is providing data
            return "PROVIDES_DATA"
    
    async def _classify_start_intent(
        self,
        message: str
    ) -> str:
        """
        Classify user's intent at START: ASKS_INFO, READY_TO_PROCEED, or PROVIDES_EMAIL.
        
        Args:
            message: User's natural language input
            
        Returns:
            One of: "ASKS_INFO", "READY_TO_PROCEED", "PROVIDES_EMAIL"
        """
        try:
            # Build prompt from configuration (start intent classification)
            system_prompt = self.intent_config.start.system
            user_prompt = self.intent_config.start.user_template.format(
                user_message=message
            )
            
            # Combine prompts for LLM
            full_prompt = f"{system_prompt}\n\n{user_prompt}"
            
            # Ensure LLM is initialized
            await self.llm._ensure_initialized()
            
            # Call LLM for intent classification
            response = await self.llm.generate(full_prompt)
            intent = response.content.strip().upper()
            
            # Validate intent
            valid_intents = ["ASKS_INFO", "READY_TO_PROCEED", "PROVIDES_EMAIL"]
            if intent not in valid_intents:
                logger.warning(f"Invalid START intent returned: {intent}, defaulting to ASKS_INFO")
                return "ASKS_INFO"
            
            logger.info(f"START Intent Classification - Input: '{message}', Intent: {intent}")
            return intent
            
        except Exception as e:
            logger.error(f"Error classifying START intent: {e}")
            # Fallback: assume user is asking for info
            return "ASKS_INFO"
    
    async def _generate_intelligent_clarification(
        self,
        message: str,
        field_type: str
    ) -> str:
        """
        Use LLM to answer user's specific question about a field, then ask for the field.
        
        This makes the conversation feel natural - answering "What do you mean by email address?"
        with a specific answer rather than generic instructions.
        
        Args:
            message: User's question (e.g., "What do you mean by email address?")
            field_type: The field being asked for (e.g., "email address")
            
        Returns:
            Personalized clarification that answers their question
            
        Examples:
            >>> await _generate_intelligent_clarification("What do you mean by email address?", "email address")
            "An email address is your digital contact - like john@gmail.com. We'll use it to log you in and send important notifications. What's your email address?"
        """
        try:
            # Get clarification prompt from configuration (workflows/application-signup.yaml)
            clarification_config = settings.workflows.signup.conversational_auth.field_clarification
            system_prompt = clarification_config.system.format(field_type=field_type)
            user_prompt = clarification_config.user_template.format(
                field_type=field_type,
                user_message=message
            )
            
            # Combine prompts
            full_prompt = f"{system_prompt}\n\n{user_prompt}"
            
            # Ensure LLM is initialized
            await self.llm._ensure_initialized()
            
            # Call LLM for intelligent clarification
            response = await self.llm.generate(full_prompt)
            clarification = response.content.strip()
            
            logger.info(f"Intelligent Clarification - Field: {field_type}, Question: '{message}', Response length: {len(clarification)}")
            return clarification
            
        except Exception as e:
            logger.error(f"Error generating intelligent clarification: {e}")
            # Fallback to simple clarification
            return getattr(self.clarifications, field_type.replace(" ", ""), 
                          f"Could you please provide your {field_type}?")
    
    async def _generate_start_clarification(
        self,
        message: str
    ) -> str:
        """
        Use LLM to answer user's question about the signup process naturally.
        
        This provides a conversational, context-aware response instead of a robotic
        "I'm your signup assistant" message.
        
        Args:
            message: User's question (e.g., "What do I need to create an account?")
            
        Returns:
            Natural, conversational answer to their question
            
        Examples:
            >>> await _generate_start_clarification("What do I need to create an account?")
            "To create an account, you'll need 5 things: your email, a username, a password, and your first and last name. The whole process takes less than a minute. Ready to get started?"
        """
        try:
            # Get START clarification prompt from configuration (workflows/application-signup.yaml)
            clarification_config = settings.workflows.signup.conversational_auth.start_clarification
            system_prompt = clarification_config.system
            user_prompt = clarification_config.user_template.format(
                user_message=message
            )
            
            # Combine prompts
            full_prompt = f"{system_prompt}\n\n{user_prompt}"
            
            # Ensure LLM is initialized
            await self.llm._ensure_initialized()
            
            # Call LLM for intelligent START clarification
            response = await self.llm.generate(full_prompt)
            clarification = response.content.strip()
            
            logger.info(f"START Clarification - Question: '{message}', Response length: {len(clarification)}")
            return clarification
            
        except Exception as e:
            logger.error(f"Error generating START clarification: {e}")
            # Fallback to greeting explanation
            return self.prompts.greeting_explanation


    
    async def process_signup_step(
        self, request: ConversationalSignupRequest
    ) -> ConversationalSignupResponse:
        """
        Process a single step in the conversational signup flow with Redis session management.
        
        Uses registry design pattern to dispatch to appropriate handler based on step.
        
        Args:
            request: Conversational signup request with user input
            
        Returns:
            ConversationalSignupResponse with bot message and next step
        """
        # Generate or use existing session ID
        session_id = request.session_id or str(uuid.uuid4())
        
        # Determine current step
        current_step = request.current_step or SignupStep.START
        
        # If START, handle conversationally based on user's message
        if current_step == SignupStep.START:
            # If message is empty or just whitespace, show default start message
            if not request.message or request.message.strip() == "":
                # Initialize Redis session
                await signup_session_repository.create_session(
                    session_id,
                    {"current_step": SignupStep.EMAIL.value}
                )
                
                return ConversationalSignupResponse(
                    success=True,
                    message=self.prompts.start,
                    next_step=SignupStep.EMAIL,
                    session_id=session_id,
                    is_valid=True,
                    progress_percentage=0,
                    fields_remaining=5,
                )
            
            # User sent a message - classify their intent
            intent = await self._classify_start_intent(request.message)
            
            if intent == "ASKS_INFO":
                # User is asking about the signup process
                # Generate intelligent, contextual response to their specific question
                clarification = await self._generate_start_clarification(request.message)
                
                # Don't create session yet, stay on START
                return ConversationalSignupResponse(
                    success=True,
                    message=clarification,
                    next_step=SignupStep.START,  # Stay on START
                    session_id=session_id,
                    is_valid=True,
                    progress_percentage=0,
                    fields_remaining=5,
                )
            
            elif intent == "READY_TO_PROCEED":
                # User is ready to start (said yes, sure, let's go, etc.)
                # Create Redis session and move to EMAIL
                await signup_session_repository.create_session(
                    session_id,
                    {"current_step": SignupStep.EMAIL.value}
                )
                
                return ConversationalSignupResponse(
                    success=True,
                    message=self.prompts.proceed_to_signup,
                    next_step=SignupStep.EMAIL,
                    session_id=session_id,
                    is_valid=True,
                    progress_percentage=0,
                    fields_remaining=5,
                )
            
            elif intent == "PROVIDES_EMAIL":
                # User directly provided email - extract and process it
                # This will be handled by _process_email
                current_step = SignupStep.EMAIL
                # Create session before processing email
                await signup_session_repository.create_session(
                    session_id,
                    {"current_step": SignupStep.EMAIL.value}
                )
                # Fall through to handler below
        
        # Use registry pattern to get handler function
        handler = self._step_handlers.get(current_step)
        
        if handler:
            return await handler(request, session_id)
        
        # Should not reach here - invalid step
        logger.error(f"Invalid signup step: {current_step}")
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
        """Process email input step with intent classification, LLM extraction, and Redis storage."""
        # Step 1: Classify user intent
        intent = await self._classify_intent(request.message, "email address")
        
        # If user is asking for clarification, use intelligent LLM response
        if intent == "ASKS_CLARIFICATION":
            # Generate personalized answer to their specific question
            clarification = await self._generate_intelligent_clarification(
                request.message,
                "email address"
            )
            
            return ConversationalSignupResponse(
                success=True,
                message=clarification,
                next_step=SignupStep.EMAIL,
                session_id=session_id,
                is_valid=True,
                progress_percentage=0,
                fields_remaining=5,
            )
        
        # If user seems confused, provide clarification too
        if intent == "CONFUSED":
            return ConversationalSignupResponse(
                success=False,
                message=self.validation_errors.extraction_failed.format(field_type="email address"),
                next_step=SignupStep.EMAIL,
                session_id=session_id,
                is_valid=False,
                validation_error="Could not understand input",
                progress_percentage=0,
                fields_remaining=5,
            )
        
        # Step 2: Extract email from natural language using LLM
        extracted_email = await self._extract_field_from_message(
            request.message, 
            field_type="email address"
        )
        
        logger.info(f"Email validation - Extracted: '{extracted_email}', Pattern match: {bool(self.EMAIL_PATTERN.match(extracted_email))}")
        
        # Step 3: Validate email format
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
        
        # Step 4: Check if email already exists
        existing_user = await user_repository.get_user_by_email(extracted_email)
        if existing_user:
            logger.info(f"Email already exists: {extracted_email}")
            return ConversationalSignupResponse(
                success=False,
                message=self.validation_errors.email_exists,
                next_step=SignupStep.EMAIL,
                session_id=session_id,
                is_valid=False,
                validation_error="Email already registered",
                progress_percentage=0,
                fields_remaining=5,
            )
        
        # Step 5: Store validated email in Redis
        await signup_session_repository.update_field(session_id, "email", extracted_email)
        await signup_session_repository.update_field(session_id, "current_step", SignupStep.USERNAME.value)
        logger.info(f"Email stored in Redis session: {session_id}")
        
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
        """Process username input step with intent classification, LLM extraction, and Redis storage."""
        # Step 1: Classify user intent
        intent = await self._classify_intent(request.message, "username")
        
        # If user is asking for clarification, use intelligent LLM response
        if intent == "ASKS_CLARIFICATION":
            clarification = await self._generate_intelligent_clarification(
                request.message,
                "username"
            )
            
            return ConversationalSignupResponse(
                success=True,
                message=clarification,
                next_step=SignupStep.USERNAME,
                session_id=session_id,
                is_valid=True,
                progress_percentage=20,
                fields_remaining=4,
            )
        
        # If user seems confused, provide clarification too
        if intent == "CONFUSED":
            return ConversationalSignupResponse(
                success=False,
                message=self.validation_errors.extraction_failed.format(field_type="username"),
                next_step=SignupStep.USERNAME,
                session_id=session_id,
                is_valid=False,
                validation_error="Could not understand input",
                progress_percentage=20,
                fields_remaining=4,
            )
        
        # Step 2: Extract username from natural language using LLM
        extracted_username = await self._extract_field_from_message(
            request.message, 
            field_type="username"
        )
        
        # Step 3: Validate username format
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
        
        # Step 4: Check if username already exists
        existing_user = await user_repository.get_user_by_username(extracted_username)
        if existing_user:
            logger.info(f"Username already exists: {extracted_username}")
            return ConversationalSignupResponse(
                success=False,
                message=self.validation_errors.username_exists,
                next_step=SignupStep.USERNAME,
                session_id=session_id,
                is_valid=False,
                validation_error="Username already taken",
                progress_percentage=20,
                fields_remaining=4,
            )
        
        # Step 5: Store validated username in Redis
        await signup_session_repository.update_field(session_id, "username", extracted_username)
        await signup_session_repository.update_field(session_id, "current_step", SignupStep.PASSWORD.value)
        logger.info(f"Username stored in Redis session: {session_id}")
        
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
        """Process password input step with intent classification, LLM extraction, hashing, and Redis storage."""
        # Step 1: Classify user intent
        intent = await self._classify_intent(request.message, "password")
        
        # If user is asking for clarification, use intelligent LLM response
        if intent == "ASKS_CLARIFICATION":
            clarification = await self._generate_intelligent_clarification(
                request.message,
                "password"
            )
            
            return ConversationalSignupResponse(
                success=True,
                message=clarification,
                next_step=SignupStep.PASSWORD,
                session_id=session_id,
                is_valid=True,
                progress_percentage=40,
                fields_remaining=3,
            )
        
        # If user seems confused, provide clarification too
        if intent == "CONFUSED":
            return ConversationalSignupResponse(
                success=False,
                message=self.validation_errors.extraction_failed.format(field_type="password"),
                next_step=SignupStep.PASSWORD,
                session_id=session_id,
                is_valid=False,
                validation_error="Could not understand input",
                progress_percentage=40,
                fields_remaining=3,
            )
        
        # Step 2: Extract password from natural language using LLM
        extracted_password = await self._extract_field_from_message(
            request.message, 
            field_type="password"
        )
        
        # Step 3: Validate password strength (simplified: min 8 chars, 1 uppercase, 1 lowercase, 1 number)
        if not self.PASSWORD_PATTERN.match(extracted_password):
            feedback = []
            if len(extracted_password) < 8:
                feedback.append("at least 8 characters")
            if not re.search(r"[a-z]", extracted_password):
                feedback.append("one lowercase letter")
            if not re.search(r"[A-Z]", extracted_password):
                feedback.append("one uppercase letter")
            if not re.search(r"\d", extracted_password):
                feedback.append("one number")
            
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
        
        # Step 4: Hash password immediately (CRITICAL SECURITY)
        hashed_password = self.password_manager.hash_password(extracted_password)
        
        # Step 5: Store hashed password in Redis (never store plaintext)
        await signup_session_repository.update_field(session_id, "password_hash", hashed_password)
        await signup_session_repository.update_field(session_id, "current_step", SignupStep.FIRSTNAME.value)
        logger.info(f"Password hashed and stored in Redis session: {session_id}")
        
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
        """Process first name input step with intent classification, LLM extraction, and Redis storage."""
        # Step 1: Classify user intent
        intent = await self._classify_intent(request.message, "first name")
        
        # If user is asking for clarification, use intelligent LLM response
        if intent == "ASKS_CLARIFICATION":
            clarification = await self._generate_intelligent_clarification(
                request.message,
                "first name"
            )
            
            return ConversationalSignupResponse(
                success=True,
                message=clarification,
                next_step=SignupStep.FIRSTNAME,
                session_id=session_id,
                is_valid=True,
                progress_percentage=60,
                fields_remaining=2,
            )
        
        # If user seems confused, provide clarification too
        if intent == "CONFUSED":
            return ConversationalSignupResponse(
                success=False,
                message=self.validation_errors.extraction_failed.format(field_type="first name"),
                next_step=SignupStep.FIRSTNAME,
                session_id=session_id,
                is_valid=False,
                validation_error="Could not understand input",
                progress_percentage=60,
                fields_remaining=2,
            )
        
        # Step 2: Extract first name from natural language using LLM
        extracted_firstname = await self._extract_field_from_message(
            request.message, 
            field_type="first name"
        )
        
        # Step 3: Validate name format
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
        
        # Step 4: Store validated first name in Redis
        await signup_session_repository.update_field(session_id, "firstname", extracted_firstname)
        await signup_session_repository.update_field(session_id, "current_step", SignupStep.LASTNAME.value)
        logger.info(f"First name stored in Redis session: {session_id}")
        
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
        """Process last name, retrieve all data from Redis, create MongoDB user, and cleanup session."""
        # Step 1: Classify user intent
        intent = await self._classify_intent(request.message, "last name")
        
        # If user is asking for clarification, use intelligent LLM response
        if intent == "ASKS_CLARIFICATION":
            clarification = await self._generate_intelligent_clarification(
                request.message,
                "last name"
            )
            
            return ConversationalSignupResponse(
                success=True,
                message=clarification,
                next_step=SignupStep.LASTNAME,
                session_id=session_id,
                is_valid=True,
                progress_percentage=80,
                fields_remaining=1,
            )
        
        # If user seems confused, provide clarification too
        if intent == "CONFUSED":
            return ConversationalSignupResponse(
                success=False,
                message=self.validation_errors.extraction_failed.format(field_type="last name"),
                next_step=SignupStep.LASTNAME,
                session_id=session_id,
                is_valid=False,
                validation_error="Could not understand input",
                progress_percentage=80,
                fields_remaining=1,
            )
        
        # Step 2: Extract last name from natural language using LLM
        extracted_lastname = await self._extract_field_from_message(
            request.message, 
            field_type="last name"
        )
        
        # Step 3: Validate name format
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
        
        # Step 4: Retrieve all data from Redis session
        session_data = await signup_session_repository.get_session(session_id)
        
        if not session_data:
            logger.error(f"Session not found: {session_id}")
            return ConversationalSignupResponse(
                success=False,
                message=self.validation_errors.session_not_found,
                next_step=SignupStep.START,
                session_id=session_id,
                is_valid=False,
                validation_error="Session expired or not found",
                progress_percentage=0,
                fields_remaining=5,
            )
        
        # Step 5: Create user in MongoDB with all collected data
        try:
            signup_result = await auth_service.signup(
                email=session_data.get("email"),
                username=session_data.get("username"),
                password=session_data.get("password_hash"),  # Already hashed
                firstname=session_data.get("firstname"),
                lastname=extracted_lastname,
            )
            
            # Step 6: Delete Redis session (cleanup)
            await signup_session_repository.delete_session(session_id)
            logger.info(f"Signup complete, Redis session deleted: {session_id}")
            
            # Format completion message with user's first name
            completion_message = self.prompts.complete.format(firstname=session_data.get("firstname"))
            
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
            # Don't delete session on error - allow retry
            return ConversationalSignupResponse(
                success=False,
                message=error_message,
                next_step=SignupStep.LASTNAME,
                session_id=session_id,
                is_valid=False,
                validation_error=str(e),
                progress_percentage=80,
                fields_remaining=1,
            )


# Singleton instance
conversational_auth_service = ConversationalAuthService()
