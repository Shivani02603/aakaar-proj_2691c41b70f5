from fastapi import APIRouter, Depends, HTTPException, Request, UploadFile, File
from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID
from pydantic import BaseModel, Field
from database.models import User, Document, Query, DocumentChunk
from database.config import get_db
from backend.services.auth_service import get_current_user
from backend.services.ui_service import (
    list_documents_by_user,
    list_queries_by_user,
    get_query_sources,
    upload_document,
    get_document,
    get_document_chunk,
)

router = APIRouter(prefix="/ui", tags=["UI"])

# Pydantic schemas for request and response
class UserResponse(BaseModel):
    id: UUID
    username: str
    email: str
    created_at: str

    class Config:
        orm_mode = True


class DocumentResponse(BaseModel):
    id: UUID
    filename: str
    file_type: str
    status: str
    uploaded_at: str
    processed_at: Optional[str]
    error_message: Optional[str]

    class Config:
        orm_mode = True


class QueryResponse(BaseModel):
    id: UUID
    question: str
    answer: str
    sources: List[dict]
    created_at: str

    class Config:
        orm_mode = True


class DocumentChunkResponse(BaseModel):
    id: UUID
    chunk_index: int
    chunk_text: str
    metadata: dict
    created_at: str

    class Config:
        orm_mode = True


# Routes for UI functionality

@router.get("/documents", response_model=List[DocumentResponse])
async def list_user_documents(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    List all documents uploaded by the current user.
    """
    documents = list_documents_by_user(db, current_user)
    return documents


@router.get("/documents/{document_id}", response_model=DocumentResponse)
async def get_user_document(
    document_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get details of a specific document uploaded by the current user.
    """
    document = get_document(document_id, db, current_user)
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    return document


@router.get("/documents/{document_id}/chunks", response_model=List[DocumentChunkResponse])
async def list_document_chunks(
    document_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    List all chunks of a specific document uploaded by the current user.
    """
    chunks = list_documents_by_user(db, current_user)
    return chunks


@router.get("/documents/{document_id}/chunks/{chunk_id}", response_model=DocumentChunkResponse)
async def get_document_chunk_details(
    document_id: UUID,
    chunk_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get details of a specific chunk of a document uploaded by the current user.
    """
    chunk = get_document_chunk(document_id, chunk_id, db, current_user)
    if not chunk:
        raise HTTPException(status_code=404, detail="Chunk not found")
    return chunk


@router.post("/documents/upload", response_model=DocumentResponse)
async def upload_user_document(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Upload a new document for processing.
    """
    document = upload_document(file, db, current_user)
    return document


@router.get("/queries", response_model=List[QueryResponse])
async def list_user_queries(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    List all queries made by the current user.
    """
    queries = list_queries_by_user(db, current_user)
    return queries


@router.get("/queries/{query_id}", response_model=QueryResponse)
async def get_user_query(
    query_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get details of a specific query made by the current user.
    """
    query = get_query_sources(query_id, db, current_user)
    if not query:
        raise HTTPException(status_code=404, detail="Query not found")
    return query