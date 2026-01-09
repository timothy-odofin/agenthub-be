"""
Global Exception Handler Test

This script tests the global exception handlers by making requests
to a test FastAPI application with various error scenarios.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from fastapi import FastAPI, Request
from fastapi.testclient import TestClient
from fastapi.exceptions import RequestValidationError
from pydantic import BaseModel

from app.core.middleware import RequestContextMiddleware
from app.core.handlers import (
    base_app_exception_handler,
    validation_error_handler,
    http_exception_handler,
    generic_exception_handler,
)
from app.core.exceptions import (
    BaseAppException,
    ValidationError,
    AuthenticationError,
    NotFoundError,
    DatabaseError,
    InternalError,
)
from starlette.exceptions import HTTPException as StarletteHTTPException


# Create test app
app = FastAPI(title="Test App")

# Add middleware
app.add_middleware(RequestContextMiddleware)

# Register exception handlers
app.add_exception_handler(BaseAppException, base_app_exception_handler)
app.add_exception_handler(RequestValidationError, validation_error_handler)
app.add_exception_handler(StarletteHTTPException, http_exception_handler)
app.add_exception_handler(Exception, generic_exception_handler)


# Test models
class UserCreate(BaseModel):
    email: str
    password: str
    age: int


# Test endpoints
@app.get("/test/validation-error")
def test_validation_error():
    """Test ValidationError (custom exception)"""
    raise ValidationError(
        message="Invalid email format",
        field="email",
        constraint="Must be a valid email"
    )


@app.get("/test/authentication-error")
def test_authentication_error():
    """Test AuthenticationError"""
    raise AuthenticationError(
        message="Invalid credentials provided"
    )


@app.get("/test/not-found")
def test_not_found():
    """Test NotFoundError"""
    raise NotFoundError(
        message="User not found",
        resource_type="user",
        resource_id="usr_123"
    )


@app.get("/test/database-error")
def test_database_error():
    """Test DatabaseError (external service)"""
    raise DatabaseError(
        message="Failed to connect to MongoDB",
        database="agenthub",
        operation="find_one",
        internal_details={
            "host": "localhost:27017",
            "collection": "users"
        }
    )


@app.get("/test/http-exception")
def test_http_exception():
    """Test standard HTTPException"""
    raise StarletteHTTPException(status_code=404, detail="Resource not found")


@app.get("/test/unhandled-exception")
def test_unhandled_exception():
    """Test unhandled generic exception"""
    # This simulates an unexpected error
    result = 1 / 0  # ZeroDivisionError


@app.post("/test/pydantic-validation")
def test_pydantic_validation(user: UserCreate):
    """Test Pydantic validation error"""
    return {"message": "User created"}


@app.get("/test/success")
def test_success():
    """Test successful response with request ID"""
    return {"message": "Success", "data": {"id": 123}}


# Test client
client = TestClient(app)


def print_response(name: str, response):
    """Pretty print test response"""
    print(f"\n{'='*70}")
    print(f"Test: {name}")
    print(f"{'='*70}")
    print(f"Status Code: {response.status_code}")
    print(f"Headers:")
    print(f"  X-Request-ID: {response.headers.get('X-Request-ID', 'Not Present')}")
    print(f"\nResponse Body:")
    import json
    print(json.dumps(response.json(), indent=2))


def run_tests():
    """Run all exception handler tests"""
    print("\n" + "🔥"*35)
    print("GLOBAL EXCEPTION HANDLER TESTS")
    print("🔥"*35)
    
    # Test 1: Custom ValidationError
    response = client.get("/test/validation-error")
    print_response("ValidationError (Custom Exception)", response)
    assert response.status_code == 400
    assert "error" in response.json()
    assert response.json()["error"]["type"] == "validation_error"
    assert "request_id" in response.json()["error"]
    
    # Test 2: AuthenticationError
    response = client.get("/test/authentication-error")
    print_response("AuthenticationError", response)
    assert response.status_code == 401
    assert response.json()["error"]["type"] == "authentication_error"
    
    # Test 3: NotFoundError
    response = client.get("/test/not-found")
    print_response("NotFoundError", response)
    assert response.status_code == 404
    assert response.json()["error"]["type"] == "not_found_error"
    assert "resource_type" in response.json()["error"]["details"]
    
    # Test 4: DatabaseError (ExternalServiceError)
    response = client.get("/test/database-error")
    print_response("DatabaseError (External Service)", response)
    assert response.status_code == 503
    assert response.json()["error"]["type"] == "database_error"
    # Verify internal_details are NOT exposed
    assert "host" not in str(response.json())
    assert "collection" not in str(response.json())
    
    # Test 5: Standard HTTPException
    response = client.get("/test/http-exception")
    print_response("HTTPException (Legacy)", response)
    assert response.status_code == 404
    assert response.json()["error"]["type"] == "client_error"
    
    # Test 6: Unhandled Exception (ZeroDivisionError)
    response = client.get("/test/unhandled-exception")
    print_response("Unhandled Exception (ZeroDivisionError)", response)
    assert response.status_code == 500
    assert response.json()["error"]["type"] == "internal_error"
    # Verify internal details are NOT exposed
    assert "ZeroDivisionError" not in response.json()["error"]["message"]
    
    # Test 7: Pydantic Validation Error
    response = client.post("/test/pydantic-validation", json={"email": "not-an-email"})
    print_response("Pydantic Validation Error", response)
    assert response.status_code == 400
    assert "validation_errors" in response.json()["error"]["details"]
    
    # Test 8: Success with Request ID
    response = client.get("/test/success")
    print_response("Successful Request", response)
    assert response.status_code == 200
    assert "X-Request-ID" in response.headers
    
    # Test 9: Request ID Propagation
    print(f"\n{'='*70}")
    print("Test: Request ID Propagation")
    print(f"{'='*70}")
    
    # Send request with custom request ID
    custom_request_id = "req_custom_12345"
    response = client.get(
        "/test/validation-error",
        headers={"X-Request-ID": custom_request_id}
    )
    print(f"Sent Request ID: {custom_request_id}")
    print(f"Response Request ID: {response.json()['error']['request_id']}")
    assert response.json()["error"]["request_id"] == custom_request_id
    print("✅ Request ID propagated correctly")
    
    # Verify response headers
    print(f"\n{'='*70}")
    print("VERIFICATION SUMMARY")
    print(f"{'='*70}")
    print("\n✅ All tests passed!")
    print("\nKey Features Verified:")
    print("  ✅ All exceptions return uniform error format")
    print("  ✅ Request IDs generated automatically")
    print("  ✅ Request IDs propagated from headers")
    print("  ✅ Request IDs included in error responses")
    print("  ✅ HTTP status codes mapped correctly")
    print("  ✅ Internal details hidden from clients")
    print("  ✅ Pydantic validation errors formatted")
    print("  ✅ Unhandled exceptions caught and formatted")
    print("  ✅ Legacy HTTPException handled")
    print("\n" + "="*70)


if __name__ == "__main__":
    run_tests()
