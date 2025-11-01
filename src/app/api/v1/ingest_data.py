from typing import List
from fastapi import APIRouter

from app.services.ingestion.file_ingestion_service import FileIngestionService
from app.core.constants import DataSourceType
from app.core.schemas.ingestion_config import DataSourceConfig

router = APIRouter()
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
@router.post("/load")
async def load_data():
    success = await create_ingestion_service(file_paths=[
                                                     '/Users/oyejide/Downloads/questions/1706.03762v1.pdf'], source_name='documents')
    if success:
        return {"message": "Data loaded successfully"}
    else:
        return {"message": "Data loading failed"}