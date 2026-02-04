"""
PostgreSQL with PgVector extension connection manager implementation.

Provides connection management for PgVector (PostgreSQL with pgvector extension)
with proper configuration validation and health checking.

Requirements:
    - asyncpg: pip install asyncpg
"""

from typing import Any, Optional, Dict, List
import asyncpg

from app.infrastructure.connections.base import AsyncBaseConnectionManager, ConnectionRegistry, ConnectionType
from app.core.utils.logger import get_logger

logger = get_logger(__name__)


@ConnectionRegistry.register(ConnectionType.PGVECTOR)
class PgVectorConnectionManager(AsyncBaseConnectionManager):
    """PostgreSQL with PgVector extension connection manager implementation."""
    
    def __init__(self):
        super().__init__()
        self._pg_connection: Optional[asyncpg.Connection] = None
    
    def get_connection_name(self) -> str:
        """Return the configuration name for PgVector."""
        return ConnectionType.PGVECTOR.value
    
    def get_config_category(self) -> str:
        """Return the configuration category for vector stores."""
        return "vector"
    
    def validate_config(self) -> None:
        """Validate PgVector configuration."""
        config_dict = self._get_config_dict()
        required_fields = ['connection_string', 'collection_name']
        
        for field in required_fields:
            if not config_dict.get(field):
                raise ValueError(f"PgVector connection requires '{field}' in configuration")
        
        # Validate connection string format
        connection_string = config_dict.get('connection_string')
        if not connection_string.startswith('postgresql://'):
            raise ValueError(f"PgVector connection_string must start with postgresql://, got: {connection_string}")
        
        # Validate embedding dimension
        embedding_dimension = config_dict.get('embedding_dimension', 1536)
        if not isinstance(embedding_dimension, int) or embedding_dimension <= 0:
            raise ValueError(f"PgVector embedding_dimension must be a positive integer, got: {embedding_dimension}")
        
        # Validate distance strategy
        distance_strategy = config_dict.get('distance_strategy', 'cosine')
        valid_strategies = ['cosine', 'euclidean', 'dot_product']
        if distance_strategy not in valid_strategies:
            raise ValueError(f"PgVector distance_strategy must be one of {valid_strategies}, got: {distance_strategy}")
        
        logger.info("PgVector connection configuration validated successfully")
    
    async def connect(self) -> asyncpg.Connection:
        """Establish PgVector connection."""
        if self._pg_connection:
            # Test existing connection
            if await self._test_connection():
                return self._pg_connection
            else:
                # Connection might be stale, recreate
                await self.disconnect()
        
        try:
            config_dict = self._get_config_dict()
            
            # Create PostgreSQL connection
            self._pg_connection = await asyncpg.connect(config_dict['connection_string'])
            
            # Test connection by checking pgvector extension
            result = await self._pg_connection.fetch(
                "SELECT extname FROM pg_extension WHERE extname = 'vector'"
            )
            
            if not result:
                # Try to install pgvector extension
                logger.warning("PgVector extension not found. Attempting to install...")
                try:
                    await self._pg_connection.execute("CREATE EXTENSION IF NOT EXISTS vector")
                    logger.info("PgVector extension installed successfully")
                except Exception as e:
                    raise ConnectionError(f"Failed to install pgvector extension: {e}")
            
            # Ensure collection table exists
            collection_name = config_dict['collection_name']
            embedding_dimension = config_dict.get('embedding_dimension', 1536)
            
            # Create table if it doesn't exist
            await self._create_collection_table(collection_name, embedding_dimension)
            
            self._connection = self._pg_connection
            self._is_connected = True
            
            logger.info(f"PgVector connection established to {config_dict['connection_string']}")
            return self._pg_connection
            
        except Exception as e:
            self._connection = None
            self._is_connected = False
            logger.error(f"Failed to connect to PgVector: {e}")
            raise ConnectionError(f"PgVector connection failed: {e}")
    
    async def disconnect(self) -> None:
        """Close PgVector connection."""
        if self._pg_connection:
            try:
                await self._pg_connection.close()
                logger.info("PgVector connection closed")
            except Exception as e:
                logger.warning(f"Error closing PgVector connection: {e}")
            finally:
                self._pg_connection = None
                self._connection = None
                self._is_connected = False
    
    def is_healthy(self) -> bool:
        """Check if PgVector connection is healthy."""
        if not self._pg_connection:
            return False
        
        try:
            # Quick sync test - check if connection is still alive
            return not self._pg_connection.is_closed()
        except Exception:
            return False
    
    async def _test_connection(self) -> bool:
        """Test PgVector connection asynchronously."""
        if not self._pg_connection:
            return False
        
        try:
            # Test with a simple query
            await self._pg_connection.fetchval("SELECT 1")
            return True
        except Exception:
            return False
    
    async def _create_collection_table(self, collection_name: str, embedding_dimension: int) -> None:
        """Create collection table if it doesn't exist."""
        try:
            # Create table with vector column
            create_table_query = f"""
            CREATE TABLE IF NOT EXISTS {collection_name} (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                content TEXT NOT NULL,
                metadata JSONB,
                embedding vector({embedding_dimension}),
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
            )
            """
            await self._pg_connection.execute(create_table_query)
            
            # Create index on embedding column for efficient similarity search
            index_query = f"""
            CREATE INDEX IF NOT EXISTS {collection_name}_embedding_idx 
            ON {collection_name} USING ivfflat (embedding vector_cosine_ops) 
            WITH (lists = 100)
            """
            await self._pg_connection.execute(index_query)
            
            logger.info(f"PgVector collection table '{collection_name}' ready")
            
        except Exception as e:
            logger.error(f"Failed to create collection table: {e}")
            raise
    
    # PgVector-specific convenience methods
    
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
            # Get table info
            result = await self._pg_connection.fetch("""
                SELECT 
                    tablename,
                    schemaname,
                    tableowner
                FROM pg_tables 
                WHERE tablename = $1
            """, collection_name)
            
            if not result:
                return {'exists': False}
            
            # Get row count
            count_result = await self._pg_connection.fetchval(
                f"SELECT COUNT(*) FROM {collection_name}"
            )
            
            return {
                'exists': True,
                'name': collection_name,
                'schema': result[0]['schemaname'],
                'owner': result[0]['tableowner'],
                'document_count': count_result or 0
            }
        except Exception as e:
            logger.error(f"Failed to get collection info for {collection_name}: {e}")
            raise
    
    async def count_documents(self, collection_name: Optional[str] = None) -> int:
        """
        Count documents in a collection.
        
        Args:
            collection_name: Name of collection, defaults to configured collection
            
        Returns:
            Number of documents in collection
        """
        await self.ensure_connected()
        
        if collection_name is None:
            collection_name = self.config['collection_name']
        
        try:
            count = await self._pg_connection.fetchval(
                f"SELECT COUNT(*) FROM {collection_name}"
            )
            return count or 0
        except Exception as e:
            logger.error(f"Failed to count documents in {collection_name}: {e}")
            return 0
    
    async def delete_collection(self, collection_name: str) -> bool:
        """
        Delete a collection table.
        
        Args:
            collection_name: Name of collection to delete
            
        Returns:
            True if successfully deleted
        """
        await self.ensure_connected()
        
        try:
            await self._pg_connection.execute(f"DROP TABLE IF EXISTS {collection_name}")
            logger.info(f"Deleted PgVector collection: {collection_name}")
            return True
        except Exception as e:
            logger.error(f"Failed to delete collection {collection_name}: {e}")
            return False
    
    async def similarity_search(
        self, 
        embedding: List[float], 
        limit: int = 10,
        distance_threshold: Optional[float] = None,
        collection_name: Optional[str] = None
    ) -> List[Dict]:
        """
        Search for similar documents in the collection.
        
        Args:
            embedding: Query embedding vector
            limit: Maximum number of results
            distance_threshold: Maximum distance threshold
            collection_name: Name of collection, defaults to configured collection
            
        Returns:
            List of search results
        """
        await self.ensure_connected()
        
        if collection_name is None:
            collection_name = self.config['collection_name']
        
        try:
            distance_op = '<->'  # Cosine distance operator
            
            query = f"""
                SELECT id, content, metadata, embedding <-> $1 as distance
                FROM {collection_name}
                ORDER BY embedding <-> $1
                LIMIT $2
            """
            
            if distance_threshold is not None:
                query = f"""
                    SELECT id, content, metadata, embedding <-> $1 as distance
                    FROM {collection_name}
                    WHERE embedding <-> $1 < $3
                    ORDER BY embedding <-> $1
                    LIMIT $2
                """
                results = await self._pg_connection.fetch(query, embedding, limit, distance_threshold)
            else:
                results = await self._pg_connection.fetch(query, embedding, limit)
            
            return [
                {
                    'id': str(result['id']),
                    'content': result['content'],
                    'metadata': result['metadata'],
                    'distance': float(result['distance'])
                }
                for result in results
            ]
        except Exception as e:
            logger.error(f"Failed to perform similarity search: {e}")
            return []
    
    def get_connection_info(self) -> Dict[str, Any]:
        """Get PgVector connection information."""
        base_info = super().get_connection_info()
        
        if self._pg_connection:
            try:
                # PostgreSQL connection info
                base_info.update({
                    'connection_string': self.config.get('connection_string', '').split('@')[-1] if '@' in self.config.get('connection_string', '') else 'N/A',  # Hide credentials
                    'collection_name': self.config.get('collection_name'),
                    'embedding_dimension': self.config.get('embedding_dimension'),
                    'distance_strategy': self.config.get('distance_strategy'),
                })
            except Exception as e:
                base_info['connection_error'] = str(e)
        
        return base_info
