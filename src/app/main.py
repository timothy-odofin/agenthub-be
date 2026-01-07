import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.v1 import chat, health, ingest_data as ingest, auth, conversational_auth

# Get allowed origins from environment variable
allowed_origins = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000").split(",")
allow_credentials = os.getenv("ALLOW_CREDENTIALS", "true").lower() == "true"

app = FastAPI(
    title="AgentHub API",
    version="1.0.0",
    description="AI-powered agent hub with multi-provider LLM support"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[origin.strip() for origin in allowed_origins],
    allow_credentials=allow_credentials,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
app.include_router(auth.router, prefix="/api/v1/auth", tags=["authentication"])
app.include_router(conversational_auth.router, prefix="/api/v1/auth", tags=["conversational-auth"])
app.include_router(chat.router, prefix="/api/v1/chat", tags=["chat"])
app.include_router(health.router, prefix="/api/v1/health", tags=["health"])
app.include_router(ingest.router, prefix="/api/v1/data", tags=["ingest"])


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
