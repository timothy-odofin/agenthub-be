"""
Configuration management package.

This package provides domain-separated configuration classes for better
organization and maintainability, plus centralized default configuration management.

The package is now organized into:
- framework/: Core configuration framework (Settings, DynamicConfig, etc.)
- providers/: Infrastructure provider configurations (database, vector, external)
- application/: Application-specific configurations (app, llm)
- utils/: Configuration utilities and helpers
"""

# Import from reorganized structure
from .framework import Settings, settings, DynamicConfig, YamlLoader
from .providers import database_config, vector_config, external_services_config
from .application import app_config, llm_config

# Backward compatibility imports - maintain existing import paths
from .providers.database import database_config
from .providers.vector import vector_config
from .providers.external import external_services_config
from .application.app import app_config
from .application.llm import llm_config

# Backward compatibility - create a unified config object
class UnifiedConfig:
    """Unified configuration object for backward compatibility."""
    
    def __init__(self):
        self.app = app_config
        self.database = database_config
        self.vector = vector_config
        self.external = external_services_config
        self.llm = llm_config
        # self.session = session_config  # Future addition example
    
    # Backward compatibility properties
    @property
    def postgres_config(self):
        return self.database.postgres_config
    
    @property
    def redis_config(self):
        return self.database.redis_config
    
    @property
    def qdrant_config(self):
        return self.vector.qdrant_config
    
    @property
    def pgvector_config(self):
        return self.vector.pgvector_config
    
    @property
    def chromadb_config(self):
        return self.vector.chromadb_config
    
    @property
    def chroma_config(self):
        return self.vector.chroma_config
    
    @property
    def pinecone_config(self):
        return self.vector.pinecone_config
    
    @property
    def weaviate_config(self):
        return self.vector.weaviate_config
    
    @property
    def milvus_config(self):
        return self.vector.milvus_config
    
    @property
    def opensearch_config(self):
        return self.vector.opensearch_config
    
    @property
    def embedding_config(self):
        return self.vector.embedding_config
    
    @property
    def atlassian_config(self):
        return self.external.atlassian_config
    
    @property
    def llm_config(self):
        return self.llm.llm_config
    
    # App config properties
    @property
    def app_env(self):
        return self.app.app_env
    
    @property
    def debug(self):
        return self.app.debug
    
    @property
    def project_root(self):
        return self.app.project_root
    
    @property
    def resources_path(self):
        return self.app.resources_path
    
    @property
    def ingestion_config_path(self):
        return self.app.ingestion_config_path
    
    @property
    def ingestion_config(self):
        return self.app.ingestion_config
    
    def reload_ingestion_config(self):
        return self.app.reload_ingestion_config()


# Create the unified config instance for backward compatibility
config = UnifiedConfig()

# Export both new modular configs, unified config, and settings system
__all__ = [
    'app_config',
    'database_config', 
    'vector_config',
    'external_services_config',
    'llm_config',
    'config',  # Backward compatibility
    'Settings',  # New profile-based settings system
    'settings',  # Module-level instance for convenience
    'DynamicConfig',
    'YamlLoader',
]
