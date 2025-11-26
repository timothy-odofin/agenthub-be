"""
MongoDB connection manager implementation.

Provides connection management for MongoDB with proper
configuration validation and health checking.

Requirements:
    - pymongo: pip install pymongo
"""

from typing import Any, Optional, Dict, List
from urllib.parse import quote_plus
import pymongo
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError

from app.connections.base import BaseConnectionManager, ConnectionRegistry, ConnectionType
from app.core.utils.logger import get_logger

logger = get_logger(__name__)


@ConnectionRegistry.register(ConnectionType.MONGODB)
class MongoDBConnectionManager(BaseConnectionManager):
    """MongoDB connection manager implementation."""
    
    def __init__(self):
        super().__init__()
        self._mongo_client: Optional[MongoClient] = None
        self._database: Optional[Any] = None
    
    def get_connection_name(self) -> str:
        """Return the configuration name for MongoDB."""
        return ConnectionType.MONGODB.value
    
    def get_config_source(self) -> Any:
        """Return the database configuration source."""
        from app.core.config.database_config import database_config
        return database_config
    
    def validate_config(self) -> None:
        """Validate MongoDB configuration."""
        # Check if we have a connection string or individual components
        connection_string = self.config.get('connection_string')
        if connection_string:
            # Validate connection string format
            if not connection_string.startswith('mongodb://') and not connection_string.startswith('mongodb+srv://'):
                raise ValueError("MongoDB connection_string must start with 'mongodb://' or 'mongodb+srv://'")
        else:
            # Validate individual components
            required_fields = ['host', 'port', 'database']
            
            for field in required_fields:
                if not self.config.get(field):
                    raise ValueError(f"MongoDB connection requires '{field}' in configuration when not using connection_string")
            
            # Validate port
            port = self.config.get('port')
            if not isinstance(port, int) or port <= 0:
                raise ValueError(f"MongoDB port must be a positive integer, got: {port}")
        
        logger.info("MongoDB connection configuration validated successfully")
    
    def _build_connection_string(self) -> str:
        """Build MongoDB connection string from individual config components."""
        # Use provided connection string if available
        if self.config.get('connection_string'):
            return self.config['connection_string']
        
        # Build connection string from components
        username = self.config.get('username')
        password = self.config.get('password')
        host = self.config['host']
        port = self.config['port']
        database = self.config['database']
        
        # URL-encode username and password
        if username and password:
            auth_part = f"{quote_plus(username)}:{quote_plus(password)}@"
        elif username:
            auth_part = f"{quote_plus(username)}@"
        else:
            auth_part = ""
        
        # Build connection string
        connection_string = f"mongodb://{auth_part}{host}:{port}/{database}"
        
        # Add additional options
        options = []
        
        if self.config.get('auth_source'):
            options.append(f"authSource={self.config['auth_source']}")
        
        if self.config.get('ssl', False):
            options.append("ssl=true")
        
        if self.config.get('replica_set'):
            options.append(f"replicaSet={self.config['replica_set']}")
        
        if self.config.get('connect_timeout'):
            options.append(f"connectTimeoutMS={self.config['connect_timeout']}")
        
        if self.config.get('server_selection_timeout'):
            options.append(f"serverSelectionTimeoutMS={self.config['server_selection_timeout']}")
        
        if options:
            connection_string += "?" + "&".join(options)
        
        return connection_string
    
    async def connect(self) -> MongoClient:
        """Establish MongoDB connection."""
        if self._mongo_client:
            # Test existing connection
            if await self._test_connection():
                return self._mongo_client
            else:
                # Connection might be stale, recreate
                await self.disconnect()
        
        try:
            # Build connection string
            connection_string = self._build_connection_string()
            
            # Create MongoDB client
            self._mongo_client = MongoClient(
                connection_string,
                serverSelectionTimeoutMS=self.config.get('server_selection_timeout', 5000),
                connectTimeoutMS=self.config.get('connect_timeout', 10000),
                maxPoolSize=self.config.get('max_pool_size', 100),
                minPoolSize=self.config.get('min_pool_size', 0),
                maxIdleTimeMS=self.config.get('max_idle_time', 300000),  # 5 minutes
                retryWrites=self.config.get('retry_writes', True)
            )
            
            # Get database
            database_name = self.config['database']
            self._database = self._mongo_client[database_name]
            
            # Test connection by pinging the database
            self._mongo_client.admin.command('ping')
            
            # Get server info for logging
            server_info = self._mongo_client.server_info()
            logger.info(f"Connected to MongoDB server version {server_info.get('version', 'Unknown')}")
            
            self._connection = self._mongo_client
            self._is_connected = True
            
            logger.info(f"MongoDB connection established to database '{database_name}'")
            return self._mongo_client
            
        except (ConnectionFailure, ServerSelectionTimeoutError) as e:
            self._connection = None
            self._is_connected = False
            logger.error(f"Failed to connect to MongoDB: {e}")
            raise ConnectionError(f"MongoDB connection failed: {e}")
        except Exception as e:
            self._connection = None
            self._is_connected = False
            logger.error(f"Unexpected error connecting to MongoDB: {e}")
            raise ConnectionError(f"MongoDB connection failed: {e}")
    
    async def disconnect(self) -> None:
        """Close MongoDB connection."""
        if self._mongo_client:
            try:
                self._mongo_client.close()
                logger.info("MongoDB connection closed")
            except Exception as e:
                logger.warning(f"Error closing MongoDB connection: {e}")
            finally:
                self._mongo_client = None
                self._database = None
                self._connection = None
                self._is_connected = False
    
    def is_healthy(self) -> bool:
        """Check if MongoDB connection is healthy."""
        if not self._mongo_client:
            return False
        
        try:
            # Quick test - ping the server
            self._mongo_client.admin.command('ping')
            return True
        except Exception:
            return False
    
    async def _test_connection(self) -> bool:
        """Test MongoDB connection asynchronously."""
        if not self._mongo_client:
            return False
        
        try:
            # Test with a simple ping command
            self._mongo_client.admin.command('ping')
            return True
        except Exception:
            return False
    
    # MongoDB-specific convenience methods
    
    def get_database(self) -> Any:
        """Get the MongoDB database instance."""
        if not self._database:
            raise RuntimeError("MongoDB connection not established. Call connect() first.")
        return self._database
    
    def get_collection(self, collection_name: str) -> Any:
        """
        Get a collection from the database.
        
        Args:
            collection_name: Name of the collection
            
        Returns:
            MongoDB collection object
        """
        database = self.get_database()
        return database[collection_name]
    
    async def get_server_info(self) -> Dict:
        """Get MongoDB server information."""
        await self.ensure_connected()
        
        try:
            return self._mongo_client.server_info()
        except Exception as e:
            logger.error(f"Failed to get server info: {e}")
            raise
    
    async def list_collections(self) -> List[str]:
        """List all collections in the database."""
        await self.ensure_connected()
        
        try:
            return self._database.list_collection_names()
        except Exception as e:
            logger.error(f"Failed to list collections: {e}")
            raise
    
    async def get_collection_stats(self, collection_name: str) -> Dict:
        """
        Get statistics for a collection.
        
        Args:
            collection_name: Name of the collection
            
        Returns:
            Collection statistics
        """
        await self.ensure_connected()
        
        try:
            return self._database.command('collStats', collection_name)
        except Exception as e:
            logger.error(f"Failed to get stats for collection {collection_name}: {e}")
            raise
    
    async def create_index(self, collection_name: str, index_spec: List, **kwargs) -> str:
        """
        Create an index on a collection.
        
        Args:
            collection_name: Name of the collection
            index_spec: Index specification
            **kwargs: Additional index options
            
        Returns:
            Name of the created index
        """
        await self.ensure_connected()
        
        try:
            collection = self.get_collection(collection_name)
            index_name = collection.create_index(index_spec, **kwargs)
            logger.info(f"Created index '{index_name}' on collection '{collection_name}'")
            return index_name
        except Exception as e:
            logger.error(f"Failed to create index on collection {collection_name}: {e}")
            raise
    
    async def drop_collection(self, collection_name: str) -> None:
        """
        Drop a collection.
        
        Args:
            collection_name: Name of the collection to drop
        """
        await self.ensure_connected()
        
        try:
            self._database.drop_collection(collection_name)
            logger.info(f"Dropped collection '{collection_name}'")
        except Exception as e:
            logger.error(f"Failed to drop collection {collection_name}: {e}")
            raise
    
    async def count_documents(self, collection_name: str, filter_dict: Optional[Dict] = None) -> int:
        """
        Count documents in a collection.
        
        Args:
            collection_name: Name of the collection
            filter_dict: Optional filter to apply
            
        Returns:
            Number of documents
        """
        await self.ensure_connected()
        
        try:
            collection = self.get_collection(collection_name)
            return collection.count_documents(filter_dict or {})
        except Exception as e:
            logger.error(f"Failed to count documents in collection {collection_name}: {e}")
            return 0
    
    def get_connection_info(self) -> Dict[str, Any]:
        """Get MongoDB connection information."""
        base_info = super().get_connection_info()
        
        if self._mongo_client:
            try:
                server_info = self._mongo_client.server_info()
                base_info.update({
                    'host': self.config.get('host', 'connection_string_based'),
                    'port': self.config.get('port', 'connection_string_based'),
                    'database': self.config.get('database'),
                    'server_version': server_info.get('version'),
                    'git_version': server_info.get('gitVersion'),
                    'max_bson_object_size': server_info.get('maxBsonObjectSize'),
                    'max_write_batch_size': server_info.get('maxWriteBatchSize'),
                })
            except Exception as e:
                base_info['connection_error'] = str(e)
        
        return base_info
