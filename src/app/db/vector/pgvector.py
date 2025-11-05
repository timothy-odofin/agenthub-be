"""
PostgreSQL with pgvector implementation of VectorDB.
"""
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

import asyncpg
from langchain.schema import Document
from langchain_postgres import PGVector
from langchain_postgres.vectorstores import DistanceStrategy

from .providers.db_provider import VectorDBRegistry
from ...core.constants import EmbeddingType, VectorDBType
from ...core.config import config
from ..repositories.pgvector_repo import PgVectorRepository
from .base import VectorDB
from app.db.vector.embeddings.embedding import EmbeddingFactory

@VectorDBRegistry.register(VectorDBType.PGVECTOR)
class PgVectorDB(VectorDB):
    """PostgreSQL with pgvector implementation."""

    def __init__(self):
        super().__init__()
        self._repo: Optional[PgVectorRepository] = None

    def get_vector_db_config(self) -> Dict[str, Any]:
        return config.pgvector_config

    async def _create_connection(self):
        self._connection = await asyncpg.connect(self.config["connection_string"])
        self._repo = PgVectorRepository(self._connection)
        await self._repo.create_collection(
            self.config["collection_name"],
            self.config.get("embedding_dimension", 1536)
        )
        return self._connection

    async def _close_connection(self):
        if self._connection:
            await self._connection.close()
            self._connection = None
            self._repo = None

    def _get_embeddings(self, embedding_type: EmbeddingType):
        embedding_model = EmbeddingFactory.get_embedding_model(embedding_type, config)
        distance_strategy_mapping = {
            "cosine": DistanceStrategy.COSINE,
            "euclidean": DistanceStrategy.EUCLIDEAN,
            "inner_product": DistanceStrategy.MAX_INNER_PRODUCT
        }
        return PGVector(
            connection_string=self.config["connection_string"],
            embedding_function=embedding_model,
            collection_name=self.config["collection_name"],
            distance_strategy=distance_strategy_mapping.get(self.config["distance_strategy"], DistanceStrategy.COSINE),
            pre_delete_collection=self.config["pre_delete_collection"]
        )

    async def save_and_embed(self, embedding_type: EmbeddingType, docs: List[Document]) -> List[str]:
        embedding_model = EmbeddingFactory.get_embedding_model(embedding_type)
        ids, embeddings, enhanced_docs = [], [], []

        for doc in docs:
            doc_id = str(uuid.uuid4())
            metadata = {**doc.metadata, 'embedded_at': datetime.now().isoformat(), 'document_id': doc_id}
            enhanced_docs.append(Document(page_content=doc.page_content, metadata=metadata))
            embeddings.append(embedding_model.embed_query(doc.page_content))
            ids.append(doc_id)

        await self._repo.add_documents(self.config["collection_name"], enhanced_docs, embeddings, ids)
        return ids

    async def update_document(self, document_id: str, updated_doc: Document, embedding_type: EmbeddingType) -> bool:
        embedding_model = EmbeddingFactory.get_embedding_model(embedding_type)
        new_embedding = embedding_model.embed_query(updated_doc.page_content)
        enhanced_doc = Document(
            page_content=updated_doc.page_content,
            metadata={**updated_doc.metadata, "document_id": document_id, "updated_at": datetime.now().isoformat()}
        )
        return await self._repo.update_document(self.config["collection_name"], document_id, enhanced_doc,
                                                new_embedding)

    async def delete_by_document_id(self, document_id: str) -> bool:
        return await self._repo.delete_document(self.config["collection_name"], document_id)

    async def get_document_metadata(self, document_id: str):
        return await self._repo.get_document_metadata(self.config["collection_name"], document_id)

    async def search_similar(self, query: str, k: int = 5, filter_criteria: Optional[Dict[str, Any]] = None) -> List[
        Document]:
        embedding_model = EmbeddingFactory.get_embedding_model(EmbeddingType.OPENAI, config)
        query_embedding = embedding_model.embed_query(query)
        return await self._repo.search_similar(self.config["collection_name"], query_embedding, k=k,
                                               filter_criteria=filter_criteria)

    def as_retriever(self, embedding_type: EmbeddingType, **kwargs):
        embedding_model = self._get_embeddings(embedding_type)
        vector_store = PGVector(
            connection_string=self.config["connection_string"],
            collection_name=self.config["collection_name"],
            embedding_function=embedding_model
        )
        return vector_store.as_retriever(**kwargs)

