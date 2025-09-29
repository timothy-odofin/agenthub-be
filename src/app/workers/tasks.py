import asyncio
import logging
from typing import List
from celery import shared_task
from app.core.schemas.ingestion_config import DataSourceConfig, DataSourceType
from app.services.ingestion.file_ingestion_service import FileIngestionService

logger = logging.getLogger(__name__)

async def create_ingestion_service(file_paths: List[str], source_name: str = "documents"):
    """
    Create a file ingestion service with the given configuration.
    
    Args:
        file_paths: List of file paths to ingest
        source_name: Name of the data source
    """
    config = DataSourceConfig(
        name=source_name,
        type=DataSourceType.FILE,
        sources=file_paths
    )
    return await FileIngestionService(config).ingest()

@shared_task
def example_task(x, y):
    """Example task that adds two numbers."""
    return x + y

@shared_task
def task_file_ingestion(file_paths: List[str], source_name: str = "documents"):
    """
    Task to perform file ingestion.
    
    Args:
        file_paths: List of file paths to process
        source_name: Name of the data source
    
    Returns:
        bool: True if ingestion was successful, False otherwise
    """
    asyncio.run(create_ingestion_service(file_paths, source_name))
    return True
