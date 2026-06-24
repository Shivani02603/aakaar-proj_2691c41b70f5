from typing import List, Optional
from uuid import UUID
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from database.models import User, Document, Query
from database.config import get_db


class UIService:
    @staticmethod
    def create_user(user_data: dict, db: Session) -> User:
        existing_user = db.query(User).filter(User.email == user_data["email"]).first()
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="A user with this email already exists.",
            )
        new_user = User(**user_data)
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        return new_user

    @staticmethod
    def get_user_by_id(user_id: UUID, db: Session) -> User:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found.",
            )
        return user

    @staticmethod
    def list_all_users(db: Session) -> List[User]:
        return db.query(User).all()

    @staticmethod
    def update_user(user_id: UUID, user_data: dict, db: Session) -> User:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found.",
            )
        for key, value in user_data.items():
            setattr(user, key, value)
        db.commit()
        db.refresh(user)
        return user

    @staticmethod
    def delete_user(user_id: UUID, db: Session) -> None:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found.",
            )
        db.delete(user)
        db.commit()

    @staticmethod
    def list_documents_by_user(user_id: UUID, db: Session) -> List[Document]:
        documents = db.query(Document).filter(Document.user_id == user_id).all()
        if not documents:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No documents found for this user.",
            )
        return documents

    @staticmethod
    def list_queries_by_user(user_id: UUID, db: Session) -> List[Query]:
        queries = db.query(Query).filter(Query.user_id == user_id).all()
        if not queries:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No queries found for this user.",
            )
        return queries

    @staticmethod
    def get_query_sources(query_id: UUID, db: Session) -> List[dict]:
        query = db.query(Query).filter(Query.id == query_id).first()
        if not query:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Query not found.",
            )
        return query.sources