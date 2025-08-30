"""
Base class for data ingestion services.
"""
from abc import ABC, abstractmethod
from typing import List, Dict, Any

from ...core.constants import DataSourceType
from ...core.schemas.ingestion_config import DataSourceConfig


class BaseIngestionService(ABC):
    """Base class for all data ingestion services."""
    
    def __init__(self, config: DataSourceConfig):
        """Initialize the ingestion service.
        
        Args:
            config: Configuration for the data source
        """
        self.config = config
        self.validate_config()
    
    @abstractmethod
    def validate_config(self) -> None:
        """Validate the configuration specific to this ingestion type.
        
        Raises:
            ValueError: If configuration is invalid
        """
        pass
    
    @abstractmethod
    async def ingest(self) -> bool:
        """Ingest all data from the configured sources.
        
        Returns:
            bool: True if all sources were ingested successfully, False otherwise
            
        Raises:
            Exception: If ingestion process encounters a critical error
        """
        pass
    
    @abstractmethod
    async def ingest_single(self, source: str) -> bool:
        """Ingest a single source.
        
        Args:
            source: The source identifier to ingest
            
        Returns:
            bool: True if ingestion was successful, False otherwise
            
        Raises:
            Exception: If ingestion process encounters a critical error
        """
        pass
    
    @abstractmethod
    async def source_meta(self, source: str) -> Dict[str, Any]:
        """Get metadata about a specific source.
        
        Args:
            source: The source identifier to get metadata for
            
        Returns:
            Dict containing metadata about the source. Examples:
            - For files: size, creation date, mime type, etc.
            - For URLs: last modified, content type, size, etc.
            - For S3: bucket, key, tags, last modified, etc.
            
        Raises:
            ValueError: If the source is invalid or not accessible
        """
        pass
    
    @property
    @abstractmethod
    def source_type(self) -> DataSourceType:
        """Get the type of data source this service handles."""
        pass
