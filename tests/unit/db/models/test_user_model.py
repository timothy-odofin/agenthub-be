"""
Unit tests for User model.

Tests user model validation, field constraints, and data transformations.
All dependencies are open-source (pytest - MIT License).
"""

import pytest
from datetime import datetime
from pydantic import ValidationError

from app.db.models.user import User, UserInDB


class TestUserModel:
    """Test suite for User model."""
    
    def test_valid_user_creation(self):
        """Test creating a user with valid data."""
        user = User(
            email="john.doe@example.com",
            username="johndoe",
            firstname="John",
            lastname="Doe",
            password_hash="$2b$12$hashed_password"
        )
        
        assert user.email == "john.doe@example.com"
        assert user.username == "johndoe"
        assert user.firstname == "John"
        assert user.lastname == "Doe"
        assert user.is_active is True
        assert isinstance(user.created_at, datetime)
        assert isinstance(user.updated_at, datetime)
    
    def test_email_normalization(self):
        """Test that email is converted to lowercase."""
        user = User(
            email="John.Doe@EXAMPLE.COM",
            username="johndoe",
            firstname="John",
            lastname="Doe",
            password_hash="$2b$12$hashed"
        )
        
        assert user.email == "john.doe@example.com"
    
    def test_username_normalization(self):
        """Test that username is converted to lowercase."""
        user = User(
            email="john@example.com",
            username="JohnDoe123",
            firstname="John",
            lastname="Doe",
            password_hash="$2b$12$hashed"
        )
        
        assert user.username == "johndoe123"
    
    def test_name_capitalization(self):
        """Test that names are capitalized."""
        user = User(
            email="john@example.com",
            username="johndoe",
            firstname="john",
            lastname="doe",
            password_hash="$2b$12$hashed"
        )
        
        assert user.firstname == "John"
        assert user.lastname == "Doe"
    
    def test_invalid_email(self):
        """Test that invalid email raises validation error."""
        with pytest.raises(ValidationError) as exc_info:
            User(
                email="not-an-email",
                username="johndoe",
                firstname="John",
                lastname="Doe",
                password_hash="$2b$12$hashed"
            )
        
        assert "email" in str(exc_info.value).lower()
    
    def test_username_too_short(self):
        """Test that username shorter than 3 chars raises error."""
        with pytest.raises(ValidationError) as exc_info:
            User(
                email="john@example.com",
                username="ab",
                firstname="John",
                lastname="Doe",
                password_hash="$2b$12$hashed"
            )
        
        assert "username" in str(exc_info.value).lower()
    
    def test_username_too_long(self):
        """Test that username longer than 30 chars raises error."""
        with pytest.raises(ValidationError) as exc_info:
            User(
                email="john@example.com",
                username="a" * 31,
                firstname="John",
                lastname="Doe",
                password_hash="$2b$12$hashed"
            )
        
        assert "username" in str(exc_info.value).lower()
    
    def test_username_invalid_characters(self):
        """Test that username with invalid characters raises error."""
        invalid_usernames = [
            "john@doe",
            "john.doe",
            "john-doe",
            "john doe",
            "123john",  # Cannot start with number
            "john#doe"
        ]
        
        for invalid_username in invalid_usernames:
            with pytest.raises(ValidationError) as exc_info:
                User(
                    email="john@example.com",
                    username=invalid_username,
                    firstname="John",
                    lastname="Doe",
                    password_hash="$2b$12$hashed"
                )
            
            assert "username" in str(exc_info.value).lower()
    
    def test_username_valid_with_underscore(self):
        """Test that username with underscore is valid."""
        user = User(
            email="john@example.com",
            username="john_doe",
            firstname="John",
            lastname="Doe",
            password_hash="$2b$12$hashed"
        )
        
        assert user.username == "john_doe"
    
    def test_firstname_too_short(self):
        """Test that firstname shorter than 2 chars raises error."""
        with pytest.raises(ValidationError) as exc_info:
            User(
                email="john@example.com",
                username="johndoe",
                firstname="J",
                lastname="Doe",
                password_hash="$2b$12$hashed"
            )
        
        assert "firstname" in str(exc_info.value).lower()
    
    def test_lastname_too_short(self):
        """Test that lastname shorter than 2 chars raises error."""
        with pytest.raises(ValidationError) as exc_info:
            User(
                email="john@example.com",
                username="johndoe",
                firstname="John",
                lastname="D",
                password_hash="$2b$12$hashed"
            )
        
        assert "lastname" in str(exc_info.value).lower()
    
    def test_name_with_hyphen(self):
        """Test that names with hyphens are valid."""
        user = User(
            email="john@example.com",
            username="johndoe",
            firstname="Jean-Pierre",
            lastname="Smith-Jones",
            password_hash="$2b$12$hashed"
        )
        
        assert user.firstname == "Jean-pierre"
        assert user.lastname == "Smith-jones"
    
    def test_name_with_apostrophe(self):
        """Test that names with apostrophes are valid."""
        user = User(
            email="john@example.com",
            username="johndoe",
            firstname="O'Connor",
            lastname="D'Angelo",
            password_hash="$2b$12$hashed"
        )
        
        # capitalize() converts first letter of each word, so "O'connor" becomes "O'connor"
        assert user.firstname == "O'connor"
        assert user.lastname == "D'angelo"
    
    def test_name_invalid_characters(self):
        """Test that names with invalid characters raise error."""
        invalid_names = ["John123", "John@Doe", "John_Doe", "John.Doe"]
        
        for invalid_name in invalid_names:
            with pytest.raises(ValidationError):
                User(
                    email="john@example.com",
                    username="johndoe",
                    firstname=invalid_name,
                    lastname="Doe",
                    password_hash="$2b$12$hashed"
                )
    
    def test_name_only_whitespace(self):
        """Test that names with only whitespace raise error."""
        with pytest.raises(ValidationError):
            User(
                email="john@example.com",
                username="johndoe",
                firstname="   ",
                lastname="Doe",
                password_hash="$2b$12$hashed"
            )
    
    def test_missing_required_fields(self):
        """Test that missing required fields raise error."""
        required_fields = ["email", "username", "firstname", "lastname", "password_hash"]
        
        for field in required_fields:
            user_data = {
                "email": "john@example.com",
                "username": "johndoe",
                "firstname": "John",
                "lastname": "Doe",
                "password_hash": "$2b$12$hashed"
            }
            
            del user_data[field]
            
            with pytest.raises(ValidationError) as exc_info:
                User(**user_data)
            
            assert field in str(exc_info.value).lower()
    
    def test_to_dict(self):
        """Test conversion to dictionary."""
        user = User(
            email="john@example.com",
            username="johndoe",
            firstname="John",
            lastname="Doe",
            password_hash="$2b$12$hashed"
        )
        
        user_dict = user.to_dict()
        
        assert user_dict["email"] == "john@example.com"
        assert user_dict["username"] == "johndoe"
        assert user_dict["firstname"] == "John"
        assert user_dict["lastname"] == "Doe"
        assert user_dict["password_hash"] == "$2b$12$hashed"
        assert "created_at" in user_dict
        assert "updated_at" in user_dict
        assert user_dict["is_active"] is True
    
    def test_to_public_dict(self):
        """Test conversion to public dictionary (no password)."""
        user = User(
            email="john@example.com",
            username="johndoe",
            firstname="John",
            lastname="Doe",
            password_hash="$2b$12$hashed"
        )
        
        public_dict = user.to_public_dict()
        
        assert public_dict["email"] == "john@example.com"
        assert public_dict["username"] == "johndoe"
        assert public_dict["firstname"] == "John"
        assert public_dict["lastname"] == "Doe"
        assert "password_hash" not in public_dict
        assert "created_at" in public_dict
        assert public_dict["is_active"] is True
    
    def test_default_is_active(self):
        """Test that is_active defaults to True."""
        user = User(
            email="john@example.com",
            username="johndoe",
            firstname="John",
            lastname="Doe",
            password_hash="$2b$12$hashed"
        )
        
        assert user.is_active is True
    
    def test_custom_is_active(self):
        """Test setting custom is_active value."""
        user = User(
            email="john@example.com",
            username="johndoe",
            firstname="John",
            lastname="Doe",
            password_hash="$2b$12$hashed",
            is_active=False
        )
        
        assert user.is_active is False


class TestUserInDBModel:
    """Test suite for UserInDB model."""
    
    def test_user_in_db_with_id(self):
        """Test UserInDB with MongoDB ObjectId."""
        user = UserInDB(
            _id="507f1f77bcf86cd799439011",
            email="john@example.com",
            username="johndoe",
            firstname="John",
            lastname="Doe",
            password_hash="$2b$12$hashed"
        )
        
        assert user.id == "507f1f77bcf86cd799439011"
        assert user.email == "john@example.com"
    
    def test_user_in_db_without_id(self):
        """Test UserInDB without ID (before database insert)."""
        user = UserInDB(
            email="john@example.com",
            username="johndoe",
            firstname="John",
            lastname="Doe",
            password_hash="$2b$12$hashed"
        )
        
        assert user.id is None
        assert user.email == "john@example.com"
