"""
Unified connection management system.

This package provides a standardized approach to managing connections
to databases, vector stores, and external services.
"""

# Import all connection managers to trigger registration
import app.infrastructure.connections.database
import app.infrastructure.connections.external
import app.infrastructure.connections.vector

from .base import BaseConnectionManager, ConnectionRegistry, ConnectionType
from .factory import ConnectionFactory

__all__ = [
    'BaseConnectionManager',
    'ConnectionRegistry', 
    'ConnectionType',
    'ConnectionFactory'
]