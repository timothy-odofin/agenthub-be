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
            config: Configuration for the data sources
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
        """Ingest a single sources.
        
        Args:
            source: The sources identifier to ingest
            
        Returns:
            bool: True if ingestion was successful, False otherwise
            
        Raises:
            Exception: If ingestion process encounters a critical error
        """
        pass
    
    
    
    @property
    @abstractmethod
    def source_type(self) -> DataSourceType:
        """Get the type of data sources this service handles."""
        pass
