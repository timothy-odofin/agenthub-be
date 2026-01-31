"""
Unit tests for signup workflow.

Tests the LangGraph signup workflow with validation and user creation.
"""

import pytest
from unittest.mock import patch, AsyncMock, MagicMock

from src.app.agent.workflows.signup_workflow import (
    SignupState,
    validate_email,
    validate_username,
    validate_password,
    validate_names,
    should_create_user,
    create_user,
    format_error,
    signup_workflow
)
from src.app.db.models.user import User


class TestSignupWorkflowValidation:
    """Test suite for signup workflow validation nodes."""
    
    @pytest.mark.asyncio
    async def test_validate_email_success(self):
        """Test email validation with valid email."""
        state: SignupState = {
            "email": "test@example.com",
            "username": "",
            "password": "",
            "firstname": "",
            "lastname": "",
            "validation_errors": [],
            "user_id": None,
            "success": False,
            "message": ""
        }
        
        with patch('src.app.agent.workflows.signup_workflow.user_repository.get_user_by_email', new=AsyncMock(return_value=None)):
            result = await validate_email(state)
            
        assert result["validation_errors"] == []
    
    @pytest.mark.asyncio
    async def test_validate_email_invalid_format(self):
        """Test email validation with invalid format."""
        state: SignupState = {
            "email": "invalid-email",
            "username": "",
            "password": "",
            "firstname": "",
            "lastname": "",
            "validation_errors": [],
            "user_id": None,
            "success": False,
            "message": ""
        }
        
        result = await validate_email(state)
        
        assert "Invalid email format" in result["validation_errors"]
    
    @pytest.mark.asyncio
    async def test_validate_email_already_exists(self):
        """Test email validation when email already registered."""
        state: SignupState = {
            "email": "existing@example.com",
            "username": "",
            "password": "",
            "firstname": "",
            "lastname": "",
            "validation_errors": [],
            "user_id": None,
            "success": False,
            "message": ""
        }
        
        mock_user = MagicMock(spec=User)
        with patch('src.app.agent.workflows.signup_workflow.user_repository.get_user_by_email', new=AsyncMock(return_value=mock_user)):
            result = await validate_email(state)
            
        assert "Email already registered" in result["validation_errors"]
    
    @pytest.mark.asyncio
    async def test_validate_username_success(self):
        """Test username validation with valid username."""
        state: SignupState = {
            "email": "",
            "username": "johndoe",
            "password": "",
            "firstname": "",
            "lastname": "",
            "validation_errors": [],
            "user_id": None,
            "success": False,
            "message": ""
        }
        
        with patch('src.app.agent.workflows.signup_workflow.user_repository.get_user_by_username', new=AsyncMock(return_value=None)):
            result = await validate_username(state)
            
        assert result["validation_errors"] == []
    
    @pytest.mark.asyncio
    async def test_validate_username_too_short(self):
        """Test username validation with too short username."""
        state: SignupState = {
            "email": "",
            "username": "ab",
            "password": "",
            "firstname": "",
            "lastname": "",
            "validation_errors": [],
            "user_id": None,
            "success": False,
            "message": ""
        }
        
        result = await validate_username(state)
        
        assert any("at least" in error for error in result["validation_errors"])
    
    @pytest.mark.asyncio
    async def test_validate_username_invalid_characters(self):
        """Test username validation with invalid characters."""
        state: SignupState = {
            "email": "",
            "username": "john@doe",
            "password": "",
            "firstname": "",
            "lastname": "",
            "validation_errors": [],
            "user_id": None,
            "success": False,
            "message": ""
        }
        
        result = await validate_username(state)
        
        assert any("only contain" in error for error in result["validation_errors"])
    
    @pytest.mark.asyncio
    async def test_validate_password_success(self):
        """Test password validation with strong password."""
        state: SignupState = {
            "email": "",
            "username": "",
            "password": "StrongP@ss123",
            "firstname": "",
            "lastname": "",
            "validation_errors": [],
            "user_id": None,
            "success": False,
            "message": ""
        }
        
        result = await validate_password(state)
        
        assert result["validation_errors"] == []
    
    @pytest.mark.asyncio
    async def test_validate_password_weak(self):
        """Test password validation with weak password."""
        state: SignupState = {
            "email": "",
            "username": "",
            "password": "weak",
            "firstname": "",
            "lastname": "",
            "validation_errors": [],
            "user_id": None,
            "success": False,
            "message": ""
        }
        
        result = await validate_password(state)
        
        assert len(result["validation_errors"]) > 0
    
    @pytest.mark.asyncio
    async def test_validate_names_success(self):
        """Test names validation with valid names."""
        state: SignupState = {
            "email": "",
            "username": "",
            "password": "",
            "firstname": "John",
            "lastname": "Doe",
            "validation_errors": [],
            "user_id": None,
            "success": False,
            "message": ""
        }
        
        result = await validate_names(state)
        
        assert result["validation_errors"] == []
    
    @pytest.mark.asyncio
    async def test_validate_names_missing(self):
        """Test names validation with missing names."""
        state: SignupState = {
            "email": "",
            "username": "",
            "password": "",
            "firstname": "",
            "lastname": "",
            "validation_errors": [],
            "user_id": None,
            "success": False,
            "message": ""
        }
        
        result = await validate_names(state)
        
        assert "First name is required" in result["validation_errors"]
        assert "Last name is required" in result["validation_errors"]


class TestSignupWorkflowDecisionNodes:
    """Test suite for workflow decision nodes."""
    
    def test_should_create_user_with_no_errors(self):
        """Test decision node with no validation errors."""
        state: SignupState = {
            "email": "test@example.com",
            "username": "johndoe",
            "password": "StrongP@ss123",
            "firstname": "John",
            "lastname": "Doe",
            "validation_errors": [],
            "user_id": None,
            "success": False,
            "message": ""
        }
        
        result = should_create_user(state)
        
        assert result == "create_user"
    
    def test_should_create_user_with_errors(self):
        """Test decision node with validation errors."""
        state: SignupState = {
            "email": "invalid",
            "username": "a",
            "password": "weak",
            "firstname": "",
            "lastname": "",
            "validation_errors": ["Email invalid", "Username too short"],
            "user_id": None,
            "success": False,
            "message": ""
        }
        
        result = should_create_user(state)
        
        assert result == "format_error"


class TestSignupWorkflowActionNodes:
    """Test suite for workflow action nodes."""
    
    @pytest.mark.asyncio
    async def test_create_user_success(self):
        """Test user creation with valid data."""
        state: SignupState = {
            "email": "test@example.com",
            "username": "johndoe",
            "password": "StrongP@ss123",
            "firstname": "John",
            "lastname": "Doe",
            "validation_errors": [],
            "user_id": None,
            "success": False,
            "message": ""
        }
        
        mock_user = MagicMock(spec=User)
        mock_user.id = "user123"
        
        with patch('src.app.agent.workflows.signup_workflow.user_repository.create_user', new=AsyncMock(return_value=mock_user)):
            result = await create_user(state)
            
        assert result["success"] is True
        assert result["user_id"] == "user123"
        assert "successfully" in result["message"]
    
    @pytest.mark.asyncio
    async def test_create_user_error(self):
        """Test user creation with database error."""
        state: SignupState = {
            "email": "test@example.com",
            "username": "johndoe",
            "password": "StrongP@ss123",
            "firstname": "John",
            "lastname": "Doe",
            "validation_errors": [],
            "user_id": None,
            "success": False,
            "message": ""
        }
        
        with patch('src.app.agent.workflows.signup_workflow.user_repository.create_user', new=AsyncMock(side_effect=Exception("DB error"))):
            result = await create_user(state)
            
        assert result["success"] is False
        assert "Error creating user" in result["message"]
    
    @pytest.mark.asyncio
    async def test_format_error(self):
        """Test error formatting node."""
        state: SignupState = {
            "email": "test@example.com",
            "username": "johndoe",
            "password": "weak",
            "firstname": "John",
            "lastname": "Doe",
            "validation_errors": ["Password too weak", "Email invalid"],
            "user_id": None,
            "success": False,
            "message": ""
        }
        
        result = await format_error(state)
        
        assert result["success"] is False
        assert "Password too weak" in result["message"]
        assert "Email invalid" in result["message"]


class TestSignupWorkflowIntegration:
    """Integration tests for complete signup workflow."""
    
    @pytest.mark.asyncio
    async def test_complete_signup_success(self):
        """Test complete signup workflow with valid data."""
        input_state = {
            "email": "newuser@example.com",
            "username": "newuser",
            "password": "SecureP@ss123",
            "firstname": "New",
            "lastname": "User",
            "validation_errors": [],
            "user_id": None,
            "success": False,
            "message": ""
        }
        
        mock_user = MagicMock(spec=User)
        mock_user.id = "user_new123"
        
        with patch('src.app.agent.workflows.signup_workflow.user_repository.get_user_by_email', new=AsyncMock(return_value=None)), \
             patch('src.app.agent.workflows.signup_workflow.user_repository.get_user_by_username', new=AsyncMock(return_value=None)), \
             patch('src.app.agent.workflows.signup_workflow.user_repository.create_user', new=AsyncMock(return_value=mock_user)):
            
            result = await signup_workflow.ainvoke(input_state)
            
        assert result["success"] is True
        assert result["user_id"] == "user_new123"
        assert "successfully" in result["message"]
    
    @pytest.mark.asyncio
    async def test_complete_signup_validation_failure(self):
        """Test complete signup workflow with validation errors."""
        input_state = {
            "email": "invalid-email",
            "username": "a",
            "password": "weak",
            "firstname": "",
            "lastname": "",
            "validation_errors": [],
            "user_id": None,
            "success": False,
            "message": ""
        }
        
        result = await signup_workflow.ainvoke(input_state)
        
        assert result["success"] is False
        assert len(result["validation_errors"]) > 0
        assert result["user_id"] is None
