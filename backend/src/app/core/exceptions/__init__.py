"""
Exception Hierarchy for AgentHub Backend

This module provides a comprehensive exception hierarchy following industry best practices
from Google (gRPC error codes), Microsoft (ASP.NET Core), and AWS (boto3 error handling).

Exception Hierarchy:
    BaseAppException
    ├── ClientError (4xx - client's fault)
    │   ├── ValidationError
    │   ├── AuthenticationError
    │   ├── AuthorizationError
    │   ├── NotFoundError
    │   ├── ConflictError
    │   └── RateLimitError
    ├── ServerError (5xx - server's fault)
    │   ├── InternalError
    │   ├── ServiceUnavailableError
    │   └── ConfigurationError
    └── ExternalServiceError (dependencies failed)
        ├── DatabaseError
        ├── CacheError
        ├── QueueError
        ├── VectorDBError
        └── ThirdPartyAPIError

Domain-Specific Exceptions:
    ├── AgentError
    ├── SessionError
    ├── WorkflowError
    ├── LLMError
    └── FileOperationError
"""

from .base import BaseAppException, ClientError, ExternalServiceError, ServerError
from .client_errors import (
    AuthenticationError,
    AuthorizationError,
    BadRequestError,
    ConflictError,
    NotFoundError,
    RateLimitError,
    ValidationError,
)
from .domain_errors import (
    AgentError,
    EmbeddingError,
    FileOperationError,
    LLMError,
    PromptError,
    SessionError,
    WorkflowError,
)
from .external_errors import (
    CacheError,
    DatabaseError,
    QueueError,
    ThirdPartyAPIError,
    VectorDBError,
)
from .server_errors import (
    ConfigurationError,
    InternalError,
    ServiceUnavailableError,
    TimeoutError,
)

__all__ = [
    # Base exceptions
    "BaseAppException",
    "ClientError",
    "ServerError",
    "ExternalServiceError",
    # Client errors (4xx)
    "ValidationError",
    "AuthenticationError",
    "AuthorizationError",
    "NotFoundError",
    "ConflictError",
    "RateLimitError",
    "BadRequestError",
    # Server errors (5xx)
    "InternalError",
    "ServiceUnavailableError",
    "ConfigurationError",
    "TimeoutError",
    # External service errors
    "DatabaseError",
    "CacheError",
    "QueueError",
    "VectorDBError",
    "ThirdPartyAPIError",
    # Domain-specific errors
    "AgentError",
    "SessionError",
    "WorkflowError",
    "LLMError",
    "FileOperationError",
    "PromptError",
    "EmbeddingError",
]
