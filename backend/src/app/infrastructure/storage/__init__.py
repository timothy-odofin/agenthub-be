"""
File-based storage infrastructure.

Provides a generic FileStorageService for persisting JSON data to disk.
Used by the route sync system to store frontend route definitions that
the LLM agent reads dynamically at tool-call time.
"""

from app.infrastructure.storage.file_storage_service import FileStorageService

__all__ = ["FileStorageService"]
