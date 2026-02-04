from fastapi import APIRouter

from app.core.constants import DataSourceType
from app.infrastructure.ingestion.rag_data_provider import RagDataProvider

router = APIRouter()

@router.post("/load/{data_source}")
async def load_data(data_source: DataSourceType):
    rag_data_loader = RagDataProvider.get_class(data_source)()
    success = await rag_data_loader.ingest()
    if success:
        return {"message": "Data loaded successfully"}
    else:
        return {"message": "Data loading failed"}