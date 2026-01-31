"""
User Model for MongoDB.

This module defines the User data structure for authentication and user management.
Uses Pydantic for validation (MIT License - Open Source compliant).
"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr, Field, field_validator
import re


class User(BaseModel):
    """
    User model for authentication and profile management.
    
    All fields use open-source libraries:
    - Pydantic (MIT License)
    - EmailStr validation (built-in Pydantic)
    
    Attributes:
        email: User's email address (unique)
        username: User's username (unique)
        firstname: User's first name
        lastname: User's last name
        password_hash: Bcrypt hashed password
        created_at: Account creation timestamp
        updated_at: Last update timestamp
        is_active: Account active status
    """
    
    email: EmailStr = Field(..., description="User's email address")
    username: str = Field(..., min_length=3, max_length=30, description="Unique username")
    firstname: str = Field(..., min_length=2, max_length=50, description="User's first name")
    lastname: str = Field(..., min_length=2, max_length=50, description="User's last name")
    password_hash: str = Field(..., description="Bcrypt hashed password")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Account creation time")
    updated_at: datetime = Field(default_factory=datetime.utcnow, description="Last update time")
    is_active: bool = Field(default=True, description="Account active status")
    
    @field_validator('username')
    @classmethod
    def validate_username(cls, v: str) -> str:
        """
        Validate username format.
        
        Rules:
        - Must be alphanumeric with optional underscores
        - Cannot start with a number
        - No special characters except underscore
        
        Args:
            v: Username to validate
            
        Returns:
            Validated username
            
        Raises:
            ValueError: If username format is invalid
        """
        if not re.match(r'^[a-zA-Z][a-zA-Z0-9_]*$', v):
            raise ValueError(
                "Username must start with a letter and contain only "
                "letters, numbers, and underscores"
            )
        return v.lower()  # Store usernames in lowercase
    
    @field_validator('firstname', 'lastname')
    @classmethod
    def validate_name_fields(cls, v: str) -> str:
        """
        Validate name fields (firstname, lastname).
        
        Rules:
        - Must contain only letters, spaces, hyphens, and apostrophes
        - Cannot be only whitespace
        
        Args:
            v: Name to validate
            
        Returns:
            Validated and capitalized name
            
        Raises:
            ValueError: If name format is invalid
        """
        v = v.strip()
        if not v:
            raise ValueError("Name cannot be empty or only whitespace")
        
        if not re.match(r"^[a-zA-Z\s\-']+$", v):
            raise ValueError(
                "Name must contain only letters, spaces, hyphens, and apostrophes"
            )
        
        return v.capitalize()
    
    @field_validator('email')
    @classmethod
    def normalize_email(cls, v: str) -> str:
        """
        Normalize email to lowercase.
        
        Args:
            v: Email to normalize
            
        Returns:
            Lowercase email
        """
        return v.lower()
    
    def to_dict(self) -> dict:
        """
        Convert user model to dictionary for MongoDB storage.
        
        Returns:
            Dictionary representation of user
        """
        return {
            "email": self.email,
            "username": self.username,
            "firstname": self.firstname,
            "lastname": self.lastname,
            "password_hash": self.password_hash,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "is_active": self.is_active
        }
    
    def to_public_dict(self) -> dict:
        """
        Convert user model to public dictionary (excludes sensitive data).
        
        Returns:
            Public dictionary representation (no password_hash)
        """
        return {
            "email": self.email,
            "username": self.username,
            "firstname": self.firstname,
            "lastname": self.lastname,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "is_active": self.is_active
        }
    
    class Config:
        """Pydantic configuration."""
        json_schema_extra = {
            "example": {
                "email": "john.doe@example.com",
                "username": "johndoe",
                "firstname": "John",
                "lastname": "Doe",
                "password_hash": "$2b$12$...",
                "created_at": "2026-01-04T12:00:00",
                "updated_at": "2026-01-04T12:00:00",
                "is_active": True
            }
        }


class UserInDB(User):
    """
    User model with MongoDB ID.
    
    Extends User model to include MongoDB ObjectId.
    """
    
    id: Optional[str] = Field(None, alias="_id", description="MongoDB ObjectId as string")
    
    class Config:
        """Pydantic configuration."""
        populate_by_name = True
