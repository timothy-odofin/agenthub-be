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
    
    **IMPORTANT FOR SWAGGER TESTING:**
    - Each request MUST include `current_step` matching the `next_step` from previous response
    - Use the `session_id` from the first response in all subsequent requests
    
    **Complete Flow Example:**
    
    **Request 1 (Start):**
    ```json
    {
      "message": "",
      "current_step": "start"
    }
    ```
    Response: `next_step: "email"`, `session_id: "abc-123"`
    
    **Request 2 (Email):**
    ```json
    {
      "message": "john@example.com",
      "current_step": "email",
      "session_id": "abc-123"
    }
    ```
    Response: `next_step: "username"`
    
    **Request 3 (Username):**
    ```json
    {
      "message": "johndoe",
      "current_step": "username",
      "session_id": "abc-123",
      "email": "john@example.com"
    }
    ```
    Response: `next_step: "password"`
    
    **Request 4 (Password):**
    ```json
    {
      "message": "Password123",
      "current_step": "password",
      "session_id": "abc-123",
      "email": "john@example.com",
      "username": "johndoe"
    }
    ```
    Response: `next_step: "firstname"`
    
    **Request 5 (First Name):**
    ```json
    {
      "message": "John",
      "current_step": "firstname",
      "session_id": "abc-123",
      "email": "john@example.com",
      "username": "johndoe",
      "password": "Password123"
    }
    ```
    Response: `next_step: "lastname"`
    
    **Request 6 (Last Name - Final):**
    ```json
    {
      "message": "Doe",
      "current_step": "lastname",
      "session_id": "abc-123",
      "email": "john@example.com",
      "username": "johndoe",
      "password": "Password123",
      "firstname": "John"
    }
    ```
    Response: `next_step: "complete"`, includes `access_token` and `refresh_token`
    
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
