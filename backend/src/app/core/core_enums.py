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


# Agent-related enums
class AgentCapability(str, Enum):
    REACT = "react"
    PLANNING = "planning"
    CHAIN_OF_THOUGHT = "chain_of_thought"
    TOOL_CALLING = "tool_calling"
    FUNCTION_CALLING = "function_calling"
    API_INTEGRATION = "api_integration"
    HUMAN_IN_THE_LOOP = "human_in_the_loop"
    APPROVAL_WORKFLOWS = "approval_workflows"
    INTERACTIVE_MODE = "interactive_mode"
    MEMORY_MANAGEMENT = "memory_management"
    CONTEXT_RETRIEVAL = "context_retrieval"
    LONG_TERM_MEMORY = "long_term_memory"
    TIME_TRAVELING = "time_traveling"
    STATE_BRANCHING = "state_branching"
    CONVERSATION_REPLAY = "conversation_replay"
    STREAMING = "streaming"
    ASYNC_PROCESSING = "async_processing"
    MULTI_TURN_CONVERSATION = "multi_turn_conversation"
    CODE_GENERATION = "code_generation"
    DOCUMENT_ANALYSIS = "document_analysis"
    WORKFLOW_ORCHESTRATION = "workflow_orchestration"


class AgentType(str, Enum):
    REACT = "react"
    PLANNING = "planning"
    RESEARCH = "research"
    CODE_ASSISTANT = "code_assistant"
    WORKFLOW = "workflow"
    CUSTOM = "custom"


class AgentFramework(str, Enum):
    LANGCHAIN = "langchain"
    CREWAI = "crewai"
    LANGGRAPH = "langgraph"
    CUSTOM = "custom"


class AgentStatus(str, Enum):
    IDLE = "idle"
    PROCESSING = "processing"
    WAITING_APPROVAL = "waiting_approval"
    WAITING_INPUT = "waiting_input"
    COMPLETED = "completed"
    ERROR = "error"
    CANCELLED = "cancelled"


class CacheType(str, Enum):
    """Supported cache provider types."""
    REDIS = "redis"
    MEMCACHED = "memcached"
    IN_MEMORY = "in_memory"
    ELASTICACHE = "elasticache"
