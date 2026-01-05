"""
FastAPI dependencies for JWT authentication.

Provides reusable dependencies for protecting endpoints with JWT authentication.
"""

from typing import Optional, Dict, Any
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from src.app.core.security.token_manager import token_manager
from src.app.db.repositories.user_repository import user_repository
from src.app.db.models.user import UserInDB


# HTTP Bearer token scheme
security = HTTPBearer(
    scheme_name="JWT",
    description="JWT authentication using Bearer token",
    auto_error=False,  # Don't auto-raise, we'll handle it ourselves
)


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> UserInDB:
    """
    FastAPI dependency to get the current authenticated user.
    
    Extracts and verifies JWT token from Authorization header,
    then retrieves the user from the database.
    
    Args:
        credentials: HTTP Bearer credentials from Authorization header
        
    Returns:
        UserInDB object for the authenticated user
        
    Raises:
        HTTPException: 401 if token is missing, invalid, or user not found
        
    Example:
        ```python
        @router.get("/protected")
        async def protected_route(user: UserInDB = Depends(get_current_user)):
            return {"user_id": user.id, "email": user.email}
        ```
    """
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Extract token
    token = credentials.credentials
    
    # Verify token
    payload = token_manager.verify_token(token)
    
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Extract user_id from payload
    user_id: str = payload.get("user_id")
    
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Get user from database
    user = await user_repository.get_user_by_id(user_id)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return user


async def get_current_user_optional(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> Optional[UserInDB]:
    """
    FastAPI dependency to optionally get the current authenticated user.
    
    Similar to get_current_user but returns None instead of raising
    an exception if authentication fails. Useful for endpoints that
    have different behavior for authenticated vs anonymous users.
    
    Args:
        credentials: HTTP Bearer credentials from Authorization header
        
    Returns:
        UserInDB object if authenticated, None otherwise
        
    Example:
        ```python
        @router.get("/public")
        async def public_route(user: Optional[UserInDB] = Depends(get_current_user_optional)):
            if user:
                return {"message": f"Hello {user.username}"}
            return {"message": "Hello guest"}
        ```
    """
    if not credentials:
        return None
    
    token = credentials.credentials
    payload = token_manager.verify_token(token)
    
    if not payload:
        return None
    
    user_id: str = payload.get("user_id")
    if not user_id:
        return None
    
    user = await user_repository.get_user_by_id(user_id)
    return user


async def get_token_payload(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> Dict[str, Any]:
    """
    FastAPI dependency to get JWT token payload without database lookup.
    
    Verifies the token and returns the payload. Lighter weight than
    get_current_user since it doesn't hit the database. Useful when
    you only need basic user info from the token.
    
    Args:
        credentials: HTTP Bearer credentials from Authorization header
        
    Returns:
        Dictionary containing token payload (user_id, email, username, etc.)
        
    Raises:
        HTTPException: 401 if token is missing or invalid
        
    Example:
        ```python
        @router.get("/quick-check")
        async def quick_check(payload: Dict = Depends(get_token_payload)):
            return {"user_id": payload["user_id"]}
        ```
    """
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    token = credentials.credentials
    payload = token_manager.verify_token(token)
    
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return payload


def require_auth(user: UserInDB = Depends(get_current_user)) -> UserInDB:
    """
    Alias for get_current_user for more explicit endpoint protection.
    
    Use this when you want to make it very clear that an endpoint
    requires authentication.
    
    Args:
        user: User from get_current_user dependency
        
    Returns:
        UserInDB object for the authenticated user
        
    Example:
        ```python
        @router.delete("/account")
        async def delete_account(user: UserInDB = Depends(require_auth)):
            # Only authenticated users can access this
            return {"message": "Account deleted"}
        ```
    """
    return user
