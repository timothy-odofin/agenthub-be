"""
Base connection management components.
"""

from .base_connection_manager import BaseConnectionManager
from .connection_registry import ConnectionRegistry, ConnectionType

__all__ = ['BaseConnectionManager', 'ConnectionRegistry', 'ConnectionType']