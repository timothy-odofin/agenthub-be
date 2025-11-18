from typing import Any, Callable, Dict

from app.core.config import AppConfig
from app.core.constants import EmbeddingType
from app.core.utils.logger import get_logger

logger = get_logger(__name__)

class EmbeddingFactory:
    """Factory for creating and caching embedding models."""

    _registry: Dict[EmbeddingType, Callable[[Dict[str, Any]], Any]] = {}

    @classmethod
    def register(cls, name):
        """Decorator for registering embedding creators."""
        def decorator(func: Callable[[Dict[str, Any]], Any]):
            cls._registry[name] = func
            return func
        return decorator

    @classmethod
    def get_embedding_model(cls, embedding_type: EmbeddingType, config:AppConfig):
        """Get or create an embedding model by type."""

        if embedding_type not in cls._registry:
            raise ValueError(f"Unsupported embedding type: {embedding_type}")

        logger.info(f"Creating new embedding model for type: {embedding_type}")
        try:
            embedding_model = cls._registry[embedding_type](config.embedding_config)
            return embedding_model
        except Exception as e:
            logger.error(f"Failed to initialize {embedding_type} embedding: {e}")
            raise
