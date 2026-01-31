"""
Password hashing and verification utilities.

This module provides a singleton PasswordManager for secure password operations.
Uses bcrypt directly for industry-standard password hashing.

Example:
    >>> from app.core.security.password_handler import password_manager
    >>> hashed = password_manager.hash_password("MyP@ssw0rd123!")
    >>> password_manager.verify_password("MyP@ssw0rd123!", hashed)
    True
"""

import re
import bcrypt
from typing import Optional, Tuple

from app.core.utils.logger import get_logger

logger = get_logger(__name__)

# Password validation constants
MIN_PASSWORD_LENGTH = 8
MAX_PASSWORD_LENGTH = 72  # bcrypt's maximum password length
BCRYPT_ROUNDS = 12

# Password strength regex patterns
UPPERCASE_PATTERN = re.compile(r'[A-Z]')
LOWERCASE_PATTERN = re.compile(r'[a-z]')
DIGIT_PATTERN = re.compile(r'\d')
SPECIAL_CHAR_PATTERN = re.compile(r'[!@#$%^&*(),.?":{}|<>_\-+=\[\]\\\/;\'`~]')


class PasswordManager:
    """
    Singleton password manager for secure password operations.
    
    Provides centralized password hashing, verification, and validation
    following the same pattern as the application settings object.
    
    Usage:
        from app.core.security.password_handler import password_manager
        
        hashed = password_manager.hash_password("MyP@ssw0rd")
        is_valid = password_manager.verify_password("MyP@ssw0rd", hashed)
    """
    
    _instance: Optional['PasswordManager'] = None
    
    def __new__(cls) -> 'PasswordManager':
        """Ensure only one instance of PasswordManager exists."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self) -> None:
        """Initialize the password manager (only once due to singleton)."""
        if not hasattr(self, '_initialized'):
            self._rounds = BCRYPT_ROUNDS
            self._initialized = True
            logger.info(f"PasswordManager initialized with {self._rounds} bcrypt rounds")
    
    def hash_password(self, password: str) -> str:
        """
        Hash a password using bcrypt.
        
        Args:
            password: Plain text password to hash
            
        Returns:
            str: Hashed password string
            
        Raises:
            ValueError: If password is empty or None
            
        Example:
            >>> hashed = password_manager.hash_password("MySecureP@ssw0rd!")
            >>> print(hashed)
            $2b$12$...
        """
        if not password:
            raise ValueError("Password cannot be empty")
        
        try:
            # Convert password to bytes and hash with bcrypt
            password_bytes = password.encode('utf-8')
            hashed = bcrypt.hashpw(password_bytes, bcrypt.gensalt(rounds=self._rounds))
            return hashed.decode('utf-8')
        except Exception as e:
            logger.error(f"Error hashing password: {e}", exc_info=True)
            raise

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """
        Verify a plain password against a hashed password.
        
        Args:
            plain_password: Plain text password to verify
            hashed_password: Hashed password to compare against
            
        Returns:
            bool: True if password matches, False otherwise
            
        Example:
            >>> hashed = password_manager.hash_password("MySecureP@ssw0rd!")
            >>> password_manager.verify_password("MySecureP@ssw0rd!", hashed)
            True
            >>> password_manager.verify_password("WrongPassword", hashed)
            False
        """
        if not plain_password or not hashed_password:
            return False
        
        try:
            password_bytes = plain_password.encode('utf-8')
            hashed_bytes = hashed_password.encode('utf-8')
            return bcrypt.checkpw(password_bytes, hashed_bytes)
        except Exception as e:
            logger.error(f"Error verifying password: {e}", exc_info=True)
            return False

    def needs_rehash(self, hashed_password: str, rounds: Optional[int] = None) -> bool:
        """
        Check if a hashed password needs to be rehashed.
        
        This is useful for updating password hashes when security settings change
        (e.g., increasing bcrypt rounds).
        
        Args:
            hashed_password: Hashed password to check
            rounds: Desired number of bcrypt rounds (default: use configured rounds)
            
        Returns:
            bool: True if password needs rehashing, False otherwise
            
        Example:
            >>> hashed = password_manager.hash_password("MySecureP@ssw0rd!")
            >>> password_manager.needs_rehash(hashed)
            False
        """
        if rounds is None:
            rounds = self._rounds
            
        try:
            # Extract cost factor from hash
            # Bcrypt hash format: $2b$12$... where 12 is the cost factor
            parts = hashed_password.split('$')
            if len(parts) >= 3:
                current_rounds = int(parts[2])
                return current_rounds < rounds
            return False
        except Exception as e:
            logger.error(f"Error checking if password needs rehash: {e}", exc_info=True)
            return False

    def validate_password_strength(self, password: str) -> Tuple[bool, Optional[str]]:
        """
        Validate password strength against security requirements.
        
        Requirements:
        - Minimum 8 characters
        - Maximum 72 characters (bcrypt limit)
        - At least one uppercase letter
        - At least one lowercase letter
        - At least one digit
        - At least one special character
        
        Args:
            password: Password to validate
            
        Returns:
            tuple: (is_valid, error_message)
                - is_valid: True if password meets requirements
                - error_message: Description of failed requirement, None if valid
                
        Example:
            >>> password_manager.validate_password_strength("weak")
            (False, "Password must be at least 8 characters long")
            >>> password_manager.validate_password_strength("SecureP@ss123")
            (True, None)
        """
        if not password:
            return False, "Password cannot be empty"
        
        if len(password) < MIN_PASSWORD_LENGTH:
            return False, f"Password must be at least {MIN_PASSWORD_LENGTH} characters long"
        
        if len(password) > MAX_PASSWORD_LENGTH:
            return False, f"Password must not exceed {MAX_PASSWORD_LENGTH} characters (bcrypt limit)"
        
        if not UPPERCASE_PATTERN.search(password):
            return False, "Password must contain at least one uppercase letter"
        
        if not LOWERCASE_PATTERN.search(password):
            return False, "Password must contain at least one lowercase letter"
        
        if not DIGIT_PATTERN.search(password):
            return False, "Password must contain at least one digit"
        
        if not SPECIAL_CHAR_PATTERN.search(password):
            return False, "Password must contain at least one special character"
        
        return True, None


# Singleton instance - following the same pattern as settings
password_manager = PasswordManager()
