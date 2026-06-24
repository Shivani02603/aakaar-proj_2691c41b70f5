import os
from typing import List, Dict
from database.models import DocumentChunk
from database.config import SessionLocal

class VectorStore:
    """
    VectorStore class for interacting with pgvector-backed vector storage.
    """

    def upsert(self, id: str, vector: List[float], doc_metadata: Dict) -> None:
        """
        Add or update a DocumentChunk row in the vector store.
        """
        if len(vector) != 1536:  # Ensure vector dimensionality matches the spec
            raise ValueError("Vector dimensionality must match the embedding model (1536).")
        
        with SessionLocal() as session:
            chunk = session.query(DocumentChunk).filter_by(id=id).first()
            if chunk:
                # Update existing row
                chunk.embedding = vector
                chunk.doc_metadata = doc_metadata
            else:
                # Insert new row
                chunk = DocumentChunk(id=id, embedding=vector, doc_metadata=doc_metadata)
                session.add(chunk)
            session.commit()

    def search(self, query_embedding: List[float], top_k: int) -> List[Dict]:
        """
        Search for the top_k most similar document chunks based on cosine similarity.
        """
        if len(query_embedding) != 1536:  # Ensure query embedding dimensionality matches the spec
            raise ValueError("Query embedding dimensionality must match the embedding model (1536).")
        
        with SessionLocal() as session:
            results = (
                session.query(DocumentChunk)
                .order_by(DocumentChunk.embedding.cosine_distance(query_embedding))
                .limit(top_k)
                .all()
            )
            return [
                {"id": chunk.id, "content": chunk.content, "doc_metadata": chunk.doc_metadata}
                for chunk in results
            ]

# Singleton instance of VectorStore
vector_store = VectorStore()