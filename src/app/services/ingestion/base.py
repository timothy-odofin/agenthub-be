"""
Base class for data ingestion services.
"""
from abc import ABC, abstractmethod

from langchain_text_splitters import RecursiveCharacterTextSplitter

from ...core.constants import DataSourceType
from ...core.schemas.ingestion_config import DataSourceConfig


class BaseIngestionService(ABC):
    """Base class for all data ingestion services."""
    
    # Each subclass must define its SOURCE_TYPE
    SOURCE_TYPE: DataSourceType = None

    def __init__(self):
        """Initialize the ingestion service.
        
        Automatically locates its configuration from AppConfig singleton.

        Raises:
            ValueError: If SOURCE_TYPE is not defined or config not found
        """
        if self.SOURCE_TYPE is None:
            raise ValueError(f"{self.__class__.__name__} must define SOURCE_TYPE class attribute")

        # Import here to avoid circular imports
        from ...core.config.application import AppConfig

        # Get the singleton instance
        app_config = AppConfig()

        if not app_config.ingestion_config:
            raise ValueError("No ingestion configuration loaded in AppConfig")

        # Locate the config for this service's type
        source_type_key = self.SOURCE_TYPE.value.lower()
        if source_type_key not in app_config.ingestion_config.data_sources:
            raise ValueError(
                f"No configuration found for data source type: {self.SOURCE_TYPE.value}. "
                f"Available types: {list(app_config.ingestion_config.data_sources.keys())}"
            )

        self.config: DataSourceConfig = app_config.ingestion_config.data_sources[source_type_key]
        self.app_config = app_config
        self.validate_config()
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            length_function=len,
            is_separator_regex=False,
        )
    
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
    def source_type(self) -> DataSourceType:
        """Get the type of data sources this service handles."""
        return self.SOURCE_TYPE
