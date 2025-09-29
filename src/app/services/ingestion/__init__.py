"""
Data ingestion service package.
"""
from .base import BaseIngestionService
from app.services.ingestion.file_ingestion_service import FileIngestionService

__all__ = [
    'BaseIngestionService',
    'FileIngestionService',
]
