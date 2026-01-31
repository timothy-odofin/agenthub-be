"""
Unit tests for TokenManager.

Tests JWT token creation, verification, and expiration handling.
"""

import pytest
from datetime import timedelta, datetime, timezone
from unittest.mock import patch
from jose import jwt

from src.app.core.security.token_manager import (
    token_manager,
    TokenManager,
)


class TestTokenManager:
    """Test suite for TokenManager singleton."""
    
    def test_singleton_pattern(self):
        """Test that TokenManager is a singleton."""
        manager1 = TokenManager()
        manager2 = TokenManager()
        
        assert manager1 is manager2
        assert manager1 is token_manager
        assert manager2 is token_manager


class TestAccessTokenCreation:
    """Test suite for access token creation."""
    
    def test_create_access_token_basic(self):
        """Test creating a basic access token."""
        token = token_manager.create_access_token(
            user_id="user123",
            email="test@example.com"
        )
        
        assert token is not None
        assert isinstance(token, str)
        assert len(token) > 0
    
    def test_create_access_token_with_username(self):
        """Test creating token with username."""
        token = token_manager.create_access_token(
            user_id="user123",
            email="test@example.com",
            username="johndoe"
        )
        
        payload = token_manager.verify_token(token)
        assert payload is not None
        assert payload["user_id"] == "user123"
        assert payload["email"] == "test@example.com"
        assert payload["username"] == "johndoe"
    
    def test_create_access_token_with_additional_claims(self):
        """Test creating token with additional claims."""
        token = token_manager.create_access_token(
            user_id="user123",
            email="test@example.com",
            additional_claims={"role": "admin", "permissions": ["read", "write"]}
        )
        
        payload = token_manager.verify_token(token)
        assert payload is not None
        assert payload["role"] == "admin"
        assert payload["permissions"] == ["read", "write"]
    
    def test_create_access_token_with_custom_expiry(self):
        """Test creating token with custom expiration."""
        token = token_manager.create_access_token(
            user_id="user123",
            email="test@example.com",
            expires_delta=timedelta(hours=2)
        )
        
        payload = token_manager.verify_token(token)
        assert payload is not None
        
        # Check expiration is approximately 2 hours from now
        exp = datetime.fromtimestamp(payload["exp"], tz=timezone.utc)
        now = datetime.now(timezone.utc)
        diff = (exp - now).total_seconds()
        
        # Should be close to 2 hours (7200 seconds), allow 10 second margin
        assert 7190 < diff < 7210
    
    def test_token_contains_standard_claims(self):
        """Test that token contains standard JWT claims."""
        token = token_manager.create_access_token(
            user_id="user123",
            email="test@example.com"
        )
        
        payload = token_manager.verify_token(token)
        assert payload is not None
        
        # Standard claims
        assert "sub" in payload  # Subject
        assert "exp" in payload  # Expiration
        assert "iat" in payload  # Issued at
        assert "type" in payload  # Token type
        
        assert payload["sub"] == "user123"
        assert payload["type"] == "access"
    
    def test_token_type_is_access(self):
        """Test that created tokens have correct type."""
        token = token_manager.create_access_token(
            user_id="user123",
            email="test@example.com"
        )
        
        payload = token_manager.verify_token(token)
        assert payload["type"] == "access"


class TestAccessTokenVerification:
    """Test suite for access token verification."""
    
    def test_verify_valid_token(self):
        """Test verifying a valid token."""
        token = token_manager.create_access_token(
            user_id="user123",
            email="test@example.com"
        )
        
        payload = token_manager.verify_token(token)
        
        assert payload is not None
        assert payload["user_id"] == "user123"
        assert payload["email"] == "test@example.com"
    
    def test_verify_expired_token(self):
        """Test verifying an expired token."""
        token = token_manager.create_access_token(
            user_id="user123",
            email="test@example.com",
            expires_delta=timedelta(seconds=-1)  # Already expired
        )
        
        payload = token_manager.verify_token(token)
        
        assert payload is None
    
    def test_verify_invalid_token(self):
        """Test verifying an invalid token."""
        payload = token_manager.verify_token("invalid.token.here")
        
        assert payload is None
    
    def test_verify_tampered_token(self):
        """Test verifying a tampered token."""
        token = token_manager.create_access_token(
            user_id="user123",
            email="test@example.com"
        )
        
        # Tamper with the token
        tampered = token[:-10] + "tampered00"
        
        payload = token_manager.verify_token(tampered)
        
        assert payload is None
    
    def test_verify_token_wrong_type(self):
        """Test verifying a token with wrong type."""
        # Create a token with wrong type
        token = token_manager.create_refresh_token(user_id="user123")
        
        # Try to verify as access token
        payload = token_manager.verify_token(token)
        
        assert payload is None


class TestRefreshTokens:
    """Test suite for refresh token operations."""
    
    def test_create_refresh_token(self):
        """Test creating a refresh token."""
        token = token_manager.create_refresh_token(user_id="user123")
        
        assert token is not None
        assert isinstance(token, str)
        assert len(token) > 0
    
    def test_verify_refresh_token(self):
        """Test verifying a refresh token."""
        token = token_manager.create_refresh_token(user_id="user123")
        
        user_id = token_manager.verify_refresh_token(token)
        
        assert user_id == "user123"
    
    def test_verify_expired_refresh_token(self):
        """Test verifying an expired refresh token."""
        token = token_manager.create_refresh_token(
            user_id="user123",
            expires_delta=timedelta(seconds=-1)
        )
        
        user_id = token_manager.verify_refresh_token(token)
        
        assert user_id is None
    
    def test_refresh_token_has_longer_expiry(self):
        """Test that refresh tokens have longer expiration than access tokens."""
        access_token = token_manager.create_access_token(
            user_id="user123",
            email="test@example.com"
        )
        refresh_token = token_manager.create_refresh_token(user_id="user123")
        
        access_payload = token_manager.decode_token_without_verification(access_token)
        refresh_payload = token_manager.decode_token_without_verification(refresh_token)
        
        access_exp = datetime.fromtimestamp(access_payload["exp"], tz=timezone.utc)
        refresh_exp = datetime.fromtimestamp(refresh_payload["exp"], tz=timezone.utc)
        
        # Refresh token should expire after access token
        assert refresh_exp > access_exp


class TestTokenUtilities:
    """Test suite for token utility functions."""
    
    def test_decode_token_without_verification(self):
        """Test decoding token without verification."""
        token = token_manager.create_access_token(
            user_id="user123",
            email="test@example.com"
        )
        
        payload = token_manager.decode_token_without_verification(token)
        
        assert payload is not None
        assert payload["user_id"] == "user123"
        assert payload["email"] == "test@example.com"
    
    def test_decode_expired_token_without_verification(self):
        """Test decoding expired token without verification."""
        token = token_manager.create_access_token(
            user_id="user123",
            email="test@example.com",
            expires_delta=timedelta(seconds=-1)
        )
        
        # Should still decode even though expired
        payload = token_manager.decode_token_without_verification(token)
        
        assert payload is not None
        assert payload["user_id"] == "user123"
    
    def test_get_token_expiry(self):
        """Test getting token expiration time."""
        token = token_manager.create_access_token(
            user_id="user123",
            email="test@example.com"
        )
        
        expiry = token_manager.get_token_expiry(token)
        
        assert expiry is not None
        assert isinstance(expiry, datetime)
        assert expiry > datetime.now(timezone.utc)
    
    def test_get_expiry_of_invalid_token(self):
        """Test getting expiry of invalid token."""
        expiry = token_manager.get_token_expiry("invalid.token")
        
        assert expiry is None


class TestTokenIntegration:
    """Integration tests for token workflows."""
    
    def test_access_and_refresh_token_workflow(self):
        """Test complete workflow with access and refresh tokens."""
        # Create both tokens
        access_token = token_manager.create_access_token(
            user_id="user123",
            email="test@example.com"
        )
        refresh_token = token_manager.create_refresh_token(user_id="user123")
        
        # Verify access token
        access_payload = token_manager.verify_token(access_token)
        assert access_payload is not None
        assert access_payload["user_id"] == "user123"
        
        # Verify refresh token
        user_id = token_manager.verify_refresh_token(refresh_token)
        assert user_id == "user123"
        
        # Use refresh token to create new access token
        new_access_token = token_manager.create_access_token(
            user_id=user_id,
            email="test@example.com"
        )
        
        new_payload = token_manager.verify_token(new_access_token)
        assert new_payload is not None
        assert new_payload["user_id"] == "user123"
    
    def test_token_contains_all_user_info(self):
        """Test that token contains all necessary user information."""
        token = token_manager.create_access_token(
            user_id="user123",
            email="john@example.com",
            username="johndoe",
            additional_claims={
                "firstname": "John",
                "lastname": "Doe",
                "role": "user"
            }
        )
        
        payload = token_manager.verify_token(token)
        
        assert payload["user_id"] == "user123"
        assert payload["email"] == "john@example.com"
        assert payload["username"] == "johndoe"
        assert payload["firstname"] == "John"
        assert payload["lastname"] == "Doe"
        assert payload["role"] == "user"
    
    def test_multiple_tokens_for_different_users(self):
        """Test creating tokens for different users."""
        token1 = token_manager.create_access_token(
            user_id="user1",
            email="user1@example.com"
        )
        token2 = token_manager.create_access_token(
            user_id="user2",
            email="user2@example.com"
        )
        
        payload1 = token_manager.verify_token(token1)
        payload2 = token_manager.verify_token(token2)
        
        assert payload1["user_id"] == "user1"
        assert payload2["user_id"] == "user2"
        assert token1 != token2
