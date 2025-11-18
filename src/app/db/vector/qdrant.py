"""
Qdrant vector database implementation.
"""
from abc import ABC
from datetime import datetime
from typing import List, Dict, Any, Optional
from langchain.schema import Document
from langchain_qdrant import Qdrant as LangchainQdrant
from qdrant_client import QdrantClient
from qdrant_client.http.models import Distance, VectorParams

from .providers.db_provider import VectorDBRegistry
from ...core.config import config
from ...core.constants import EmbeddingType, VectorDBType
from ...core.utils.logger import get_logger
from .base import VectorDB, DocumentMetadata
from app.db.vector.embeddings.embedding import EmbeddingFactory

logger = get_logger(__name__)

@VectorDBRegistry.register(VectorDBType.QDRANT)
class QdrantDB(VectorDB, ABC):
    """Qdrant vector database implementation."""
    
    def __init__(self):
        super().__init__()
        self._vectorstore = None

    def get_vector_db_config(self) -> Dict[str, Any]:
        return config.qdrant_config

    async def _create_connection(self):
        """Create connection to Qdrant."""
        try:
            logger.info("Obtaining Qdrant connection...")
            self._connection = QdrantClient(
                url=self.config["url"],
                api_key=self.config["api_key"]
            )
            
            # Ensure collection exists
            collections = self._connection.get_collections().collections
            collection_names = [c.name for c in collections]
            
            if self.config["collection_name"] not in collection_names:
                logger.info(f"Creating new collection: {self.config['collection_name']}")
                self._connection.create_collection(
                    collection_name=self.config["collection_name"],
                    vectors_config=VectorParams(
                        size=self.config["embedding_dimension"],
                        distance=Distance.COSINE
                    )
                )
            logger.info(f"Successfully obtained Qdrant connection to {self.config['url']}")
            return self._connection
            
        except Exception as e:
            logger.error(f"Failed to connect to Qdrant: {str(e)}")
            raise

    async def _close_connection(self):
        """Close connection to Qdrant."""
        if self._connection:
            self._connection.close()
            self._connection = None
            logger.info("Successfully closed Qdrant connection.")

    def _get_vectorstore(self, embedding_function):
        """Get or create Langchain Qdrant vectorstore instance."""
        if not self._vectorstore:
            self._vectorstore = LangchainQdrant(
                client=self._connection,
                collection_name=self.config["collection_name"],
                embeddings=embedding_function
            )
        logger.info("Using existing Qdrant vectorstore instance.")
        return self._vectorstore

    async def save_and_embed(self, embedding_type: EmbeddingType, docs: List[Document]) -> List[str]:
        """Save documents and generate embeddings."""
        try:
            # Get embedding model
            logger.info(f"Saving {len(docs)} documents...")
            embedding_model = EmbeddingFactory.get_embedding_model(embedding_type,config)
            logger.info(f"Using embedding model: {embedding_model.__class__.__name__}")
            
            # Get vectorstore with embedding model
            vectorstore = self._get_vectorstore(embedding_model)
            
            # Add documents
            logger.info("Adding documents to Qdrant...")
            ids = vectorstore.add_documents(docs)
            logger.info(f"Successfully added {len(docs)} documents to Qdrant collection {self.config['collection_name']}")
            
            return ids
            
        except Exception as e:
            logger.error(f"Failed to save documents to Qdrant: {str(e)}")
            raise

    async def search_similar(
        self,
        query: str,
        k: int = 5,
        filter_criteria: Optional[Dict[str, Any]] = None
    ) -> List[Document]:
        """Search for similar documents."""
        try:
            # Get embedding model (using default for now)
            embedding_model = EmbeddingFactory.get_embedding_model(EmbeddingType.DEFAULT, config)
            
            # Get vectorstore with embedding model
            vectorstore = self._get_vectorstore(embedding_model)
            
            # Perform search
            docs = vectorstore.similarity_search(
                query,
                k=k,
                filter=filter_criteria
            )
            logger.debug(f"Found {len(docs)} similar documents")
            
            return docs
            
        except Exception as e:
            logger.error(f"Error searching similar documents in Qdrant: {str(e)}")
            raise

    def as_retriever(self, **kwargs):
        """Return vectorstore as retriever."""
        # Use default embedding type if not specified
        embedding_model = EmbeddingFactory.get_embedding_model(EmbeddingType.DEFAULT, config)
        vector_store = self._get_vectorstore(embedding_model)
        return vector_store.as_retriever(**kwargs)

    async def delete_by_document_id(self, document_id: str) -> bool:
        """Delete all chunks of a document by its ID."""
        try:
            logger.info(f"Deleting document with ID: {document_id}")
            
            # Use the Qdrant client to delete by filter
            # We'll filter by document_id in metadata
            from qdrant_client.http.models import Filter, FieldCondition, MatchValue
            
            delete_filter = Filter(
                must=[
                    FieldCondition(
                        key="document_id",
                        match=MatchValue(value=document_id)
                    )
                ]
            )
            
            self._connection.delete(
                collection_name=self.config["collection_name"],
                points_selector=delete_filter
            )
            
            logger.info(f"Successfully deleted document {document_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete document {document_id}: {str(e)}")
            return False

    async def get_document_metadata(self, document_id: str) -> Optional[DocumentMetadata]:
        """Get metadata for a document."""
        try:
            from qdrant_client.http.models import Filter, FieldCondition, MatchValue
            
            # Search for the document by ID
            search_filter = Filter(
                must=[
                    FieldCondition(
                        key="document_id", 
                        match=MatchValue(value=document_id)
                    )
                ]
            )
            
            result = self._connection.scroll(
                collection_name=self.config["collection_name"],
                scroll_filter=search_filter,
                limit=1
            )
            
            if result[0]:  # result is a tuple (points, next_page_offset)
                point = result[0][0]  # First point
                payload = point.payload
                
                return DocumentMetadata(
                    document_id=document_id,
                    source_path=payload.get("source_path", ""),
                    file_type=payload.get("file_type", ""),
                    embedded_at=datetime.fromisoformat(payload.get("embedded_at", datetime.now().isoformat())),
                    custom_metadata=payload.get("custom_metadata", {})
                )
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to get metadata for document {document_id}: {str(e)}")
            return None

    async def update_document(self, document_id: str, updated_doc: Document, embedding_type: EmbeddingType) -> bool:
        """Update an existing document."""
        try:
            logger.info(f"Updating document with ID: {document_id}")
            
            # First delete the old document
            delete_success = await self.delete_by_document_id(document_id)
            if not delete_success:
                logger.error(f"Failed to delete old document {document_id}")
                return False
            
            # Then add the updated document
            # Make sure the document has the same ID in metadata
            updated_doc.metadata["document_id"] = document_id
            ids = await self.save_and_embed(embedding_type, [updated_doc])
            
            success = len(ids) > 0
            if success:
                logger.info(f"Successfully updated document {document_id}")
            else:
                logger.error(f"Failed to save updated document {document_id}")
            
            return success
            
        except Exception as e:
            logger.error(f"Failed to update document {document_id}: {str(e)}")
            return False
