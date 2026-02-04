from typing import List, Dict

from langchain.schema import Document

from app.core.constants import DataSourceType, EmbeddingType
from app.core.utils.exception.http_exception_handler import handle_atlassian_errors
from app.core.utils.logger import get_logger
from app.db.vector.providers.db_provider import VectorStoreFactory
from app.services.external.confluence_service import ConfluenceService
from app.infrastructure.ingestion.base import BaseIngestionService
from app.infrastructure.ingestion.rag_data_provider import RagDataProvider

logger = get_logger(__name__)

@RagDataProvider.register(DataSourceType.CONFLUENCE)
class ConfluenceIngestionService(BaseIngestionService):
    """Service for ingesting Confluence pages and spaces"""
    
    # Define the source type this service handles
    SOURCE_TYPE = DataSourceType.CONFLUENCE

    def __init__(self):
        # Call parent to auto-locate config by SOURCE_TYPE from settings singleton
        super().__init__()
        
        # Initialize Confluence client
        self._atlassian_service = ConfluenceService()
        self._processed_pages: Dict[str, bool] = {}
        
        # Initialize vector store
        self._vector_store = VectorStoreFactory.get_default_vector_store()
        self._embedding_type = EmbeddingType.DEFAULT

    def validate_config(self) -> None:
        if not self.config.sources:
            raise ValueError("No sources(spaces) provided in configuration")

    async def ingest(self) -> bool:
        """Ingest all configured Confluence spaces and pages."""
        success = True
        await self._vector_store.get_connection()

        if self.config.sources:
            spaces_to_embed = self._atlassian_service.list_confluence_spaces(self.config.sources)
            logger.info(f"Space Retrieved {spaces_to_embed}")
            for space_key in spaces_to_embed:
                pages = self._atlassian_service.list_confluence_pages_in_space(space_key)
                for page in pages:
                    page_success = await self.ingest_single(page)
                    success = success and page_success

        return success

    @handle_atlassian_errors(default_return=False)
    async def ingest_single(self, page) -> bool:
        """Ingest a single Confluence  page."""
        try:
            # Ensure vector store connection
            await self._vector_store.get_connection()

            documents = await self._process_page_by_id(page) if isinstance(page, str) else await self._process_page(page)
            page_id = page if isinstance(page, str) else page.get('id', 'unknown')

            # Save documents to vector store
            if documents:
                document_ids = await self._vector_store.save_and_embed(
                    self._embedding_type,
                    documents
                )
                logger.info(f"Successfully processed Page: {len(document_ids)} chunks saved")
                self._processed_pages[page_id] = True
                return True
            else:
                logger.info(f"No documents extracted from {page_id}")
                self._processed_pages[page_id] = False
                return False
        except Exception as e:
            logger.error(f"Error ingesting  {e}")
            self._processed_pages[page if isinstance(page, str) else page.get('id', 'unknown')] = False
            return False

    async def _process_page_by_id(self, page_id: str) -> List[Document]:
        """Process a single page by ID."""
        content, metadata = self._atlassian_service.retrieve_confluence_page(page_id)
        return  self.__chunk_doc(content, metadata)


    @handle_atlassian_errors(default_return=[])
    async def _process_page(self, page: dict) -> List[Document]:
        """Process a single Confluence page into documents."""

        content, metadata = self._atlassian_service.extract_content_from_a_page(page)

        return self.__chunk_doc(content, metadata)

    def __chunk_doc(self, content, metadata) -> List[Document]:
        """Chunk a single document using the text splitter."""
        document = Document(
            page_content=content,
            metadata=metadata
        )
        return self.text_splitter.split_documents([document])



    async def close(self):
        """Close vector store connections."""
        if self._vector_store:
            await self._vector_store.close_connection()
    
    def get_processed_pages_status(self) -> Dict[str, bool]:
        """Get the status of processed pages."""
        return self._processed_pages.copy()
    
    def set_embedding_type(self, embedding_type: EmbeddingType):
        """Set the embedding type to use."""
        self._embedding_type = embedding_type