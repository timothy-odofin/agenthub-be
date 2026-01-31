"""
Security utilities for authentication and authorization.

This module provides password hashing, JWT token management,
and authentication dependencies for FastAPI.

Usage:
    from app.core.security import (
        password_manager,
        token_manager,
        get_current_user,
        get_current_user_optional,
        require_auth,
    )
    
    # Password operations
    hashed = password_manager.hash_password("MyP@ssw0rd!")
    is_valid = password_manager.verify_password("MyP@ssw0rd!", hashed)
    
    # Token operations
    token = token_manager.create_access_token(
        user_id="123",
        email="user@example.com"
    )
    payload = token_manager.verify_token(token)
    
    # Protect endpoints
    @router.get("/protected")
    async def protected(user = Depends(get_current_user)):
        return {"user_id": user.id}
    
    # Optional authentication
    @router.get("/optional")
    async def optional(user = Depends(get_current_user_optional)):
        if user:
            return {"user_id": user.id}
        return {"message": "Anonymous access"}
"""

from app.core.security.password_handler import (
    password_manager,
    PasswordManager,
)
from app.core.security.token_manager import (
    token_manager,
    TokenManager,
)
from app.core.security.dependencies import (
    get_current_user,
    get_current_user_optional,
    get_token_payload,
    require_auth,
)

__all__ = [
    "password_manager",
    "PasswordManager",
    "token_manager",
    "TokenManager",
    "get_current_user",
    "get_current_user_optional",
    "get_token_payload",
    "require_auth",
]
