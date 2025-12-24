"""
Test configuration and fixtures for integration tests.
Provides both real MongoDB and mock MongoDB fixtures for different testing needs.
"""
import os
import sys
import pytest
import uuid
import asyncio
from pathlib import Path
from typing import Generator, AsyncGenerator
from unittest.mock import patch

# Add the src directory to the Python path for imports
src_path = Path(__file__).parent.parent.parent / "src"
sys.path.insert(0, str(src_path))

# Try to import mongomock for unit testing
try:
    import mongomock
    MONGOMOCK_AVAILABLE = True
except ImportError:
    MONGOMOCK_AVAILABLE = False

# Ensure environment variables are set for testing
if "MONGODB_URI" not in os.environ:
    # Default to localhost MongoDB - adjust if needed
    os.environ["MONGODB_URI"] = "mongodb://localhost:27017"

if "MONGODB_DATABASE" not in os.environ:
    # Use test database name
    os.environ["MONGODB_DATABASE"] = "polyagent_sessions_test"

# Set test-specific environment variables
if "TEST_MONGODB_URI" not in os.environ:
    os.environ["TEST_MONGODB_URI"] = "mongodb://localhost:27017"

if "TEST_MONGODB_DATABASE" not in os.environ:
    os.environ["TEST_MONGODB_DATABASE"] = "agenthub_test"


@pytest.fixture(scope="function")
def test_run_id() -> str:
    """Generate unique test run identifier for resource isolation."""
    return uuid.uuid4().hex[:8]


@pytest.fixture(scope="function") 
def test_database_name(test_run_id: str) -> str:
    """Generate unique test database name."""
    return f"agenthub_test_{test_run_id}"


@pytest.fixture(scope="function")
def test_user_prefix(test_run_id: str) -> str:
    """Generate unique test user prefix."""
    return f"test_user_{test_run_id}"


@pytest.fixture(scope="function")
def mock_mongodb_client():
    """Provide in-memory MongoDB client for unit testing."""
    if not MONGOMOCK_AVAILABLE:
        pytest.skip("mongomock not available, install with: pip install mongomock")
    
    client = mongomock.MongoClient()
    yield client
    # Automatic cleanup - mongomock is in-memory, no persistence


@pytest.fixture(scope="function") 
def mock_mongodb_database(mock_mongodb_client, test_database_name: str):
    """Provide in-memory MongoDB database for unit testing."""
    database = mock_mongodb_client[test_database_name]
    yield database
    # Cleanup handled by client fixture


class MongoDBTestMixin:
    """Mixin class providing common MongoDB testing utilities."""
    
    @staticmethod
    async def cleanup_test_data(repository, user_prefix: str, database_name: str = None):
        """Utility method for cleaning up test data."""
        try:
            if not hasattr(repository, '_sessions_collection') or not repository._sessions_collection:
                return
                
            # Get session IDs for cleanup
            def get_session_ids():
                cursor = repository._sessions_collection.find({
                    "user_id": {"$regex": f"^{user_prefix}"}
                }, {"session_id": 1})
                return [session["session_id"] for session in cursor]
            
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as executor:
                session_ids = await asyncio.get_event_loop().run_in_executor(
                    executor, get_session_ids
                )
            
            # Delete messages first
            if session_ids and hasattr(repository, '_messages_collection'):
                def delete_messages():
                    return repository._messages_collection.delete_many({
                        "session_id": {"$in": session_ids}
                    })
                
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    message_result = await asyncio.get_event_loop().run_in_executor(
                        executor, delete_messages
                    )
                    print(f"✓ Cleaned up {message_result.deleted_count} test messages")
            
            # Delete sessions
            def delete_sessions():
                return repository._sessions_collection.delete_many({
                    "user_id": {"$regex": f"^{user_prefix}"}
                })
            
            with concurrent.futures.ThreadPoolExecutor() as executor:
                session_result = await asyncio.get_event_loop().run_in_executor(
                    executor, delete_sessions
                )
                print(f"✓ Cleaned up {session_result.deleted_count} test sessions")
                
            # Drop entire test database if specified
            if database_name and hasattr(repository, '_database'):
                def drop_database():
                    client = repository._database.client
                    client.drop_database(database_name)
                
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    await asyncio.get_event_loop().run_in_executor(
                        executor, drop_database
                    )
                    print(f"✓ Dropped test database: {database_name}")
                    
        except Exception as e:
            print(f"Warning: Could not clean up test data: {e}")
    
    @staticmethod
    def generate_test_session_data(test_suffix: str = "") -> dict:
        """Generate test session data."""
        return {
            'title': f'Test Chat Session {test_suffix}',
            'metadata': {
                'test': True,
                'integration': True,
                'test_id': uuid.uuid4().hex[:8]
            }
        }
    
    @staticmethod
    def generate_test_user_id(prefix: str, suffix: str = "") -> str:
        """Generate test user ID with prefix."""
        return f"{prefix}_{suffix}" if suffix else prefix
