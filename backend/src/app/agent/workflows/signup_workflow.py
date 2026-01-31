"""
LangGraph Signup Workflow.

This module implements a LangGraph-based workflow for user signup with validation.
Follows YAGNI - only what we need for basic signup.

Workflow Steps:
1. validate_email - Check email format and uniqueness
2. validate_username - Check username format, length, and uniqueness  
3. validate_password - Check password strength requirements
4. validate_names - Check firstname and lastname
5. create_user - Create user with hashed password
6. format_response - Return success or error response

Example:
    >>> from app.agent.workflows import signup_workflow
    >>> result = await signup_workflow.ainvoke({
    ...     "email": "user@example.com",
    ...     "username": "johndoe",
    ...     "password": "SecureP@ss123",
    ...     "firstname": "John",
    ...     "lastname": "Doe"
    ... })
"""

import re
from typing import TypedDict, Optional, Dict, Any, List
from langgraph.graph import StateGraph, END

from app.core.utils.logger import get_logger
from app.core.security import password_manager
from app.db.repositories import user_repository
from app.core.config import settings

logger = get_logger(__name__)


class SignupState(TypedDict):
    """
    State for the signup workflow.
    
    Attributes:
        email: User's email address
        username: User's username
        password: User's plain text password (will be hashed)
        firstname: User's first name
        lastname: User's last name
        validation_errors: List of validation errors encountered
        user_id: Created user's ID (set on success)
        success: Whether signup was successful
        message: Success or error message
    """
    email: str
    username: str
    password: str
    firstname: str
    lastname: str
    validation_errors: List[str]  # Plain list of strings, not messages
    user_id: Optional[str]
    success: bool
    message: str


# Load validation config from settings
def get_validation_config() -> Dict[str, Any]:
    """Get validation configuration from application-signup.yaml."""
    try:
        # Try to get workflow config from settings
        workflow_config = settings.get_value("workflows.signup", {})
        if workflow_config:
            return workflow_config.get("validation", {})
    except Exception as e:
        logger.warning(f"Could not load signup workflow config: {e}. Using defaults.")
    
    # Default configuration (YAGNI - matches our simplified YAML)
    return {
        "email": {
            "required": True,
            "pattern": r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
        },
        "username": {
            "required": True,
            "min_length": 3,
            "max_length": 30,
            "pattern": r"^[a-zA-Z0-9_-]+$"
        },
        "password": {
            "required": True,
            "min_length": 8,
            "max_length": 72
        },
        "firstname": {
            "required": True,
            "min_length": 1,
            "max_length": 50
        },
        "lastname": {
            "required": True,
            "min_length": 1,
            "max_length": 50
        }
    }


# Validation nodes
async def validate_email(state: SignupState) -> SignupState:
    """
    Validate email format and check if it's already registered.
    
    Args:
        state: Current signup state
        
    Returns:
        Updated state with validation errors if any
    """
    email = state.get("email", "").strip()
    validation_errors = state.get("validation_errors", [])
    
    if not email:
        validation_errors.append("Email is required")
        return {**state, "validation_errors": validation_errors}
    
    # Check email format
    config = get_validation_config()
    email_pattern = config.get("email", {}).get("pattern", r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$")
    
    if not re.match(email_pattern, email):
        validation_errors.append("Invalid email format")
        return {**state, "validation_errors": validation_errors}
    
    # Check if email already exists
    try:
        existing_user = await user_repository.get_user_by_email(email)
        if existing_user:
            validation_errors.append("Email already registered")
            return {**state, "validation_errors": validation_errors}
    except Exception as e:
        logger.error(f"Error checking email existence: {e}", exc_info=True)
        validation_errors.append("Error validating email")
        return {**state, "validation_errors": validation_errors}
    
    logger.info(f"Email validation passed: {email}")
    return {**state, "validation_errors": validation_errors}


async def validate_username(state: SignupState) -> SignupState:
    """
    Validate username format, length, and uniqueness.
    
    Args:
        state: Current signup state
        
    Returns:
        Updated state with validation errors if any
    """
    username = state.get("username", "").strip()
    validation_errors = state.get("validation_errors", [])
    
    if not username:
        validation_errors.append("Username is required")
        return {**state, "validation_errors": validation_errors}
    
    config = get_validation_config()
    username_config = config.get("username", {})
    
    # Check length
    min_length = username_config.get("min_length", 3)
    max_length = username_config.get("max_length", 30)
    
    if len(username) < min_length:
        validation_errors.append(f"Username must be at least {min_length} characters")
        return {**state, "validation_errors": validation_errors}
    
    if len(username) > max_length:
        validation_errors.append(f"Username must not exceed {max_length} characters")
        return {**state, "validation_errors": validation_errors}
    
    # Check format
    username_pattern = username_config.get("pattern", r"^[a-zA-Z0-9_-]+$")
    if not re.match(username_pattern, username):
        validation_errors.append("Username can only contain letters, numbers, underscores, and hyphens")
        return {**state, "validation_errors": validation_errors}
    
    # Check if username already exists
    try:
        existing_user = await user_repository.get_user_by_username(username)
        if existing_user:
            validation_errors.append("Username already taken")
            return {**state, "validation_errors": validation_errors}
    except Exception as e:
        logger.error(f"Error checking username existence: {e}", exc_info=True)
        validation_errors.append("Error validating username")
        return {**state, "validation_errors": validation_errors}
    
    logger.info(f"Username validation passed: {username}")
    return {**state, "validation_errors": validation_errors}


async def validate_password(state: SignupState) -> SignupState:
    """
    Validate password strength using password_manager.
    
    Args:
        state: Current signup state
        
    Returns:
        Updated state with validation errors if any
    """
    password = state.get("password", "")
    validation_errors = state.get("validation_errors", [])
    
    if not password:
        validation_errors.append("Password is required")
        return {**state, "validation_errors": validation_errors}
    
    # Use password_manager for validation
    is_valid, error_message = password_manager.validate_password_strength(password)
    
    if not is_valid:
        validation_errors.append(error_message)
        return {**state, "validation_errors": validation_errors}
    
    logger.info("Password validation passed")
    return {**state, "validation_errors": validation_errors}


async def validate_names(state: SignupState) -> SignupState:
    """
    Validate firstname and lastname.
    
    Args:
        state: Current signup state
        
    Returns:
        Updated state with validation errors if any
    """
    firstname = state.get("firstname", "").strip()
    lastname = state.get("lastname", "").strip()
    validation_errors = state.get("validation_errors", [])
    
    config = get_validation_config()
    firstname_config = config.get("firstname", {})
    lastname_config = config.get("lastname", {})
    
    # Validate firstname
    if not firstname:
        validation_errors.append("First name is required")
    else:
        min_length = firstname_config.get("min_length", 1)
        max_length = firstname_config.get("max_length", 50)
        
        if len(firstname) < min_length:
            validation_errors.append(f"First name must be at least {min_length} character")
        elif len(firstname) > max_length:
            validation_errors.append(f"First name must not exceed {max_length} characters")
    
    # Validate lastname
    if not lastname:
        validation_errors.append("Last name is required")
    else:
        min_length = lastname_config.get("min_length", 1)
        max_length = lastname_config.get("max_length", 50)
        
        if len(lastname) < min_length:
            validation_errors.append(f"Last name must be at least {min_length} character")
        elif len(lastname) > max_length:
            validation_errors.append(f"Last name must not exceed {max_length} characters")
    
    if not validation_errors or len(validation_errors) == len(state.get("validation_errors", [])):
        logger.info(f"Names validation passed: {firstname} {lastname}")
    
    return {**state, "validation_errors": validation_errors}


def should_create_user(state: SignupState) -> str:
    """
    Decision node: proceed to create user or return error.
    
    Args:
        state: Current signup state
        
    Returns:
        "create_user" if no validation errors, "format_error" otherwise
    """
    validation_errors = state.get("validation_errors", [])
    
    if validation_errors:
        logger.warning(f"Validation failed with {len(validation_errors)} errors")
        return "format_error"
    
    logger.info("All validations passed, proceeding to create user")
    return "create_user"


async def create_user(state: SignupState) -> SignupState:
    """
    Create user with hashed password.
    
    Handles both regular signup (plaintext password) and conversational signup 
    (pre-hashed password from Redis). Checks if password is already hashed 
    to prevent double-hashing issue that breaks login.
    
    Args:
        state: Current signup state
        
    Returns:
        Updated state with user_id on success or error on failure
    """
    try:
        password = state["password"]
        
        # Check if password is already hashed (from conversational signup)
        # Bcrypt hashes always start with $2a$, $2b$, or $2y$ and are 60 chars
        is_already_hashed = (
            password.startswith(("$2a$", "$2b$", "$2y$")) and 
            len(password) == 60
        )
        
        if is_already_hashed:
            # Password already hashed (from conversational signup via Redis)
            logger.info("Password already hashed (conversational signup), skipping hash")
            hashed_password = password
        else:
            # Regular signup - hash the plaintext password
            logger.info("Hashing plaintext password (regular signup)")
            hashed_password = password_manager.hash_password(password)
        
        # Create user
        user = await user_repository.create_user(
            email=state["email"],
            username=state["username"],
            password_hash=hashed_password,
            firstname=state["firstname"],
            lastname=state["lastname"]
        )
        
        logger.info(f"User created successfully: {user.id}")
        
        return {
            **state,
            "user_id": str(user.id),
            "success": True,
            "message": "User registered successfully"
        }
        
    except Exception as e:
        logger.error(f"Error creating user: {e}", exc_info=True)
        return {
            **state,
            "success": False,
            "message": f"Error creating user: {str(e)}"
        }


async def format_error(state: SignupState) -> SignupState:
    """
    Format validation errors into response message.
    
    Args:
        state: Current signup state
        
    Returns:
        Updated state with error message
    """
    validation_errors = state.get("validation_errors", [])
    error_message = "; ".join(validation_errors) if validation_errors else "Validation failed"
    
    return {
        **state,
        "success": False,
        "message": error_message
    }


# Build the workflow graph
def create_signup_workflow() -> StateGraph:
    """
    Create the LangGraph signup workflow.
    
    Returns:
        Compiled StateGraph for signup workflow
    """
    workflow = StateGraph(SignupState)
    
    # Add validation nodes
    workflow.add_node("validate_email", validate_email)
    workflow.add_node("validate_username", validate_username)
    workflow.add_node("validate_password", validate_password)
    workflow.add_node("validate_names", validate_names)
    
    # Add action nodes
    workflow.add_node("create_user", create_user)
    workflow.add_node("format_error", format_error)
    
    # Define the flow
    workflow.set_entry_point("validate_email")
    workflow.add_edge("validate_email", "validate_username")
    workflow.add_edge("validate_username", "validate_password")
    workflow.add_edge("validate_password", "validate_names")
    
    # Conditional edge after validation
    workflow.add_conditional_edges(
        "validate_names",
        should_create_user,
        {
            "create_user": "create_user",
            "format_error": "format_error"
        }
    )
    
    # End nodes
    workflow.add_edge("create_user", END)
    workflow.add_edge("format_error", END)
    
    return workflow.compile()


# Singleton instance - following the same pattern as settings and password_manager
signup_workflow = create_signup_workflow()
