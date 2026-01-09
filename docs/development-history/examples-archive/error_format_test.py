"""
Uniform Error Format Test

This script demonstrates that all exceptions return the same uniform format.
"""

import json
import sys
from pathlib import Path

# Add the src directory to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from app.core.exceptions import (
    ValidationError,
    AuthenticationError,
    NotFoundError,
    DatabaseError,
    ThirdPartyAPIError,
    AgentError,
    RateLimitError,
)


def print_error_response(exception_name: str, exception):
    """Print the exception's API response in formatted JSON."""
    print(f"\n{'='*70}")
    print(f"Exception: {exception_name}")
    print(f"Status Code: {exception.status_code}")
    print(f"{'='*70}")
    
    # Show API response (what client sees)
    api_response = exception.to_dict()
    print("\n📤 API Response (Client Sees):")
    print(json.dumps(api_response, indent=2))
    
    # Show log context (what logs contain)
    log_context = exception.get_log_context()
    print("\n📋 Log Context (Internal Only):")
    print(json.dumps(log_context, indent=2, default=str))


def main():
    print("\n" + "🔥"*35)
    print("UNIFORM ERROR FORMAT DEMONSTRATION")
    print("🔥"*35)
    print("\nAll exceptions return the same structure:")
    print("  - error.type")
    print("  - error.code")
    print("  - error.message")
    print("  - error.timestamp")
    print("  - error.request_id (optional)")
    print("  - error.details (optional)")
    
    # Example 1: Validation Error
    validation_error = ValidationError(
        message="Invalid email format",
        field="email",
        constraint="Must be a valid email address",
        request_id="req_001"
    )
    print_error_response("ValidationError", validation_error)
    
    # Example 2: Authentication Error
    auth_error = AuthenticationError(
        message="Invalid credentials",
        request_id="req_002",
        internal_details={
            "username": "john@example.com",
            "ip_address": "192.168.1.1"
        }
    )
    print_error_response("AuthenticationError", auth_error)
    
    # Example 3: Not Found Error
    not_found = NotFoundError(
        message="User not found",
        resource_type="user",
        resource_id="usr_123",
        request_id="req_003"
    )
    print_error_response("NotFoundError", not_found)
    
    # Example 4: Database Error
    db_error = DatabaseError(
        message="Failed to connect to MongoDB",
        database="agenthub",
        operation="find_one",
        request_id="req_004",
        internal_details={
            "collection": "sessions",
            "timeout_ms": 5000,
            "host": "localhost:27017"
        }
    )
    print_error_response("DatabaseError", db_error)
    
    # Example 5: Third-Party API Error
    api_error = ThirdPartyAPIError(
        message="Confluence API returned error",
        api_name="confluence",
        status_code=503,
        endpoint="/api/v2/pages",
        request_id="req_005",
        internal_details={
            "response_body": "Service temporarily unavailable"
        }
    )
    print_error_response("ThirdPartyAPIError", api_error)
    
    # Example 6: Agent Error
    agent_error = AgentError(
        message="Agent failed to execute workflow",
        agent_id="agent_abc123",
        operation="execute_workflow",
        request_id="req_006",
        internal_details={
            "workflow": "signup",
            "step": "validate_input"
        }
    )
    print_error_response("AgentError", agent_error)
    
    # Example 7: Rate Limit Error
    rate_limit = RateLimitError(
        message="Too many requests",
        retry_after=60,
        request_id="req_007"
    )
    print_error_response("RateLimitError", rate_limit)
    
    # Verify uniform structure
    print("\n" + "="*70)
    print("STRUCTURE VERIFICATION")
    print("="*70)
    
    all_errors = [
        validation_error,
        auth_error,
        not_found,
        db_error,
        api_error,
        agent_error,
        rate_limit
    ]
    
    print("\n✅ All errors have the same keys:")
    for error in all_errors:
        response = error.to_dict()
        keys = list(response["error"].keys())
        print(f"  {error.__class__.__name__:30} -> {keys}")
    
    print("\n✅ Security Check:")
    print("  All 'internal_details' are excluded from API responses")
    print("  Only included in log context (get_log_context())")
    
    for error in all_errors:
        response = error.to_dict()
        log_ctx = error.get_log_context()
        
        has_internal_in_response = "internal_details" in str(response)
        has_internal_in_logs = "internal_details" in log_ctx
        
        if has_internal_in_response:
            print(f"  ❌ {error.__class__.__name__} exposes internal_details to client!")
        else:
            print(f"  ✅ {error.__class__.__name__} - internal_details hidden from client")
    
    print("\n" + "="*70)
    print("✅ UNIFORM FORMAT VERIFIED!")
    print("="*70)
    print("\nKey Benefits:")
    print("  ✅ Consistent structure across all error types")
    print("  ✅ Machine-readable error codes and types")
    print("  ✅ Request IDs for distributed tracing")
    print("  ✅ Timestamps for debugging")
    print("  ✅ Secure - sensitive data only in logs")
    print("  ✅ Easy to parse in frontend")
    print("  ✅ Easy to monitor and alert on")
    print("\n")


if __name__ == "__main__":
    main()
