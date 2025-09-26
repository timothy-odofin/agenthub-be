"""
Data ingestion service package.
"""
from .base import BaseIngestionService
from src.app.services.ingestion.file_ingestion_service import FileIngestionService

__all__ = [
    'BaseIngestionService',
    'FileIngestionService',
]
