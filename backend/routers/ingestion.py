from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID
from pydantic import BaseModel, Field
from database.models import DocumentChunk
from database.config import get_db
from backend.services.auth_service import get_current_user
from backend.services.ingestion_service import (
    extract_text_from_pdf,
    extract_text_from_docx,
    extract_text_from_txt,
    chunk_text,
    embed_batch,
)
from backend.services.ingestion_service import IngestionService

router = APIRouter(prefix="/ingestion", tags=["Ingestion"])

# Pydantic schemas
class DocumentChunkCreate(BaseModel):
    document_id: UUID
    user_id: UUID
    session_id: UUID
    chunk_index: int
    chunk_text: str
    embedding: List[float]
    metadata: dict

class DocumentChunkResponse(BaseModel):
    id: UUID
    document_id: UUID
    user_id: UUID
    session_id: UUID
    chunk_index: int
    chunk_text: str
    embedding: List[float]
    metadata: dict

class DocumentChunkListResponse(BaseModel):
    chunks: List[DocumentChunkResponse]

# Routes
@router.post("/upload", response_model=DocumentChunkListResponse)
async def upload_file(
    file: UploadFile = File(...),
    session_id: UUID = Form(...),
    user_id: UUID = Form(...),
    db: Session = Depends(get_db),
    token: str = Depends(get_current_user),
):
    """
    Upload a file, extract text, chunk it, embed chunks, and store them in the database.
    """
    try:
        # Extract text based on file type
        if file.content_type == "application/pdf":
            extracted_text = extract_text_from_pdf(file.file)
        elif file.content_type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
            extracted_text = extract_text_from_docx(file.file)
        elif file.content_type == "text/plain":
            extracted_text = extract_text_from_txt(file.file)
        else:
            raise HTTPException(status_code=400, detail="Unsupported file type")

        # Chunk the extracted text
        chunks = chunk_text(extracted_text, chunk_size=1000, overlap=200)

        # Embed the chunks
        embeddings = embed_batch(chunks)

        # Store chunks in the database
        ingestion_service = IngestionService(db)
        stored_chunks = ingestion_service.embed_and_store_chunks(
            chunks=chunks,
            embeddings=embeddings,
            session_id=session_id,
            user_id=user_id,
            source_filename=file.filename,
        )

        return DocumentChunkListResponse(chunks=stored_chunks)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/", response_model=DocumentChunkListResponse)
async def list_chunks(
    db: Session = Depends(get_db),
    token: str = Depends(get_current_user),
):
    """
    List all document chunks for the current user.
    """
    try:
        ingestion_service = IngestionService(db)
        chunks = ingestion_service.list_all(user_id=token.id)
        return DocumentChunkListResponse(chunks=chunks)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{chunk_id}", response_model=DocumentChunkResponse)
async def get_chunk(
    chunk_id: UUID,
    db: Session = Depends(get_db),
    token: str = Depends(get_current_user),
):
    """
    Retrieve a specific document chunk by ID.
    """
    try:
        ingestion_service = IngestionService(db)
        chunk = ingestion_service.get_by_id(chunk_id=chunk_id, user_id=token.id)
        if not chunk:
            raise HTTPException(status_code=404, detail="Chunk not found")
        return chunk
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{chunk_id}", response_model=dict)
async def delete_chunk(
    chunk_id: UUID,
    db: Session = Depends(get_db),
    token: str = Depends(get_current_user),
):
    """
    Delete a specific document chunk by ID.
    """
    try:
        ingestion_service = IngestionService(db)
        success = ingestion_service.delete_chunk(chunk_id=chunk_id, user_id=token.id)
        if not success:
            raise HTTPException(status_code=404, detail="Chunk not found")
        return {"message": "Chunk deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))