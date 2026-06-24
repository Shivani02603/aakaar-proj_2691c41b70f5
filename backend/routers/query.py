from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID
from pydantic import BaseModel, Field
from database.models import Query
from database.config import get_db
from backend.services.auth_service import get_current_user
from backend.services.query_service import QueryService
from ai.rag import retrieve_context, answer_question

router = APIRouter(prefix="/query", tags=["Query"])

# Pydantic schemas
class QueryBase(BaseModel):
    question: str = Field(..., example="What is the capital of France?")
    session_id: UUID = Field(..., example="123e4567-e89b-12d3-a456-426614174000")

class QueryCreate(QueryBase):
    pass

class QueryResponse(BaseModel):
    id: UUID
    question: str
    answer: str
    sources: List[dict]
    created_at: str

class QueryListResponse(BaseModel):
    queries: List[QueryResponse]

# Create a new query
@router.post("/", response_model=QueryResponse)
async def create_query(
    query_data: QueryCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    try:
        # Retrieve context from user's documents
        context = await retrieve_context(
            query=query_data.question,
            top_k=5,
            session_id=query_data.session_id,
            user_id=current_user["id"],
        )
        
        # Generate answer using LLM
        answer_data = await answer_question(
            query=query_data.question,
            session_id=query_data.session_id,
            user_id=current_user["id"],
        )
        
        # Save query to database
        query_service = QueryService(db)
        new_query = query_service.create_query({
            "user_id": current_user["id"],
            "session_id": query_data.session_id,
            "question": query_data.question,
            "answer": answer_data["answer"],
            "sources": answer_data["sources"],
        })
        
        return QueryResponse(
            id=new_query.id,
            question=new_query.question,
            answer=new_query.answer,
            sources=new_query.sources,
            created_at=new_query.created_at.isoformat(),
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Get a list of queries
@router.get("/", response_model=QueryListResponse)
async def list_queries(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    try:
        query_service = QueryService(db)
        queries = query_service.list_queries(user_id=current_user["id"])
        return QueryListResponse(
            queries=[
                QueryResponse(
                    id=query.id,
                    question=query.question,
                    answer=query.answer,
                    sources=query.sources,
                    created_at=query.created_at.isoformat(),
                )
                for query in queries
            ]
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Get a specific query by ID
@router.get("/{query_id}", response_model=QueryResponse)
async def get_query(
    query_id: UUID,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    try:
        query_service = QueryService(db)
        query = query_service.get_query_by_id(query_id=query_id, user_id=current_user["id"])
        if not query:
            raise HTTPException(status_code=404, detail="Query not found")
        return QueryResponse(
            id=query.id,
            question=query.question,
            answer=query.answer,
            sources=query.sources,
            created_at=query.created_at.isoformat(),
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Update a query
@router.put("/{query_id}", response_model=QueryResponse)
async def update_query(
    query_id: UUID,
    query_data: QueryCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    try:
        query_service = QueryService(db)
        updated_query = query_service.update_query(
            query_id=query_id,
            user_id=current_user["id"],
            update_data={
                "question": query_data.question,
                "session_id": query_data.session_id,
            },
        )
        if not updated_query:
            raise HTTPException(status_code=404, detail="Query not found")
        return QueryResponse(
            id=updated_query.id,
            question=updated_query.question,
            answer=updated_query.answer,
            sources=updated_query.sources,
            created_at=updated_query.created_at.isoformat(),
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Delete a query
@router.delete("/{query_id}")
async def delete_query(
    query_id: UUID,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    try:
        query_service = QueryService(db)
        deleted = query_service.delete_query(query_id=query_id, user_id=current_user["id"])
        if not deleted:
            raise HTTPException(status_code=404, detail="Query not found")
        return {"detail": "Query deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))