"""
JWT Token Manager for authentication.

This module provides a singleton TokenManager for JWT token operations including:
- Creating access tokens with user claims
- Verifying and decoding tokens
- Token expiration management
- Refresh token support (future)

Example:
    >>> from app.core.security.token_manager import token_manager
    >>> token = token_manager.create_access_token(
    ...     user_id="user123",
    ...     email="user@example.com"
    ... )
    >>> payload = token_manager.verify_token(token)
    >>> print(payload["user_id"])
"""

from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any
from jose import JWTError, jwt

from src.app.core.utils.logger import get_logger
from src.app.core.config import settings

logger = get_logger(__name__)


class TokenManager:
    """
    Singleton token manager for JWT operations.
    
    Provides centralized JWT token creation and verification
    following the same pattern as password_manager and user_repository.
    
    Usage:
        from app.core.security.token_manager import token_manager
        
        # Create token
        token = token_manager.create_access_token(
            user_id="123",
            email="user@example.com"
        )
        
        # Verify token
        payload = token_manager.verify_token(token)
        if payload:
            user_id = payload["user_id"]
    """
    
    _instance: Optional['TokenManager'] = None
    
    def __new__(cls) -> 'TokenManager':
        """Ensure only one instance of TokenManager exists."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self) -> None:
        """Initialize the token manager (only once due to singleton)."""
        if not hasattr(self, '_initialized'):
            # Load JWT configuration from settings
            try:
                self._secret_key = settings.get_value("security.jwt_secret_key", "your-secret-key-change-in-production")
                self._algorithm = settings.get_value("security.jwt_algorithm", "HS256")
                self._access_token_expire_minutes = int(settings.get_value("security.access_token_expire_minutes", 30))
            except Exception as e:
                logger.warning(f"Could not load JWT config from settings: {e}. Using defaults.")
                self._secret_key = "your-secret-key-change-in-production"
                self._algorithm = "HS256"
                self._access_token_expire_minutes = 30
            
            self._initialized = True
            logger.info(f"TokenManager initialized (algorithm: {self._algorithm}, expiry: {self._access_token_expire_minutes}min)")
    
    def create_access_token(
        self,
        user_id: str,
        email: str,
        username: Optional[str] = None,
        additional_claims: Optional[Dict[str, Any]] = None,
        expires_delta: Optional[timedelta] = None
    ) -> str:
        """
        Create a JWT access token.
        
        Args:
            user_id: User's unique identifier
            email: User's email address
            username: User's username (optional)
            additional_claims: Additional data to include in token (optional)
            expires_delta: Custom expiration time (optional, uses config default if not provided)
            
        Returns:
            str: Encoded JWT token
            
        Example:
            >>> token = token_manager.create_access_token(
            ...     user_id="user123",
            ...     email="john@example.com",
            ...     username="johndoe"
            ... )
        """
        try:
            # Prepare token payload
            to_encode = {
                "sub": user_id,  # Subject (standard JWT claim)
                "user_id": user_id,
                "email": email,
                "type": "access"
            }
            
            if username:
                to_encode["username"] = username
            
            # Add any additional claims
            if additional_claims:
                to_encode.update(additional_claims)
            
            # Set expiration
            if expires_delta:
                expire = datetime.now(timezone.utc) + expires_delta
            else:
                expire = datetime.now(timezone.utc) + timedelta(minutes=self._access_token_expire_minutes)
            
            to_encode["exp"] = expire
            to_encode["iat"] = datetime.now(timezone.utc)  # Issued at
            
            # Encode token
            encoded_jwt = jwt.encode(to_encode, self._secret_key, algorithm=self._algorithm)
            
            logger.debug(f"Created access token for user: {user_id}")
            return encoded_jwt
            
        except Exception as e:
            logger.error(f"Error creating access token: {e}", exc_info=True)
            raise
    
    def verify_token(self, token: str) -> Optional[Dict[str, Any]]:
        """
        Verify and decode a JWT token.
        
        Args:
            token: JWT token string to verify
            
        Returns:
            Dict containing token payload if valid, None if invalid or expired
            
        Example:
            >>> payload = token_manager.verify_token(token)
            >>> if payload:
            ...     user_id = payload["user_id"]
            ...     email = payload["email"]
        """
        try:
            payload = jwt.decode(
                token,
                self._secret_key,
                algorithms=[self._algorithm]
            )
            
            # Verify token type
            if payload.get("type") != "access":
                logger.warning("Invalid token type")
                return None
            
            logger.debug(f"Token verified for user: {payload.get('user_id')}")
            return payload
            
        except jwt.ExpiredSignatureError:
            logger.warning("Token has expired")
            return None
        except JWTError as e:
            logger.warning(f"Token verification failed: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error verifying token: {e}", exc_info=True)
            return None
    
    def decode_token_without_verification(self, token: str) -> Optional[Dict[str, Any]]:
        """
        Decode a token without verifying signature or expiration.
        
        Useful for debugging or getting user info from expired tokens.
        DO NOT use for authentication - use verify_token() instead.
        
        Args:
            token: JWT token string to decode
            
        Returns:
            Dict containing token payload, None if malformed
        """
        try:
            # Decode without verification - no key needed
            payload = jwt.get_unverified_claims(token)
            return payload
        except Exception as e:
            logger.warning(f"Could not decode token: {e}")
            return None
    
    def create_refresh_token(
        self,
        user_id: str,
        expires_delta: Optional[timedelta] = None
    ) -> str:
        """
        Create a JWT refresh token.
        
        Refresh tokens have longer expiration and can be used to obtain new access tokens.
        
        Args:
            user_id: User's unique identifier
            expires_delta: Custom expiration time (default: 7 days)
            
        Returns:
            str: Encoded JWT refresh token
            
        Example:
            >>> refresh_token = token_manager.create_refresh_token(user_id="user123")
        """
        try:
            to_encode = {
                "sub": user_id,
                "user_id": user_id,
                "type": "refresh"
            }
            
            # Refresh tokens expire in 7 days by default
            if expires_delta:
                expire = datetime.now(timezone.utc) + expires_delta
            else:
                expire = datetime.now(timezone.utc) + timedelta(days=7)
            
            to_encode["exp"] = expire
            to_encode["iat"] = datetime.now(timezone.utc)
            
            encoded_jwt = jwt.encode(to_encode, self._secret_key, algorithm=self._algorithm)
            
            logger.debug(f"Created refresh token for user: {user_id}")
            return encoded_jwt
            
        except Exception as e:
            logger.error(f"Error creating refresh token: {e}", exc_info=True)
            raise
    
    def verify_refresh_token(self, token: str) -> Optional[str]:
        """
        Verify a refresh token and return the user_id.
        
        Args:
            token: JWT refresh token string
            
        Returns:
            User ID if token is valid, None otherwise
        """
        try:
            payload = jwt.decode(
                token,
                self._secret_key,
                algorithms=[self._algorithm]
            )
            
            # Verify token type
            if payload.get("type") != "refresh":
                logger.warning("Invalid token type - expected refresh token")
                return None
            
            user_id = payload.get("user_id")
            logger.debug(f"Refresh token verified for user: {user_id}")
            return user_id
            
        except jwt.ExpiredSignatureError:
            logger.warning("Refresh token has expired")
            return None
        except JWTError as e:
            logger.warning(f"Refresh token verification failed: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error verifying refresh token: {e}", exc_info=True)
            return None
    
    def get_token_expiry(self, token: str) -> Optional[datetime]:
        """
        Get the expiration time of a token without full verification.
        
        Args:
            token: JWT token string
            
        Returns:
            Expiration datetime if available, None otherwise
        """
        payload = self.decode_token_without_verification(token)
        if payload and "exp" in payload:
            return datetime.fromtimestamp(payload["exp"], tz=timezone.utc)
        return None


# Singleton instance - following the same pattern as password_manager
token_manager = TokenManager()
