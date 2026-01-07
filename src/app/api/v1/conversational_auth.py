"""
Conversational authentication endpoints for chatbot-style signup and login.
"""

from fastapi import APIRouter, status
from app.schemas.conversational_auth import (
    ConversationalSignupRequest,
    ConversationalSignupResponse,
)
from app.services.conversational_auth_service import conversational_auth_service

router = APIRouter()


@router.post(
    "/signup/conversation",
    response_model=ConversationalSignupResponse,
    status_code=status.HTTP_200_OK,
)
async def conversational_signup(
    request: ConversationalSignupRequest,
) -> ConversationalSignupResponse:
    """
    Conversational signup endpoint - handles step-by-step user registration via chatbot interface.
    
    This endpoint provides a conversational flow for user signup where:
    1. User sends a message (e.g., their email)
    2. Backend validates and responds with next question
    3. Process continues until all required fields are collected
    4. Account is created automatically when complete
    
    **Flow Steps:**
    - START: Initial greeting, ask for email
    - EMAIL: Validate email, ask for username
    - USERNAME: Validate username, ask for password
    - PASSWORD: Validate password strength, ask for first name
    - FIRSTNAME: Validate first name, ask for last name
    - LASTNAME: Validate last name, create account
    - COMPLETE: Return tokens and welcome message
    
    **Progress Tracking:**
    - `progress_percentage`: Shows completion (0-100%)
    - `fields_remaining`: Number of fields still needed
    - `next_step`: What the bot is asking for next
    
    **Frontend Integration:**
    ```javascript
    // Step 1: Start conversation
    POST /api/v1/auth/signup/conversation
    { "message": "", "current_step": "start" }
    
    // Step 2: User provides email
    POST /api/v1/auth/signup/conversation
    { 
      "message": "john@example.com",
      "session_id": "...",
      "current_step": "email"
    }
    
    // Continue until complete...
    ```
    
    Args:
        request: Conversational signup request with user input and conversation state
        
    Returns:
        ConversationalSignupResponse with bot message, validation feedback, and tokens if complete
    """
    result = await conversational_auth_service.process_signup_step(request)
    return result


@router.get(
    "/signup/conversation/start",
    response_model=ConversationalSignupResponse,
    status_code=status.HTTP_200_OK,
)
async def start_conversational_signup() -> ConversationalSignupResponse:
    """
    Start a new conversational signup flow.
    
    This is a convenience endpoint for initiating the signup conversation.
    It returns the initial greeting message and a new session ID.
    
    Returns:
        ConversationalSignupResponse with welcome message and session ID
    """
    result = await conversational_auth_service.process_signup_step(
        ConversationalSignupRequest(message="", current_step="start")
    )
    return result
