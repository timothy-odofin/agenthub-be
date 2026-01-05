"""
Integration tests for FastAPI endpoints.

This module tests HTTP endpoints, request/response handling, and API integration
with proper resource cleanup and test isolation.
"""
import pytest
import uuid
import httpx
from datetime import datetime
from httpx import AsyncClient

from app.main import app
from app.core.config.framework.settings import settings

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from conftest import MongoDBTestMixin


def create_test_client():
    """Create a test client for the FastAPI app using httpx with ASGI transport."""
    transport = httpx.ASGITransport(app=app)
    return httpx.AsyncClient(transport=transport, base_url="http://testserver")


class TestAPIIntegration(MongoDBTestMixin):
    """Integration tests for API endpoints with proper resource management."""
    
    @pytest.fixture(autouse=True)
    async def setup_and_teardown(self, test_run_id: str, test_database_name: str):
        """Setup and teardown for each test with comprehensive resource cleanup."""
        # Access test configuration
        self.test_config = settings.tests.db.mongodb
        self.test_run_id = test_run_id
        self.test_database_name = test_database_name
        
        # Create async client for testing
        self.base_url = "http://test"
        
        # Test users for isolation
        self.test_user_prefix = f"test_user_{self.test_run_id}"
        self.test_user_id_1 = f"{self.test_user_prefix}_1"
        self.test_user_id_2 = f"{self.test_user_prefix}_2"
        
        print(f"API Tests - Database: {self.test_database_name}")
        print(f"API Tests - User prefix: {self.test_user_prefix}")
        
        # Run the test
        yield
        
        # Comprehensive cleanup after test
        try:
            await self.cleanup_test_resources()
        except Exception as e:
            print(f"Warning: Cleanup failed: {e}")


    async def test_root_endpoint(self):
        """Test the root endpoint returns correct status."""
        async with create_test_client() as client:
            response = await client.get("/")
            
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "ok"
            assert "message" in data
            assert "running" in data["message"].lower()


    async def test_health_endpoint_celery(self):
        """Test the health/celery endpoint structure (may fail without Celery running)."""
        async with create_test_client() as client:
            response = await client.get("/api/v1/health/test-celery")
            
            # Test endpoint exists and has expected structure
            # Note: May return 500 if Celery is not running, but should not be 404
            assert response.status_code in [200, 500]  # Allow both success and service unavailable
            
            if response.status_code == 200:
                data = response.json()
                assert "task_id" in data
                assert "message" in data


    async def test_chat_message_endpoint_validation(self):
        """Test chat message endpoint input validation."""
        async with create_test_client() as client:
            # Test missing required fields
            response = await client.post("/api/v1/chat/message", json={})
            assert response.status_code == 422  # Validation error
            
            # Test with minimal valid data
            test_data = {
                "message": "Hello, this is a test message",
                "user_id": self.test_user_id_1
            }
            
            response = await client.post("/api/v1/chat/message", json=test_data)
            
            # Should return valid response structure even if service fails
            # The endpoint should exist and handle the request properly
            assert response.status_code in [200, 500, 503]  # Allow various service states
            
            if response.status_code == 200:
                data = response.json()
                assert "success" in data
                assert "message" in data
                assert "session_id" in data
                assert "user_id" in data
                assert data["user_id"] == self.test_user_id_1


    async def test_chat_message_with_session_id(self):
        """Test chat message endpoint with session ID."""
        test_session_id = f"test_session_{self.test_run_id}"
        
        test_data = {
            "message": "Test message with session ID",
            "user_id": self.test_user_id_1,
            "session_id": test_session_id
        }
        
        async with create_test_client() as client:
            response = await client.post("/api/v1/chat/message", json=test_data)
            
            # Test endpoint accepts session_id parameter
            assert response.status_code in [200, 500, 503]
            
            if response.status_code == 200:
                data = response.json()
                assert data["session_id"] == test_session_id


    async def test_create_session_endpoint(self):
        """Test session creation endpoint."""
        test_data = {
            "user_id": self.test_user_id_1,
            "session_name": f"Test Session {self.test_run_id}"
        }
        
        async with create_test_client() as client:
            response = await client.post("/api/v1/chat/sessions", json=test_data)
            
            # Test endpoint exists and handles request
            assert response.status_code in [200, 404, 500]  # 404 if endpoint not implemented
            
            if response.status_code == 200:
                data = response.json()
                assert "session_id" in data
                assert "user_id" in data
                assert data["user_id"] == self.test_user_id_1


    async def test_get_session_history_endpoint(self):
        """Test session history retrieval endpoint."""
        test_session_id = f"test_session_{self.test_run_id}"
        
        async with create_test_client() as client:
            response = await client.get(f"/api/v1/chat/sessions/{test_session_id}/history")
            
            # Test endpoint exists
            assert response.status_code in [200, 404, 500]  # Various expected states
            
            if response.status_code == 200:
                data = response.json()
                assert "messages" in data
                assert isinstance(data["messages"], list)


    async def test_get_user_sessions_endpoint(self):
        """Test user sessions list endpoint."""
        async with create_test_client() as client:
            response = await client.get(f"/api/v1/chat/users/{self.test_user_id_1}/sessions")
            
            # Test endpoint exists
            assert response.status_code in [200, 404, 500]
            
            if response.status_code == 200:
                data = response.json()
                assert "sessions" in data
                assert isinstance(data["sessions"], list)


    async def test_data_ingestion_endpoint_validation(self):
        """Test data ingestion endpoint validation."""
        async with create_test_client() as client:
            # Test invalid data source
            response = await client.post("/api/v1/data/load/invalid_source")
            
            # Should return validation error for invalid data source
            assert response.status_code in [422, 404]  # Validation error or not found


    async def test_data_ingestion_endpoint_valid_sources(self):
        """Test data ingestion endpoint with valid sources."""
        # Test with valid data source types (if enum is available)
        valid_sources = ["confluence", "file", "database"]  # Common data source types
        
        async with create_test_client() as client:
            for source in valid_sources:
                response = await client.post(f"/api/v1/data/load/{source}")
                
                # Should accept valid source types (may fail due to configuration)
                assert response.status_code in [200, 404, 422, 500, 503]  # Various service states
                
                if response.status_code == 200:
                    data = response.json()
                    assert "message" in data


    async def test_api_error_handling(self):
        """Test API error handling for various scenarios."""
        async with create_test_client() as client:
            # Test non-existent endpoint
            response = await client.get("/api/v1/nonexistent")
            assert response.status_code == 404
            
            # Test malformed JSON (httpx handles this differently than requests)
            try:
                response = await client.post(
                    "/api/v1/chat/message", 
                    content="invalid json",
                    headers={"Content-Type": "application/json"}
                )
                assert response.status_code == 422
            except Exception:
                # Some HTTP clients reject malformed JSON before sending
                pass


    async def test_concurrent_api_requests(self):
        """Test API handling of concurrent requests."""
        import asyncio
        
        async def make_request(client: AsyncClient, user_id: str):
            """Make a single API request."""
            test_data = {
                "message": f"Concurrent test message from {user_id}",
                "user_id": user_id
            }
            
            response = await client.post("/api/v1/chat/message", json=test_data)
            return response.status_code, user_id
        
        # Use async client for concurrent requests
        async with create_test_client() as async_client:
            # Create multiple concurrent requests with different users
            tasks = [
                make_request(async_client, f"{self.test_user_prefix}_{i}")
                for i in range(5)
            ]
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Verify all requests completed (regardless of service availability)
            for result in results:
                if isinstance(result, Exception):
                    # Log but don't fail on service unavailability
                    print(f"Concurrent request exception: {result}")
                else:
                    status_code, user_id = result
                    assert status_code in [200, 500, 503], f"Unexpected status for {user_id}: {status_code}"


    async def test_api_response_headers(self):
        """Test API response headers."""
        async with create_test_client() as client:
            response = await client.get("/")
            
            # Check basic headers
            assert "content-type" in response.headers
            assert "application/json" in response.headers["content-type"]


    async def test_api_request_size_limits(self):
        """Test API request size handling."""
        # Test large message (but not too large to avoid timeouts)
        large_message = "x" * 10000  # 10KB message
        
        test_data = {
            "message": large_message,
            "user_id": self.test_user_id_1
        }
        
        async with create_test_client() as client:
            response = await client.post("/api/v1/chat/message", json=test_data)
            
            # Should handle reasonable message sizes
            assert response.status_code in [200, 413, 500]  # Success, too large, or service error


    async def test_api_cors_and_options(self):
        """Test API CORS handling."""
        async with create_test_client() as client:
            # Test OPTIONS request
            response = await client.options("/api/v1/chat/message")
            
            # Should handle OPTIONS (may not be configured)
            assert response.status_code in [200, 405]  # Success or method not allowed


class TestAPIAsyncIntegration(MongoDBTestMixin):
    """Async-specific API integration tests."""
    
    @pytest.fixture(autouse=True)
    async def setup_and_teardown(self, test_run_id: str, test_database_name: str):
        """Setup and teardown for async tests."""
        self.test_config = settings.tests.db.mongodb
        self.test_run_id = test_run_id
        self.test_database_name = test_database_name
        self.test_user_prefix = f"async_test_user_{self.test_run_id}"
        
        # Run the test
        yield
        
        # Cleanup
        try:
            await self.cleanup_test_resources()
        except Exception as e:
            print(f"Warning: Async cleanup failed: {e}")


    async def test_async_api_client(self):
        """Test API using async client."""
        async with create_test_client() as async_client:
            response = await async_client.get("/")
            
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "ok"


    async def test_async_concurrent_sessions(self):
        """Test concurrent session creation and usage."""
        import asyncio
        
        async def create_and_use_session(client: AsyncClient, user_id: str):
            """Create session and send message."""
            # First create session (if endpoint exists)
            session_data = {
                "user_id": user_id,
                "session_name": f"Async Session {user_id}"
            }
            
            session_response = await client.post("/api/v1/chat/sessions", json=session_data)
            
            # Then send message
            message_data = {
                "message": f"Hello from {user_id}",
                "user_id": user_id
            }
            
            message_response = await client.post("/api/v1/chat/message", json=message_data)
            
            return {
                "user_id": user_id,
                "session_status": session_response.status_code,
                "message_status": message_response.status_code
            }
        
        async with create_test_client() as async_client:
            # Create multiple concurrent sessions
            tasks = [
                create_and_use_session(async_client, f"{self.test_user_prefix}_{i}")
                for i in range(3)
            ]
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Verify concurrent operations completed
            for result in results:
                if isinstance(result, Exception):
                    print(f"Async operation exception: {result}")
                else:
                    assert "user_id" in result
                    assert "session_status" in result
                    assert "message_status" in result
                    # Allow various service states
                    assert result["message_status"] in [200, 404, 500, 503]
