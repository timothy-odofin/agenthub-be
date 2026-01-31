"""
Authentication endpoints for user signup, login, and token management.
"""

from fastapi import APIRouter, status
from app.schemas.auth import (
    SignupRequest,
    SignupResponse,
    LoginRequest,
    LoginResponse,
    RefreshTokenRequest,
    RefreshTokenResponse,
)
from app.services.auth_service import auth_service

router = APIRouter()


@router.post("/signup", response_model=SignupResponse, status_code=status.HTTP_201_CREATED)
async def signup(request: SignupRequest) -> SignupResponse:
    """
    Register a new user account.
    
    This endpoint uses the LangGraph signup workflow to validate and create a new user.
    Validation includes:
    - Email format and uniqueness
    - Username format (3-30 chars) and uniqueness
    - Password strength (8-72 chars, complexity requirements)
    - Name length (1-50 chars)
    
    Args:
        request: Signup request containing user details
        
    Returns:
        SignupResponse with success status, message, and tokens if successful
    """
    result = await auth_service.signup(
        email=request.email,
        username=request.username,
        password=request.password,
        firstname=request.firstname,
        lastname=request.lastname,
    )
    
    return SignupResponse(**result)


@router.post("/login", response_model=LoginResponse, status_code=status.HTTP_200_OK)
async def login(request: LoginRequest) -> LoginResponse:
    """
    Authenticate a user and return JWT tokens.
    
    Users can log in with either their email or username along with their password.
    
    Args:
        request: Login request containing identifier (email/username) and password
        
    Returns:
        LoginResponse with success status, message, tokens, and user info if successful
    """
    result = await auth_service.login(
        identifier=request.identifier,
        password=request.password,
    )
    
    return LoginResponse(**result)


@router.post("/refresh", response_model=RefreshTokenResponse, status_code=status.HTTP_200_OK)
async def refresh_token(request: RefreshTokenRequest) -> RefreshTokenResponse:
    """
    Refresh an access token using a valid refresh token.
    
    This endpoint allows clients to obtain a new access token without re-authenticating.
    The refresh token must be valid and not expired.
    
    Args:
        request: Refresh token request containing the refresh token
        
    Returns:
        RefreshTokenResponse with new access token if successful
    """
    result = await auth_service.refresh_token(
        refresh_token=request.refresh_token,
    )
    
    return RefreshTokenResponse(**result)
