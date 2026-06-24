from typing import List, Optional
from uuid import UUID
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from database.models import Query, DocumentChunk
from database.config import get_db
from ai.embeddings import embed_text
from ai.vector_store import VectorStore
from ai.rag import retrieve_context, answer_question

class QueryService:
    @staticmethod
    def create_query(query_data: dict, db: Session, current_user: UUID) -> Query:
        """
        Create a new query and store it in the database.
        """
        try:
            query_embedding = embed_text(query_data["question"])
            vector_store = VectorStore()
            
            # Perform similarity search filtered by session and user
            search_results = vector_store.search(
                embedding=query_embedding,
                top_k=5,
                filters={
                    "session_id": str(query_data["session_id"]),
                    "user_id": str(current_user)
                }
            )
            
            if not search_results:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="No relevant chunks found for the query."
                )
            
            # Build context prompt from retrieved chunks
            context_prompt = retrieve_context(
                query=query_data["question"],
                top_k=5,
                session_id=query_data["session_id"],
                user_id=current_user
            )
            
            # Call runtime LLM to get the answer
            llm_response = answer_question(
                query=query_data["question"],
                session_id=query_data["session_id"],
                user_id=current_user
            )
            
            # Create Query object
            new_query = Query(
                id=UUID(),
                user_id=current_user,
                session_id=query_data["session_id"],
                question=query_data["question"],
                answer=llm_response["answer"],
                sources=llm_response["sources"],
                created_at=query_data["created_at"]
            )
            
            db.add(new_query)
            db.commit()
            db.refresh(new_query)
            return new_query
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to create query: {str(e)}"
            )

    @staticmethod
    def get_query_by_id(query_id: UUID, db: Session, current_user: UUID) -> Query:
        """
        Retrieve a query by its ID.
        """
        query = db.query(Query).filter(Query.id == query_id, Query.user_id == current_user).first()
        if not query:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Query not found."
            )
        return query

    @staticmethod
    def list_queries(db: Session, current_user: UUID) -> List[Query]:
        """
        List all queries for the current user.
        """
        queries = db.query(Query).filter(Query.user_id == current_user).all()
        if not queries:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No queries found for the current user."
            )
        return queries

    @staticmethod
    def update_query(query_id: UUID, update_data: dict, db: Session, current_user: UUID) -> Query:
        """
        Update an existing query.
        """
        query = db.query(Query).filter(Query.id == query_id, Query.user_id == current_user).first()
        if not query:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Query not found."
            )
        
        for key, value in update_data.items():
            setattr(query, key, value)
        
        db.commit()
        db.refresh(query)
        return query

    @staticmethod
    def delete_query(query_id: UUID, db: Session, current_user: UUID) -> None:
        """
        Delete a query by its ID.
        """
        query = db.query(Query).filter(Query.id == query_id, Query.user_id == current_user).first()
        if not query:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Query not found."
            )
        
        db.delete(query)
        db.commit()