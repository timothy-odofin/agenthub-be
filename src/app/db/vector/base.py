"""
Abstract base class for vector database operations.
"""
import hashlib
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from langchain.schema import Document
from langchain.schema.retriever import BaseRetriever

from ...core.constants import EmbeddingType


@dataclass
class DocumentMetadata:
    """Metadata for tracking documents in vector store."""
    document_id: str
    source_path: str
    file_type: str
    embedded_at: datetime
    custom_metadata: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def create_hash(cls, content: str) -> str:
        """Create SHA-256 hash of content for change detection."""
        return hashlib.sha256(content.encode()).hexdigest()
    
    @classmethod
    def get_change_detection_info(cls, source_path: str) -> Dict[str, Any]:
        """
        Get change detection information appropriate for the sources type.
        Uses efficient file metadata instead of expensive hashing.
        
        Args:
            source_path: Path to sources
            
        Returns:
            Dict with change detection metadata
        """
        info = {
            "source_path": source_path,
            "source_type": "url" if "://" in source_path else "local_file",
            "timestamp": datetime.now().isoformat()
        }
        
        # For local files, add file metadata (fast operations)
        if info["source_type"] == "local_file":
            try:
                path_obj = Path(source_path)
                if path_obj.exists():
                    stat = path_obj.stat()
                    info.update({
                        "file_size": stat.st_size,
                        "modified_time": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                        "creation_time": datetime.fromtimestamp(stat.st_ctime).isoformat(),
                        "inode": stat.st_ino,  # Additional change detection
                        # Removed file_hash - it's expensive and unnecessary!
                    })
            except (OSError, ValueError):
                pass
        
        return info
    
    @classmethod
    def generate_document_id(cls, source_path: str) -> str:
        """
        Generate a deterministic document ID based on sources path only.
        This ensures the same sources always gets the same document ID,
        regardless of how many chunks it has.
        
        Args:
            source_path: Path to the sources (local file, URL, database ID, etc.)
            
        Returns:
            Deterministic document ID (without chunk information)
        """
        # Normalize the sources path for consistency
        normalized_path = cls._normalize_source_path(source_path)
        
        # Create a deterministic ID using normalized path only
        return hashlib.sha256(normalized_path.encode()).hexdigest()[:32]  # 32 char hex string



class VectorDB(ABC):
    """Abstract base class for vector database implementations."""
    
    def __init__(self):
        self.config = self.get_vector_db_config()
        self._connection = None
    
    @abstractmethod
    def get_vector_db_config(self) -> Dict[str, Any]:
        """
        Each implementation provides its own configuration.
        
        Returns:
            Dict containing configuration parameters specific to the vector DB.
        """
        pass
    
    @abstractmethod
    async def _create_connection(self):
        """Create and return a connection to the vector database."""
        pass
    
    @abstractmethod
    async def save_and_embed(
        self, 
        embedding_type: EmbeddingType, 
        docs: List[Document]
    ) -> List[str]:
        """
        Save documents and generate embeddings.
        
        Args:
            embedding_type: Type of embedding to use
            docs: List of documents to save and embed
            
        Returns:
            List of document IDs that were created
        """
        pass
    
    @abstractmethod
    async def update_document(
        self, 
        document_id: str, 
        updated_doc: Document, 
        embedding_type: EmbeddingType
    ) -> bool:
        """
        Update an existing document.
        
        Args:
            document_id: ID of document to update
            updated_doc: New document content
            embedding_type: Type of embedding to use
            
        Returns:
            True if update was successful, False otherwise
        """
        pass
    
    @abstractmethod
    async def delete_by_document_id(self, document_id: str) -> bool:
        """
        Delete all chunks of a document by its ID.
        
        Args:
            document_id: ID of document to delete
            
        Returns:
            True if deletion was successful, False otherwise
        """
        pass
    
    @abstractmethod
    async def get_document_metadata(self, document_id: str) -> Optional[DocumentMetadata]:
        """
        Get metadata for a document.
        
        Args:
            document_id: ID of document to get metadata for
            
        Returns:
            DocumentMetadata if found, None otherwise
        """
        pass
    
    async def check_document_exists(self, source_path: str) -> Optional[DocumentMetadata]:
        """
        Check if a document from a specific sources path exists in the vector store.
        Returns metadata of the first chunk if found.
        
        Args:
            source_path: Path to the sources to check (local file, URL, etc.)
            
        Returns:
            DocumentMetadata if document exists, None otherwise
        """
        # Look for any chunk of this document (start with chunk 0)
        chunk_id = DocumentMetadata.generate_chunk_id(source_path, chunk_index=0)
        return await self.get_document_metadata(chunk_id)
    

    
    async def re_embed_document(
        self, 
        source_path: str, 
        new_docs: List[Document], 
        embedding_type: EmbeddingType
    ) -> bool:
        """
        Re-embed a document by replacing all its chunks with new ones.
        This is the recommended way to update documents.
        
        Args:
            source_path: Path to the sources
            new_docs: New document chunks to embed
            embedding_type: Type of embedding to use
            
        Returns:
            True if re-embedding was successful
        """
        # First, delete all existing chunks of this document
        await self.delete_document_by_file_path(source_path)
        
        # Then embed the new document chunks
        chunk_ids = await self.save_and_embed(embedding_type, new_docs)
        
        return len(chunk_ids) > 0
    
    @abstractmethod
    async def search_similar(
        self, 
        query: str, 
        k: int = 5, 
        filter_criteria: Optional[Dict[str, Any]] = None
    ) -> List[Document]:
        """
        Search for similar documents.
        
        Args:
            query: Search query text
            k: Number of results to return
            filter_criteria: Optional metadata filters
            
        Returns:
            List of similar documents
        """
        pass
    
    @abstractmethod
    def as_retriever(self, **kwargs) -> BaseRetriever:
        """
        Expose as LangChain retriever for use in chains.
        
        Args:
            **kwargs: Additional retriever configuration
            
        Returns:
            BaseRetriever instance
        """
        pass
    
    async def get_connection(self):
        """Get or create database connection."""
        if self._connection is None:
            # Check if _create_connection is async or sync
            import asyncio
            import inspect
            
            if inspect.iscoroutinefunction(self._create_connection):
                # Async connection
                self._connection = await self._create_connection()
            else:
                # Sync connection 
                self._connection = self._create_connection()
        return self._connection
    
    async def close_connection(self):
        """Close database connection."""
        if self._connection:
            # Check if _close_connection is async or sync
            import asyncio
            import inspect
            
            if inspect.iscoroutinefunction(self._close_connection):
                # Async close
                await self._close_connection()
            else:
                # Sync close 
                self._close_connection()
            self._connection = None
    
    @abstractmethod
    async def _close_connection(self):
        """Implementation-specific connection closing."""
        pass

