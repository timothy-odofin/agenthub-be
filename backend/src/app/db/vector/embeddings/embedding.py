from typing import Any

from langchain_community.embeddings import HuggingFaceEmbeddings, HuggingFaceInstructEmbeddings, CohereEmbeddings
from langchain_openai import OpenAIEmbeddings

from app.core.constants import EmbeddingType
from app.db.vector.providers.embedding_provider import EmbeddingFactory


@EmbeddingFactory.register(EmbeddingType.OPENAI)
def _create_openai_embedding(config):
    return OpenAIEmbeddings(
        openai_api_key=config["openai_api_key"],
        model=config["openai_model"]
    )

@EmbeddingFactory.register(EmbeddingType.HUGGINGFACE)
def _create_huggingface_embedding(config:dict[str, Any]):
    return HuggingFaceEmbeddings(
        model_name=config["huggingface_model"],
        model_kwargs={"device": config["device"]},
        encode_kwargs={"batch_size": config["batch_size"]}
    )

@EmbeddingFactory.register(EmbeddingType.INSTRUCTOR)
def _create_instructor_embedding(config:dict[str, Any]):
    return HuggingFaceInstructEmbeddings(
        model_name=config["instructor_model"],
        model_kwargs={"device": config["device"]},
        encode_kwargs={"batch_size": config["batch_size"]}
    )

@EmbeddingFactory.register(EmbeddingType.COHERE)
def _create_cohere_embedding(config:dict[str, Any]):
    return CohereEmbeddings(cohere_api_key=config.get("cohere_api_key"))