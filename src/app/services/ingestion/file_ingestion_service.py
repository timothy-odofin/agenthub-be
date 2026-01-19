import gzip
import os
import shutil
import tarfile
import tempfile
import zipfile
from pathlib import Path
from typing import List, Dict

import magic
from langchain.schema import Document
from langchain_community.document_loaders import (
    TextLoader

)

from app.core.constants import DataSourceType, EmbeddingType
from app.core.utils.logger import get_logger
from app.db.vector.providers.db_provider import VectorStoreFactory
from app.services.ingestion.base import BaseIngestionService
from .file_data_source_util import FileType, _construct_mapping
from .rag_data_provider import RagDataProvider

logger = get_logger(__name__)


@RagDataProvider.register(DataSourceType.FILE)
class FileIngestionService(BaseIngestionService):
    # Define the source type this service handles
    SOURCE_TYPE = DataSourceType.FILE

    def __init__(self):
        # Call parent to auto-locate config by SOURCE_TYPE from AppConfig singleton
        super().__init__()

        self._processed_files: Dict[str, bool] = {}

        # Initialize loader mapping
        self._loader_mapping = _construct_mapping()

        # Initialize vector store
        self._vector_store = VectorStoreFactory.get_default_vector_store()
        self._embedding_type = EmbeddingType.DEFAULT  # Default embedding type

    def validate_config(self) -> None:
        """Validate the file ingestion configuration."""
        if not self.config.sources:
            raise ValueError("No sources paths provided in configuration")
        for path in self.config.sources:
            if not os.path.exists(path):
                raise ValueError(f"Source path does not exist: {path}")

    async def ingest(self) -> bool:
        """Ingest all files from the configured sources."""
        success = True

        for source_path in self.config.sources:
            try:
                await self._process_files_in_folder(source_path)
            except Exception as e:
                self._processed_files[source_path] = False
                success = False
                logger.error(f"Error processing {source_path}: {str(e)}")

        return success

    async def _process_files_in_folder(self, folder_path: str) -> bool:

        for file_path in Path(folder_path).iterdir():
            if file_path.is_file() and os.path.exists(file_path):
                file_abs_path = str(file_path)
                process_status = await self.ingest_single(file_abs_path)
                self._processed_files[file_abs_path] = True
                logger.info(f"Processed {file_abs_path} Status: {process_status}")
        return True

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

            # Save documents to vector store
            if documents:
                document_ids = await self._vector_store.save_and_embed(
                    self._embedding_type,
                    documents
                )
                logger.info(f"Successfully processed {source}: {len(document_ids)} chunks saved")
                self._processed_files[source] = True
                return True
            else:
                logger.info(f"No documents extracted from {source}")
                self._processed_files[source] = False
                return False

        except Exception as e:
            self._processed_files[source] = False
            logger.error(f"Error processing {source}: {str(e)}")
            return False

    async def _process_file(self, file_path: str) -> List[Document]:
        """
        Process a single file: detect type, load content, and split into chunks.
        """

        # Load documents
        documents = self._load_document(file_path)
        logger.info(f"Loaded {len(documents)} documents from {file_path}")
        # Split into chunks
        return self.text_splitter.split_documents(documents)

    def _detect_file_type(self, file_path: str) -> FileType:
        """
        Detect the MIME type of a file and return corresponding FileType.
        """
        mime_type = magic.from_file(file_path, mime=True)
        logger.info(f"Detected MIME type {mime_type} for file {file_path}")
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
        logger.info(f"Detected file type {file_type} for {file_path}")

        if file_type not in self._loader_mapping:
            raise ValueError(f"Unsupported file type: {file_type}")

        # Special handling for archives
        if file_type in [FileType.ZIP, FileType.RAR, FileType.TAR, FileType.GZIP]:
            return self._handle_archive(file_path, file_type)

        # Standard handling for other file types
        loader_class, loader_config = self._loader_mapping[file_type]
        logger.info(f"Using loader {loader_class.__name__} for {file_path}")
        loader = loader_class(file_path)
        loaded_docs = loader.load()
        return loaded_docs

    def _handle_archive(self, file_path: str, file_type: FileType) -> List[Document]:
        """
        Handle archive files by extracting and processing their contents.
        Directly loads extracted files without recursive archive handling.
        """
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
