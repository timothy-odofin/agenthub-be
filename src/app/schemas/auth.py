"""
Authentication request and response schemas.
"""

from pydantic import BaseModel, EmailStr, Field
from typing import Optional


class SignupRequest(BaseModel):
    """Request schema for user signup."""
    email: EmailStr = Field(..., description="User's email address")
    username: str = Field(..., min_length=3, max_length=30, description="Unique username")
    password: str = Field(..., min_length=8, max_length=72, description="User password")
    firstname: str = Field(..., min_length=1, max_length=50, description="User's first name")
    lastname: str = Field(..., min_length=1, max_length=50, description="User's last name")


class SignupResponse(BaseModel):
    """Response schema for user signup."""
    success: bool = Field(..., description="Whether signup was successful")
    message: str = Field(..., description="Response message")
    user_id: Optional[str] = Field(None, description="Created user ID if successful")
    access_token: Optional[str] = Field(None, description="JWT access token if successful")
    refresh_token: Optional[str] = Field(None, description="JWT refresh token if successful")
    token_type: str = Field(default="bearer", description="Token type")


class LoginRequest(BaseModel):
    """Request schema for user login."""
    identifier: str = Field(..., description="Email or username")
    password: str = Field(..., description="User password")


class LoginResponse(BaseModel):
    """Response schema for user login."""
    success: bool = Field(..., description="Whether login was successful")
    message: str = Field(..., description="Response message")
    access_token: Optional[str] = Field(None, description="JWT access token if successful")
    refresh_token: Optional[str] = Field(None, description="JWT refresh token if successful")
    token_type: str = Field(default="bearer", description="Token type")
    user: Optional[dict] = Field(None, description="User information if successful")


class RefreshTokenRequest(BaseModel):
    """Request schema for token refresh."""
    refresh_token: str = Field(..., description="Valid refresh token")


class RefreshTokenResponse(BaseModel):
    """Response schema for token refresh."""
    success: bool = Field(..., description="Whether refresh was successful")
    message: str = Field(..., description="Response message")
    access_token: Optional[str] = Field(None, description="New JWT access token if successful")
    token_type: str = Field(default="bearer", description="Token type")
