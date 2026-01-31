from enum import Enum
from typing import Optional

from app.core.constants import VectorDBType
from app.core.utils.logger import get_logger
from app.db.vector import VectorDB

logger = get_logger(__name__)

class VectorDBRegistry:
    """Central registry that keeps track of all available Vector Database providers."""
    _registry = {}

    @classmethod
    def register(cls, name):
        """Decorator to register a class under a given name."""
        def decorator(processor_cls):
            cls._registry[name] = processor_cls
            logger.debug(f"Registered vector DB provider: {name}")
            return processor_cls
        return decorator

    @classmethod
    def get_class(cls, name):
        """Get a registered processor class by name."""
        if name not in cls._registry:
            raise ValueError(f"Processor '{name}' not found in registry. Available: {list(cls._registry.keys())}")
        return cls._registry[name]

    @classmethod
    def all_processors(cls):
        """List all registered processors."""
        return list(cls._registry.keys())


class VectorStoreFactory:
    """Factory class for creating vector store instances."""

    _instance: Optional['VectorStoreFactory'] = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    @staticmethod
    def get_vector_store(name: VectorDBType, **kwargs) -> VectorDB:
        """Instantiate a registered processor by name."""
        processor_cls = VectorDBRegistry.get_class(name)
        if processor_cls:
            return processor_cls(**kwargs)
        raise ValueError(f"Unsupported vector database type: {name}")

    @classmethod
    def get_default_vector_store(cls) -> VectorDB:
        """Get the default vector store."""
        return cls.get_vector_store(VectorDBType.QDRANT)
