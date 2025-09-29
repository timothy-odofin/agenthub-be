"""
Qdrant vector database implementation.
"""
from typing import List, Dict, Any, Optional
from langchain.schema import Document
from langchain_community.vectorstores import Qdrant as LangchainQdrant
from qdrant_client import QdrantClient
from qdrant_client.http.models import Distance, VectorParams

from ...core.config import config
from ...core.constants import EmbeddingType
from ...core.utils.logger import get_logger
from .base import VectorDB
from .embedding import EmbeddingFactory

logger = get_logger(__name__)

class QdrantDB(VectorDB):
    """Qdrant vector database implementation."""
    
    def __init__(self):
        super().__init__()
        self._client = None
        self._vectorstore = None

    def get_vector_db_config(self) -> Dict[str, Any]:
        return config.qdrant_config

    async def _create_connection(self):
        """Create connection to Qdrant."""
        try:
            self._client = QdrantClient(
                url=self.config["url"],
                api_key=self.config["api_key"]
            )
            
            # Ensure collection exists
            collections = self._client.get_collections().collections
            collection_names = [c.name for c in collections]
            
            if self.config["collection_name"] not in collection_names:
                logger.info(f"Creating new collection: {self.config['collection_name']}")
                self._client.create_collection(
                    collection_name=self.config["collection_name"],
                    vectors_config=VectorParams(
                        size=self.config["embedding_dimension"],
                        distance=Distance.COSINE
                    )
                )
            
            return self._client
            
        except Exception as e:
            logger.error(f"Failed to connect to Qdrant: {str(e)}")
            raise

    async def _close_connection(self):
        """Close connection to Qdrant."""
        if self._client:
            self._client.close()
            self._client = None

    def _get_vectorstore(self, embedding_function):
        """Get or create Langchain Qdrant vectorstore instance."""
        if not self._vectorstore:
            self._vectorstore = LangchainQdrant(
                client=self._client,
                collection_name=self.config["collection_name"],
                embedding_function=embedding_function
            )
        return self._vectorstore

    async def save_and_embed(self, embedding_type: EmbeddingType, docs: List[Document]) -> List[str]:
        """Save documents and generate embeddings."""
        try:
            # Get embedding model
            embedding_model = EmbeddingFactory.get_embedding_model(embedding_type)
            
            # Get vectorstore with embedding model
            vectorstore = self._get_vectorstore(embedding_model)
            
            # Add documents
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
            embedding_model = EmbeddingFactory.get_embedding_model(EmbeddingType.OPENAI_EMBEDDING)
            
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
