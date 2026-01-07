"""
Database repositories for data access.

This module provides repository classes for database operations following
the repository pattern with singleton instances.
"""

from src.app.db.repositories.user_repository import (
    UserRepository,
    user_repository,
)

__all__ = [
    "UserRepository",
    "user_repository",
]