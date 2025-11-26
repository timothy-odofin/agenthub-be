"""
Constants used throughout the application.
"""
from enum import Enum

# Re-export enums for backward compatibility
from app.core.enums import (
    DataSourceType,
    ModelProvider,
    VectorDBType,
    DatabaseType,
    ExternalServiceType,
    ConnectionType
)


class VectorDBType(str, Enum):
    """Supported vector database types."""
    PGVECTOR = "pgvector"
    CHROMA = "chroma"
    QDRANT = "qdrant"
    MILVUS = "milvus"
    REDIS = "redis"
    OPENSEARCH = "opensearch"


class GroqModelVersion(str, Enum):
    """Supported Groq model versions.
    Reference: https://console.groq.com/docs/models
    """
    # Production Models
    LLAMA_3_1_8B = "llama-3.1-8b-instant"
    LLAMA_3_3_70B = "llama-3.3-70b-versatile"
    LLAMA_GUARD_12B = "meta-llama/llama-guard-4-12b"
    GPT_OSS_120B = "openai/gpt-oss-120b"
    GPT_OSS_20B = "openai/gpt-oss-20b"
    WHISPER_LARGE_V3 = "whisper-large-v3"
    WHISPER_LARGE_V3_TURBO = "whisper-large-v3-turbo"
    
    # Preview Models (Not recommended for production)
    DEEPSEEK_70B = "deepseek-r1-distill-llama-70b"
    LLAMA_4_MAVERICK = "meta-llama/llama-4-maverick-17b-128e-instruct"
    LLAMA_4_SCOUT = "meta-llama/llama-4-scout-17b-16e-instruct"
    KIMI_K2 = "moonshotai/kimi-k2-instruct"
    QWEN_32B = "qwen/qwen3-32b"


class EmbeddingType(str, Enum):
    """Supported embedding types and their models."""
    OPENAI = "openai"  # For OpenAI ada-002
    HUGGINGFACE = "huggingface"  # For sentence-transformers, BGE, etc.
    INSTRUCTOR = "instructor"     # For instructor models
    COHERE = "cohere"           # For Cohere embeddings
    TENSORFLOW = "tensorflow"    # For TensorFlow Hub models
    VERTEX = "vertex"           # For Google Cloud Vertex AI embeddings
    DEFAULT = "openai"  # Application default embedding


class ModelProvider(str, Enum):
    """Supported model providers."""
    GROQ = "groq"
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    GOOGLE = "google"
    META = "meta"
    MISTRAL = "mistral"

class AtlassianProperties(str, Enum):
    """Atlassian properties used for metadata."""
    PAGE_ID = "page_id"
    TITLE = "title"
    SPACE_KEY = "space_key"
    JIRA_BASE_URL = "jira_base_url"
    CONFLUENCE_BASE_URL = "confluence_base_url"
    LAST_MODIFIED = "last_modified"
    AUTHOR = "author"
    API_KEY = "api_key"
    EMAIL = "email"

class SessionStorageType(str, Enum):
    """Supported session storage types."""
    POSTGRES = "postgres"
    MONGODB = "mongodb"
    ELASTICSEARCH = "elasticsearch"
    REDIS = "redis"


class LLMProvider(str, Enum):
    """Supported LLM providers for the platform."""
    GROQ = "groq"
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    HUGGINGFACE = "huggingface"
    OLLAMA = "ollama"
    GOOGLE = "google"
    LOCAL = "local"


class LLMCapability(str, Enum):
    """LLM capabilities for dynamic selection."""
    CHAT = "chat"
    CODE_GENERATION = "code_generation"
    FUNCTION_CALLING = "function_calling"
    STREAMING = "streaming"
    MULTIMODAL = "multimodal"