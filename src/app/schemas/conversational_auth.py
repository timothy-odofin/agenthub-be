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
    """Request schema for conversational signup."""
    message: str = Field(..., description="User's message/input for current step")
    session_id: Optional[str] = Field(None, description="Session ID to track conversation state")
    current_step: Optional[SignupStep] = Field(None, description="Current step in signup process")
    
    # Accumulated data (sent back from frontend to maintain state)
    email: Optional[str] = Field(None, description="Email collected so far")
    username: Optional[str] = Field(None, description="Username collected so far")
    password: Optional[str] = Field(None, description="Password collected so far")
    firstname: Optional[str] = Field(None, description="First name collected so far")
    lastname: Optional[str] = Field(None, description="Last name collected so far")


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
