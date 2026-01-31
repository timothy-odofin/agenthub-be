"""
Utility functions for extracting and managing user context information.

This module provides helper functions to extract user information from various sources
like JWT tokens, request headers, and other authentication mechanisms.
"""

from typing import Dict, Any, Optional
from app.core.utils.logger import get_logger

logger = get_logger(__name__)


def extract_user_from_token(token_payload: Dict[str, Any]) -> str:
    """
    Extract user identification from JWT token payload.
    
    This utility creates a human-readable user identifier from the token payload,
    useful for logging, "on behalf of" comments, and audit trails.
    
    Args:
        token_payload: Decoded JWT token payload containing user information.
                      Expected fields (all optional):
                      - firstname: User's first name
                      - lastname: User's last name
                      - email: User's email address
                      - username: User's username
                      - user_id: User's ID
                      - sub: Subject (user identifier)
        
    Returns:
        User identification string in one of these formats:
        - "FirstName LastName (email@example.com)" if name and email available
        - "FirstName LastName (@username)" if name and username available
        - "FirstName LastName" if only name available
        - "email@example.com" if only email available
        - "username" if only username available
        - "Unknown User" if no identifiable information
        
    Example:
        >>> from app.core.security.token_manager import token_manager
        >>> token = "eyJ..."
        >>> payload = token_manager.verify_token(token)
        >>> user_info = extract_user_from_token(payload)
        >>> # Returns: "John Doe (john.doe@company.com)"
        
    Example with minimal info:
        >>> payload = {"email": "user@example.com"}
        >>> extract_user_from_token(payload)
        'user@example.com'
        
    Example with full name:
        >>> payload = {"firstname": "Jane", "lastname": "Smith", "username": "jsmith"}
        >>> extract_user_from_token(payload)
        'Jane Smith (@jsmith)'
    """
    # Extract available fields
    firstname = token_payload.get('firstname', '').strip()
    lastname = token_payload.get('lastname', '').strip()
    email = token_payload.get('email', '').strip()
    username = token_payload.get('username', '').strip()
    
    # Build user identification string with priority:
    # 1. Full name with email/username
    # 2. Full name only
    # 3. Email
    # 4. Username
    # 5. Unknown
    
    if firstname and lastname:
        full_name = f"{firstname} {lastname}"
        if email:
            return f"{full_name} ({email})"
        elif username:
            return f"{full_name} (@{username})"
        else:
            return full_name
    elif email:
        return email
    elif username:
        return username
    elif firstname:
        # Just first name if that's all we have
        return firstname
    else:
        logger.warning("Could not extract user information from token payload")
        return "Unknown User"


def extract_user_display_name(token_payload: Dict[str, Any]) -> str:
    """
    Extract just the display name from token payload (without email/username suffix).
    
    Args:
        token_payload: Decoded JWT token payload
        
    Returns:
        Display name string
        
    Example:
        >>> payload = {"firstname": "John", "lastname": "Doe", "email": "john@example.com"}
        >>> extract_user_display_name(payload)
        'John Doe'
    """
    firstname = token_payload.get('firstname', '').strip()
    lastname = token_payload.get('lastname', '').strip()
    username = token_payload.get('username', '').strip()
    email = token_payload.get('email', '').strip()
    
    if firstname and lastname:
        return f"{firstname} {lastname}"
    elif firstname:
        return firstname
    elif username:
        return username
    elif email:
        # Use email prefix as name if that's all we have
        return email.split('@')[0] if '@' in email else email
    else:
        return "Unknown User"


def extract_user_email(token_payload: Dict[str, Any]) -> Optional[str]:
    """
    Extract email from token payload.
    
    Args:
        token_payload: Decoded JWT token payload
        
    Returns:
        Email address or None if not available
        
    Example:
        >>> payload = {"email": "user@example.com"}
        >>> extract_user_email(payload)
        'user@example.com'
    """
    return token_payload.get('email', '').strip() or None


def extract_user_id(token_payload: Dict[str, Any]) -> Optional[str]:
    """
    Extract user ID from token payload.
    
    Checks multiple possible fields: user_id, sub, id
    
    Args:
        token_payload: Decoded JWT token payload
        
    Returns:
        User ID or None if not available
        
    Example:
        >>> payload = {"user_id": "12345", "email": "user@example.com"}
        >>> extract_user_id(payload)
        '12345'
    """
    # Try different possible user ID fields
    user_id = token_payload.get('user_id') or token_payload.get('sub') or token_payload.get('id')
    return str(user_id).strip() if user_id else None


def format_on_behalf_of_context(token_payload: Dict[str, Any], additional_context: str = "") -> str:
    """
    Format a complete "on behalf of" context string from token payload.
    
    This is useful for creating comments or actions on behalf of another user.
    
    Args:
        token_payload: Decoded JWT token payload
        additional_context: Optional additional context to append
        
    Returns:
        Formatted context string
        
    Example:
        >>> payload = {"firstname": "John", "lastname": "Doe", "email": "john@company.com"}
        >>> format_on_behalf_of_context(payload, "via API")
        'John Doe (john@company.com) via API'
    """
    user_info = extract_user_from_token(token_payload)
    
    if additional_context:
        return f"{user_info} {additional_context}"
    return user_info


def create_audit_context(token_payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Create a comprehensive audit context dictionary from token payload.
    
    Useful for logging and audit trails.
    
    Args:
        token_payload: Decoded JWT token payload
        
    Returns:
        Dictionary with extracted user context
        
    Example:
        >>> payload = {"user_id": "123", "email": "john@example.com", "firstname": "John"}
        >>> create_audit_context(payload)
        {
            'user_id': '123',
            'email': 'john@example.com',
            'display_name': 'John',
            'full_context': 'John (john@example.com)'
        }
    """
    return {
        'user_id': extract_user_id(token_payload),
        'email': extract_user_email(token_payload),
        'display_name': extract_user_display_name(token_payload),
        'full_context': extract_user_from_token(token_payload)
    }
