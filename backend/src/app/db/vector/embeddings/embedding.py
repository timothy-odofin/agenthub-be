from typing import Any, Dict

from langchain_community.embeddings import HuggingFaceEmbeddings, HuggingFaceInstructEmbeddings, CohereEmbeddings
from langchain_openai import OpenAIEmbeddings

from app.core.constants import EmbeddingType
from app.db.vector.providers.embedding_provider import EmbeddingFactory


@EmbeddingFactory.register(EmbeddingType.OPENAI)
def _create_openai_embedding(config: Dict[str, Any]):
    """
    Create OpenAI embedding model.
    
    Args:
        config: Configuration dict from settings.embeddings.openai
        Expected keys: api_key, model
    """
    return OpenAIEmbeddings(
        openai_api_key=config.get("api_key"),
        model=config.get("model", "text-embedding-ada-002")
    )


@EmbeddingFactory.register(EmbeddingType.HUGGINGFACE)
def _create_huggingface_embedding(config: Dict[str, Any]):
    """
    Create HuggingFace embedding model.
    
    Args:
        config: Configuration dict from settings.embeddings.huggingface
        Expected keys: model, device, batch_size
    """
    return HuggingFaceEmbeddings(
        model_name=config.get("model", "sentence-transformers/all-MiniLM-L6-v2"),
        model_kwargs={"device": config.get("device", "cpu")},
        encode_kwargs={"batch_size": config.get("batch_size", 32)}
    )


@EmbeddingFactory.register(EmbeddingType.INSTRUCTOR)
def _create_instructor_embedding(config: Dict[str, Any]):
    """
    Create Instructor embedding model.
    
    Args:
        config: Configuration dict from settings.embeddings.instructor
        Expected keys: model, device, batch_size
    """
    return HuggingFaceInstructEmbeddings(
        model_name=config.get("model", "hkunlp/instructor-xl"),
        model_kwargs={"device": config.get("device", "cpu")},
        encode_kwargs={"batch_size": config.get("batch_size", 32)}
    )


@EmbeddingFactory.register(EmbeddingType.COHERE)
def _create_cohere_embedding(config: Dict[str, Any]):
    """
    Create Cohere embedding model.
    
    Args:
        config: Configuration dict from settings.embeddings.cohere
        Expected keys: api_key
    """
    return CohereEmbeddings(cohere_api_key=config.get("api_key"))