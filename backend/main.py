import os
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import ValidationError
from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from starlette.middleware.cors import CORSMiddleware
from starlette.middleware.trustedhost import TrustedHostMiddleware
from database.config import init_db
from backend.routers.auth import router as auth_router
from backend.routers.users import router as users_router
from backend.routers.sessions import router as sessions_router
from backend.routers.document_management import router as document_management_router
from backend.routers.query import router as query_router
from backend.routers.ingestion import router as ingestion_router
from backend.routers.ui import router as ui_router
from backend.routers.system import router as system_router
from backend.main import _rate_limit_handler, general_exception_handler, validation_exception_handler, http_exception_handler, health_check, lifespan

# Initialize FastAPI app
app = FastAPI(
    title="Aakaar Project",
    description="Backend for AI-powered web application",
    version="1.0.0",
    lifespan=lifespan,
)

# Initialize database
init_db()

# Configure CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[os.getenv('FRONTEND_URL', 'http://localhost:3000')],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure TrustedHost middleware
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["*"],  # Adjust this based on your deployment
)

# Configure rate limiter
limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_handler)

# Mount routers
app.include_router(auth_router, prefix="/api/auth", tags=["Auth"])
app.include_router(users_router, prefix="/api/users", tags=["Users"])
app.include_router(sessions_router, prefix="/api/sessions", tags=["Sessions"])
app.include_router(document_management_router, prefix="/api/document_management", tags=["Document_management"])
app.include_router(query_router, prefix="/api/query", tags=["Query"])
app.include_router(ingestion_router, prefix="/api/ingestion", tags=["Ingestion"])
app.include_router(ui_router, prefix="/api/ui", tags=["Ui"])
app.include_router(system_router, prefix="/api/system", tags=["System"])

# Global exception handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return await http_exception_handler(request, exc)

@app.exception_handler(ValidationError)
async def validation_exception_handler(request: Request, exc: ValidationError):
    return await validation_exception_handler(request, exc)

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    return await general_exception_handler(request, exc)

# Health check endpoint
@app.get("/health")
async def health_check():
    return await health_check()

# AI_ROUTER_INJECTION_POINT — do not remove this line