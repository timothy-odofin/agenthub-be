
import os
from datetime import datetime
from enum import Enum
from typing import List, Dict

import magic
from langchain.schema import Document
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import (
    UnstructuredPDFLoader,
    UnstructuredFileLoader,
    Docx2txtLoader,
    UnstructuredPowerPointLoader,
    UnstructuredExcelLoader,
    UnstructuredImageLoader,
    TextLoader,
    UnstructuredMarkdownLoader,
    JSONLoader,
    UnstructuredXMLLoader,
    UnstructuredHTMLLoader,
    UnstructuredEmailLoader,
    UnstructuredRTFLoader
    
)

from app.services.ingestion.base import BaseIngestionService
from app.core.constants import DataSourceType, EmbeddingType
from app.core.schemas.ingestion_config import DataSourceConfig
from app.db.vector.factory import VectorStoreFactory


class FileType(str, Enum):
    """Supported file types and their MIME types."""
    PDF = 'application/pdf'
    DOC = 'application/msword'
    DOCX = 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
    XLS = 'application/vnd.ms-excel'
    XLSX = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    PPT = 'application/vnd.ms-powerpoint'
    PPTX = 'application/vnd.openxmlformats-officedocument.presentationml.presentation'
    TXT = 'text/plain'
    CSV = 'text/csv'
    JPEG = 'image/jpeg'
    PNG = 'image/png'
    TIFF = 'image/tiff'
    JSON = 'application/json'
    YAML = 'application/x-yaml'
    YML = 'application/x-yaml'
    MARKDOWN = 'text/markdown'
    MD = 'text/markdown'
    XML = 'application/xml'
    XML_ALT = 'text/xml'  # Alternative MIME type for XML
    HTML = 'text/html'
    HTM = 'text/html'
    CSS = 'text/css'
    JS = 'application/javascript'
    RTF = 'application/rtf'
    EML = 'message/rfc822'
    MSG = 'application/vnd.ms-outlook'
    ZIP = 'application/zip'
    RAR = 'application/x-rar-compressed'
    TAR = 'application/x-tar'
    GZIP = 'application/gzip'


class FileIngestionService(BaseIngestionService):
    def __init__(self, config: DataSourceConfig):
        super().__init__(config)
        self._processed_files: Dict[str, bool] = {}
        self._text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            length_function=len,
            is_separator_regex=False,
        )
        # Initialize loader mapping
        self._loader_mapping = self._construct_mapping()
        
        # Initialize vector store
        self._vector_store = VectorStoreFactory.get_default_vector_store()
        self._embedding_type = EmbeddingType.OPENAI_EMBEDDING  # Default embedding type

    def validate_config(self) -> None:
        """Validate the file ingestion configuration."""
        if not self.config.sources:
            raise ValueError("No sources paths provided in configuration")
        for path in self.config.sources:
            if not os.path.exists(path):
                raise ValueError(f"Source path does not exist: {path}")
 
    @property
    def source_type(self) -> DataSourceType:
        """Get the type of data sources this service handles."""
        return DataSourceType.FILE

    async def ingest(self) -> bool:
        """Ingest all files from the configured sources."""
        success = True
        all_documents = []
        
        # Ensure vector store connection
        await self._vector_store.get_connection()
        
        for source_path in self.config.sources:
            try:
                documents = await self._process_file(source_path)
                # Add source path to metadata for tracking
                for doc in documents:
                    doc.metadata.update({
                        "source_path": source_path,
                        "ingestion_timestamp": datetime.now().isoformat()
                    })
                all_documents.extend(documents)
                self._processed_files[source_path] = True
                print(f"Processed {source_path}: {len(documents)} chunks")
            except Exception as e:
                self._processed_files[source_path] = False
                success = False
                print(f"Error processing {source_path}: {str(e)}")
        
        # Save all documents to vector store if any were processed
        if all_documents:
            try:
                document_ids = await self._vector_store.save_and_embed(
                    self._embedding_type, 
                    all_documents
                )
                print(f"Successfully saved {len(document_ids)} document chunks to vector store")
            except Exception as e:
                print(f"Error saving documents to vector store: {str(e)}")
                success = False
        
        return success

    async def ingest_single(self, source: str) -> bool:
        """
        Ingest a single file source.
        
        Args:
            source: Path to the file to ingest
            
        Returns:
            bool: True if ingestion was successful
        """
        try:
            # Ensure vector store connection
            await self._vector_store.get_connection()
            
            # Process the file
            documents = await self._process_file(source)
            
            # Add metadata to documents
            for doc in documents:
                doc.metadata.update({
                    "source_path": source,
                    "ingestion_timestamp": datetime.now().isoformat()
                })
            
            # Save documents to vector store
            if documents:
                document_ids = await self._vector_store.save_and_embed(
                    self._embedding_type, 
                    documents
                )
                print(f"Successfully processed {source}: {len(document_ids)} chunks saved")
                self._processed_files[source] = True
                return True
            else:
                print(f"No documents extracted from {source}")
                self._processed_files[source] = False
                return False
                
        except Exception as e:
            self._processed_files[source] = False
            print(f"Error processing {source}: {str(e)}")
            return False


    def _construct_mapping(self):
        return {
            FileType.PDF: (UnstructuredPDFLoader, {
                "strategy": "fast",
                "mode": "elements",
                "ocr_enabled": True
            }),
            FileType.DOC: (UnstructuredFileLoader, {
                "mode": "elements",
                "strategy": "fast",
                "ocr_enabled": True,
                "preserve_formatting": True
            }),
            FileType.DOCX: (Docx2txtLoader, {
            }),
            FileType.XLS: (UnstructuredExcelLoader, {
                "mode": "elements",
                "strategy": "fast",
                "preserve_formatting": True,
                "include_header": True,
                "include_formulas": True
            }),
            FileType.XLSX: (UnstructuredExcelLoader, {
                "mode": "elements",
                "strategy": "fast",
                "preserve_formatting": True,
                "include_header": True,
                "include_formulas": True
            }),
            FileType.PPT: (UnstructuredPowerPointLoader, {
                "mode": "elements",
                "strategy": "fast",
                "ocr_enabled": True,
                "preserve_formatting": True
            }),
            FileType.PPTX: (UnstructuredPowerPointLoader, {
                "mode": "elements",
                "strategy": "fast",
                "ocr_enabled": True,
                "preserve_formatting": True
            }),
            FileType.JPEG: (UnstructuredImageLoader, {"mode": "elements", "strategy": "fast"}),
            FileType.PNG: (UnstructuredImageLoader, {"mode": "elements", "strategy": "fast"}),
            FileType.TIFF: (UnstructuredImageLoader, {"mode": "elements", "strategy": "fast"}),
            FileType.TXT: (TextLoader, {}),
            FileType.CSV: (TextLoader, {}),
            FileType.JSON: (JSONLoader, {
                "jq_schema": ".",  # Extract all content
                "text_content": False,  # Preserve JSON structure
                "metadata_func": lambda metadata: {"source_type": "json"}
            }),
            FileType.YAML: (TextLoader, {}),
            FileType.YML: (TextLoader, {}),
            FileType.MARKDOWN: (UnstructuredMarkdownLoader, {
                "mode": "elements",
                "strategy": "fast",
                "preserve_formatting": True
            }),
            FileType.MD: (UnstructuredMarkdownLoader, {
                "mode": "elements",
                "strategy": "fast",
                "preserve_formatting": True
            }),
            FileType.XML: (UnstructuredXMLLoader, {
                "mode": "elements",
                "strategy": "fast",
                "preserve_formatting": True,
                "include_metadata": True,
                "include_tags": True
            }),
            FileType.XML_ALT: (UnstructuredXMLLoader, {
                "mode": "elements",
                "strategy": "fast",
                "preserve_formatting": True,
                "include_metadata": True,
                "include_tags": True
            }),
            # HTML and Web Files
            FileType.HTML: (UnstructuredHTMLLoader, {
                "mode": "elements",
                "strategy": "fast",
                "preserve_formatting": True,
                "include_links": True
            }),
            FileType.HTM: (UnstructuredHTMLLoader, {
                "mode": "elements",
                "strategy": "fast",
                "preserve_formatting": True,
                "include_links": True
            }),
            FileType.CSS: (TextLoader, {}),
            FileType.JS: (TextLoader, {}),
            
            # Rich Text Format
            FileType.RTF: (UnstructuredRTFLoader, {
                "mode": "elements",
                "strategy": "fast",
                "preserve_formatting": True
            }),
            
            # Email Files
            FileType.EML: (UnstructuredEmailLoader, {
                "mode": "elements",
                "strategy": "fast",
                "include_headers": True,
                "include_attachments": True
            }),
            FileType.MSG: (UnstructuredEmailLoader, {
                "mode": "elements",
                "strategy": "fast",
                "include_headers": True,
                "include_attachments": True
            }),
            
            # Archive Files - These will need special handling in _load_document
            FileType.ZIP: (TextLoader, {}),
            FileType.RAR: (TextLoader, {}),
            FileType.TAR: (TextLoader, {}),
            FileType.GZIP: (TextLoader, {}),
        }
    
    async def _process_file(self, file_path: str) -> List[Document]:
        """
        Process a single file: detect type, load content, and split into chunks.
        """ 
       
        # Load documents
        documents = self._load_document(file_path)
        
        # Split into chunks
        return self._text_splitter.split_documents(documents)

    def _detect_file_type(self, file_path: str) -> FileType:
        """
        Detect the MIME type of a file and return corresponding FileType.
        """
        mime_type = magic.from_file(file_path, mime=True)
        try:
            return FileType(mime_type)
        except ValueError:
            raise ValueError(f"Unsupported MIME type: {mime_type}")

    def _load_document(self, file_path: str) -> List[Document]:
        """
        Load a document using the appropriate loader based on file type.
        
        Args:
            file_path: Path to the file to load
            
        Returns:
            List[Document]: Loaded documents
            
        Raises:
            ValueError: If file type is not supported
        """
        file_type = self._detect_file_type(file_path)
        
        if file_type not in self._loader_mapping:
            raise ValueError(f"Unsupported file type: {file_type}")

        # Special handling for archives
        if file_type in [FileType.ZIP, FileType.RAR, FileType.TAR, FileType.GZIP]:
            return self._handle_archive(file_path, file_type)
        
        # Standard handling for other file types
        loader_class, loader_config = self._loader_mapping[file_type]
        loader = loader_class(file_path, **loader_config)
        return loader.load()

    def _handle_archive(self, file_path: str, file_type: FileType) -> List[Document]:
        """
        Handle archive files by extracting and processing their contents.
        Directly loads extracted files without recursive archive handling.
        """
        import tempfile
        import zipfile
        import tarfile
        import gzip
        import shutil

        documents = []
        with tempfile.TemporaryDirectory() as temp_dir:
            # Extract archive based on type
            if file_type == FileType.ZIP:
                with zipfile.ZipFile(file_path, 'r') as zip_ref:
                    zip_ref.extractall(temp_dir)
            elif file_type == FileType.RAR:
                # Note: RAR support requires additional setup
                raise NotImplementedError("RAR support requires the 'rarfile' package and external RAR binary")
            elif file_type == FileType.TAR:
                with tarfile.open(file_path, 'r') as tar_ref:
                    tar_ref.extractall(temp_dir)
            elif file_type == FileType.GZIP:
                output_path = os.path.join(temp_dir, 'extracted_file')
                with gzip.open(file_path, 'rb') as f_in:
                    with open(output_path, 'wb') as f_out:
                        shutil.copyfileobj(f_in, f_out)

            # Process each extracted file
            for root, _, files in os.walk(temp_dir):
                for file in files:
                    extracted_path = os.path.join(root, file)
                    try:
                        # Detect the file type
                        mime_type = magic.from_file(extracted_path, mime=True)
                        relative_path = os.path.relpath(extracted_path, temp_dir)
                        
                        # Use TextLoader as fallback if mime type isn't recognized
                        loader_info = None
                        try:
                            file_type = FileType(mime_type)
                            if file_type in self._loader_mapping:
                                loader_info = self._loader_mapping[file_type]
                        except ValueError:
                            loader_info = (TextLoader, {})

                        if loader_info:
                            loader_class, loader_config = loader_info
                            # Skip nested archives to prevent recursion
                            if loader_class not in [FileType.ZIP, FileType.RAR, FileType.TAR, FileType.GZIP]:
                                loader = loader_class(extracted_path, **loader_config)
                                docs = loader.load()
                                # Add archive context to metadata
                                for doc in docs:
                                    doc.metadata.update({
                                        "archive_source": file_path,
                                        "archive_path": relative_path
                                    })
                                documents.extend(docs)
                    except Exception as e:
                        # Log error and continue with next file
                        print(f"Error processing {extracted_path}: {str(e)}")
                        continue

        return documents

    async def close(self):
        """Close vector store connections."""
        if self._vector_store:
            await self._vector_store.close_connection()
    
    def get_processed_files_status(self) -> Dict[str, bool]:
        """Get the status of processed files."""
        return self._processed_files.copy()
    
    def set_embedding_type(self, embedding_type: EmbeddingType):
        """Set the embedding type to use."""
        self._embedding_type = embedding_type
