"""
ChromaDB connection manager implementation.

Provides connection management for ChromaDB vector database with proper
configuration validation and health checking.

Requirements:
    - chromadb: pip install chromadb
"""

import os
from pathlib import Path
from typing import Any, Optional, Dict, List
from datetime import datetime
import chromadb
from chromadb.config import Settings

from app.infrastructure.connections.base import BaseConnectionManager, ConnectionRegistry, ConnectionType
from app.core.utils.logger import get_logger

logger = get_logger(__name__)


@ConnectionRegistry.register(ConnectionType.CHROMADB)
class ChromaDBConnectionManager(BaseConnectionManager):
    """ChromaDB vector database connection manager implementation."""
    
    def __init__(self):
        super().__init__()
        self._chroma_client: Optional[chromadb.Client] = None
    
    def get_connection_name(self) -> str:
        """Return the configuration name for ChromaDB."""
        return ConnectionType.CHROMADB.value
    
    def validate_config(self) -> None:
        """Validate ChromaDB configuration."""
        required_fields = ['collection_name']
        
        for field in required_fields:
            if not self.config.get(field):
                raise ValueError(f"ChromaDB connection requires '{field}' in configuration")
        
        # Validate persist directory if provided
        persist_directory = self.config.get('persist_directory')
        if persist_directory:
            persist_path = Path(persist_directory)
            # Create directory if it doesn't exist
            persist_path.mkdir(parents=True, exist_ok=True)
            
            if not persist_path.is_dir():
                raise ValueError(f"ChromaDB persist_directory must be a valid directory path: {persist_directory}")
        
        logger.info("ChromaDB connection configuration validated successfully")
    
    def connect(self) -> chromadb.Client:
        """Establish ChromaDB connection."""
        if self._chroma_client:
            # Test existing connection
            if self._test_connection():
                return self._chroma_client
            else:
                # Connection might be stale, recreate
                self.disconnect()
        
        try:
            # Configure ChromaDB settings
            settings = Settings()
            
            persist_directory = self.config.get('persist_directory')
            if persist_directory:
                settings = Settings(
                    chroma_db_impl="duckdb+parquet",
                    persist_directory=persist_directory
                )
            
            # Create ChromaDB client
            self._chroma_client = chromadb.Client(settings)
            
            # Test connection by listing collections
            collections = self._chroma_client.list_collections()
            
            # Ensure collection exists
            collection_name = self.config['collection_name']
            collection_names = [c.name for c in collections]
            
            if collection_name not in collection_names:
                logger.info(f"Creating new ChromaDB collection: {collection_name}")
                self._chroma_client.create_collection(
                    name=collection_name,
                    metadata={"created_at": str(datetime.now())}
                )
                logger.info(f"Created ChromaDB collection: {collection_name}")
            else:
                logger.info(f"Using existing ChromaDB collection: {collection_name}")
            
            self._connection = self._chroma_client
            self._is_connected = True
            
            logger.info("ChromaDB connection established")
            return self._chroma_client
            
        except Exception as e:
            self._connection = None
            self._is_connected = False
            logger.error(f"Failed to connect to ChromaDB: {e}")
            raise ConnectionError(f"ChromaDB connection failed: {e}")
    
    def disconnect(self) -> None:
        """Close ChromaDB connection."""
        if self._chroma_client:
            try:
                # ChromaDB doesn't require explicit cleanup in most cases
                # Just clear the reference
                self._chroma_client = None
                logger.info("ChromaDB connection closed")
            except Exception as e:
                logger.warning(f"Error closing ChromaDB connection: {e}")
            finally:
                self._chroma_client = None
                self._connection = None
                self._is_connected = False
    
    def is_healthy(self) -> bool:
        """Check if ChromaDB connection is healthy."""
        if not self._chroma_client:
            return False
        
        try:
            # Quick sync test
            self._chroma_client.heartbeat()
            return True
        except Exception:
            return False
    
    def _test_connection(self) -> bool:
        """Test ChromaDB connection synchronously."""
        if not self._chroma_client:
            return False
        
        try:
            # Test with a simple API call
            self._chroma_client.list_collections()
            return True
        except Exception:
            return False
    
    # ChromaDB-specific convenience methods
    
    def get_collection_info(self, collection_name: Optional[str] = None) -> Dict:
        """
        Get information about a collection.
        
        Args:
            collection_name: Name of collection, defaults to configured collection
            
        Returns:
            Collection information
        """
        self.ensure_connected()
        
        if collection_name is None:
            collection_name = self.config['collection_name']
        
        try:
            collection = self._chroma_client.get_collection(collection_name)
            return {
                'name': collection.name,
                'id': collection.id,
                'metadata': collection.metadata,
                'count': collection.count()
            }
        except Exception as e:
            logger.error(f"Failed to get collection info for {collection_name}: {e}")
            raise
    
    def list_collections(self) -> List[Dict]:
        """
        List all collections in ChromaDB.
        
        Returns:
            List of collection information
        """
        self.ensure_connected()
        
        try:
            collections = self._chroma_client.list_collections()
            return [
                {
                    'name': collection.name,
                    'id': collection.id,
                    'metadata': collection.metadata,
                    'count': collection.count()
                }
                for collection in collections
            ]
        except Exception as e:
            logger.error(f"Failed to list collections: {e}")
            raise
    
    def count_documents(self, collection_name: Optional[str] = None) -> int:
        """
        Count documents in a collection.
        
        Args:
            collection_name: Name of collection, defaults to configured collection
            
        Returns:
            Number of documents in collection
        """
        self.ensure_connected()
        
        if collection_name is None:
            collection_name = self.config['collection_name']
        
        try:
            collection = self._chroma_client.get_collection(collection_name)
            return collection.count()
        except Exception as e:
            logger.error(f"Failed to count documents in {collection_name}: {e}")
            return 0
    
    def delete_collection(self, collection_name: str) -> bool:
        """
        Delete a collection.
        
        Args:
            collection_name: Name of collection to delete
            
        Returns:
            True if successfully deleted
        """
        self.ensure_connected()
        
        try:
            self._chroma_client.delete_collection(name=collection_name)
            logger.info(f"Deleted ChromaDB collection: {collection_name}")
            return True
        except Exception as e:
            logger.error(f"Failed to delete collection {collection_name}: {e}")
            return False
    
    def get_connection_info(self) -> Dict[str, Any]:
        """Get ChromaDB connection information."""
        base_info = super().get_connection_info()
        
        if self._chroma_client:
            try:
                collections = self._chroma_client.list_collections()
                base_info.update({
                    'collection_name': self.config.get('collection_name'),
                    'persist_directory': self.config.get('persist_directory'),
                    'total_collections': len(collections),
                    'collections': [c.name for c in collections]
                })
            except Exception as e:
                base_info['connection_error'] = str(e)
        
        return base_info
