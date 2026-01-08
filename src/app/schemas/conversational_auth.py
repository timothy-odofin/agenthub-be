"""
Conversational authentication schemas for chatbot-style signup/login.
"""

from pydantic import BaseModel, Field
from typing import Optional, Literal
from enum import Enum


class SignupStep(str, Enum):
    """Enumeration of signup conversation steps."""
    START = "start"
    EMAIL = "email"
    USERNAME = "username"
    PASSWORD = "password"
    FIRSTNAME = "firstname"
    LASTNAME = "lastname"
    COMPLETE = "complete"


class ConversationalSignupRequest(BaseModel):
    """
    Request schema for conversational signup with Redis session management.
    
    Client sends 3 fields:
    1. message: User's input (required)
    2. session_id: Tracking ID (null for START, required for all other steps)
    3. current_step: Current step (null for START, required for all other steps)
    
    All validated data is stored server-side in Redis.
    This prevents password exposure and ensures data integrity.
    
    Flow:
    - First request: {"message": "", "session_id": null, "current_step": "start"}
    - Server returns: session_id in response (e.g., "abc-123")
    - Subsequent requests: {"message": "user input", "session_id": "abc-123", "current_step": "email"}
    """
    message: str = Field(..., description="User's message/input for current step", examples=["john@example.com"])
    session_id: Optional[str] = Field(None, description="Session ID from server response (null only for START step)", examples=["abc-123"])
    current_step: Optional[SignupStep] = Field(None, description="Current step (MUST match next_step from previous response, null only for START)", examples=["email"])
    
    # NOTE: Validated fields (email, username, password, etc.) are stored in Redis, 
    # NOT sent by client. This ensures security and prevents tampering.
    
    
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "description": "Step 1: START - Initialize signup (session_id is null)",
                    "message": "",
                    "current_step": "start",
                    "session_id": None
                },
                {
                    "description": "Step 2: EMAIL - Provide email (session_id from server response)",
                    "message": "john@example.com",
                    "current_step": "email",
                    "session_id": "abc-123-uuid-from-server"
                },
                {
                    "description": "Step 3: USERNAME - Provide username (same session_id)",
                    "message": "johndoe",
                    "current_step": "username",
                    "session_id": "abc-123-uuid-from-server"
                },
                {
                    "description": "Step 4: PASSWORD - Provide password (same session_id)",
                    "message": "SecurePass123",
                    "current_step": "password",
                    "session_id": "abc-123-uuid-from-server"
                },
                {
                    "description": "Step 5: FIRSTNAME - Provide first name (same session_id)",
                    "message": "John",
                    "current_step": "firstname",
                    "session_id": "abc-123-uuid-from-server"
                },
                {
                    "description": "Step 6: LASTNAME - Provide last name (same session_id)",
                    "message": "Doe",
                    "current_step": "lastname",
                    "session_id": "abc-123-uuid-from-server"
                }
            ]
        }
    }


class ConversationalSignupResponse(BaseModel):
    """Response schema for conversational signup."""
    success: bool = Field(..., description="Whether the current step was successful")
    message: str = Field(..., description="Bot's response message to user")
    next_step: SignupStep = Field(..., description="Next step in the signup process")
    session_id: str = Field(..., description="Session ID for tracking conversation")
    
    # Validation feedback
    is_valid: bool = Field(default=True, description="Whether current input is valid")
    validation_error: Optional[str] = Field(None, description="Validation error message if any")
    
    # Completed signup data (only populated when signup is complete)
    user_id: Optional[str] = Field(None, description="Created user ID if signup complete")
    access_token: Optional[str] = Field(None, description="JWT access token if signup complete")
    refresh_token: Optional[str] = Field(None, description="JWT refresh token if signup complete")
    token_type: str = Field(default="bearer", description="Token type")
    
    # Progress tracking
    progress_percentage: int = Field(..., description="Signup completion percentage (0-100)")
    fields_remaining: int = Field(..., description="Number of fields still needed")


class ConversationalLoginRequest(BaseModel):
    """Request schema for conversational login."""
    message: str = Field(..., description="User's message/input")
    session_id: Optional[str] = Field(None, description="Session ID to track conversation state")


class ConversationalLoginResponse(BaseModel):
    """Response schema for conversational login."""
    success: bool = Field(..., description="Whether login was successful")
    message: str = Field(..., description="Bot's response message to user")
    session_id: str = Field(..., description="Session ID for tracking conversation")
    
    # Login tokens (only populated when login is complete)
    access_token: Optional[str] = Field(None, description="JWT access token if login successful")
    refresh_token: Optional[str] = Field(None, description="JWT refresh token if login successful")
    token_type: str = Field(default="bearer", description="Token type")
    user: Optional[dict] = Field(None, description="User information if login successful")
    
    # State tracking
    awaiting_input: Literal["identifier", "password", "complete"] = Field(
        ..., 
        description="What input the bot is waiting for next"
    )
