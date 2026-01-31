"""
Unified connection management system.

This package provides a standardized approach to managing connections
to databases, vector stores, and external services.
"""

# Import all connection managers to trigger registration
import app.connections.database
import app.connections.external
import app.connections.vector

from .base import BaseConnectionManager, ConnectionRegistry, ConnectionType
from .factory import ConnectionFactory

__all__ = [
    'BaseConnectionManager',
    'ConnectionRegistry', 
    'ConnectionType',
    'ConnectionFactory'
]