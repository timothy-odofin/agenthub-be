import uuid
from typing import List, Optional, Dict, Any
from langchain.schema import Document
from langchain_community.vectorstores import PGVector

class PgVectorRepository:
    """Repository for PgVector operations."""

    def __init__(self, connection):
        self._connection = connection

    async def create_collection(self, collection_name: str, embedding_dimension: int):
        await self._connection.execute('CREATE EXTENSION IF NOT EXISTS vector')
        await self._connection.execute(f'''
        CREATE TABLE IF NOT EXISTS {collection_name} (
            id TEXT PRIMARY KEY,
            embedding vector({embedding_dimension}),
            metadata JSONB,
            embedded_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        await self._connection.execute(f'''
        CREATE INDEX IF NOT EXISTS {collection_name}_embedding_idx 
        ON {collection_name} 
        USING ivfflat (embedding vector_cosine_ops)
        WITH (lists = 100)
        ''')

    async def add_documents(self,
                            collection_name: str,
                            documents: List[Document],
                            embeddings: List[List[float]],
                            ids: Optional[List[str]] = None) -> bool:
        if ids is None:
            ids = [str(uuid.uuid4()) for _ in range(len(documents))]
        PGVector.from_documents(
            collection_name=collection_name,
            connection_string=self._connection.dsn,  # Use connection string
            embedding_function=embeddings,       # Placeholder, actual embedding done outside
            documents=documents,
            ids=ids
        )
        return True

    async def update_document(self,
                              collection_name: str,
                              document_id: str,
                              document: Document,
                              embedding: List[float]) -> bool:
        query = f"""
        UPDATE {collection_name}
        SET embedding = $1, metadata = $2
        WHERE id = $3
        """
        result = await self._connection.execute(
            query, embedding, document.metadata, document_id
        )
        return result.split()[-1] != "0"

    async def delete_document(self, collection_name: str, document_id: str) -> bool:
        query = f"DELETE FROM {collection_name} WHERE id = $1"
        result = await self._connection.execute(query, document_id)
        return result.split()[-1] != "0"

    async def get_document_metadata(self, collection_name: str, document_id: str) -> Optional[Dict[str, Any]]:
        query = f"SELECT metadata FROM {collection_name} WHERE id = $1"
        return await self._connection.fetchval(query, document_id)

    async def search_similar(self,
                             collection_name: str,
                             query_embedding: List[float],
                             k: int = 5,
                             filter_criteria: Optional[Dict[str, Any]] = None) -> List[Document]:
        vector_store = PGVector(
            collection_name=collection_name,
            connection_string=self._connection.dsn,
            embedding_function=lambda x: query_embedding  # embeddings already computed
        )
        docs_with_scores = vector_store.similarity_search_with_score(query_embedding, k=k, filter=filter_criteria)
        for doc, score in docs_with_scores:
            doc.metadata['similarity'] = 1 - score
        return [doc for doc, _ in docs_with_scores]
