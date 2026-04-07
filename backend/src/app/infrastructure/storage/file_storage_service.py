"""
File Storage Service — atomic, thread-safe JSON file persistence.

This service provides a simple way to persist structured data to JSON files.
It's designed for the route sync system where the frontend pushes its route
registry to the backend, and the backend stores it in a JSON file that the
LLM navigation tool reads dynamically.

Design Rationale:
─────────────────
- Atomic writes: Uses write-to-temp + rename to prevent partial reads
- Thread-safe: Uses a threading lock so concurrent requests don't corrupt data
- Generic: Works with any JSON-serializable data (routes, config, etc.)
- No database needed: Simple file storage suitable for config-like data

Usage:
    from app.infrastructure.storage import FileStorageService

    storage = FileStorageService("routes")

    # Write data
    storage.save({"routes": [...]})

    # Read data
    data = storage.load()

    # Check existence
    if storage.exists():
        ...
"""

import json
import os
import tempfile
import threading
from pathlib import Path
from typing import Any, Dict, Optional

from app.core.utils.logger import get_logger

logger = get_logger(__name__)

# Default directory for storage files — sits alongside the running app
_STORAGE_DIR = Path(__file__).resolve().parent / "data"


class FileStorageService:
    """
    Thread-safe JSON file storage.

    Each instance is scoped to a single file identified by `name`.
    The file is stored at: infrastructure/storage/data/{name}.json
    """

    def __init__(self, name: str, storage_dir: Optional[Path] = None):
        """
        Initialize storage for a named file.

        Args:
            name: Logical name of the file (e.g., "routes"). Extension added automatically.
            storage_dir: Override the default storage directory.
        """
        self._dir = storage_dir or _STORAGE_DIR
        self._dir.mkdir(parents=True, exist_ok=True)
        self._path = self._dir / f"{name}.json"
        self._lock = threading.Lock()

        logger.info(f"FileStorageService initialized: {self._path}")

    @property
    def path(self) -> Path:
        """Return the full path to the storage file."""
        return self._path

    def exists(self) -> bool:
        """Check whether the storage file exists."""
        return self._path.is_file()

    def load(self, default: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Read and parse the JSON file.

        Args:
            default: Value to return if the file doesn't exist.
                     Defaults to an empty dict.

        Returns:
            Parsed JSON content as a dictionary.
        """
        if default is None:
            default = {}

        with self._lock:
            if not self._path.is_file():
                logger.debug(f"Storage file not found, returning default: {self._path}")
                return default

            try:
                with open(self._path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                logger.debug(f"Loaded storage: {self._path} ({len(str(data))} chars)")
                return data
            except (json.JSONDecodeError, IOError) as e:
                logger.error(f"Failed to load storage {self._path}: {e}")
                return default

    def save(self, data: Dict[str, Any]) -> bool:
        """
        Write data to the JSON file atomically.

        Uses write-to-temp + os.replace to ensure readers never see
        a partially written file.

        Args:
            data: JSON-serializable dictionary to persist.

        Returns:
            True if successful, False on error.
        """
        with self._lock:
            try:
                # Write to a temp file in the same directory, then atomically replace
                fd, tmp_path = tempfile.mkstemp(
                    dir=str(self._dir), suffix=".tmp", prefix=".storage_"
                )
                try:
                    with os.fdopen(fd, "w", encoding="utf-8") as f:
                        json.dump(data, f, indent=2, ensure_ascii=False)
                    os.replace(tmp_path, str(self._path))
                except Exception:
                    # Clean up temp file on failure
                    if os.path.exists(tmp_path):
                        os.unlink(tmp_path)
                    raise

                logger.info(f"Saved storage: {self._path}")
                return True

            except (IOError, TypeError, ValueError) as e:
                logger.error(f"Failed to save storage {self._path}: {e}")
                return False

    def delete(self) -> bool:
        """
        Remove the storage file.

        Returns:
            True if deleted, False if not found or on error.
        """
        with self._lock:
            try:
                if self._path.is_file():
                    self._path.unlink()
                    logger.info(f"Deleted storage: {self._path}")
                    return True
                return False
            except IOError as e:
                logger.error(f"Failed to delete storage {self._path}: {e}")
                return False
