"""
Unit tests for PasswordManager singleton.

Tests password hashing, verification, and strength validation using the singleton pattern.
"""

import pytest
from unittest.mock import patch

from src.app.core.security.password_handler import (
    password_manager,
    PasswordManager,
    MIN_PASSWORD_LENGTH,
    MAX_PASSWORD_LENGTH
)


class TestPasswordManager:
    """Test suite for PasswordManager singleton."""
    
    def test_singleton_pattern(self):
        """Test that PasswordManager is a singleton."""
        manager1 = PasswordManager()
        manager2 = PasswordManager()
        
        assert manager1 is manager2
        assert manager1 is password_manager
        assert manager2 is password_manager


class TestPasswordHashing:
    """Test suite for password hashing functions."""
    
    def test_hash_password_creates_bcrypt_hash(self):
        """Test that hash_password creates a valid bcrypt hash."""
        password = "TestPassword123!"
        hashed = password_manager.hash_password(password)
        
        # Bcrypt hashes start with $2b$ and are 60 characters long
        assert hashed.startswith('$2b$')
        assert len(hashed) == 60

    def test_hash_password_different_hashes_for_same_password(self):
        """Test that same password produces different hashes (due to salt)."""
        password = "TestPassword123!"
        hash1 = password_manager.hash_password(password)
        hash2 = password_manager.hash_password(password)
        
        # Hashes should be different due to random salt
        assert hash1 != hash2

    def test_hash_password_empty_string_raises_error(self):
        """Test that hashing empty string raises ValueError."""
        with pytest.raises(ValueError, match="Password cannot be empty"):
            password_manager.hash_password("")

    def test_hash_password_none_raises_error(self):
        """Test that hashing None raises ValueError."""
        with pytest.raises(ValueError, match="Password cannot be empty"):
            password_manager.hash_password(None)

    def test_hash_password_with_special_characters(self):
        """Test hashing password with special characters."""
        password = "P@ssw0rd!#$%^&*()"
        hashed = password_manager.hash_password(password)
        
        assert hashed.startswith('$2b$')
        assert len(hashed) == 60

    def test_hash_password_with_unicode_characters(self):
        """Test hashing password with unicode characters."""
        password = "Pässw0rd123!αβγ"
        hashed = password_manager.hash_password(password)
        
        assert hashed.startswith('$2b$')
        assert len(hashed) == 60

    def test_hash_password_error_handling(self):
        """Test error handling in hash_password."""
        with patch('src.app.core.security.password_handler.bcrypt.hashpw') as mock_hash:
            mock_hash.side_effect = Exception("Hashing failed")
            
            with pytest.raises(Exception, match="Hashing failed"):
                password_manager.hash_password("TestPassword123!")


class TestPasswordVerification:
    """Test suite for password verification."""

    def test_verify_password_correct_password_returns_true(self):
        """Test that correct password verification returns True."""
        password = "TestPassword123!"
        hashed = password_manager.hash_password(password)
        
        assert password_manager.verify_password(password, hashed) is True

    def test_verify_password_incorrect_password_returns_false(self):
        """Test that incorrect password verification returns False."""
        password = "TestPassword123!"
        wrong_password = "WrongPassword123!"
        hashed = password_manager.hash_password(password)
        
        assert password_manager.verify_password(wrong_password, hashed) is False

    def test_verify_password_case_sensitive(self):
        """Test that password verification is case-sensitive."""
        password = "TestPassword123!"
        wrong_case = "testpassword123!"
        hashed = password_manager.hash_password(password)
        
        assert password_manager.verify_password(wrong_case, hashed) is False

    def test_verify_password_empty_plain_password_returns_false(self):
        """Test that empty plain password returns False."""
        hashed = password_manager.hash_password("TestPassword123!")
        
        assert password_manager.verify_password("", hashed) is False

    def test_verify_password_empty_hashed_password_returns_false(self):
        """Test that empty hashed password returns False."""
        assert password_manager.verify_password("TestPassword123!", "") is False

    def test_verify_password_none_plain_password_returns_false(self):
        """Test that None plain password returns False."""
        hashed = password_manager.hash_password("TestPassword123!")
        
        assert password_manager.verify_password(None, hashed) is False

    def test_verify_password_none_hashed_password_returns_false(self):
        """Test that None hashed password returns False."""
        assert password_manager.verify_password("TestPassword123!", None) is False

    def test_verify_password_with_unicode(self):
        """Test password verification with unicode characters."""
        password = "Pässw0rd123!αβγ"
        hashed = password_manager.hash_password(password)
        
        assert password_manager.verify_password(password, hashed) is True
        assert password_manager.verify_password("WrongPassword", hashed) is False

    def test_verify_password_error_handling(self):
        """Test error handling in verify_password."""
        with patch('src.app.core.security.password_handler.bcrypt.checkpw') as mock_check:
            mock_check.side_effect = Exception("Verification failed")
            hashed = password_manager.hash_password("TestPassword123!")
            
            result = password_manager.verify_password("TestPassword123!", hashed)
            assert result is False


class TestPasswordRehash:
    """Test suite for password rehashing checks."""

    def test_needs_rehash_fresh_hash_returns_false(self):
        """Test that a fresh hash with correct rounds returns False."""
        password = "TestPassword123!"
        hashed = password_manager.hash_password(password)
        
        # Fresh hash with 12 rounds should not need rehashing
        assert password_manager.needs_rehash(hashed, 12) is False

    def test_needs_rehash_error_handling(self):
        """Test error handling in needs_rehash."""
        # Invalid hash format should return False
        result = password_manager.needs_rehash("invalid_hash_format")
        assert result is False


class TestPasswordStrengthValidation:
    """Test suite for password strength validation."""

    def test_validate_strong_password(self):
        """Test validation of a strong password."""
        password = "StrongP@ssw0rd"
        is_valid, error = password_manager.validate_password_strength(password)
        
        assert is_valid is True
        assert error is None

    def test_validate_password_too_short(self):
        """Test validation fails for password too short."""
        password = "Sh0rt!"
        is_valid, error = password_manager.validate_password_strength(password)
        
        assert is_valid is False
        assert f"at least {MIN_PASSWORD_LENGTH} characters" in error

    def test_validate_password_too_long(self):
        """Test validation fails for password too long."""
        password = "A1b!" + "x" * 70  # 74 characters total
        is_valid, error = password_manager.validate_password_strength(password)
        
        assert is_valid is False
        assert f"not exceed {MAX_PASSWORD_LENGTH} characters" in error

    def test_validate_password_no_uppercase(self):
        """Test validation fails when no uppercase letter."""
        password = "weakpassw0rd!"
        is_valid, error = password_manager.validate_password_strength(password)
        
        assert is_valid is False
        assert "uppercase" in error.lower()

    def test_validate_password_no_lowercase(self):
        """Test validation fails when no lowercase letter."""
        password = "WEAKPASSW0RD!"
        is_valid, error = password_manager.validate_password_strength(password)
        
        assert is_valid is False
        assert "lowercase" in error.lower()

    def test_validate_password_no_digit(self):
        """Test validation fails when no digit."""
        password = "WeakPassword!"
        is_valid, error = password_manager.validate_password_strength(password)
        
        assert is_valid is False
        assert "digit" in error.lower()

    def test_validate_password_no_special_character(self):
        """Test validation fails when no special character."""
        password = "WeakPassword123"
        is_valid, error = password_manager.validate_password_strength(password)
        
        assert is_valid is False
        assert "special character" in error.lower()

    def test_validate_password_empty_string(self):
        """Test validation fails for empty string."""
        is_valid, error = password_manager.validate_password_strength("")
        
        assert is_valid is False
        assert "cannot be empty" in error.lower()

    def test_validate_password_none(self):
        """Test validation fails for None."""
        is_valid, error = password_manager.validate_password_strength(None)
        
        assert is_valid is False
        assert "cannot be empty" in error.lower()

    def test_validate_password_all_special_characters_accepted(self):
        """Test that all common special characters are accepted."""
        special_chars = "!@#$%^&*()_+-=[]{}|;:,.<>?/"
        for char in special_chars:
            password = f"Password123{char}"
            is_valid, error = password_manager.validate_password_strength(password)
            assert is_valid is True, f"Failed for special char: {char}"

    def test_validate_password_minimum_length(self):
        """Test password with exactly minimum length."""
        password = "Pass1@rd"  # Exactly 8 characters
        is_valid, error = password_manager.validate_password_strength(password)
        
        assert is_valid is True
        assert error is None

    def test_validate_password_maximum_length(self):
        """Test password with exactly maximum length."""
        password = "A1b!" + "x" * 68  # Exactly 72 characters
        is_valid, error = password_manager.validate_password_strength(password)
        
        assert is_valid is True
        assert error is None

    def test_validate_password_with_spaces(self):
        """Test that password with spaces is accepted."""
        password = "Pass Word 123!"
        is_valid, error = password_manager.validate_password_strength(password)
        
        assert is_valid is True
        assert error is None


class TestPasswordIntegration:
    """Integration tests for complete password workflows."""

    def test_hash_and_verify_workflow(self):
        """Test complete hash and verify workflow."""
        password = "MySecureP@ssw0rd123"
        
        # Hash the password
        hashed = password_manager.hash_password(password)
        
        # Verify correct password
        assert password_manager.verify_password(password, hashed) is True
        
        # Verify incorrect password
        assert password_manager.verify_password("WrongPassword", hashed) is False

    def test_validate_then_hash_workflow(self):
        """Test validation before hashing workflow."""
        password = "SecureP@ssw0rd123"
        
        # Validate password strength
        is_valid, error = password_manager.validate_password_strength(password)
        assert is_valid is True
        
        # Hash if valid
        if is_valid:
            hashed = password_manager.hash_password(password)
            assert password_manager.verify_password(password, hashed) is True

    def test_weak_password_workflow(self):
        """Test workflow with weak password."""
        weak_password = "weak"
        
        # Validate password strength
        is_valid, error = password_manager.validate_password_strength(weak_password)
        assert is_valid is False
        assert error is not None
        
        # Should not hash weak passwords in production
        # But test that it still technically works
        hashed = password_manager.hash_password("WeakP@ss1" if not is_valid else weak_password)
        assert hashed.startswith('$2b$')

    def test_multiple_users_same_password_different_hashes(self):
        """Test that same password for different users produces different hashes."""
        password = "SharedP@ssw0rd123"
        
        user1_hash = password_manager.hash_password(password)
        user2_hash = password_manager.hash_password(password)
        user3_hash = password_manager.hash_password(password)
        
        # All hashes should be different
        assert user1_hash != user2_hash
        assert user2_hash != user3_hash
        assert user1_hash != user3_hash
        
        # But all should verify correctly
        assert password_manager.verify_password(password, user1_hash) is True
        assert password_manager.verify_password(password, user2_hash) is True
        assert password_manager.verify_password(password, user3_hash) is True
