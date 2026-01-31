"""
External Service Error Exceptions

These exceptions represent errors from external dependencies (databases, caches, APIs, etc.).
They should be logged at WARN or ERROR level and may trigger circuit breakers or retry logic.
"""

from typing import Any, Dict, Optional
from .base import ExternalServiceError


class DatabaseError(ExternalServiceError):
    """
    Raised when database operations fail (connection issues, query errors, etc.).
    HTTP Status: 503 Service Unavailable
    """
    
    status_code: int = 503
    error_code: str = "DATABASE_ERROR"
    error_type: str = "database_error"
    
    def __init__(
        self,
        message: str = "Database operation failed",
        database: Optional[str] = None,
        operation: Optional[str] = None,
        **kwargs
    ):
        internal_details = kwargs.get("internal_details", {})
        if database:
            internal_details["database"] = database
        if operation:
            internal_details["operation"] = operation
        
        kwargs["internal_details"] = internal_details
        super().__init__(
            message=message,
            service_name=database or "database",
            **kwargs
        )


class CacheError(ExternalServiceError):
    """
    Raised when cache operations fail (Redis connection issues, etc.).
    HTTP Status: 503 Service Unavailable
    """
    
    status_code: int = 503
    error_code: str = "CACHE_ERROR"
    error_type: str = "cache_error"
    
    def __init__(
        self,
        message: str = "Cache operation failed",
        operation: Optional[str] = None,
        **kwargs
    ):
        internal_details = kwargs.get("internal_details", {})
        if operation:
            internal_details["operation"] = operation
        
        kwargs["internal_details"] = internal_details
        super().__init__(
            message=message,
            service_name="redis",
            **kwargs
        )


class QueueError(ExternalServiceError):
    """
    Raised when message queue operations fail (RabbitMQ, Celery, etc.).
    HTTP Status: 503 Service Unavailable
    """
    
    status_code: int = 503
    error_code: str = "QUEUE_ERROR"
    error_type: str = "queue_error"
    
    def __init__(
        self,
        message: str = "Queue operation failed",
        queue_name: Optional[str] = None,
        operation: Optional[str] = None,
        **kwargs
    ):
        internal_details = kwargs.get("internal_details", {})
        if queue_name:
            internal_details["queue_name"] = queue_name
        if operation:
            internal_details["operation"] = operation
        
        kwargs["internal_details"] = internal_details
        super().__init__(
            message=message,
            service_name="queue",
            **kwargs
        )


class VectorDBError(ExternalServiceError):
    """
    Raised when vector database operations fail (Qdrant, Pinecone, etc.).
    HTTP Status: 503 Service Unavailable
    """
    
    status_code: int = 503
    error_code: str = "VECTOR_DB_ERROR"
    error_type: str = "vector_db_error"
    
    def __init__(
        self,
        message: str = "Vector database operation failed",
        operation: Optional[str] = None,
        collection: Optional[str] = None,
        **kwargs
    ):
        internal_details = kwargs.get("internal_details", {})
        if operation:
            internal_details["operation"] = operation
        if collection:
            internal_details["collection"] = collection
        
        kwargs["internal_details"] = internal_details
        super().__init__(
            message=message,
            service_name="vector_db",
            **kwargs
        )


class ThirdPartyAPIError(ExternalServiceError):
    """
    Raised when third-party API calls fail (Atlassian, Slack, etc.).
    HTTP Status: 502 Bad Gateway or 503 Service Unavailable
    """
    
    status_code: int = 502
    error_code: str = "THIRD_PARTY_API_ERROR"
    error_type: str = "third_party_api_error"
    
    def __init__(
        self,
        message: str = "Third-party API call failed",
        api_name: Optional[str] = None,
        status_code: Optional[int] = None,
        endpoint: Optional[str] = None,
        **kwargs
    ):
        internal_details = kwargs.get("internal_details", {})
        if status_code:
            internal_details["api_status_code"] = status_code
        if endpoint:
            internal_details["endpoint"] = endpoint
        
        kwargs["internal_details"] = internal_details
        super().__init__(
            message=message,
            service_name=api_name or "third_party_api",
            **kwargs
        )
