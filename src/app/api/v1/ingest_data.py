from typing import List
from fastapi import APIRouter

from app.services.ingestion.file_ingestion_service import FileIngestionService
from app.core.constants import DataSourceType
from app.core.schemas.ingestion_config import DataSourceConfig

router = APIRouter()

@router.post("/load")
async def load_data():
    success = await FileIngestionService().ingest()
    if success:
        return {"message": "Data loaded successfully"}
    else:
        return {"message": "Data loading failed"}