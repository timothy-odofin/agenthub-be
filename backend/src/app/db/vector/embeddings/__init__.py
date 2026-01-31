"""
Embedding providers package.

This module automatically imports all embedding implementations
to ensure they are registered with the EmbeddingFactory.
"""

from .embedding import EmbeddingFactory

# Import the embedding implementations to trigger registration
from . import embedding

__all__ = [
    'EmbeddingFactory',
]