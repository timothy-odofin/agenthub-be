"""
Data ingestion service package.
"""
from .base import BaseIngestionService
from .file_ingestion_service import FileIngestionService

__all__ = [
    'BaseIngestionService',
    'FileIngestionService',
]
