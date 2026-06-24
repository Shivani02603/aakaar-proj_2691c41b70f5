from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID
from pydantic import BaseModel, Field
from database.models import User
from database.config import get_db
from backend.services.auth_service import get_current_user
import os

router = APIRouter(prefix="/system", tags=["System"])

# Pydantic Schemas
class SystemConfig(BaseModel):
    openai_api_key: str = Field(..., description="OpenAI API key")
    embedding_model: str = Field(..., description="Embedding model name")
    embedding_dimension: int = Field(..., description="Embedding model dimension")
    generation_model: str = Field(..., description="Generation model name")

class SystemConfigResponse(BaseModel):
    openai_api_key: str = Field(..., description="OpenAI API key")
    embedding_model: str = Field(..., description="Embedding model name")
    embedding_dimension: int = Field(..., description="Embedding model dimension")
    generation_model: str = Field(..., description="Generation model name")

class SystemStatus(BaseModel):
    database_status: str = Field(..., description="Database connection status")
    openai_api_key_status: str = Field(..., description="OpenAI API key status")

# Helper Functions
def check_openai_api_key() -> str:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise HTTPException(status_code=500, detail="OpenAI API key is not configured")
    return api_key

# Routes
@router.get("/config", response_model=SystemConfigResponse, dependencies=[Depends(get_current_user)])
async def get_system_config():
    """
    Retrieve system configuration details.
    """
    return SystemConfigResponse(
        openai_api_key=os.getenv("OPENAI_API_KEY", ""),
        embedding_model="text-embedding-3-small",
        embedding_dimension=1536,
        generation_model="gpt-4o-mini"
    )

@router.put("/config", response_model=SystemConfigResponse, dependencies=[Depends(get_current_user)])
async def update_system_config(config: SystemConfig, db: Session = Depends(get_db)):
    """
    Update system configuration details.
    """
    # Update environment variables or database settings here
    os.environ["OPENAI_API_KEY"] = config.openai_api_key
    return SystemConfigResponse(
        openai_api_key=config.openai_api_key,
        embedding_model=config.embedding_model,
        embedding_dimension=config.embedding_dimension,
        generation_model=config.generation_model
    )

@router.get("/status", response_model=SystemStatus, dependencies=[Depends(get_current_user)])
async def get_system_status(db: Session = Depends(get_db)):
    """
    Retrieve system status details.
    """
    # Check database connection
    try:
        db.execute("SELECT 1")
        database_status = "Healthy"
    except Exception:
        database_status = "Unhealthy"

    # Check OpenAI API key
    try:
        check_openai_api_key()
        openai_api_key_status = "Configured"
    except HTTPException:
        openai_api_key_status = "Not Configured"

    return SystemStatus(
        database_status=database_status,
        openai_api_key_status=openai_api_key_status
    )

@router.post("/reset", dependencies=[Depends(get_current_user)])
async def reset_system_config(user: User = Depends(get_current_user)):
    """
    Reset system configuration to default values.
    """
    os.environ["OPENAI_API_KEY"] = ""
    return {"message": "System configuration has been reset to default values."}