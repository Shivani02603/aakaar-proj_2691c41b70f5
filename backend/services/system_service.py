from typing import List, Optional
from uuid import UUID
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from database.models import User
from database.config import get_db
from env import OPENAI_API_KEY, EMBEDDING_MODEL, GENERATION_MODEL


class SystemService:
    @staticmethod
    def create_user(user_data: dict, db: Session) -> User:
        """Create a new user in the database."""
        existing_user = db.query(User).filter(User.email == user_data["email"]).first()
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="A user with this email already exists.",
            )
        new_user = User(
            id=user_data["id"],
            username=user_data["username"],
            email=user_data["email"],
            hashed_password=user_data["hashed_password"],
            created_at=user_data["created_at"],
        )
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        return new_user

    @staticmethod
    def get_user_by_id(user_id: UUID, db: Session) -> User:
        """Retrieve a user by their ID."""
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found.",
            )
        return user

    @staticmethod
    def list_all_users(db: Session) -> List[User]:
        """List all users in the database."""
        users = db.query(User).all()
        return users

    @staticmethod
    def update_user(user_id: UUID, user_data: dict, db: Session) -> User:
        """Update an existing user's information."""
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
        """Delete a user from the database."""
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found.",
            )
        db.delete(user)
        db.commit()

    @staticmethod
    def get_openai_api_key() -> str:
        """Retrieve the OpenAI API key from environment variables."""
        if not OPENAI_API_KEY:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="OpenAI API key is not configured.",
            )
        return OPENAI_API_KEY

    @staticmethod
    def get_embedding_model_info() -> dict:
        """Retrieve information about the embedding model."""
        if not EMBEDDING_MODEL:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Embedding model is not configured.",
            )
        return {
            "model_name": EMBEDDING_MODEL,
            "dimension": 1536,  # As per FR-039
        }

    @staticmethod
    def get_generation_model_info() -> dict:
        """Retrieve information about the generation model."""
        if not GENERATION_MODEL:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Generation model is not configured.",
            )
        return {
            "model_name": GENERATION_MODEL,
        }