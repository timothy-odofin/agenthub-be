"""
Authentication service for handling user authentication operations.

This service encapsulates all authentication business logic including
signup, login, and token refresh operations.
"""

from typing import Dict, Any, Optional
from app.agent.workflows.signup_workflow import signup_workflow
from app.db.repositories.user_repository import user_repository
from app.core.security.password_handler import password_manager
from app.core.security.token_manager import token_manager
from app.core.utils.logger import get_logger

logger = get_logger(__name__)


class AuthService:
    """Service class for authentication operations."""
    
    def __init__(self):
        """Initialize the authentication service."""
        self.user_repository = user_repository
        self.password_manager = password_manager
        self.token_manager = token_manager
        logger.info("AuthService initialized")
    
    async def signup(
        self,
        email: str,
        username: str,
        password: str,
        firstname: str,
        lastname: str
    ) -> Dict[str, Any]:
        """
        Register a new user account.
        
        This method uses the LangGraph signup workflow to validate and create a new user.
        Validation includes:
        - Email format and uniqueness
        - Username format (3-30 chars) and uniqueness
        - Password strength (8-72 chars, complexity requirements)
        - Name length (1-50 chars)
        
        Args:
            email: User's email address
            username: Desired username
            password: User's password
            firstname: User's first name
            lastname: User's last name
            
        Returns:
            Dict containing:
                - success: bool indicating if signup was successful
                - message: str with result message
                - user_id: str with the new user's ID (if successful)
                - access_token: str JWT access token (if successful)
                - refresh_token: str JWT refresh token (if successful)
        """
        logger.info(f"Processing signup request for email: {email}")
        
        # Prepare workflow input
        workflow_input = {
            "email": email,
            "username": username,
            "password": password,
            "firstname": firstname,
            "lastname": lastname,
        }
        
        # Execute signup workflow
        result = await signup_workflow.ainvoke(workflow_input)
        
        # Check if signup was successful
        if result["success"]:
            logger.info(f"Signup successful for user: {username}")
            
            # Create tokens for the new user
            access_token = self.token_manager.create_access_token(
                user_id=result["user_id"],
                email=email,
                username=username,
                additional_claims={
                    "firstname": firstname,
                    "lastname": lastname,
                }
            )
            
            refresh_token = self.token_manager.create_refresh_token(
                user_id=result["user_id"]
            )
            
            return {
                "success": True,
                "message": result["message"],
                "user_id": result["user_id"],
                "access_token": access_token,
                "refresh_token": refresh_token,
            }
        else:
            logger.warning(f"Signup failed for email: {email} - {result['message']}")
            return {
                "success": False,
                "message": result["message"],
            }
    
    async def login(
        self,
        identifier: str,
        password: str
    ) -> Dict[str, Any]:
        """
        Authenticate a user and return JWT tokens.
        
        Users can log in with either their email or username along with their password.
        
        Args:
            identifier: User's email or username
            password: User's password
            
        Returns:
            Dict containing:
                - success: bool indicating if login was successful
                - message: str with result message
                - access_token: str JWT access token (if successful)
                - refresh_token: str JWT refresh token (if successful)
                - user: dict with user information (if successful)
        """
        logger.info(f"Processing login request for identifier: {identifier}")
        
        # Try to find user by email first
        user = await self.user_repository.get_user_by_email(identifier)
        
        # If not found by email, try username
        if not user:
            user = await self.user_repository.get_user_by_username(identifier)
        
        # If user not found
        if not user:
            logger.warning(f"Login failed: User not found for identifier: {identifier}")
            return {
                "success": False,
                "message": "Invalid credentials",
            }
        
        # Verify password
        is_valid = self.password_manager.verify_password(
            password,
            user.password_hash
        )
        
        if not is_valid:
            logger.warning(f"Login failed: Invalid password for user: {identifier}")
            return {
                "success": False,
                "message": "Invalid credentials",
            }
        
        logger.info(f"Login successful for user: {user.username}")
        
        # Create tokens
        access_token = self.token_manager.create_access_token(
            user_id=str(user.id),
            email=user.email,
            username=user.username,
            additional_claims={
                "firstname": user.firstname,
                "lastname": user.lastname,
            }
        )
        
        refresh_token = self.token_manager.create_refresh_token(
            user_id=str(user.id)
        )
        
        # Prepare user info (exclude sensitive data)
        user_info = {
            "user_id": str(user.id),
            "email": user.email,
            "username": user.username,
            "firstname": user.firstname,
            "lastname": user.lastname,
            "created_at": user.created_at.isoformat() if user.created_at else None,
        }
        
        return {
            "success": True,
            "message": "Login successful",
            "access_token": access_token,
            "refresh_token": refresh_token,
            "user": user_info,
        }
    
    async def refresh_token(
        self,
        refresh_token: str
    ) -> Dict[str, Any]:
        """
        Refresh an access token using a valid refresh token.
        
        This method allows clients to obtain a new access token without re-authenticating.
        The refresh token must be valid and not expired.
        
        Args:
            refresh_token: The refresh token to verify
            
        Returns:
            Dict containing:
                - success: bool indicating if refresh was successful
                - message: str with result message
                - access_token: str JWT access token (if successful)
        """
        logger.info("Processing token refresh request")
        
        # Verify refresh token
        user_id = self.token_manager.verify_refresh_token(refresh_token)
        
        if not user_id:
            logger.warning("Token refresh failed: Invalid or expired refresh token")
            return {
                "success": False,
                "message": "Invalid or expired refresh token",
            }
        
        # Get user details
        user = await self.user_repository.get_user_by_id(user_id)
        
        if not user:
            logger.warning(f"Token refresh failed: User not found for ID: {user_id}")
            return {
                "success": False,
                "message": "User not found",
            }
        
        logger.info(f"Token refresh successful for user: {user.username}")
        
        # Create new access token
        access_token = self.token_manager.create_access_token(
            user_id=str(user.id),
            email=user.email,
            username=user.username,
            additional_claims={
                "firstname": user.firstname,
                "lastname": user.lastname,
            }
        )
        
        return {
            "success": True,
            "message": "Token refreshed successfully",
            "access_token": access_token,
        }


# Create singleton instance
auth_service = AuthService()
