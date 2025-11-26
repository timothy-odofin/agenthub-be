"""
Core enums used throughout the application.
"""
from enum import Enum


class DataSourceType(str, Enum):
    """Supported data sources types for ingestion."""
    S3 = "s3"
    CONFLUENCE = "confluence"
    FILE = "file"
    SHAREPOINT = "sharepoint"
    DATABASE = "database"
    URL = "url"
    WEB = "web"
    JIRA = "jira"


class ModelProvider(str, Enum):
    """Supported LLM providers."""
    OPENAI = "openai"
    AZURE_OPENAI = "azure_openai"
    ANTHROPIC = "anthropic"
    GROQ = "groq"
    HUGGINGFACE = "huggingface"
    GOOGLE = "google"
    OLLAMA = "ollama"


class VectorDBType(str, Enum):
    """Supported vector database types."""
    QDRANT = "qdrant"
    CHROMA = "chroma"
    PGVECTOR = "pgvector"


class DatabaseType(str, Enum):
    """Supported database types."""
    POSTGRESQL = "postgresql"
    REDIS = "redis"


class ExternalServiceType(str, Enum):
    """Supported external service types."""
    CONFLUENCE = "confluence"
    JIRA = "jira"


class ConnectionType(str, Enum):
    """Supported connection types for the connection registry."""
    # Database connections
    POSTGRES = "postgres"
    MONGODB = "mongodb" 
    REDIS = "redis"
    
    # Vector databases
    PGVECTOR = "pgvector"
    CHROMADB = "chromadb"
    QDRANT = "qdrant"
    
    # External services
    CONFLUENCE = "confluence"
    JIRA = "jira"
    
    # Legacy compatibility
    DATABASE = "database"
    VECTOR_DB = "vector_db"
    EXTERNAL_SERVICE = "external_service"
