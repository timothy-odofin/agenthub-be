"""
Embedding model factory and management.
"""
from typing import Dict, Any

from langchain_community.embeddings import (
    OpenAIEmbeddings, 
    HuggingFaceEmbeddings,
    HuggingFaceInstructEmbeddings,
    CohereEmbeddings
)

from ...core.constants import EmbeddingType
from ...core.config import config


class EmbeddingFactory:
    """Factory for creating and caching embedding models."""
    
    _embedding_cache: Dict[EmbeddingType, Any] = {}
    
    @classmethod
    def get_embedding_model(cls, embedding_type: EmbeddingType):
        """Get or create embedding model based on type."""
        if embedding_type in cls._embedding_cache:
            return cls._embedding_cache[embedding_type]
        
        embedding_config = config.embedding_config
        
        if embedding_type == EmbeddingType.OPENAI_EMBEDDING:
            embedding_model = OpenAIEmbeddings(
                openai_api_key=embedding_config['openai_api_key'],
                model=embedding_config['openai_model']
            )
        elif embedding_type == EmbeddingType.HUGGINGFACE:
            embedding_model = HuggingFaceEmbeddings(
                model_name=embedding_config['huggingface_model'],
                model_kwargs={'device': embedding_config['device']},
                encode_kwargs={'batch_size': embedding_config['batch_size']}
            )
        elif embedding_type == EmbeddingType.INSTRUCTOR:
            embedding_model = HuggingFaceInstructEmbeddings(
                model_name=embedding_config['instructor_model'],
                model_kwargs={'device': embedding_config['device']},
                encode_kwargs={'batch_size': embedding_config['batch_size']}
            )
        elif embedding_type == EmbeddingType.COHERE:
            embedding_model = CohereEmbeddings(
                cohere_api_key=embedding_config.get('cohere_api_key')
            )
        else:
            raise ValueError(f"Unsupported embedding type: {embedding_type}")
        
        cls._embedding_cache[embedding_type] = embedding_model
        return embedding_model
    
    @classmethod
    def clear_cache(cls):
        """Clear the embedding model cache."""
        cls._embedding_cache.clear()
