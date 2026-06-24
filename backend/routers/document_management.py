from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID
from pydantic import BaseModel, Field
from database.models import Document
from database.config import get_db
from backend.services.auth_service import get_current_user
from backend.services.document_service import (
    create_document,
    get_document_by_id,
    list_all_documents,
    update_document,
    delete_document,
)
from backend.services.ingestion_service import (
    extract_text_from_pdf,
    extract_text_from_docx,
    extract_text_from_txt,
)

router = APIRouter(prefix="/document-management", tags=["Document Management"])

# Pydantic Schemas
class DocumentBase(BaseModel):
    filename: str
    file_type: str
    file_path: str
    status: str
    uploaded_at: str
    processed_at: str | None = None
    error_message: str | None = None


class DocumentCreate(DocumentBase):
    user_id: UUID
    session_id: UUID


class DocumentResponse(DocumentBase):
    id: UUID


class DocumentUpdate(BaseModel):
    status: str | None = None
    processed_at: str | None = None
    error_message: str | None = None


# Routes
@router.post("/", response_model=DocumentResponse)
async def upload_document(
    file: UploadFile = File(...),
    session_id: UUID = Form(...),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    Upload a document in PDF, DOCX, or TXT format.
    """
    if file.content_type not in ["application/pdf", "application/vnd.openxmlformats-officedocument.wordprocessingml.document", "text/plain"]:
        raise HTTPException(status_code=400, detail="Unsupported file type.")

    try:
        file_path = f"/uploads/{file.filename}"
        with open(file_path, "wb") as f:
            f.write(file.file.read())

        if file.content_type == "application/pdf":
            text = extract_text_from_pdf(file_path)
        elif file.content_type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
            text = extract_text_from_docx(file_path)
        elif file.content_type == "text/plain":
            text = extract_text_from_txt(file_path)
        else:
            raise HTTPException(status_code=400, detail="Unsupported file type.")

        document_data = {
            "filename": file.filename,
            "file_type": file.content_type,
            "file_path": file_path,
            "status": "uploaded",
            "uploaded_at": str(datetime.utcnow()),
            "user_id": current_user["id"],
            "session_id": session_id,
        }

        document = create_document(document_data, db)
        return document
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing file: {str(e)}")


@router.get("/", response_model=List[DocumentResponse])
async def list_documents(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    List all documents for the current user.
    """
    try:
        documents = list_all_documents(db, current_user)
        return documents
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving documents: {str(e)}")


@router.get("/{document_id}", response_model=DocumentResponse)
async def get_document(
    document_id: UUID,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    Retrieve a specific document by ID.
    """
    try:
        document = get_document_by_id(document_id, db, current_user)
        if not document:
            raise HTTPException(status_code=404, detail="Document not found.")
        return document
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving document: {str(e)}")


@router.put("/{document_id}", response_model=DocumentResponse)
async def update_document_route(
    document_id: UUID,
    update_data: DocumentUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    Update a document's metadata.
    """
    try:
        document = update_document(document_id, update_data.dict(exclude_unset=True), db, current_user)
        if not document:
            raise HTTPException(status_code=404, detail="Document not found.")
        return document
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating document: {str(e)}")


@router.delete("/{document_id}")
async def delete_document_route(
    document_id: UUID,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    Delete a document by ID.
    """
    try:
        success = delete_document(document_id, db, current_user)
        if not success:
            raise HTTPException(status_code=404, detail="Document not found.")
        return {"detail": "Document deleted successfully."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting document: {str(e)}")