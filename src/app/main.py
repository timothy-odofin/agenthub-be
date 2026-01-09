import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.api.v1 import chat, health, ingest_data as ingest, auth, conversational_auth, resilience
from app.core.middleware import RequestContextMiddleware
from app.core.handlers import (
    base_app_exception_handler,
    validation_error_handler,
    http_exception_handler,
    generic_exception_handler,
)
from app.core.exceptions import BaseAppException
from app.core.utils.logger import get_logger

logger = get_logger(__name__)

# Get allowed origins from environment variable
allowed_origins = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000").split(",")
allow_credentials = os.getenv("ALLOW_CREDENTIALS", "true").lower() == "true"

app = FastAPI(
    title="AgentHub API",
    version="1.0.0",
    description="AI-powered agent hub with multi-provider LLM support"
)

# ============================================================================
# MIDDLEWARE CONFIGURATION
# ============================================================================

# Request Context Middleware (must be added first to track all requests)
app.add_middleware(RequestContextMiddleware)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[origin.strip() for origin in allowed_origins],
    allow_credentials=allow_credentials,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================================================
# EXCEPTION HANDLERS
# ============================================================================

# Register exception handlers in order of specificity (most specific first)

# 1. Custom application exceptions (our exception hierarchy)
app.add_exception_handler(BaseAppException, base_app_exception_handler)

# 2. FastAPI/Pydantic validation errors
app.add_exception_handler(RequestValidationError, validation_error_handler)

# 3. Starlette/FastAPI HTTPException
app.add_exception_handler(StarletteHTTPException, http_exception_handler)

# 4. Catch-all for any unhandled exceptions
app.add_exception_handler(Exception, generic_exception_handler)

logger.info("Exception handlers registered successfully")

# ============================================================================
# ROUTERS
# ============================================================================
app.include_router(auth.router, prefix="/api/v1/auth", tags=["authentication"])
app.include_router(conversational_auth.router, prefix="/api/v1/auth", tags=["conversational-auth"])
app.include_router(chat.router, prefix="/api/v1/chat", tags=["chat"])
app.include_router(health.router, prefix="/api/v1/health", tags=["health"])
app.include_router(ingest.router, prefix="/api/v1/data", tags=["ingest"])
app.include_router(resilience.router, prefix="/api/v1", tags=["resilience"])


@app.get("/")
def root():
    return {
        "status": "ok",
        "message": "AgentHub API is running",
        "version": "1.0.0",
        "docs": "/docs"
    }


@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "version": "1.0.0"
    }
