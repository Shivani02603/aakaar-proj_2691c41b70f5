from typing import List, Optional
from uuid import UUID
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from database.models import DocumentChunk
from database.config import get_db
from ai.embeddings import embed_text
from pypdf import PdfReader
from docx import Document as DocxDocument

class IngestionService:
    CHUNK_SIZE = 1000
    OVERLAP = 200

    @staticmethod
    def extract_text_from_pdf(file_path: str) -> str:
        try:
            reader = PdfReader(file_path)
            text = ""
            for page in reader.pages:
                text += page.extract_text() or ""
            return text.strip()
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to extract text from PDF: {str(e)}"
            )

    @staticmethod
    def extract_text_from_docx(file_path: str) -> str:
        try:
            doc = DocxDocument(file_path)
            text = "\n".join([paragraph.text for paragraph in doc.paragraphs])
            return text.strip()
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to extract text from DOCX: {str(e)}"
            )

    @staticmethod
    def extract_text_from_txt(file_path: str) -> str:
        try:
            with open(file_path, "r", encoding="utf-8") as file:
                text = file.read()
            return text.strip()
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to extract text from TXT: {str(e)}"
            )

    @staticmethod
    def chunk_text(text: str, chunk_size: int = CHUNK_SIZE, overlap: int = OVERLAP) -> List[str]:
        chunks = []
        start = 0
        while start < len(text):
            end = min(start + chunk_size, len(text))
            chunks.append(text[start:end])
            start += chunk_size - overlap
        return chunks

    @staticmethod
    def embed_and_store_chunks(
        chunks: List[str],
        session_id: UUID,
        user_id: UUID,
        source_filename: str,
        db: Session
    ) -> None:
        try:
            for index, chunk_text in enumerate(chunks):
                embedding = embed_text(chunk_text)
                metadata = {
                    "session_id": str(session_id),
                    "user_id": str(user_id),
                    "source_filename": source_filename,
                    "chunk_text": chunk_text
                }
                document_chunk = DocumentChunk(
                    chunk_index=index,
                    chunk_text=chunk_text,
                    embedding=embedding,
                    metadata=metadata,
                    session_id=session_id,
                    user_id=user_id
                )
                db.add(document_chunk)
            db.commit()
        except Exception as e:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to store chunks: {str(e)}"
            )

    @staticmethod
    def create(document_chunk_data: dict, db: Session) -> DocumentChunk:
        try:
            document_chunk = DocumentChunk(**document_chunk_data)
            db.add(document_chunk)
            db.commit()
            db.refresh(document_chunk)
            return document_chunk
        except Exception as e:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to create document chunk: {str(e)}"
            )

    @staticmethod
    def get_by_id(chunk_id: UUID, db: Session) -> DocumentChunk:
        document_chunk = db.query(DocumentChunk).filter(DocumentChunk.id == chunk_id).first()
        if not document_chunk:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Document chunk not found"
            )
        return document_chunk

    @staticmethod
    def list_all(db: Session) -> List[DocumentChunk]:
        return db.query(DocumentChunk).all()

    @staticmethod
    def update(chunk_id: UUID, update_data: dict, db: Session) -> DocumentChunk:
        document_chunk = db.query(DocumentChunk).filter(DocumentChunk.id == chunk_id).first()
        if not document_chunk:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Document chunk not found"
            )
        for key, value in update_data.items():
            setattr(document_chunk, key, value)
        db.commit()
        db.refresh(document_chunk)
        return document_chunk

    @staticmethod
    def delete(chunk_id: UUID, db: Session) -> None:
        document_chunk = db.query(DocumentChunk).filter(DocumentChunk.id == chunk_id).first()
        if not document_chunk:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Document chunk not found"
            )
        db.delete(document_chunk)
        db.commit()