"""
ChromaDB implementation of VectorDB.
"""
from typing import Any, Dict, List, Optional
from datetime import datetime
import uuid

from langchain.schema import Document
from langchain_community.vectorstores import Chroma

from ...core.constants import EmbeddingType
from ...core.config import config
from .base import VectorDB, DocumentMetadata
from .embedding import EmbeddingFactory

class ChromaDB(VectorDB):
    """ChromaDB implementation."""

    def __init__(self):
        super().__init__()
        self._collection = None

    def get_vector_db_config(self) -> Dict[str, Any]:
        return config.chromadb_config

    async def _create_connection(self):
        # Initialize ChromaDB with persistence
        embedding_model = EmbeddingFactory.get_embedding_model(EmbeddingType.OPENAI_EMBEDDING)
        
        self._collection = Chroma(
            collection_name=self.config["collection_name"],
            embedding_function=embedding_model,
            persist_directory=self.config.get("persist_directory", None)
        )
        return self._collection

    async def _close_connection(self):
        # Chroma does not require explicit close, but clear reference
        self._collection = None

    async def save_and_embed(self, embedding_type: EmbeddingType, docs: List[Document]) -> List[str]:
        if not self._collection:
            await self._create_connection()
            
        ids, enhanced_docs = [], []
        for doc in docs:
            doc_id = doc.metadata.get("document_id") or str(uuid.uuid4())
            metadata = {**doc.metadata, 'embedded_at': datetime.now().isoformat(), 'document_id': doc_id}
            enhanced_docs.append(Document(page_content=doc.page_content, metadata=metadata))
            ids.append(doc_id)
        
        # Add documents to ChromaDB
        self._collection.add_documents(enhanced_docs, ids=ids)
        return ids

    async def update_document(self, document_id: str, updated_doc: Document, embedding_type: EmbeddingType) -> bool:
        # ChromaDB doesn't support direct update, so delete and re-add
        try:
            if not self._collection:
                await self._create_connection()
                
            self._collection.delete(ids=[document_id])
            updated_doc.metadata["document_id"] = document_id
            await self.save_and_embed(embedding_type, [updated_doc])
            return True
        except Exception:
            return False

    async def delete_by_document_id(self, document_id: str) -> bool:
        try:
            if not self._collection:
                await self._create_connection()
                
            self._collection.delete(ids=[document_id])
            return True
        except Exception:
            return False

    async def get_document_metadata(self, document_id: str) -> Optional[DocumentMetadata]:
        # ChromaDB doesn't have a direct way to get metadata by ID
        # This would require querying and filtering, which is not straightforward
        # For now, return None - this could be implemented with additional queries
        return None

    async def search_similar(self, query: str, k: int = 5, filter_criteria: Optional[Dict[str, Any]] = None) -> List[Document]:
        if not self._collection:
            await self._create_connection()
            
        # Use ChromaDB's similarity search functionality
        results = self._collection.similarity_search(query, k=k, filter=filter_criteria)
        return results

    def as_retriever(self, embedding_type: EmbeddingType, **kwargs):
        embedding_model = EmbeddingFactory.get_embedding_model(embedding_type)
        vector_store = Chroma(
            collection_name=self.config["collection_name"],
            embedding_function=embedding_model,
            persist_directory=self.config.get("persist_directory", None)
        )
        return vector_store.as_retriever(**kwargs)
