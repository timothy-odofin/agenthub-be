"""
Qdrant connection manager implementation.

Provides connection management for Qdrant vector database with proper
configuration validation and health checking.
"""

from typing import Any, Optional, Dict, List
from qdrant_client import QdrantClient
from qdrant_client.http.models import Distance, VectorParams
from qdrant_client.http import exceptions as qdrant_exceptions

from app.connections.base import BaseConnectionManager, ConnectionRegistry, ConnectionType
from app.core.utils.logger import get_logger

logger = get_logger(__name__)


@ConnectionRegistry.register(ConnectionType.QDRANT)
class QdrantConnectionManager(BaseConnectionManager):
    """Qdrant vector database connection manager implementation."""
    
    def __init__(self):
        super().__init__()
        self._qdrant_client: Optional[QdrantClient] = None
    
    def get_connection_name(self) -> str:
        """Return the configuration name for Qdrant."""
        return ConnectionType.QDRANT.value
    
    def get_config_source(self) -> Any:
        """Return the vector database configuration source."""
        from app.core.config.vector_config import vector_config
        return vector_config
    
    def validate_config(self) -> None:
        """Validate Qdrant configuration."""
        required_fields = ['url', 'collection_name']
        
        for field in required_fields:
            if not self.config.get(field):
                raise ValueError(f"Qdrant connection requires '{field}' in configuration")
        
        # Validate URL format
        url = self.config.get('url')
        if not url.startswith(('http://', 'https://')):
            raise ValueError(f"Qdrant URL must start with http:// or https://, got: {url}")
        
        # Validate embedding dimension
        embedding_dimension = self.config.get('embedding_dimension', 1536)
        if not isinstance(embedding_dimension, int) or embedding_dimension <= 0:
            raise ValueError(f"Qdrant embedding_dimension must be a positive integer, got: {embedding_dimension}")
        
        # Validate distance metric
        distance = self.config.get('distance', 'Cosine')
        valid_distances = ['Cosine', 'Euclid', 'Dot']
        if distance not in valid_distances:
            raise ValueError(f"Qdrant distance must be one of {valid_distances}, got: {distance}")
        
        logger.info("Qdrant connection configuration validated successfully")
    
    async def connect(self) -> QdrantClient:
        """Establish Qdrant connection."""
        if self._qdrant_client:
            # Test existing connection
            if await self._test_connection():
                return self._qdrant_client
            else:
                # Connection might be stale, recreate
                await self.disconnect()
        
        try:
            # Create Qdrant client
            self._qdrant_client = QdrantClient(
                url=self.config['url'],
                api_key=self.config.get('api_key'),
                timeout=self.config.get('timeout', 60)
            )
            
            # Test connection by getting collections
            collections = self._qdrant_client.get_collections()
            
            # Ensure collection exists
            collection_name = self.config['collection_name']
            collection_names = [c.name for c in collections.collections]
            
            if collection_name not in collection_names:
                logger.info(f"Creating new Qdrant collection: {collection_name}")
                
                # Map distance string to Qdrant Distance enum
                distance_mapping = {
                    'Cosine': Distance.COSINE,
                    'Euclid': Distance.EUCLID,
                    'Dot': Distance.DOT
                }
                
                self._qdrant_client.create_collection(
                    collection_name=collection_name,
                    vectors_config=VectorParams(
                        size=self.config.get('embedding_dimension', 1536),
                        distance=distance_mapping.get(self.config.get('distance', 'Cosine'), Distance.COSINE)
                    )
                )
                logger.info(f"Created Qdrant collection: {collection_name}")
            else:
                logger.info(f"Using existing Qdrant collection: {collection_name}")
            
            self._connection = self._qdrant_client
            self._is_connected = True
            
            logger.info(f"Qdrant connection established to {self.config['url']}")
            return self._qdrant_client
            
        except Exception as e:
            self._connection = None
            self._is_connected = False
            logger.error(f"Failed to connect to Qdrant: {e}")
            raise ConnectionError(f"Qdrant connection failed: {e}")
    
    async def disconnect(self) -> None:
        """Close Qdrant connection."""
        if self._qdrant_client:
            try:
                # Qdrant client doesn't have explicit close method
                # Just clear the reference
                self._qdrant_client = None
                logger.info("Qdrant connection closed")
            except Exception as e:
                logger.warning(f"Error closing Qdrant connection: {e}")
            finally:
                self._qdrant_client = None
                self._connection = None
                self._is_connected = False
    
    def is_healthy(self) -> bool:
        """Check if Qdrant connection is healthy."""
        if not self._qdrant_client:
            return False
        
        try:
            # Quick sync test
            return bool(self._qdrant_client)
        except Exception:
            return False
    
    async def _test_connection(self) -> bool:
        """Test Qdrant connection asynchronously."""
        if not self._qdrant_client:
            return False
        
        try:
            # Test with a simple API call
            collections = self._qdrant_client.get_collections()
            return bool(collections)
        except Exception:
            return False
    
    # Qdrant-specific convenience methods
    
    async def get_collection_info(self, collection_name: Optional[str] = None) -> Dict:
        """
        Get information about a collection.
        
        Args:
            collection_name: Name of collection, defaults to configured collection
            
        Returns:
            Collection information
        """
        await self.ensure_connected()
        
        if collection_name is None:
            collection_name = self.config['collection_name']
        
        try:
            return self._qdrant_client.get_collection(collection_name)
        except Exception as e:
            logger.error(f"Failed to get collection info for {collection_name}: {e}")
            raise
    
    async def list_collections(self) -> List[Dict]:
        """
        List all collections in Qdrant.
        
        Returns:
            List of collection information
        """
        await self.ensure_connected()
        
        try:
            collections = self._qdrant_client.get_collections()
            return [
                {
                    'name': collection.name,
                    'vectors_count': collection.vectors_count or 0,
                    'points_count': collection.points_count or 0
                }
                for collection in collections.collections
            ]
        except Exception as e:
            logger.error(f"Failed to list collections: {e}")
            raise
    
    async def count_points(self, collection_name: Optional[str] = None) -> int:
        """
        Count points in a collection.
        
        Args:
            collection_name: Name of collection, defaults to configured collection
            
        Returns:
            Number of points in collection
        """
        await self.ensure_connected()
        
        if collection_name is None:
            collection_name = self.config['collection_name']
        
        try:
            result = self._qdrant_client.count(collection_name=collection_name)
            return result.count
        except Exception as e:
            logger.error(f"Failed to count points in {collection_name}: {e}")
            return 0
    
    async def delete_collection(self, collection_name: str) -> bool:
        """
        Delete a collection.
        
        Args:
            collection_name: Name of collection to delete
            
        Returns:
            True if successfully deleted
        """
        await self.ensure_connected()
        
        try:
            self._qdrant_client.delete_collection(collection_name=collection_name)
            logger.info(f"Deleted Qdrant collection: {collection_name}")
            return True
        except Exception as e:
            logger.error(f"Failed to delete collection {collection_name}: {e}")
            return False
    
    async def search_points(
        self, 
        vector: List[float], 
        limit: int = 10,
        score_threshold: Optional[float] = None,
        collection_name: Optional[str] = None
    ) -> List[Dict]:
        """
        Search for similar points in the collection.
        
        Args:
            vector: Query vector
            limit: Maximum number of results
            score_threshold: Minimum score threshold
            collection_name: Name of collection, defaults to configured collection
            
        Returns:
            List of search results
        """
        await self.ensure_connected()
        
        if collection_name is None:
            collection_name = self.config['collection_name']
        
        try:
            results = self._qdrant_client.search(
                collection_name=collection_name,
                query_vector=vector,
                limit=limit,
                score_threshold=score_threshold
            )
            
            return [
                {
                    'id': result.id,
                    'score': result.score,
                    'payload': result.payload
                }
                for result in results
            ]
        except Exception as e:
            logger.error(f"Failed to search points: {e}")
            return []
    
    def get_connection_info(self) -> Dict[str, Any]:
        """Get Qdrant connection information."""
        base_info = super().get_connection_info()
        
        if self._qdrant_client:
            try:
                collections = self._qdrant_client.get_collections()
                base_info.update({
                    'url': self.config.get('url'),
                    'collection_name': self.config.get('collection_name'),
                    'total_collections': len(collections.collections),
                    'collections': [c.name for c in collections.collections]
                })
            except Exception as e:
                base_info['connection_error'] = str(e)
        
        return base_info
