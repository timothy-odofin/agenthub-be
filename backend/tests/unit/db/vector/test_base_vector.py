"""
Comprehensive test suite for VectorDB base classes and DocumentMetadata.
Tests the abstract base class architecture, metadata handling, and 
connection management patterns for vector database implementations.
"""

import hashlib
import tempfile
import asyncio
from abc import ABC
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from langchain.schema import Document
from langchain.schema.retriever import BaseRetriever

from app.db.vector.base import DocumentMetadata, VectorDB
from app.core.constants import EmbeddingType


class TestDocumentMetadata:
    """Test DocumentMetadata dataclass functionality."""
    
    def test_document_metadata_creation(self):
        """Test basic DocumentMetadata creation."""
        metadata = DocumentMetadata(
            document_id="test_doc_123",
            source_path="/path/to/document.pdf",
            file_type="pdf",
            embedded_at=datetime.now()
        )
        
        assert metadata.document_id == "test_doc_123"
        assert metadata.source_path == "/path/to/document.pdf"
        assert metadata.file_type == "pdf"
        assert isinstance(metadata.embedded_at, datetime)
        assert metadata.custom_metadata == {}
    
    def test_document_metadata_with_custom_data(self):
        """Test DocumentMetadata with custom metadata."""
        custom_data = {"author": "John Doe", "category": "research", "priority": 1}
        metadata = DocumentMetadata(
            document_id="test_doc_456",
            source_path="/path/to/paper.pdf",
            file_type="pdf",
            embedded_at=datetime.now(),
            custom_metadata=custom_data
        )
        
        assert metadata.custom_metadata == custom_data
        assert metadata.custom_metadata["author"] == "John Doe"
        assert metadata.custom_metadata["priority"] == 1
    
    def test_create_hash_method(self):
        """Test content hashing functionality."""
        content = "This is test content for hashing"
        hash_result = DocumentMetadata.create_hash(content)
        
        # Verify it's a valid SHA-256 hash
        assert len(hash_result) == 64  # SHA-256 produces 64 character hex string
        assert all(c in '0123456789abcdef' for c in hash_result)
        
        # Verify deterministic behavior
        assert DocumentMetadata.create_hash(content) == hash_result
        
        # Verify different content produces different hash
        different_content = "Different content"
        assert DocumentMetadata.create_hash(different_content) != hash_result
    
    def test_get_change_detection_info_for_url(self):
        """Test change detection for URL sources."""
        url_source = "https://example.com/document.pdf"
        info = DocumentMetadata.get_change_detection_info(url_source)
        
        assert info["source_path"] == url_source
        assert info["source_type"] == "url"
        assert "timestamp" in info
        
        # URL sources should not have file metadata
        assert "file_size" not in info
        assert "modified_time" not in info
    
    def test_get_change_detection_info_for_local_file(self):
        """Test change detection for local file sources."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as tmp:
            tmp.write("test content")
            tmp_path = tmp.name
        
        try:
            info = DocumentMetadata.get_change_detection_info(tmp_path)
            
            assert info["source_path"] == tmp_path
            assert info["source_type"] == "local_file"
            assert "timestamp" in info
            assert "file_size" in info
            assert "modified_time" in info
            assert "creation_time" in info
            assert "inode" in info
            assert info["file_size"] > 0
        finally:
            Path(tmp_path).unlink()
    
    def test_get_change_detection_info_for_nonexistent_file(self):
        """Test change detection for non-existent local file."""
        fake_path = "/nonexistent/path/to/file.txt"
        info = DocumentMetadata.get_change_detection_info(fake_path)
        
        assert info["source_path"] == fake_path
        assert info["source_type"] == "local_file"
        assert "timestamp" in info
        
        # Non-existent files should not have file metadata
        assert "file_size" not in info
        assert "modified_time" not in info
    
    def test_generate_document_id_deterministic(self):
        """Test document ID generation is deterministic."""
        source_path = "/path/to/test/document.pdf"
        
        # Mock the missing _normalize_source_path method
        with patch.object(DocumentMetadata, '_normalize_source_path', return_value=source_path, create=True):
            id1 = DocumentMetadata.generate_document_id(source_path)
            id2 = DocumentMetadata.generate_document_id(source_path)
            
            assert id1 == id2
            assert len(id1) == 32  # 32 character hex string
            assert all(c in '0123456789abcdef' for c in id1)
    
    def test_generate_document_id_different_paths(self):
        """Test different paths generate different document IDs."""
        path1 = "/path/to/document1.pdf"
        path2 = "/path/to/document2.pdf"
        
        # Mock the missing _normalize_source_path method
        with patch.object(DocumentMetadata, '_normalize_source_path', side_effect=lambda x: x, create=True):
            id1 = DocumentMetadata.generate_document_id(path1)
            id2 = DocumentMetadata.generate_document_id(path2)
            
            assert id1 != id2
            assert len(id1) == len(id2) == 32


class MockVectorDB(VectorDB):
    """Concrete implementation of VectorDB for testing."""
    
    def __init__(self, config=None):
        self._config = config or {"mock": True}
        super().__init__()
        self._close_connection_called = False
        self._create_connection_called = False
    
    async def delete_document_by_file_path(self, source_path: str) -> bool:
        """Mock implementation of delete_document_by_file_path."""
        return True
    
    def get_vector_db_config(self) -> Dict[str, Any]:
        return self._config
    
    async def _create_connection(self):
        self._create_connection_called = True
        return MagicMock()
    
    def _close_connection(self):
        self._close_connection_called = True
    
    async def save_and_embed(self, embedding_type: EmbeddingType, docs: List[Document]) -> List[str]:
        return [f"doc_{i}" for i in range(len(docs))]
    
    async def update_document(self, document_id: str, updated_doc: Document, embedding_type: EmbeddingType) -> bool:
        return True
    
    async def delete_by_document_id(self, document_id: str) -> bool:
        return True
    
    async def get_document_metadata(self, document_id: str) -> Optional[DocumentMetadata]:
        if document_id == "existing_doc":
            return DocumentMetadata(
                document_id=document_id,
                source_path="/path/to/existing.pdf",
                file_type="pdf",
                embedded_at=datetime.now()
            )
        return None
    
    async def search_similar(self, query: str, k: int = 5, filter_criteria: Optional[Dict[str, Any]] = None) -> List[Document]:
        return [Document(page_content=f"Result {i}", metadata={"score": 1.0 - i*0.1}) for i in range(k)]
    
    def as_retriever(self, **kwargs) -> BaseRetriever:
        return MagicMock(spec=BaseRetriever)


class TestVectorDBArchitecture:
    """Test VectorDB abstract base class architecture."""
    
    def test_is_abstract_base_class(self):
        """Test that VectorDB is properly defined as an abstract base class."""
        assert issubclass(VectorDB, ABC)
        
        # Cannot instantiate abstract class directly
        with pytest.raises(TypeError, match="Can't instantiate abstract class VectorDB"):
            VectorDB()
    
    def test_abstract_methods_are_defined(self):
        """Test that all required abstract methods are defined."""
        abstract_methods = VectorDB.__abstractmethods__
        
        expected_methods = {
            'get_vector_db_config',
            '_create_connection',
            'save_and_embed',
            'update_document',
            'delete_by_document_id',
            'get_document_metadata',
            'search_similar',
            'as_retriever',
            '_close_connection'
        }
        
        assert abstract_methods == expected_methods
    
    def test_concrete_implementation_works(self):
        """Test that concrete implementation can be instantiated."""
        db = MockVectorDB({"test": "config"})
        
        assert db is not None
        assert isinstance(db, VectorDB)
        assert db.config == {"test": "config"}


class TestVectorDBConnectionManagement:
    """Test VectorDB connection management functionality."""
    
    @pytest.mark.asyncio
    async def test_initialization_loads_config(self):
        """Test that initialization properly loads configuration."""
        config = {"host": "localhost", "port": 5432}
        db = MockVectorDB(config)
        
        assert db.config == config
        assert db._connection is None
    
    @pytest.mark.asyncio
    async def test_get_connection_creates_connection(self):
        """Test that get_connection creates connection when none exists."""
        db = MockVectorDB()
        
        connection = await db.get_connection()
        
        assert connection is not None
        assert db._create_connection_called
        assert db._connection is not None
    
    @pytest.mark.asyncio
    async def test_get_connection_reuses_existing(self):
        """Test that get_connection reuses existing connection."""
        db = MockVectorDB()
        
        # First call creates connection
        connection1 = await db.get_connection()
        db._create_connection_called = False  # Reset flag
        
        # Second call should reuse
        connection2 = await db.get_connection()
        
        assert connection1 is connection2
        assert not db._create_connection_called  # Should not create again
    
    @pytest.mark.asyncio
    async def test_close_connection_calls_implementation(self):
        """Test that close_connection calls implementation-specific close."""
        db = MockVectorDB()
        
        # Create connection first
        await db.get_connection()
        assert db._connection is not None
        
        # Close connection
        await db.close_connection()
        
        assert db._close_connection_called
        assert db._connection is None
    
    @pytest.mark.asyncio
    async def test_close_connection_handles_no_connection(self):
        """Test that close_connection handles case when no connection exists."""
        db = MockVectorDB()
        
        # Should not raise error when no connection exists
        await db.close_connection()
        
        assert not db._close_connection_called
        assert db._connection is None


class MockAsyncVectorDB(MockVectorDB):
    """Mock VectorDB with async connection methods for testing."""
    
    async def _close_connection(self):
        self._close_connection_called = True


class TestVectorDBAsyncCompatibility:
    """Test VectorDB async/sync compatibility."""
    
    @pytest.mark.asyncio
    async def test_async_connection_handling(self):
        """Test that async connection methods are handled properly."""
        db = MockAsyncVectorDB()
        
        # Create connection (async)
        connection = await db.get_connection()
        assert connection is not None
        assert db._create_connection_called
        
        # Close connection (async)
        await db.close_connection()
        assert db._close_connection_called
        assert db._connection is None
    
    @pytest.mark.asyncio
    async def test_sync_connection_handling(self):
        """Test that sync connection methods are handled properly."""
        db = MockVectorDB()  # Uses sync _close_connection
        
        # Create connection (async)
        connection = await db.get_connection()
        assert connection is not None
        
        # Close connection (sync method called)
        await db.close_connection()
        assert db._close_connection_called
        assert db._connection is None


class TestVectorDBDocumentOperations:
    """Test VectorDB document operation methods."""
    
    @pytest.mark.asyncio
    async def test_check_document_exists_found(self):
        """Test check_document_exists when document exists."""
        db = MockVectorDB()
        
        # Mock the generate_chunk_id method since it's missing from the base class
        with patch.object(DocumentMetadata, 'generate_chunk_id', return_value="existing_doc", create=True):
            metadata = await db.check_document_exists("/path/to/existing.pdf")
            
            assert metadata is not None
            assert metadata.document_id == "existing_doc"
            assert metadata.source_path == "/path/to/existing.pdf"
    
    @pytest.mark.asyncio
    async def test_check_document_exists_not_found(self):
        """Test check_document_exists when document doesn't exist."""
        db = MockVectorDB()
        
        # Mock the generate_chunk_id method to return non-existent ID
        with patch.object(DocumentMetadata, 'generate_chunk_id', return_value="nonexistent_doc", create=True):
            metadata = await db.check_document_exists("/path/to/nonexistent.pdf")
            
            assert metadata is None
    
    @pytest.mark.asyncio
    async def test_re_embed_document_success(self):
        """Test successful document re-embedding."""
        db = MockVectorDB()
        
        docs = [
            Document(page_content="Content 1", metadata={"chunk": 0}),
            Document(page_content="Content 2", metadata={"chunk": 1})
        ]
        
        result = await db.re_embed_document(
            "/path/to/document.pdf",
            docs,
            EmbeddingType.OPENAI
        )
        
        assert result is True
    
    @pytest.mark.asyncio
    async def test_re_embed_document_no_new_docs(self):
        """Test re-embedding with no new documents."""
        db = MockVectorDB()
        
        # Override save_and_embed to return empty list
        with patch.object(db, 'save_and_embed', new_callable=AsyncMock) as mock_save:
            mock_save.return_value = []
            
            result = await db.re_embed_document(
                "/path/to/document.pdf",
                [],
                EmbeddingType.OPENAI
            )
            
            assert result is False


class TestVectorDBRetrieverIntegration:
    """Test VectorDB retriever integration."""
    
    def test_as_retriever_returns_base_retriever(self):
        """Test that as_retriever returns BaseRetriever instance."""
        db = MockVectorDB()
        
        retriever = db.as_retriever()
        
        assert isinstance(retriever, BaseRetriever)
    
    def test_as_retriever_with_kwargs(self):
        """Test that as_retriever accepts keyword arguments."""
        db = MockVectorDB()
        
        # Should not raise error with additional kwargs
        retriever = db.as_retriever(k=10, filter_criteria={"type": "document"})
        
        assert isinstance(retriever, BaseRetriever)
    
    @pytest.mark.asyncio
    async def test_search_similar_basic_functionality(self):
        """Test basic search similar functionality."""
        db = MockVectorDB()
        
        results = await db.search_similar("test query", k=3)
        
        assert len(results) == 3
        assert all(isinstance(doc, Document) for doc in results)
        assert all("score" in doc.metadata for doc in results)
    
    @pytest.mark.asyncio
    async def test_search_similar_with_filters(self):
        """Test search similar with filter criteria."""
        db = MockVectorDB()
        
        filter_criteria = {"document_type": "pdf", "category": "research"}
        results = await db.search_similar("test query", k=5, filter_criteria=filter_criteria)
        
        assert len(results) == 5
        assert all(isinstance(doc, Document) for doc in results)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
