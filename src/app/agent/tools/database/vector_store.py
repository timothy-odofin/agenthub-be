"""
Vector store tools for information retrieval and semantic search.
"""

import json
from typing import List, Dict, Any
from langchain.tools import Tool

from app.core.constants import VectorDBType
from app.db.vector import VectorStoreFactory
from app.agent.tools.base.registry import ToolRegistry

# Defer vector store initialization until needed
_vector_store = None

def get_vector_store():
    """Get or initialize the vector store."""
    global _vector_store
    if _vector_store is None:
        _vector_store = VectorStoreFactory.get_vector_store(VectorDBType.QDRANT)
    return _vector_store


@ToolRegistry.register("vector", "database")
class VectorStoreTools:
    """Vector store operations and semantic search tools."""
    
    def __init__(self, config: Dict[str, Any] = None):
        """Initialize with optional configuration."""
        self.config = config or {}
        
    def get_tools(self) -> List[Tool]:
        """Return list of vector store tools."""
        return [
            Tool(
                name="retrieve_information",
                description="Retrieve information from vector store based on semantic search. Use this to find relevant documents, confluence pages, knowledge base articles, and other stored information.",
                func=self._retrieve_information
            )
        ]
    
    def _retrieve_information(self, query: str) -> str:
        """
        Retrieve information from the vector store based on the provided query.
        This information includes relevant confluence docs, knowledge base articles, and other related data.

        Args:
            query (str): The query string to search in the vector store.

        Returns:
            str: The retrieved information as a string.
        """
        vector_store_class = get_vector_store()
        vector_db = vector_store_class.as_retriever(search_kwargs={"k": 4})
        docs = vector_db.get_relevant_documents(query)
        formatted = []
        for d in docs:
            formatted.append(
                f"CONTENT:\n{d.page_content}\n\nMETADATA:\n{json.dumps(d.metadata)}"
            )

        return "\n\n---\n\n".join(formatted)
