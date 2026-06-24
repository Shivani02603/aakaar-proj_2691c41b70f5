from typing import List, Optional
from uuid import UUID
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from database.models import Document
from database.config import get_db
from backend.routers.ingestion import extract_text_from_pdf, extract_text_from_docx, extract_text_from_txt

class DocumentManagementService:
    def create_document(
        self,
        user_id: UUID,
        session_id: UUID,
        filename: str,
        file_type: str,
        file_path: str,
        db: Session = get_db(),
    ) -> Document:
        if file_type not in ["pdf", "docx", "txt"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Unsupported file type. Only PDF, DOCX, and TXT are allowed.",
            )

        document = Document(
            user_id=user_id,
            session_id=session_id,
            filename=filename,
            file_type=file_type,
            file_path=file_path,
            status="uploaded",
            uploaded_at=datetime.utcnow(),
        )
        db.add(document)
        db.commit()
        db.refresh(document)
        return document

    def get_document_by_id(self, document_id: UUID, db: Session = get_db()) -> Document:
        document = db.query(Document).filter(Document.id == document_id).first()
        if not document:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Document with ID {document_id} not found.",
            )
        return document

    def list_all_documents(self, user_id: UUID, db: Session = get_db()) -> List[Document]:
        documents = db.query(Document).filter(Document.user_id == user_id).all()
        return documents

    def update_document(
        self, document_id: UUID, update_data: dict, db: Session = get_db()
    ) -> Document:
        document = db.query(Document).filter(Document.id == document_id).first()
        if not document:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Document with ID {document_id} not found.",
            )

        for key, value in update_data.items():
            if hasattr(document, key):
                setattr(document, key, value)

        db.commit()
        db.refresh(document)
        return document

    def delete_document(self, document_id: UUID, db: Session = get_db()) -> None:
        document = db.query(Document).filter(Document.id == document_id).first()
        if not document:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Document with ID {document_id} not found.",
            )

        db.delete(document)
        db.commit()

    def process_document(self, document_id: UUID, db: Session = get_db()) -> Document:
        document = self.get_document_by_id(document_id, db)

        if document.file_type == "pdf":
            text = extract_text_from_pdf(document.file_path)
        elif document.file_type == "docx":
            text = extract_text_from_docx(document.file_path)
        elif document.file_type == "txt":
            text = extract_text_from_txt(document.file_path)
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Unsupported file type for processing.",
            )

        # Update document status and processed_at timestamp
        document.status = "processed"
        document.processed_at = datetime.utcnow()
        db.commit()
        db.refresh(document)

        # Additional processing logic (e.g., storing extracted text) can be added here

        return document