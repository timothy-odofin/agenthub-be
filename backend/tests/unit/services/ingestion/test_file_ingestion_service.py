"""
Unit tests for FileIngestionService.

Tests the file ingestion service including:
- File type detection and MIME type handling
- Various loader mappings (PDF, DOCX, TXT, etc.)
- Archive handling (ZIP, TAR, GZIP)
- Vector store integration
- File processing and document chunking
- Error handling and validation
- Configuration validation
- Single file and batch processing
"""

import os
import tempfile
import zipfile
from pathlib import Path
from unittest.mock import Mock, patch, AsyncMock, MagicMock, call
from typing import List

import pytest
from langchain.schema import Document

from app.services.ingestion.file_ingestion_service import FileIngestionService
from app.services.ingestion.file_data_source_util import FileType
from app.core.constants import DataSourceType, EmbeddingType
from app.core.schemas.ingestion_config import DataSourceConfig


class TestFileIngestionServiceArchitecture:
    """Test suite for FileIngestionService class architecture."""

    @patch('app.core.config.application.AppConfig')
    def test_inheritance_from_base_ingestion_service(self, mock_app_config_class):
        """Test that FileIngestionService properly inherits from BaseIngestionService."""
        # Setup mock
        mock_app_config = Mock()
        mock_app_config_class.return_value = mock_app_config
        
        mock_ingestion_config = Mock()
        mock_data_source_config = Mock(spec=DataSourceConfig)
        mock_data_source_config.sources = ['/test/path']
        mock_ingestion_config.data_sources = {'file': mock_data_source_config}
        mock_app_config.ingestion_config = mock_ingestion_config
        
        with patch('os.path.exists', return_value=True):
            service = FileIngestionService()
            
            # Verify inheritance and source type
            assert service.SOURCE_TYPE == DataSourceType.FILE
            assert hasattr(service, 'text_splitter')  # From base class
            assert hasattr(service, '_processed_files')  # Service-specific
            assert hasattr(service, '_loader_mapping')  # Service-specific

    @patch('app.core.config.application.AppConfig')
    def test_initialization_sets_required_attributes(self, mock_app_config_class):
        """Test that initialization sets all required service attributes."""
        # Setup mock
        mock_app_config = Mock()
        mock_app_config_class.return_value = mock_app_config
        
        mock_ingestion_config = Mock()
        mock_data_source_config = Mock(spec=DataSourceConfig)
        mock_data_source_config.sources = ['/test/path']
        mock_ingestion_config.data_sources = {'file': mock_data_source_config}
        mock_app_config.ingestion_config = mock_ingestion_config
        
        with patch('os.path.exists', return_value=True), \
             patch('app.services.ingestion.file_data_source_util._construct_mapping') as mock_mapping, \
             patch('app.db.vector.providers.db_provider.VectorStoreFactory.get_default_vector_store') as mock_vector_store:
            
            mock_mapping.return_value = {FileType.TXT: ('TextLoader', {})}
            mock_vector_store.return_value = Mock()
            
            service = FileIngestionService()
            
            # Verify all attributes are set
            assert isinstance(service._processed_files, dict)
            assert service._loader_mapping is not None
            assert service._vector_store is not None
            assert service._embedding_type == EmbeddingType.DEFAULT


class TestFileIngestionServiceValidation:
    """Test suite for configuration validation."""

    @patch('app.core.config.application.AppConfig')
    def test_validate_config_success(self, mock_app_config_class):
        """Test successful configuration validation with existing paths."""
        mock_app_config = Mock()
        mock_app_config_class.return_value = mock_app_config
        
        mock_ingestion_config = Mock()
        mock_data_source_config = Mock(spec=DataSourceConfig)
        mock_data_source_config.sources = ['/existing/path1', '/existing/path2']
        mock_ingestion_config.data_sources = {'file': mock_data_source_config}
        mock_app_config.ingestion_config = mock_ingestion_config
        
        with patch('os.path.exists', return_value=True):
            service = FileIngestionService()
            # validate_config is called during initialization, no exception should occur
            assert service.config.sources == ['/existing/path1', '/existing/path2']

    @patch('app.core.config.application.AppConfig')
    def test_validate_config_no_sources(self, mock_app_config_class):
        """Test validation failure when no sources are provided."""
        mock_app_config = Mock()
        mock_app_config_class.return_value = mock_app_config
        
        mock_ingestion_config = Mock()
        mock_data_source_config = Mock(spec=DataSourceConfig)
        mock_data_source_config.sources = []  # Empty sources
        mock_ingestion_config.data_sources = {'file': mock_data_source_config}
        mock_app_config.ingestion_config = mock_ingestion_config
        
        with pytest.raises(ValueError, match="No sources paths provided in configuration"):
            FileIngestionService()

    @patch('app.core.config.application.AppConfig')
    def test_validate_config_nonexistent_path(self, mock_app_config_class):
        """Test validation failure when source path doesn't exist."""
        mock_app_config = Mock()
        mock_app_config_class.return_value = mock_app_config
        
        mock_ingestion_config = Mock()
        mock_data_source_config = Mock(spec=DataSourceConfig)
        mock_data_source_config.sources = ['/nonexistent/path']
        mock_ingestion_config.data_sources = {'file': mock_data_source_config}
        mock_app_config.ingestion_config = mock_ingestion_config
        
        with patch('os.path.exists', return_value=False):
            with pytest.raises(ValueError, match="Source path does not exist: /nonexistent/path"):
                FileIngestionService()


class TestFileIngestionServiceFileTypeDetection:
    """Test suite for file type detection functionality."""

    @patch('app.core.config.application.AppConfig')
    def test_detect_file_type_pdf(self, mock_app_config_class):
        """Test PDF file type detection."""
        mock_app_config = Mock()
        mock_app_config_class.return_value = mock_app_config
        
        mock_ingestion_config = Mock()
        mock_data_source_config = Mock(spec=DataSourceConfig)
        mock_data_source_config.sources = ['/test']
        mock_ingestion_config.data_sources = {'file': mock_data_source_config}
        mock_app_config.ingestion_config = mock_ingestion_config
        
        with patch('os.path.exists', return_value=True), \
             patch('magic.from_file', return_value='application/pdf'):
            service = FileIngestionService()
            file_type = service._detect_file_type('/test/file.pdf')
            assert file_type == FileType.PDF

    @patch('app.core.config.application.AppConfig')
    def test_detect_file_type_text(self, mock_app_config_class):
        """Test text file type detection."""
        mock_app_config = Mock()
        mock_app_config_class.return_value = mock_app_config
        
        mock_ingestion_config = Mock()
        mock_data_source_config = Mock(spec=DataSourceConfig)
        mock_data_source_config.sources = ['/test']
        mock_ingestion_config.data_sources = {'file': mock_data_source_config}
        mock_app_config.ingestion_config = mock_ingestion_config
        
        with patch('os.path.exists', return_value=True), \
             patch('magic.from_file', return_value='text/plain'):
            service = FileIngestionService()
            file_type = service._detect_file_type('/test/file.txt')
            assert file_type == FileType.TXT

    @patch('app.core.config.application.AppConfig')
    def test_detect_file_type_unsupported(self, mock_app_config_class):
        """Test handling of unsupported file types."""
        mock_app_config = Mock()
        mock_app_config_class.return_value = mock_app_config
        
        mock_ingestion_config = Mock()
        mock_data_source_config = Mock(spec=DataSourceConfig)
        mock_data_source_config.sources = ['/test']
        mock_ingestion_config.data_sources = {'file': mock_data_source_config}
        mock_app_config.ingestion_config = mock_ingestion_config
        
        with patch('os.path.exists', return_value=True), \
             patch('magic.from_file', return_value='application/unknown'):
            service = FileIngestionService()
            
            with pytest.raises(ValueError, match="Unsupported MIME type: application/unknown"):
                service._detect_file_type('/test/file.unknown')


class TestFileIngestionServiceDocumentLoading:
    """Test suite for document loading functionality."""

    @patch('app.core.config.application.AppConfig')
    def test_load_document_text_file(self, mock_app_config_class):
        """Test loading a text document."""
        mock_app_config = Mock()
        mock_app_config_class.return_value = mock_app_config
        
        mock_ingestion_config = Mock()
        mock_data_source_config = Mock(spec=DataSourceConfig)
        mock_data_source_config.sources = ['/test']
        mock_ingestion_config.data_sources = {'file': mock_data_source_config}
        mock_app_config.ingestion_config = mock_ingestion_config
        
        # Mock loader instance and class
        mock_loader = Mock()
        mock_document = Document(page_content="Test content", metadata={"source": "/test/file.txt"})
        mock_loader.load.return_value = [mock_document]
        
        mock_loader_class = Mock(return_value=mock_loader)
        mock_loader_class.__name__ = "TextLoader"  # For logging
        
        with patch('os.path.exists', return_value=True), \
             patch('magic.from_file', return_value='text/plain'), \
             patch('app.services.ingestion.file_data_source_util._construct_mapping') as mock_mapping:
            
            mock_mapping.return_value = {FileType.TXT: (mock_loader_class, {})}
            
            service = FileIngestionService()
            
            # Directly override the loader mapping after service creation
            service._loader_mapping = {FileType.TXT: (mock_loader_class, {})}
            
            documents = service._load_document('/test/file.txt')
            
            assert len(documents) == 1
            assert documents[0].page_content == "Test content"
            mock_loader_class.assert_called_once_with('/test/file.txt')
            mock_loader.load.assert_called_once()

    @patch('app.core.config.application.AppConfig')
    def test_load_document_pdf_with_config(self, mock_app_config_class):
        """Test loading a PDF document with loader configuration."""
        mock_app_config = Mock()
        mock_app_config_class.return_value = mock_app_config
        
        mock_ingestion_config = Mock()
        mock_data_source_config = Mock(spec=DataSourceConfig)
        mock_data_source_config.sources = ['/test']
        mock_ingestion_config.data_sources = {'file': mock_data_source_config}
        mock_app_config.ingestion_config = mock_ingestion_config
        
        # Mock loader instance and class
        mock_loader = Mock()
        mock_document = Document(page_content="PDF content", metadata={"source": "/test/file.pdf"})
        mock_loader.load.return_value = [mock_document]
        
        mock_loader_class = Mock(return_value=mock_loader)
        mock_loader_class.__name__ = "UnstructuredPDFLoader"  # For logging
        
        with patch('os.path.exists', return_value=True), \
             patch('magic.from_file', return_value='application/pdf'), \
             patch('app.services.ingestion.file_data_source_util._construct_mapping') as mock_mapping:
            
            pdf_config = {"strategy": "hi-res", "mode": "elements"}
            mock_mapping.return_value = {FileType.PDF: (mock_loader_class, pdf_config)}
            
            service = FileIngestionService()
            
            # Directly override the loader mapping after service creation
            service._loader_mapping = {FileType.PDF: (mock_loader_class, pdf_config)}
            
            documents = service._load_document('/test/file.pdf')
            
            assert len(documents) == 1
            assert documents[0].page_content == "PDF content"
            mock_loader_class.assert_called_once_with('/test/file.pdf')

    @patch('app.core.config.application.AppConfig')
    def test_load_document_unsupported_type(self, mock_app_config_class):
        """Test handling of unsupported file types during loading."""
        mock_app_config = Mock()
        mock_app_config_class.return_value = mock_app_config
        
        mock_ingestion_config = Mock()
        mock_data_source_config = Mock(spec=DataSourceConfig)
        mock_data_source_config.sources = ['/test']
        mock_ingestion_config.data_sources = {'file': mock_data_source_config}
        mock_app_config.ingestion_config = mock_ingestion_config
        
        with patch('os.path.exists', return_value=True), \
             patch('magic.from_file', return_value='text/plain'), \
             patch('app.services.ingestion.file_data_source_util._construct_mapping') as mock_mapping:
            
            mock_mapping.return_value = {}  # No mapping for TXT type
            
            service = FileIngestionService()
            
            # Directly override the loader mapping to be empty
            service._loader_mapping = {}
            
            with pytest.raises(ValueError, match="Unsupported file type: FileType.TXT"):
                service._load_document('/test/file.txt')


class TestFileIngestionServiceArchiveHandling:
    """Test suite for archive file handling."""

    @patch('app.core.config.application.AppConfig')
    def test_handle_zip_archive(self, mock_app_config_class):
        """Test ZIP archive handling."""
        mock_app_config = Mock()
        mock_app_config_class.return_value = mock_app_config
        
        mock_ingestion_config = Mock()
        mock_data_source_config = Mock(spec=DataSourceConfig)
        mock_data_source_config.sources = ['/test']
        mock_ingestion_config.data_sources = {'file': mock_data_source_config}
        mock_app_config.ingestion_config = mock_ingestion_config
        
        with patch('os.path.exists', return_value=True), \
             patch('app.services.ingestion.file_data_source_util._construct_mapping') as mock_mapping:
            
            # Mock text loader instance and class for extracted files
            mock_loader = Mock()
            mock_document = Document(page_content="Archive content", metadata={"source": "/temp/extracted.txt"})
            mock_loader.load.return_value = [mock_document]
            
            mock_loader_class = Mock(return_value=mock_loader)
            mock_loader_class.__name__ = "TextLoader"  # For logging
            mock_mapping.return_value = {FileType.TXT: (mock_loader_class, {})}
            
            service = FileIngestionService()
            
            # Override the loader mapping to use our mock
            service._loader_mapping = {FileType.TXT: (mock_loader_class, {})}
            
            # Mock zipfile and temporary directory
            with patch('tempfile.TemporaryDirectory') as mock_temp_dir, \
                 patch('zipfile.ZipFile') as mock_zip, \
                 patch('os.walk') as mock_walk, \
                 patch('magic.from_file', return_value='text/plain'):
                
                mock_temp_dir.return_value.__enter__.return_value = '/temp'
                mock_zip.return_value.__enter__ = Mock(return_value=Mock())
                mock_zip.return_value.__enter__.return_value.extractall = Mock()
                mock_walk.return_value = [('/temp', [], ['extracted.txt'])]
                
                documents = service._handle_archive('/test/archive.zip', FileType.ZIP)
                
                assert len(documents) == 1
                assert documents[0].page_content == "Archive content"
                # Check that archive metadata was added
                assert documents[0].metadata.get("archive_source") == '/test/archive.zip'
                assert documents[0].metadata.get("archive_path") == 'extracted.txt'

    @patch('app.core.config.application.AppConfig')
    def test_handle_rar_archive_not_implemented(self, mock_app_config_class):
        """Test that RAR archive handling raises NotImplementedError."""
        mock_app_config = Mock()
        mock_app_config_class.return_value = mock_app_config
        
        mock_ingestion_config = Mock()
        mock_data_source_config = Mock(spec=DataSourceConfig)
        mock_data_source_config.sources = ['/test']
        mock_ingestion_config.data_sources = {'file': mock_data_source_config}
        mock_app_config.ingestion_config = mock_ingestion_config
        
        with patch('os.path.exists', return_value=True):
            service = FileIngestionService()
            
            with pytest.raises(NotImplementedError, match="RAR support requires"):
                service._handle_archive('/test/archive.rar', FileType.RAR)


class TestFileIngestionServiceSingleFileProcessing:
    """Test suite for single file processing."""

    @patch('app.core.config.application.AppConfig')
    @pytest.mark.asyncio
    async def test_ingest_single_success(self, mock_app_config_class):
        """Test successful single file ingestion."""
        mock_app_config = Mock()
        mock_app_config_class.return_value = mock_app_config
        
        mock_ingestion_config = Mock()
        mock_data_source_config = Mock(spec=DataSourceConfig)
        mock_data_source_config.sources = ['/test']
        mock_ingestion_config.data_sources = {'file': mock_data_source_config}
        mock_app_config.ingestion_config = mock_ingestion_config
        
        with patch('os.path.exists', return_value=True):
            service = FileIngestionService()
            
            # Mock vector store
            mock_vector_store = AsyncMock()
            mock_vector_store.get_connection = AsyncMock()
            mock_vector_store.save_and_embed = AsyncMock(return_value=['doc_id_1', 'doc_id_2'])
            service._vector_store = mock_vector_store
            
            # Mock _process_file method
            mock_documents = [
                Document(page_content="Content 1", metadata={"source": "/test/file.txt"}),
                Document(page_content="Content 2", metadata={"source": "/test/file.txt"})
            ]
            
            with patch.object(service, '_process_file', return_value=mock_documents):
                result = await service.ingest_single('/test/file.txt')
                
                assert result is True
                assert service._processed_files['/test/file.txt'] is True
                mock_vector_store.get_connection.assert_called_once()
                mock_vector_store.save_and_embed.assert_called_once_with(
                    EmbeddingType.DEFAULT, mock_documents
                )

    @patch('app.core.config.application.AppConfig')
    @pytest.mark.asyncio
    async def test_ingest_single_no_documents(self, mock_app_config_class):
        """Test single file ingestion when no documents are extracted."""
        mock_app_config = Mock()
        mock_app_config_class.return_value = mock_app_config
        
        mock_ingestion_config = Mock()
        mock_data_source_config = Mock(spec=DataSourceConfig)
        mock_data_source_config.sources = ['/test']
        mock_ingestion_config.data_sources = {'file': mock_data_source_config}
        mock_app_config.ingestion_config = mock_ingestion_config
        
        with patch('os.path.exists', return_value=True):
            service = FileIngestionService()
            
            # Mock vector store
            mock_vector_store = AsyncMock()
            mock_vector_store.get_connection = AsyncMock()
            service._vector_store = mock_vector_store
            
            # Mock _process_file to return empty list
            with patch.object(service, '_process_file', return_value=[]):
                result = await service.ingest_single('/test/file.txt')
                
                assert result is False
                assert service._processed_files['/test/file.txt'] is False
                mock_vector_store.get_connection.assert_called_once()
                mock_vector_store.save_and_embed.assert_not_called()

    @patch('app.core.config.application.AppConfig')
    @pytest.mark.asyncio
    async def test_ingest_single_error_handling(self, mock_app_config_class):
        """Test error handling during single file ingestion."""
        mock_app_config = Mock()
        mock_app_config_class.return_value = mock_app_config
        
        mock_ingestion_config = Mock()
        mock_data_source_config = Mock(spec=DataSourceConfig)
        mock_data_source_config.sources = ['/test']
        mock_ingestion_config.data_sources = {'file': mock_data_source_config}
        mock_app_config.ingestion_config = mock_ingestion_config
        
        with patch('os.path.exists', return_value=True):
            service = FileIngestionService()
            
            # Mock vector store to raise exception
            mock_vector_store = AsyncMock()
            mock_vector_store.get_connection = AsyncMock(side_effect=Exception("Vector store error"))
            service._vector_store = mock_vector_store
            
            result = await service.ingest_single('/test/file.txt')
            
            assert result is False
            assert service._processed_files['/test/file.txt'] is False


class TestFileIngestionServiceBatchProcessing:
    """Test suite for batch file processing."""

    @patch('app.core.config.application.AppConfig')
    @pytest.mark.asyncio
    async def test_ingest_multiple_sources_success(self, mock_app_config_class):
        """Test successful ingestion of multiple sources."""
        mock_app_config = Mock()
        mock_app_config_class.return_value = mock_app_config
        
        mock_ingestion_config = Mock()
        mock_data_source_config = Mock(spec=DataSourceConfig)
        mock_data_source_config.sources = ['/test/folder1', '/test/folder2']
        mock_ingestion_config.data_sources = {'file': mock_data_source_config}
        mock_app_config.ingestion_config = mock_ingestion_config
        
        with patch('os.path.exists', return_value=True):
            service = FileIngestionService()
            
            # Mock _process_files_in_folder
            with patch.object(service, '_process_files_in_folder', return_value=True) as mock_process:
                result = await service.ingest()
                
                assert result is True
                assert mock_process.call_count == 2
                mock_process.assert_has_calls([
                    call('/test/folder1'),
                    call('/test/folder2')
                ])

    @patch('app.core.config.application.AppConfig')  
    @pytest.mark.asyncio
    async def test_ingest_with_folder_error(self, mock_app_config_class):
        """Test ingestion with error in one folder."""
        mock_app_config = Mock()
        mock_app_config_class.return_value = mock_app_config
        
        mock_ingestion_config = Mock()
        mock_data_source_config = Mock(spec=DataSourceConfig)
        mock_data_source_config.sources = ['/test/folder1', '/test/folder2']
        mock_ingestion_config.data_sources = {'file': mock_data_source_config}
        mock_app_config.ingestion_config = mock_ingestion_config
        
        with patch('os.path.exists', return_value=True):
            service = FileIngestionService()
            
            # Mock _process_files_in_folder to raise exception for first folder
            def mock_process_side_effect(path):
                if path == '/test/folder1':
                    raise Exception("Processing error")
                return True
            
            with patch.object(service, '_process_files_in_folder', side_effect=mock_process_side_effect):
                result = await service.ingest()
                
                assert result is False
                assert service._processed_files['/test/folder1'] is False

    @patch('app.core.config.application.AppConfig')
    @pytest.mark.asyncio
    async def test_process_files_in_folder(self, mock_app_config_class):
        """Test processing all files in a folder."""
        mock_app_config = Mock()
        mock_app_config_class.return_value = mock_app_config
        
        mock_ingestion_config = Mock()
        mock_data_source_config = Mock(spec=DataSourceConfig)
        mock_data_source_config.sources = ['/test']
        mock_ingestion_config.data_sources = {'file': mock_data_source_config}
        mock_app_config.ingestion_config = mock_ingestion_config
        
        with patch('os.path.exists', return_value=True):
            service = FileIngestionService()
            
            # Mock Path.iterdir() to return test files
            mock_file1 = Mock()
            mock_file1.is_file.return_value = True
            mock_file1.__str__ = Mock(return_value='/test/file1.txt')
            
            mock_file2 = Mock()
            mock_file2.is_file.return_value = True
            mock_file2.__str__ = Mock(return_value='/test/file2.txt')
            
            mock_dir = Mock()
            mock_dir.is_file.return_value = False
            
            with patch.object(service, 'ingest_single', return_value=True) as mock_ingest_single:
                # Mock pathlib.Path used in the actual service module
                with patch('app.services.ingestion.file_ingestion_service.Path') as mock_path_class:
                    mock_path = Mock()
                    mock_path.iterdir.return_value = [mock_file1, mock_file2, mock_dir]
                    mock_path_class.return_value = mock_path
                    
                    result = await service._process_files_in_folder('/test')
                    
                    assert result is True
                    assert mock_ingest_single.call_count == 2
                    mock_ingest_single.assert_has_calls([
                        call('/test/file1.txt'),
                        call('/test/file2.txt')
                    ])


class TestFileIngestionServiceUtilityMethods:
    """Test suite for utility methods."""

    @patch('app.core.config.application.AppConfig')
    def test_get_processed_files_status(self, mock_app_config_class):
        """Test getting processed files status."""
        mock_app_config = Mock()
        mock_app_config_class.return_value = mock_app_config
        
        mock_ingestion_config = Mock()
        mock_data_source_config = Mock(spec=DataSourceConfig)
        mock_data_source_config.sources = ['/test']
        mock_ingestion_config.data_sources = {'file': mock_data_source_config}
        mock_app_config.ingestion_config = mock_ingestion_config
        
        with patch('os.path.exists', return_value=True):
            service = FileIngestionService()
            
            # Add some processed files
            service._processed_files = {
                '/test/file1.txt': True,
                '/test/file2.txt': False
            }
            
            status = service.get_processed_files_status()
            
            assert status == {'/test/file1.txt': True, '/test/file2.txt': False}
            # Verify it returns a copy
            status['/test/file3.txt'] = True
            assert '/test/file3.txt' not in service._processed_files

    @patch('app.core.config.application.AppConfig')
    def test_set_embedding_type(self, mock_app_config_class):
        """Test setting embedding type."""
        mock_app_config = Mock()
        mock_app_config_class.return_value = mock_app_config
        
        mock_ingestion_config = Mock()
        mock_data_source_config = Mock(spec=DataSourceConfig)
        mock_data_source_config.sources = ['/test']
        mock_ingestion_config.data_sources = {'file': mock_data_source_config}
        mock_app_config.ingestion_config = mock_ingestion_config
        
        with patch('os.path.exists', return_value=True):
            service = FileIngestionService()
            
            assert service._embedding_type == EmbeddingType.DEFAULT
            
            service.set_embedding_type(EmbeddingType.OPENAI)
            assert service._embedding_type == EmbeddingType.OPENAI

    @patch('app.core.config.application.AppConfig')
    @pytest.mark.asyncio
    async def test_close_vector_store(self, mock_app_config_class):
        """Test closing vector store connection."""
        mock_app_config = Mock()
        mock_app_config_class.return_value = mock_app_config
        
        mock_ingestion_config = Mock()
        mock_data_source_config = Mock(spec=DataSourceConfig)
        mock_data_source_config.sources = ['/test']
        mock_ingestion_config.data_sources = {'file': mock_data_source_config}
        mock_app_config.ingestion_config = mock_ingestion_config
        
        with patch('os.path.exists', return_value=True):
            service = FileIngestionService()
            
            # Mock vector store
            mock_vector_store = AsyncMock()
            mock_vector_store.close_connection = AsyncMock()
            service._vector_store = mock_vector_store
            
            await service.close()
            
            mock_vector_store.close_connection.assert_called_once()

    @patch('app.core.config.application.AppConfig')
    @pytest.mark.asyncio
    async def test_close_with_none_vector_store(self, mock_app_config_class):
        """Test closing when vector store is None."""
        mock_app_config = Mock()
        mock_app_config_class.return_value = mock_app_config
        
        mock_ingestion_config = Mock()
        mock_data_source_config = Mock(spec=DataSourceConfig)
        mock_data_source_config.sources = ['/test']
        mock_ingestion_config.data_sources = {'file': mock_data_source_config}
        mock_app_config.ingestion_config = mock_ingestion_config
        
        with patch('os.path.exists', return_value=True):
            service = FileIngestionService()
            service._vector_store = None
            
            # Should not raise exception
            await service.close()


class TestFileIngestionServiceDocumentProcessing:
    """Test suite for document processing and chunking."""

    @patch('app.core.config.application.AppConfig')
    @pytest.mark.asyncio
    async def test_process_file_with_chunking(self, mock_app_config_class):
        """Test file processing with document chunking."""
        mock_app_config = Mock()
        mock_app_config_class.return_value = mock_app_config
        
        mock_ingestion_config = Mock()
        mock_data_source_config = Mock(spec=DataSourceConfig)
        mock_data_source_config.sources = ['/test']
        mock_ingestion_config.data_sources = {'file': mock_data_source_config}
        mock_app_config.ingestion_config = mock_ingestion_config
        
        with patch('os.path.exists', return_value=True):
            service = FileIngestionService()
            
            # Mock document loading and chunking
            original_doc = Document(page_content="Long content", metadata={"source": "/test/file.txt"})
            chunk1 = Document(page_content="Long", metadata={"source": "/test/file.txt"})
            chunk2 = Document(page_content="content", metadata={"source": "/test/file.txt"})
            
            with patch.object(service, '_load_document', return_value=[original_doc]) as mock_load, \
                 patch.object(service.text_splitter, 'split_documents', return_value=[chunk1, chunk2]) as mock_split:
                
                result = await service._process_file('/test/file.txt')
                
                assert len(result) == 2
                assert result[0].page_content == "Long"
                assert result[1].page_content == "content"
                
                mock_load.assert_called_once_with('/test/file.txt')
                mock_split.assert_called_once_with([original_doc])
