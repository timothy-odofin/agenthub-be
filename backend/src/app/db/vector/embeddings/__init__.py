"""
Embedding providers package.

This module automatically imports all embedding implementations
to ensure they are registered with the EmbeddingFactory.
"""

# Import the embedding implementations to trigger registration
from . import embedding
from .embedding import EmbeddingFactory

__all__ = [
    "EmbeddingFactory",
]
