import os
import bcrypt
from datetime import datetime, timedelta
from jose import JWTError, jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer
from sqlalchemy.orm import Session
from database.models import User
from database.config import get_db

# Constants
JWT_SECRET = os.getenv("JWT_SECRET")
if not JWT_SECRET:
    raise ValueError("JWT_SECRET env var is not set")

JWT_ALGORITHM = "HS256"

# Password hashing
def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

def verify_password(password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(password.encode(), hashed_password.encode())

# JWT token creation
def create_access_token(data: dict) -> str:
    data["exp"] = datetime.utcnow() + timedelta(hours=24)
    return jwt.encode(data, JWT_SECRET, algorithm=JWT_ALGORITHM)

# JWT token decoding
def decode_access_token(token: str) -> dict:
    try:
        return jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )

# FastAPI dependency to get the current user
async def get_current_user(token: str = Depends(HTTPBearer()), db: Session = Depends(get_db)) -> User:
    try:
        payload = decode_access_token(token.credentials)
        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token payload",
                headers={"WWW-Authenticate": "Bearer"},
            )
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found",
                headers={"WWW-Authenticate": "Bearer"},
            )
        return user
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while processing the token",
        )