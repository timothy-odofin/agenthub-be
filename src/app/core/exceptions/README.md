# Exception Hierarchy Documentation

## Overview

This directory contains a comprehensive exception hierarchy for AgentHub following industry best practices from:
- **Google** (gRPC error codes, structured logging)
- **Microsoft** (ASP.NET Core exception policies)
- **AWS** (boto3 error handling)
- **Stripe/Twilio** (API error response standards)

## Exception Hierarchy

```
BaseAppException
├── ClientError (4xx - client's fault)
│   ├── ValidationError (400)
│   ├── AuthenticationError (401)
│   ├── AuthorizationError (403)
│   ├── NotFoundError (404)
│   ├── ConflictError (409)
│   ├── RateLimitError (429)
│   └── BadRequestError (400)
│
├── ServerError (5xx - server's fault)
│   ├── InternalError (500)
│   ├── ServiceUnavailableError (503)
│   ├── ConfigurationError (500)
│   └── TimeoutError (504)
│
└── ExternalServiceError (503 - dependency failed)
    ├── DatabaseError
    ├── CacheError
    ├── QueueError
    ├── VectorDBError
    └── ThirdPartyAPIError

Domain-Specific Exceptions:
├── AgentError (500)
├── SessionError (500)
├── WorkflowError (500)
├── LLMError (500/503)
├── FileOperationError (500)
├── PromptError (500)
└── EmbeddingError (500)
```

## Usage Examples

### Basic Exception Raising

```python
from src.app.core.exceptions import (
    ValidationError,
    NotFoundError,
    DatabaseError,
    AgentError,
)

# Validation error with field details
raise ValidationError(
    message="Invalid email format",
    field="email",
    constraint="Must be a valid email address"
)

# Resource not found
raise NotFoundError(
    message="User not found",
    resource_type="user",
    resource_id="usr_123"
)

# Database error with context
raise DatabaseError(
    message="Failed to connect to MongoDB",
    database="agenthub",
    operation="find_one",
    internal_details={"collection": "sessions", "timeout": 5000}
)

# Agent error with operation context
raise AgentError(
    message="Agent execution failed",
    agent_id="agent_abc123",
    operation="execute_workflow",
    internal_details={"workflow": "signup", "step": "validate_input"}
)
```

### Exception Properties

Every exception includes:

```python
exception = ValidationError(
    message="Invalid input",
    field="email",
    error_code="INVALID_EMAIL",  # Optional: overrides default
    details={"expected": "email format"},  # Safe for client
    internal_details={"raw_value": "user@"},  # Internal only, never exposed
    request_id="req_7fK3x9mP2qL8"  # Added by middleware
)

# Access properties
exception.status_code         # 400
exception.error_code          # "INVALID_EMAIL"
exception.error_type          # "validation_error"
exception.message             # "Invalid input"
exception.details             # {"field": "email", "expected": "email format"}
exception.internal_details    # {"raw_value": "user@"}
exception.request_id          # "req_7fK3x9mP2qL8"
exception.timestamp           # datetime object

# Convert to API response (sanitized)
exception.to_dict()
# {
#   "error": {
#     "type": "validation_error",
#     "code": "INVALID_EMAIL",
#     "message": "Invalid input",
#     "details": {"field": "email", "expected": "email format"},
#     "request_id": "req_7fK3x9mP2qL8",
#     "timestamp": "2025-01-08T10:30:45.123Z"
#   }
# }

# Get full context for logging (includes internal details)
exception.get_log_context()
# {
#   "error_type": "validation_error",
#   "error_code": "INVALID_EMAIL",
#   "message": "Invalid input",
#   "status_code": 400,
#   "details": {"field": "email", "expected": "email format"},
#   "internal_details": {"raw_value": "user@"},
#   "request_id": "req_7fK3x9mP2qL8",
#   "timestamp": "2025-01-08T10:30:45.123"
# }
```

## Error Categories

### 1. Client Errors (4xx)

**When to use:** Client sent invalid data or made a mistake.

**Logging level:** INFO or WARN (not our fault)

```python
# Validation errors
raise ValidationError("Invalid email", field="email")

# Authentication failures
raise AuthenticationError("Invalid credentials")

# Permission denied
raise AuthorizationError("Access denied", resource="admin_panel")

# Resource not found
raise NotFoundError("User not found", resource_type="user")

# Duplicate resource
raise ConflictError("Email already exists")

# Rate limiting
raise RateLimitError("Too many requests", retry_after=60)
```

### 2. Server Errors (5xx)

**When to use:** Server-side issue (bug, misconfiguration, timeout).

**Logging level:** ERROR (our fault, needs investigation)

```python
# Unexpected errors
raise InternalError("Unexpected error occurred")

# Service down
raise ServiceUnavailableError("Service under maintenance", retry_after=300)

# Configuration issues
raise ConfigurationError("Missing API key", config_key="OPENAI_API_KEY")

# Timeouts
raise TimeoutError("Operation timed out", timeout_seconds=30, operation="llm_call")
```

### 3. External Service Errors

**When to use:** Third-party dependency failed (database, cache, API).

**Logging level:** WARN or ERROR depending on severity

```python
# Database failures
raise DatabaseError("MongoDB connection failed", database="agenthub", operation="connect")

# Cache failures
raise CacheError("Redis connection lost", operation="get")

# Queue failures
raise QueueError("Celery task failed", queue_name="agent_tasks", operation="enqueue")

# Vector DB failures
raise VectorDBError("Qdrant search failed", operation="search", collection="documents")

# Third-party API failures
raise ThirdPartyAPIError(
    "Confluence API error",
    api_name="confluence",
    status_code=503,
    endpoint="/api/v2/pages"
)
```

### 4. Domain-Specific Errors

**When to use:** Business logic failures specific to AgentHub.

**Logging level:** ERROR

```python
# Agent errors
raise AgentError(
    "Agent failed to process request",
    agent_id="agent_123",
    operation="execute_workflow"
)

# Session errors
raise SessionError(
    "Session expired",
    session_id="sess_456",
    operation="retrieve"
)

# Workflow errors
raise WorkflowError(
    "Workflow validation failed",
    workflow_name="signup",
    step="validate_email"
)

# LLM errors
raise LLMError(
    "LLM generation failed",
    provider="openai",
    model="gpt-4",
    operation="generate_response"
)

# File operation errors
raise FileOperationError(
    "Failed to read config file",
    file_path="/path/to/config.yaml",
    operation="read"
)

# Prompt errors
raise PromptError(
    "Prompt template not found",
    prompt_name="signup_welcome",
    operation="load"
)

# Embedding errors
raise EmbeddingError(
    "Failed to generate embeddings",
    model="text-embedding-ada-002",
    operation="embed"
)
```

## Best Practices

### 1. Choose the Right Exception Type

```python
# ❌ BAD: Generic exception
raise Exception("Something went wrong")

# ✅ GOOD: Specific exception
raise ValidationError("Invalid email format", field="email")
```

### 2. Provide Context (But Sanitize!)

```python
# ❌ BAD: Exposing sensitive data
raise DatabaseError(f"Connection failed: postgres://admin:password@localhost:5432/db")

# ✅ GOOD: Sanitized message, sensitive data in internal_details
raise DatabaseError(
    "Database connection failed",
    database="agenthub",
    internal_details={"connection_string": "postgres://admin:***@localhost:5432/db"}
)
```

### 3. Use Details for Client-Safe Info

```python
# ✅ GOOD: Client can see safe context
raise NotFoundError(
    "User not found",
    resource_type="user",  # Goes to details (safe)
    details={"searched_by": "email"},  # Explicitly safe
    internal_details={"email": "user@example.com"}  # Never exposed to client
)
```

### 4. Separate Client Details from Internal Details

```python
raise DatabaseError(
    message="Database operation failed",
    details={
        # Safe for client to see
        "operation": "fetch_user"
    },
    internal_details={
        # Only for internal logs
        "query": "SELECT * FROM users WHERE email = ...",
        "execution_time_ms": 1250,
        "connection_pool_size": 10
    }
)
```

### 5. Use Request IDs (Added by Middleware)

```python
# In exception handler or middleware, add request_id
exception.request_id = request_id

# Client sees:
# "Request failed. Please contact support with request ID: req_7fK3x9mP2qL8"
```

## Migration Guide

### Replacing Existing Exceptions

**Old code (file_utils.py):**
```python
class FileReadError(Exception):
    pass

raise FileReadError(f"Error reading file: {e}")
```

**New code:**
```python
from src.app.core.exceptions import FileOperationError

raise FileOperationError(
    message="Failed to read configuration file",
    file_path=file_path,  # Goes to internal_details
    operation="read",
    internal_details={"error": str(e)}
)
```

**Old code (prompt.py):**
```python
class PromptConfigError(Exception):
    pass

raise PromptConfigError(f"Prompt not found: {name}")
```

**New code:**
```python
from src.app.core.exceptions import PromptError

raise PromptError(
    message="Prompt template not found",
    prompt_name=name,
    operation="load"
)
```

**Old code (direct HTTPException):**
```python
from fastapi import HTTPException

raise HTTPException(status_code=404, detail="User not found")
```

**New code:**
```python
from src.app.core.exceptions import NotFoundError

raise NotFoundError(
    message="User not found",
    resource_type="user",
    resource_id=user_id
)
```

## Error Response Format

All exceptions return a consistent JSON format:

```json
{
  "error": {
    "type": "validation_error",
    "code": "INVALID_EMAIL_FORMAT",
    "message": "The email address format is invalid",
    "request_id": "req_7fK3x9mP2qL8",
    "timestamp": "2025-01-08T10:30:45.123Z",
    "details": {
      "field": "email",
      "constraint": "Must be a valid email address"
    }
  }
}
```

**Note:** `internal_details` are NEVER included in API responses. They're only used for logging.

## Next Steps

After implementing this exception hierarchy:

1. ✅ **Exception hierarchy created** (Step 1 - Done!)
2. ⏭️ **Implement global exception handlers** in `main.py`
3. ⏭️ **Add exception middleware** for request ID tracking
4. ⏭️ **Migrate existing code** to use new exceptions
5. ⏭️ **Add structured logging** integration
6. ⏭️ **Implement retry/circuit breaker decorators**
7. ⏭️ **Add error metrics** (Prometheus/DataDog)
8. ⏭️ **Integrate error monitoring** (Sentry/Rollbar)

## Questions?

For implementation questions or additions to the hierarchy, refer to:
- `/docs/ERROR_HANDLING_STRATEGY.md` - Overall strategy
- `/docs/LOGGING_GUIDE.md` - Logging best practices
- `/docs/MONITORING.md` - Observability setup
