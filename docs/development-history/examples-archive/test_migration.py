"""
Test script to verify Step 3 migration is successful.

This script tests that:
1. Authentication errors use AuthenticationError (not HTTPException)
2. Service errors use ServiceUnavailableError/InternalError
3. Request IDs are properly tracked
4. Error responses are uniform
"""

import sys
import asyncio
from datetime import datetime

# Mock request object for testing
class MockRequest:
    class State:
        request_id = "req_test_123"
    
    state = State()


async def test_authentication_errors():
    """Test that authentication errors are properly raised."""
    print("\n" + "="*60)
    print("TEST 1: Authentication Error Handling")
    print("="*60)
    
    try:
        from app.core.security.dependencies import get_current_user
        from app.core.exceptions import AuthenticationError
        
        # Test with no credentials (should raise AuthenticationError)
        try:
            request = MockRequest()
            await get_current_user(request, credentials=None)
            print("❌ FAILED: Should have raised AuthenticationError")
            return False
        except AuthenticationError as e:
            print("✅ AuthenticationError raised correctly")
            print(f"   Message: {e.message}")
            print(f"   Request ID: {e.request_id}")
            print(f"   Error Code: {e.error_code}")
            
            # Verify error format
            error_dict = e.to_dict()
            assert "error" in error_dict
            assert error_dict["error"]["type"] == "authentication_error"
            assert error_dict["error"]["request_id"] == "req_test_123"
            print("✅ Error format is uniform")
            return True
            
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False


async def test_service_errors():
    """Test that service errors use proper exceptions."""
    print("\n" + "="*60)
    print("TEST 2: Service Error Handling")
    print("="*60)
    
    try:
        from app.core.exceptions import ServiceUnavailableError, InternalError
        
        # Test ServiceUnavailableError
        exc = ServiceUnavailableError(
            service_name="test_service",
            message="Service is down",
            request_id="req_test_456"
        )
        
        error_dict = exc.to_dict()
        assert error_dict["error"]["type"] == "service_unavailable_error"
        assert error_dict["error"]["code"] == "SERVICE_UNAVAILABLE"
        assert error_dict["error"]["status_code"] == 503
        print("✅ ServiceUnavailableError format correct")
        
        # Test InternalError
        exc2 = InternalError(
            message="Something went wrong",
            internal_details={"trace": "stack trace here"},
            request_id="req_test_789"
        )
        
        error_dict2 = exc2.to_dict()
        assert error_dict2["error"]["type"] == "internal_error"
        assert "internal_details" not in error_dict2["error"]  # Should be hidden
        print("✅ InternalError format correct (internal_details hidden)")
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_request_id_propagation():
    """Test that request IDs propagate through exceptions."""
    print("\n" + "="*60)
    print("TEST 3: Request ID Propagation")
    print("="*60)
    
    try:
        from app.core.exceptions import ValidationError
        
        test_request_id = "req_propagation_test"
        
        exc = ValidationError(
            message="Invalid input",
            field="email",
            request_id=test_request_id
        )
        
        error_dict = exc.to_dict()
        assert error_dict["error"]["request_id"] == test_request_id
        print(f"✅ Request ID properly propagated: {test_request_id}")
        
        # Test log context
        log_context = exc.get_log_context()
        assert log_context["request_id"] == test_request_id
        assert log_context["error_message"] == "Invalid input"  # Not 'message'
        print("✅ Log context includes request_id and error_message")
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_no_httpexception_in_migrated_files():
    """Verify migrated files don't import HTTPException."""
    print("\n" + "="*60)
    print("TEST 4: No HTTPException in Migrated Files")
    print("="*60)
    
    migrated_files = [
        "src/app/core/security/dependencies.py",
        "src/app/api/v1/chat.py",
    ]
    
    all_clean = True
    for file_path in migrated_files:
        try:
            with open(file_path, 'r') as f:
                content = f.read()
                
            # Check for HTTPException import
            if "from fastapi import" in content and "HTTPException" in content:
                # Check if it's importing HTTPException
                import_lines = [line for line in content.split('\n') if 'from fastapi import' in line]
                has_http_exc = any('HTTPException' in line for line in import_lines)
                
                if has_http_exc:
                    print(f"❌ {file_path} still imports HTTPException")
                    all_clean = False
                else:
                    print(f"✅ {file_path} - No HTTPException import")
            else:
                print(f"✅ {file_path} - No HTTPException import")
                
        except FileNotFoundError:
            print(f"⚠️  {file_path} not found")
    
    return all_clean


async def main():
    """Run all migration tests."""
    print("\n" + "🚀" + "="*58 + "🚀")
    print("   STEP 3 MIGRATION VERIFICATION")
    print("🚀" + "="*58 + "🚀")
    
    results = []
    
    # Run tests
    results.append(("Authentication Errors", await test_authentication_errors()))
    results.append(("Service Errors", await test_service_errors()))
    results.append(("Request ID Propagation", await test_request_id_propagation()))
    results.append(("No HTTPException", await test_no_httpexception_in_migrated_files()))
    
    # Summary
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {test_name}")
    
    print("\n" + "="*60)
    print(f"TOTAL: {passed}/{total} tests passed")
    print("="*60)
    
    if passed == total:
        print("\n🎉 All tests passed! Migration successful! 🎉\n")
        return 0
    else:
        print("\n⚠️  Some tests failed. Please review the output above. ⚠️\n")
        return 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
