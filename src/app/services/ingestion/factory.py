"""
Factory for creating ingestion services based on configuration.
"""
from typing import Type, Dict

from ...core.constants import DataSourceType
from ...core.schemas.ingestion_config import DataSourceConfig
from .base import BaseIngestionService
from .sources import (
    S3IngestionService,
    ConfluenceIngestionService,
    FileIngestionService,
    SharePointIngestionService,
    URLIngestionService
)


class IngestionServiceFactory:
    """Factory for creating appropriate ingestion service instances."""
    
    _services: Dict[DataSourceType, Type[BaseIngestionService]] = {
        DataSourceType.S3: S3IngestionService,
        DataSourceType.CONFLUENCE: ConfluenceIngestionService,
        DataSourceType.FILE: FileIngestionService,
        DataSourceType.SHAREPOINT: SharePointIngestionService,
        DataSourceType.URL: URLIngestionService,
    }
    
    @classmethod
    def create(cls, config: DataSourceConfig) -> BaseIngestionService:
        """Create an ingestion service instance based on the configuration.
        
        Args:
            config: Configuration for the data source
            
        Returns:
            An instance of the appropriate ingestion service
            
        Raises:
            ValueError: If the data source type is not supported
        """
        service_class = cls._services.get(config.type)
        if not service_class:
            raise ValueError(f"Unsupported data source type: {config.type}")
            
        return service_class(config)
