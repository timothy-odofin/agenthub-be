"""
Embedding model factory and management.
"""
from typing import Dict, Any
from langchain_openai import OpenAIEmbeddings
from langchain_community.embeddings import (
    HuggingFaceEmbeddings,
    HuggingFaceInstructEmbeddings,
    CohereEmbeddings
)

from ...core.constants import EmbeddingType
from ...core.config import config
from ...core.utils.logger import get_logger

logger = get_logger(__name__)


class EmbeddingFactory:
    """Factory for creating and caching embedding models."""
    
    _embedding_cache: Dict[EmbeddingType, Any] = {}
    
    @classmethod
    def get_embedding_model(cls, embedding_type: EmbeddingType):
        """Get or create embedding model based on type."""
        logger.debug(f"Requesting embedding model of type: {embedding_type}")
        
        if embedding_type in cls._embedding_cache:
            logger.debug(f"Found cached embedding model for type: {embedding_type}")
            return cls._embedding_cache[embedding_type]
        
        logger.info(f"Creating new embedding model for type: {embedding_type}")
        embedding_config = config.embedding_config
        
        try:
            if embedding_type == EmbeddingType.OPENAI_EMBEDDING:
                logger.debug("Initializing OpenAI embeddings")
                embedding_model = OpenAIEmbeddings(
                    openai_api_key=embedding_config['openai_api_key'],
                    model=embedding_config['openai_model']
                )
            elif embedding_type == EmbeddingType.HUGGINGFACE:
                logger.debug("Initializing HuggingFace embeddings")
                embedding_model = HuggingFaceEmbeddings(
                    model_name=embedding_config['huggingface_model'],
                    model_kwargs={'device': embedding_config['device']},
                    encode_kwargs={'batch_size': embedding_config['batch_size']}
                )
            elif embedding_type == EmbeddingType.INSTRUCTOR:
                logger.debug("Initializing Instructor embeddings")
                embedding_model = HuggingFaceInstructEmbeddings(
                    model_name=embedding_config['instructor_model'],
                    model_kwargs={'device': embedding_config['device']},
                    encode_kwargs={'batch_size': embedding_config['batch_size']}
                )
            elif embedding_type == EmbeddingType.COHERE:
                logger.debug("Initializing Cohere embeddings")
                embedding_model = CohereEmbeddings(
                    cohere_api_key=embedding_config.get('cohere_api_key')
                )
            else:
                msg = f"Unsupported embedding type: {embedding_type}"
                logger.error(msg)
                raise ValueError(msg)
            
            logger.info(f"Successfully initialized {embedding_type} embedding model")
            cls._embedding_cache[embedding_type] = embedding_model
            return embedding_model
            
        except Exception as e:
            logger.error(f"Failed to initialize {embedding_type} embedding model: {str(e)}")
            raise
    
    @classmethod
    def clear_cache(cls):
        """Clear the embedding model cache."""
        logger.info("Clearing embedding model cache")
        cache_size = len(cls._embedding_cache)
        cls._embedding_cache.clear()
        logger.debug(f"Cleared {cache_size} cached embedding models")
