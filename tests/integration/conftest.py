"""
Test configuration and fixtures for integration tests.

Provides comprehensive test fixtures for all integration test categories:
- Core system testing (configuration, utilities)
- Infrastructure testing (databases, external services)  
- API testing (endpoints, middleware)
- Service testing (business logic integration)
- Workflow testing (end-to-end scenarios)

Supports both real dependencies for integration tests and mocked dependencies
for isolated testing when appropriate.
"""
import os
import sys
import pytest
import uuid
import asyncio
import tempfile
import shutil
from pathlib import Path
from typing import Generator, AsyncGenerator, Dict, Any
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


# ===== CORE TEST FIXTURES =====

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


# ===== CORE CONFIGURATION FIXTURES =====

@pytest.fixture(scope="function")
def temp_config_dir() -> Generator[Path, None, None]:
    """Create temporary directory for configuration testing."""
    with tempfile.TemporaryDirectory() as temp_dir:
        config_path = Path(temp_dir)
        yield config_path


@pytest.fixture(scope="function")
def test_config_files(temp_config_dir: Path) -> Generator[Dict[str, Path], None, None]:
    """Create test configuration files in temporary directory."""
    config_files = {}
    
    # Main application config
    app_config = temp_config_dir / "application.yaml"
    app_config.write_text("""
app:
  name: "AgentHub Test"
  version: "test-1.0"
  environment: "test"
  debug: true

database:
  host: "localhost"
  port: 27017
  name: "agenthub_test"

api:
  host: "127.0.0.1"
  port: 8000
  cors_origins:
    - "http://localhost:3000"
    - "http://127.0.0.1:3000"
""")
    config_files["application"] = app_config
    
    # LLM config
    llm_config = temp_config_dir / "llm.yaml"
    llm_config.write_text("""
llm:
  providers:
    openai:
      enabled: true
      api_key: "${OPENAI_API_KEY:-test-key}"
      models:
        - name: "gpt-3.5-turbo"
          max_tokens: 4096
        - name: "gpt-4"
          max_tokens: 8192
    anthropic:
      enabled: false
      api_key: "${ANTHROPIC_API_KEY}"
  
  default_model: "gpt-3.5-turbo"
  max_retries: 3
  timeout: 30
""")
    config_files["llm"] = llm_config
    
    # Database config
    db_config = temp_config_dir / "database.yaml"
    db_config.write_text("""
mongodb:
  uri: "${MONGODB_URI:-mongodb://localhost:27017}"
  database: "${MONGODB_DATABASE:-agenthub_test}"
  collections:
    sessions: "sessions"
    messages: "messages"
  
redis:
  host: "${REDIS_HOST:-localhost}"
  port: ${REDIS_PORT:-6379}
  db: ${REDIS_DB:-0}
  
postgres:
  host: "${POSTGRES_HOST:-localhost}"
  port: ${POSTGRES_PORT:-5432}
  database: "${POSTGRES_DB:-agenthub_test}"
  username: "${POSTGRES_USER:-test}"
  password: "${POSTGRES_PASSWORD:-test}"
""")
    config_files["database"] = db_config
    
    yield config_files


@pytest.fixture(scope="function")
def test_env_vars() -> Generator[Dict[str, str], None, None]:
    """Set up test environment variables."""
    test_vars = {
        "OPENAI_API_KEY": "test-openai-key",
        "ANTHROPIC_API_KEY": "test-anthropic-key",
        "MONGODB_URI": "mongodb://localhost:27017",
        "MONGODB_DATABASE": "agenthub_test",
        "REDIS_HOST": "localhost",
        "REDIS_PORT": "6379",
        "REDIS_DB": "0",
        "APP_ENVIRONMENT": "test",
        "APP_DEBUG": "true"
    }
    
    # Store original values
    original_vars = {}
    for key, value in test_vars.items():
        original_vars[key] = os.environ.get(key)
        os.environ[key] = value
    
    yield test_vars
    
    # Restore original values
    for key, original_value in original_vars.items():
        if original_value is None:
            os.environ.pop(key, None)
        else:
            os.environ[key] = original_value


@pytest.fixture(scope="function")
def isolated_settings(temp_config_dir: Path, test_config_files: Dict[str, Path], test_env_vars: Dict[str, str]):
    """Provide isolated Settings instance for testing."""
    from app.core.config.settings import Settings
    
    # Create isolated Settings instance with test config directory
    with patch.dict(os.environ, test_env_vars):
        settings = Settings(config_dir=str(temp_config_dir))
        # Force reload to pick up test configs
        settings._config_cache.clear()
        yield settings


@pytest.fixture(scope="function")
def mock_property_resolver():
    """Provide mock PropertyResolver for testing."""
    from unittest.mock import Mock
    
    resolver = Mock()
    resolver.resolve.side_effect = lambda value, context=None: value
    resolver.resolve_nested.side_effect = lambda data, context=None: data
    yield resolver


# ===== API TESTING FIXTURES =====

@pytest.fixture(scope="function")
def fastapi_test_client():
    """Create FastAPI test client for API integration tests."""
    import httpx
    from app.main import app
    
    # Use httpx.AsyncClient for async testing
    transport = httpx.ASGITransport(app=app)
    
    async def create_test_client():
        return httpx.AsyncClient(transport=transport, base_url="http://testserver")
    
    return create_test_client


# ===== DATABASE FIXTURES =====

@pytest.fixture(scope="function")
async def mongodb_session_repository(test_database_name: str, test_user_prefix: str):
    """Create real MongoDB session repository for integration testing."""
    from app.db.session_repository import SessionRepository
    from app.core.config.database_config import DatabaseConfig
    
    # Create database config with test database
    db_config = DatabaseConfig()
    db_config.mongodb.database = test_database_name
    
    # Initialize repository
    repository = SessionRepository(db_config)
    await repository.connect()
    
    yield repository
    
    # Cleanup
    await MongoDBTestMixin.cleanup_test_data(
        repository, 
        test_user_prefix, 
        test_database_name
    )
    
    # Disconnect
    if hasattr(repository, '_client') and repository._client:
        repository._client.close()


# ===== SERVICE TESTING FIXTURES =====

@pytest.fixture(scope="function")
def mock_external_services():
    """Mock external services for testing."""
    from unittest.mock import Mock, AsyncMock
    
    services = {
        'jira': Mock(),
        'confluence': Mock(),
        'github': Mock(),
        'slack': Mock()
    }
    
    # Configure mocks with common async methods
    for service_name, service_mock in services.items():
        service_mock.connect = AsyncMock(return_value=True)
        service_mock.disconnect = AsyncMock()
        service_mock.health_check = AsyncMock(return_value={"status": "healthy"})
    
    yield services
