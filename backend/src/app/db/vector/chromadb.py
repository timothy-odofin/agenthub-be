"""
ChromaDB implementation of VectorDB.
"""
from typing import Any, Dict, List, Optional
from datetime import datetime
import uuid

from langchain.schema import Document
from langchain_community.vectorstores import Chroma

from .providers.db_provider import VectorDBRegistry
from ...core.constants import EmbeddingType, VectorDBType, ConnectionType
from .base import VectorDB, DocumentMetadata
from app.db.vector.embeddings.embedding import EmbeddingFactory
from app.infrastructure.connections.factory.connection_factory import ConnectionFactory

@VectorDBRegistry.register(VectorDBType.CHROMA)
class ChromaDB(VectorDB):
    """ChromaDB implementation."""

    def __init__(self):
        super().__init__()
        self._collection = None
        self._connection_manager = None

    def get_vector_db_config(self) -> Dict[str, Any]:
        """Get vector database configuration via connection manager."""
        if not self._connection_manager:
            self._connection_manager = ConnectionFactory.get_connection_manager(ConnectionType.CHROMADB)
        return self._connection_manager.config

    def _create_connection(self):
        """Initialize ChromaDB with the connection manager factory."""
        # Get connection manager from factory if not already initialized
        if not self._connection_manager:
            self._connection_manager = ConnectionFactory.get_connection_manager(ConnectionType.CHROMADB)
        
        # Initialize ChromaDB with embedding model
        embedding_model = EmbeddingFactory.get_embedding_model(EmbeddingType.OPENAI)
        
        # Get the ChromaDB client from the connection manager (now sync)
        chroma_client = self._connection_manager.connect()
        
        self._collection = Chroma(
            collection_name=self.config["collection_name"],
            embedding_function=embedding_model,
            persist_directory=self.config.get("persist_directory", None),
            client=chroma_client
        )
        return self._collection

    def _close_connection(self):
        """Close the connection through the connection manager."""
        if self._connection_manager:
            self._connection_manager.disconnect()
            self._collection = None
            self._connection_manager = None  # Reset manager for clean state

    def save_and_embed(self, embedding_type: EmbeddingType, docs: List[Document]) -> List[str]:
        if not self._collection:
            self._create_connection()
            
        ids, enhanced_docs = [], []
        for doc in docs:
            doc_id = doc.metadata.get("document_id") or str(uuid.uuid4())
            metadata = {**doc.metadata, 'embedded_at': datetime.now().isoformat(), 'document_id': doc_id}
            enhanced_docs.append(Document(page_content=doc.page_content, metadata=metadata))
            ids.append(doc_id)
        
        # Add documents to ChromaDB (sync operation)
        self._collection.add_documents(enhanced_docs, ids=ids)
        return ids

    def update_document(self, document_id: str, updated_doc: Document, embedding_type: EmbeddingType) -> bool:
        # ChromaDB doesn't support direct update, so delete and re-add
        try:
            if not self._collection:
                self._create_connection()
                
            self._collection.delete(ids=[document_id])
            updated_doc.metadata["document_id"] = document_id
            self.save_and_embed(embedding_type, [updated_doc])
            return True
        except Exception:
            return False

    def delete_by_document_id(self, document_id: str) -> bool:
        try:
            if not self._collection:
                self._create_connection()
                
            self._collection.delete(ids=[document_id])
            return True
        except Exception:
            return False

    def get_document_metadata(self, document_id: str) -> Optional[DocumentMetadata]:
        # ChromaDB doesn't have a direct way to get metadata by ID
        # This would require querying and filtering, which is not straightforward
        # For now, return None - this could be implemented with additional queries
        return None

    def search_similar(self, query: str, k: int = 5, filter_criteria: Optional[Dict[str, Any]] = None) -> List[Document]:
        if not self._collection:
            self._create_connection()
            
        # Use ChromaDB's similarity search functionality (sync operation)
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
