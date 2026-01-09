"""
Exception Hierarchy Demo Script

This script demonstrates the usage of the exception hierarchy.
Run this to see how exceptions work before integrating into the main application.
"""

import sys
from pathlib import Path

# Add the src directory to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from app.core.exceptions import (
    # Client errors
    ValidationError,
    AuthenticationError,
    NotFoundError,
    RateLimitError,
    
    # Server errors
    InternalError,
    ServiceUnavailableError,
    ConfigurationError,
    
    # External service errors
    DatabaseError,
    CacheError,
    VectorDBError,
    ThirdPartyAPIError,
    
    # Domain-specific errors
    AgentError,
    SessionError,
    WorkflowError,
    LLMError,
    FileOperationError,
)


def demo_client_errors():
    """Demonstrate client error exceptions."""
    print("\n" + "="*60)
    print("CLIENT ERRORS (4xx) - User's Fault")
    print("="*60)
    
    # Validation error
    try:
        raise ValidationError(
            message="Invalid email format",
            field="email",
            constraint="Must be a valid email address",
            details={"value": "invalid-email"}
        )
    except ValidationError as e:
        print(f"\n✗ ValidationError:")
        print(f"  Status: {e.status_code}")
        print(f"  Code: {e.error_code}")
        print(f"  Message: {e.message}")
        print(f"  API Response: {e.to_dict()}")
    
    # Not found error
    try:
        raise NotFoundError(
            message="User not found",
            resource_type="user",
            resource_id="usr_123"
        )
    except NotFoundError as e:
        print(f"\n✗ NotFoundError:")
        print(f"  Status: {e.status_code}")
        print(f"  Code: {e.error_code}")
        print(f"  Details: {e.details}")


def demo_server_errors():
    """Demonstrate server error exceptions."""
    print("\n" + "="*60)
    print("SERVER ERRORS (5xx) - Our Fault")
    print("="*60)
    
    # Internal error
    try:
        raise InternalError(
            message="Unexpected error in agent execution",
            internal_details={"traceback": "..."}
        )
    except InternalError as e:
        print(f"\n✗ InternalError:")
        print(f"  Status: {e.status_code}")
        print(f"  Code: {e.error_code}")
        print(f"  API Response (no internal details): {e.to_dict()}")
        print(f"  Log Context (with internal details): {e.get_log_context()}")
    
    # Configuration error
    try:
        raise ConfigurationError(
            message="Missing required configuration",
            config_key="OPENAI_API_KEY"
        )
    except ConfigurationError as e:
        print(f"\n✗ ConfigurationError:")
        print(f"  Status: {e.status_code}")
        print(f"  Message: {e.message}")


def demo_external_errors():
    """Demonstrate external service error exceptions."""
    print("\n" + "="*60)
    print("EXTERNAL SERVICE ERRORS - Dependency Failed")
    print("="*60)
    
    # Database error
    try:
        raise DatabaseError(
            message="Failed to connect to MongoDB",
            database="agenthub",
            operation="connect",
            internal_details={
                "host": "localhost",
                "port": 27017,
                "timeout": 5000
            }
        )
    except DatabaseError as e:
        print(f"\n✗ DatabaseError:")
        print(f"  Status: {e.status_code}")
        print(f"  Service: {e.service_name}")
        print(f"  API Response: {e.to_dict()}")
    
    # Third-party API error
    try:
        raise ThirdPartyAPIError(
            message="Confluence API returned error",
            api_name="confluence",
            status_code=503,
            endpoint="/api/v2/pages",
            internal_details={"response_body": "Service unavailable"}
        )
    except ThirdPartyAPIError as e:
        print(f"\n✗ ThirdPartyAPIError:")
        print(f"  Status: {e.status_code}")
        print(f"  Service: {e.service_name}")
        print(f"  Internal Details: {e.internal_details}")


def demo_domain_errors():
    """Demonstrate domain-specific error exceptions."""
    print("\n" + "="*60)
    print("DOMAIN-SPECIFIC ERRORS - Business Logic")
    print("="*60)
    
    # Agent error
    try:
        raise AgentError(
            message="Agent failed to execute workflow",
            agent_id="agent_abc123",
            operation="execute_workflow",
            internal_details={"workflow": "signup", "step": "validate_input"}
        )
    except AgentError as e:
        print(f"\n✗ AgentError:")
        print(f"  Code: {e.error_code}")
        print(f"  Message: {e.message}")
        print(f"  Log Context: {e.get_log_context()}")
    
    # LLM error
    try:
        raise LLMError(
            message="LLM generation timeout",
            provider="openai",
            model="gpt-4",
            operation="generate_response",
            internal_details={"timeout_seconds": 30}
        )
    except LLMError as e:
        print(f"\n✗ LLMError:")
        print(f"  Status: {e.status_code}")
        print(f"  Message: {e.message}")
    
    # Workflow error
    try:
        raise WorkflowError(
            message="Workflow validation failed",
            workflow_name="conversational_signup",
            step="email_validation"
        )
    except WorkflowError as e:
        print(f"\n✗ WorkflowError:")
        print(f"  Code: {e.error_code}")
        print(f"  API Response: {e.to_dict()}")


def demo_request_id_tracking():
    """Demonstrate request ID correlation."""
    print("\n" + "="*60)
    print("REQUEST ID TRACKING - Distributed Tracing")
    print("="*60)
    
    request_id = "req_7fK3x9mP2qL8"
    
    try:
        raise DatabaseError(
            message="Database connection lost",
            database="agenthub",
            operation="find_one",
            request_id=request_id
        )
    except DatabaseError as e:
        print(f"\n✗ Error with Request ID:")
        print(f"  Request ID: {e.request_id}")
        print(f"  API Response includes request_id: {e.to_dict()}")
        print(f"  Client can use this ID to contact support")


def demo_error_hierarchy():
    """Demonstrate exception hierarchy relationships."""
    print("\n" + "="*60)
    print("EXCEPTION HIERARCHY - isinstance() Checks")
    print("="*60)
    
    from app.core.exceptions import (
        BaseAppException,
        ClientError,
        ServerError,
        ExternalServiceError,
    )
    
    validation_err = ValidationError("Invalid input")
    database_err = DatabaseError("Connection failed")
    agent_err = AgentError("Agent failed")
    
    print(f"\nValidationError:")
    print(f"  isinstance(ValidationError) = {isinstance(validation_err, ValidationError)}")
    print(f"  isinstance(ClientError) = {isinstance(validation_err, ClientError)}")
    print(f"  isinstance(BaseAppException) = {isinstance(validation_err, BaseAppException)}")
    
    print(f"\nDatabaseError:")
    print(f"  isinstance(DatabaseError) = {isinstance(database_err, DatabaseError)}")
    print(f"  isinstance(ExternalServiceError) = {isinstance(database_err, ExternalServiceError)}")
    print(f"  isinstance(BaseAppException) = {isinstance(database_err, BaseAppException)}")
    
    print(f"\nAgentError:")
    print(f"  isinstance(AgentError) = {isinstance(agent_err, AgentError)}")
    print(f"  isinstance(ServerError) = {isinstance(agent_err, ServerError)}")
    print(f"  isinstance(BaseAppException) = {isinstance(agent_err, BaseAppException)}")


def demo_logging_levels():
    """Demonstrate recommended logging levels for different error types."""
    print("\n" + "="*60)
    print("RECOMMENDED LOGGING LEVELS")
    print("="*60)
    
    from app.core.exceptions import (
        ClientError,
        ServerError,
        ExternalServiceError,
    )
    
    errors = [
        (ValidationError("Invalid input"), "INFO"),
        (AuthenticationError("Invalid token"), "WARN"),
        (InternalError("Unexpected error"), "ERROR"),
        (DatabaseError("Connection failed"), "ERROR"),
        (ThirdPartyAPIError("API error"), "WARN"),
        (AgentError("Agent failed"), "ERROR"),
    ]
    
    print("\nError Type -> Logging Level:")
    for error, level in errors:
        error_class = error.__class__.__name__
        category = "Client" if isinstance(error, ClientError) else \
                   "Server" if isinstance(error, ServerError) else \
                   "External Service"
        print(f"  {error_class:<30} -> {level:<8} ({category})")


if __name__ == "__main__":
    print("\n" + "🔥"*30)
    print("AGENTHUB EXCEPTION HIERARCHY DEMO")
    print("🔥"*30)
    
    demo_client_errors()
    demo_server_errors()
    demo_external_errors()
    demo_domain_errors()
    demo_request_id_tracking()
    demo_error_hierarchy()
    demo_logging_levels()
    
    print("\n" + "="*60)
    print("✅ Demo completed successfully!")
    print("="*60)
    print("\nNext Steps:")
    print("  1. ✅ Exception hierarchy created")
    print("  2. ⏭️  Implement global exception handlers in main.py")
    print("  3. ⏭️  Add exception middleware for request ID tracking")
    print("  4. ⏭️  Migrate existing code to use new exceptions")
    print("  5. ⏭️  Add structured logging integration")
    print("\n")
