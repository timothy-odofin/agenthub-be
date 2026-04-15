"""
AgentHub - FastAPI Application Entry Point

This module initializes the FastAPI application with:
- Multi-environment support via CLI arguments
- Comprehensive middleware stack
- Global exception handling
- API routing
- Startup warmup (pre-loads tools, MongoDB, and agent to eliminate cold start)

Environment Configuration:
    Use --env flag to specify environment file:
        python -m uvicorn app.main:app --env .env.production

    If not specified, defaults to .env file.
"""

import os
import sys

# ============================================================================
# ENVIRONMENT INITIALIZATION (Must happen BEFORE other imports)
# ============================================================================
# Parse CLI arguments and initialize environment FIRST
from app.core.cli import get_env_file_from_cli
from app.core.utils.env_utils import initialize_environment

# Get env file from CLI and initialize environment
env_file = get_env_file_from_cli()
env = initialize_environment(env_file)

# ============================================================================
# APPLICATION IMPORTS (After environment is initialized)
# ============================================================================
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.api.v1 import auth, chat, conversational_auth, health
from app.api.v1 import ingest_data as ingest
from app.api.v1 import llm, resilience, routes, tools
from app.core.exceptions import BaseAppException
from app.core.handlers import (
    base_app_exception_handler,
    generic_exception_handler,
    http_exception_handler,
    validation_error_handler,
)
from app.core.middleware import RequestContextMiddleware
from app.core.utils.logger import get_logger

logger = get_logger(__name__)


# ============================================================================
# STARTUP WARMUP — eliminates 30s+ cold start on first request
# ============================================================================


async def _warmup():
    """
    Pre-initialize expensive resources at server startup.

    From production logs (2026-04-07), the first request takes ~54s because:
      - MongoDB connection:        ~3.5s
      - LLM provider init:         ~2.4s
      - Tool loading (86 tools):   ~30s  (GitHub repo discovery = 24s alone)
      - Agent creation:            ~0.2s

    By running this at startup, the first user request gets a cached, warm agent.
    """
    import asyncio

    logger.info("🚀 Starting warmup — pre-loading tools and agent...")
    warmup_start = asyncio.get_event_loop().time()

    try:
        # Step 1: Pre-connect MongoDB (saves ~3.5s on first request)
        try:
            from app.infrastructure.connections.base import ConnectionType
            from app.infrastructure.connections.factory.connection_factory import (
                ConnectionFactory,
            )

            mongo_manager = ConnectionFactory.get_connection_manager(
                ConnectionType.MONGODB
            )
            mongo_manager.connect()
            logger.info("✅ MongoDB pre-connected")
        except Exception as e:
            logger.warning(
                f"⚠️ MongoDB warmup failed (will retry on first request): {e}"
            )

        # Step 2: Pre-load all tools (saves ~30s — triggers GitHub discovery + caching)
        try:
            from app.agent.tools.base.registry import ToolRegistry

            tools = ToolRegistry.get_instantiated_tools()
            logger.info(f"✅ Pre-loaded {len(tools)} tools into cache")
        except Exception as e:
            logger.warning(f"⚠️ Tool warmup failed (will retry on first request): {e}")

        # Step 3: Pre-create and cache default agent (saves ~3s on first request)
        try:
            from app.services.chat_service import ChatService

            chat_svc = ChatService()
            _ = await chat_svc.agent  # Triggers lazy init + caches the agent
            logger.info("✅ Default agent pre-created and cached")
        except Exception as e:
            logger.warning(f"⚠️ Agent warmup failed (will retry on first request): {e}")

        elapsed = asyncio.get_event_loop().time() - warmup_start
        logger.info(
            f"🚀 Warmup completed in {elapsed:.1f}s — first request will be fast!"
        )

    except Exception as e:
        logger.error(f"❌ Warmup failed: {e}", exc_info=True)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan — runs warmup at startup, cleanup at shutdown."""
    await _warmup()
    yield
    logger.info("Application shutting down")


# Get allowed origins from environment variable
allowed_origins = env.get_list("ALLOWED_ORIGINS", default=["http://localhost:3000"])
allow_credentials = env.get_bool("ALLOW_CREDENTIALS", default=True)

app = FastAPI(
    title="AgentHub API",
    version="1.0.0",
    description="AI-powered agent hub with multi-provider LLM support",
    lifespan=lifespan,
)

# ============================================================================
# MIDDLEWARE CONFIGURATION
# ============================================================================

# Request Context Middleware (must be added first to track all requests)
app.add_middleware(RequestContextMiddleware)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    # allow_credentials=allow_credentials,
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
app.include_router(
    conversational_auth.router, prefix="/api/v1/auth", tags=["conversational-auth"]
)
app.include_router(chat.router, prefix="/api/v1/chat", tags=["chat"])
app.include_router(routes.router, prefix="/api/v1/routes", tags=["routes"])
app.include_router(health.router, prefix="/api/v1/health", tags=["health"])
app.include_router(ingest.router, prefix="/api/v1/data", tags=["ingest"])
app.include_router(resilience.router, prefix="/api/v1", tags=["resilience"])
app.include_router(llm.router, prefix="/api/v1/llm", tags=["llm-providers"])
app.include_router(tools.router, prefix="/api/v1/tools", tags=["tools"])


@app.get("/")
def root():
    return {
        "status": "ok",
        "message": "AgentHub API is running",
        "version": "1.0.0",
        "docs": "/docs",
    }


@app.get("/health")
def health_check():
    return {"status": "healthy", "version": "1.0.0"}
