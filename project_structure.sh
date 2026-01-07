#!/bin/bash

# ========================================
# AgentHub Backend Project Structure Setup
# ========================================
# This script creates a complete project structure for the AgentHub backend.
# It includes authentication, LangGraph workflows, database models, and comprehensive testing.
#
# Usage: ./project_structure.sh [optional_directory_name]
# Example: ./project_structure.sh my-agenthub-project

# === Settings ===
PROJECT_NAME="agenthub-be"
BASE_DIR=${1:-$(pwd)/$PROJECT_NAME}

echo "========================================="
echo "🚀 AgentHub Backend Project Structure"
echo "========================================="
echo "📂 Initializing project in: $BASE_DIR"
echo ""

# === Create main directory structure ===
echo "📁 Creating directory structure..."

# Root directories
mkdir -p $BASE_DIR/{src,tests,resources,volumes,logs,examples}

# Source directories - API
mkdir -p $BASE_DIR/src/app/api/v1

# Source directories - Core
mkdir -p $BASE_DIR/src/app/core/{config/{application,framework,providers,utils},schemas,security,utils/exception,enums}

# Source directories - Database
mkdir -p $BASE_DIR/src/app/db/{models,repositories,vector/{embeddings,providers}}

# Source directories - Services
mkdir -p $BASE_DIR/src/app/services/{external,ingestion}

# Source directories - Sessions
mkdir -p $BASE_DIR/src/app/sessions/{models,repositories}

# Source directories - LLM
mkdir -p $BASE_DIR/src/app/llm/{base,config,context,factory,providers}

# Source directories - Connections
mkdir -p $BASE_DIR/src/app/connections/{base,database,external,vector,factory}

# Source directories - Agent
mkdir -p $BASE_DIR/src/app/agent/{base,frameworks,implementations,models,tools/{atlassian,base,database,datadog,github},workflows}

# Source directories - Workers
mkdir -p $BASE_DIR/src/app/workers

# Source directories - Schemas
mkdir -p $BASE_DIR/src/app/schemas

# Test directories
mkdir -p $BASE_DIR/tests/{unit/{api,core/security,db/{models,repositories},services,agent/workflows},integration,e2e}

# Resources directories
mkdir -p $BASE_DIR/resources/workflows

# Volumes directories (for Docker)
mkdir -p $BASE_DIR/volumes/{mongodb,postgres,redis,pgadmin}

# Examples directory
mkdir -p $BASE_DIR/examples

echo "✅ Directory structure created"
echo ""

# === Create root configuration files ===
echo "📝 Creating root configuration files..."

# .env.example
cat > $BASE_DIR/.env.example << 'EOF'
# Database Configuration
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_USER=admin
POSTGRES_PASSWORD=admin123
POSTGRES_DB=agenthub

MONGODB_HOST=localhost
MONGODB_PORT=27017
MONGODB_USER=admin
MONGODB_PASSWORD=admin123
MONGODB_DB=agenthub

REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_PASSWORD=

# JWT Configuration
JWT_SECRET_KEY=your-secret-key-change-in-production
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# LLM Configuration
OPENAI_API_KEY=your-openai-api-key
ANTHROPIC_API_KEY=your-anthropic-api-key
GROQ_API_KEY=your-groq-api-key

# Azure OpenAI Configuration
AZURE_OPENAI_API_KEY=your-azure-openai-api-key
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_OPENAI_DEPLOYMENT=gpt-4
AZURE_OPENAI_API_VERSION=2024-02-15-preview

# Vector Database
QDRANT_HOST=localhost
QDRANT_PORT=6333
QDRANT_API_KEY=

# External Services
JIRA_URL=https://your-domain.atlassian.net
JIRA_EMAIL=your-email@example.com
JIRA_API_TOKEN=your-jira-api-token

CONFLUENCE_URL=https://your-domain.atlassian.net
CONFLUENCE_EMAIL=your-email@example.com
CONFLUENCE_API_TOKEN=your-confluence-api-token

GITHUB_TOKEN=your-github-token

# Application
APP_ENV=development
LOG_LEVEL=INFO
EOF

# pyproject.toml
cat > $BASE_DIR/pyproject.toml << 'EOF'
[tool.poetry]
name = "agenthub-be"
version = "1.0.0"
description = "AgentHub Backend with LangGraph workflows and JWT authentication"
authors = ["Your Name <your.email@example.com>"]

[tool.poetry.dependencies]
python = "^3.11"
fastapi = "^0.110.0"
uvicorn = {extras = ["standard"], version = "^0.27.0"}
pydantic = "^2.6.0"
pydantic-settings = "^2.1.0"
python-jose = {extras = ["cryptography"], version = "^3.3.0"}
passlib = {extras = ["bcrypt"], version = "^1.7.4"}
bcrypt = "^4.1.2"
pymongo = "^4.6.1"
motor = "^3.3.2"
psycopg2-binary = "^2.9.9"
redis = "^5.0.1"
sqlalchemy = "^2.0.25"
alembic = "^1.13.1"
langchain = "^0.1.0"
langgraph = "^0.0.20"
langchain-openai = "^0.0.5"
langchain-anthropic = "^0.0.1"
langchain-community = "^0.0.20"
qdrant-client = "^1.7.0"
chromadb = "^0.4.22"
sentence-transformers = "^2.3.1"
python-multipart = "^0.0.6"
python-dotenv = "^1.0.0"
httpx = "^0.26.0"
celery = "^5.3.4"

[tool.poetry.group.dev.dependencies]
pytest = "^8.0.0"
pytest-asyncio = "^0.23.3"
pytest-mock = "^3.12.0"
pytest-cov = "^4.1.0"
black = "^24.1.0"
ruff = "^0.1.14"
mypy = "^1.8.0"

[build-system]
requires = ["poetry-core"]
build-backend = "poetry.core.masonry.api"

[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]
python_files = ["test_*.py"]
python_classes = ["Test*"]
python_functions = ["test_*"]

[tool.black]
line-length = 100
target-version = ['py311']

[tool.ruff]
line-length = 100
target-version = "py311"
EOF

# requirements.txt
cat > $BASE_DIR/requirements.txt << 'EOF'
fastapi==0.110.0
uvicorn[standard]==0.27.0
pydantic==2.6.0
pydantic-settings==2.1.0
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4
bcrypt==4.1.2
pymongo==4.6.1
motor==3.3.2
psycopg2-binary==2.9.9
redis==5.0.1
sqlalchemy==2.0.25
alembic==1.13.1
langchain==0.1.0
langgraph==0.0.20
langchain-openai==0.0.5
langchain-anthropic==0.0.1
langchain-community==0.0.20
qdrant-client==1.7.0
chromadb==0.4.22
sentence-transformers==2.3.1
python-multipart==0.0.6
python-dotenv==1.0.0
httpx==0.26.0
celery==5.3.4
EOF

# requirements-dev.txt
cat > $BASE_DIR/requirements-dev.txt << 'EOF'
pytest==8.0.0
pytest-asyncio==0.23.3
pytest-mock==3.12.0
pytest-cov==4.1.0
black==24.1.0
ruff==0.1.14
mypy==1.8.0
EOF

# docker-compose.yml
cat > $BASE_DIR/docker-compose.yml << 'EOF'
version: '3.8'

services:
  postgres:
    image: postgres:15
    container_name: agenthub-postgres
    environment:
      POSTGRES_USER: admin
      POSTGRES_PASSWORD: admin123
      POSTGRES_DB: agenthub
    ports:
      - "5432:5432"
    volumes:
      - ./volumes/postgres:/var/lib/postgresql/data

  mongodb:
    image: mongo:7
    container_name: agenthub-mongodb
    environment:
      MONGO_INITDB_ROOT_USERNAME: admin
      MONGO_INITDB_ROOT_PASSWORD: admin123
      MONGO_INITDB_DATABASE: agenthub
    ports:
      - "27017:27017"
    volumes:
      - ./volumes/mongodb:/data/db

  redis:
    image: redis:7-alpine
    container_name: agenthub-redis
    ports:
      - "6379:6379"
    volumes:
      - ./volumes/redis:/data

  qdrant:
    image: qdrant/qdrant:latest
    container_name: agenthub-qdrant
    ports:
      - "6333:6333"
    volumes:
      - ./volumes/qdrant:/qdrant/storage
EOF

# Makefile
cat > $BASE_DIR/Makefile << 'EOF'
.PHONY: install test run docker-up docker-down clean

install:
	pip install -r requirements.txt
	pip install -r requirements-dev.txt

test:
	pytest tests/ -v

test-cov:
	pytest tests/ --cov=src/app --cov-report=html

run:
	uvicorn src.app.main:app --reload --host 0.0.0.0 --port 8000

docker-up:
	docker-compose up -d

docker-down:
	docker-compose down

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	rm -rf .pytest_cache
	rm -rf htmlcov
	rm -rf .coverage
EOF

# README.md
cat > $BASE_DIR/README.md << 'EOF'
# AgentHub Backend

A comprehensive backend application with JWT authentication, LangGraph workflows, and AI agent integration.

## Features

- 🔐 **JWT Authentication**: Secure user authentication with access and refresh tokens
- 🤖 **LangGraph Workflows**: Signup validation and agent workflows
- 📊 **Multiple Databases**: PostgreSQL, MongoDB, Redis support
- 🧠 **AI Integration**: LangChain, OpenAI, Anthropic integration
- 🔍 **Vector Search**: Qdrant and ChromaDB support
- 🧪 **Comprehensive Testing**: Unit, integration, and E2E tests
- 🐳 **Docker Support**: Easy deployment with Docker Compose

## Quick Start

1. Install dependencies:
   ```bash
   make install
   ```

2. Set up environment variables:
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

3. Start databases:
   ```bash
   make docker-up
   ```

4. Run the application:
   ```bash
   make run
   ```

5. Run tests:
   ```bash
   make test
   ```

## Project Structure

See `project_structure.sh` for the complete project structure.

## API Documentation

Once running, visit:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Authentication Endpoints

- POST `/api/v1/auth/signup` - User registration
- POST `/api/v1/auth/login` - User login
- POST `/api/v1/auth/refresh` - Token refresh

## License

MIT
EOF

# .gitignore
cat > $BASE_DIR/.gitignore << 'EOF'
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg

# Virtual Environment
.env
.venv
env/
venv/
ENV/
env.bak/
venv.bak/

# IDEs
.vscode/
.idea/
*.swp
*.swo
*~

# Testing
.pytest_cache/
.coverage
htmlcov/
.tox/
.hypothesis/

# Databases
*.db
*.sqlite
*.sqlite3
volumes/postgres/
volumes/mongodb/
volumes/redis/
volumes/qdrant/

# Logs
logs/
*.log

# OS
.DS_Store
Thumbs.db

# Environment
.env.local
.env.*.local

# Temporary files
*.tmp
*.temp
EOF

echo "✅ Root configuration files created"
echo ""

# === Create Python __init__.py files ===
echo "📝 Creating Python package files..."

# Create all __init__.py files
find $BASE_DIR/src -type d -exec touch {}/__init__.py \;
find $BASE_DIR/tests -type d -exec touch {}/__init__.py \;

echo "✅ Python package files created"
echo ""

# === Create core application files ===
echo "📝 Creating core application files..."

# Main FastAPI application
cat > $BASE_DIR/src/app/main.py << 'EOF'
"""
AgentHub Backend - Main Application Entry Point
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1 import auth, chat, health
from app.core.config import settings

app = FastAPI(
    title="AgentHub Backend",
    description="AI Agent Platform with JWT Authentication",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router, prefix="/api/v1/auth", tags=["Authentication"])
app.include_router(chat.router, prefix="/api/v1/chat", tags=["Chat"])
app.include_router(health.router, prefix="/api/v1/health", tags=["Health"])

@app.get("/")
async def root():
    return {
        "status": "ok",
        "message": "AgentHub Backend is running 🚀",
        "version": "1.0.0"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
EOF

# Authentication API
cat > $BASE_DIR/src/app/api/v1/auth.py << 'EOF'
"""
Authentication API endpoints.
"""
from fastapi import APIRouter, Depends, HTTPException, status

from app.schemas.auth import (
    SignupRequest,
    SignupResponse,
    LoginRequest,
    LoginResponse,
    RefreshTokenRequest,
    RefreshTokenResponse,
)
from app.services.auth_service import auth_service

router = APIRouter()

@router.post("/signup", response_model=SignupResponse)
async def signup(request: SignupRequest):
    """Register a new user."""
    result = await auth_service.signup(
        email=request.email,
        username=request.username,
        password=request.password,
        firstname=request.firstname,
        lastname=request.lastname,
    )
    
    if not result["success"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result["message"]
        )
    
    return SignupResponse(**result)

@router.post("/login", response_model=LoginResponse)
async def login(request: LoginRequest):
    """Authenticate a user and return JWT tokens."""
    result = await auth_service.login(
        identifier=request.identifier,
        password=request.password,
    )
    
    if not result["success"]:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=result["message"]
        )
    
    return LoginResponse(**result)

@router.post("/refresh", response_model=RefreshTokenResponse)
async def refresh_token(request: RefreshTokenRequest):
    """Refresh access token using refresh token."""
    result = await auth_service.refresh_token(request.refresh_token)
    
    if not result["success"]:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=result["message"]
        )
    
    return RefreshTokenResponse(**result)
EOF

# Health check API
cat > $BASE_DIR/src/app/api/v1/health.py << 'EOF'
"""
Health check API endpoints.
"""
from fastapi import APIRouter

router = APIRouter()

@router.get("/")
async def health_check():
    """Basic health check."""
    return {"status": "healthy"}

@router.get("/livez")
async def liveness():
    """Kubernetes liveness probe."""
    return {"status": "alive"}

@router.get("/readyz")
async def readiness():
    """Kubernetes readiness probe."""
    return {"status": "ready"}
EOF

# Chat API (placeholder)
cat > $BASE_DIR/src/app/api/v1/chat.py << 'EOF'
"""
Chat API endpoints.
"""
from fastapi import APIRouter, Depends

from app.schemas.chat import ChatRequest, ChatResponse
from app.core.security.dependencies import get_current_user
from app.db.models.user import UserInDB

router = APIRouter()

@router.post("/", response_model=ChatResponse)
async def send_message(
    request: ChatRequest,
    current_user: UserInDB = Depends(get_current_user)
):
    """Send a chat message (authenticated)."""
    # TODO: Integrate with chat service
    return ChatResponse(
        success=True,
        message="This is a placeholder response",
        session_id=request.session_id or "new_session",
        user_id=str(current_user.id)
    )
EOF

echo "✅ Core application files created"
echo ""

# === Create authentication schema files ===
echo "📝 Creating schema files..."

cat > $BASE_DIR/src/app/schemas/auth.py << 'EOF'
"""
Authentication request and response schemas.
"""
from pydantic import BaseModel, EmailStr, Field
from typing import Optional

class SignupRequest(BaseModel):
    email: EmailStr
    username: str = Field(..., min_length=3, max_length=30)
    password: str = Field(..., min_length=8, max_length=72)
    firstname: str = Field(..., min_length=1, max_length=50)
    lastname: str = Field(..., min_length=1, max_length=50)

class SignupResponse(BaseModel):
    success: bool
    message: str
    user_id: Optional[str] = None
    access_token: Optional[str] = None
    refresh_token: Optional[str] = None
    token_type: str = "bearer"

class LoginRequest(BaseModel):
    identifier: str
    password: str

class LoginResponse(BaseModel):
    success: bool
    message: str
    access_token: Optional[str] = None
    refresh_token: Optional[str] = None
    token_type: str = "bearer"
    user: Optional[dict] = None

class RefreshTokenRequest(BaseModel):
    refresh_token: str

class RefreshTokenResponse(BaseModel):
    success: bool
    message: str
    access_token: Optional[str] = None
    token_type: str = "bearer"
EOF

cat > $BASE_DIR/src/app/schemas/chat.py << 'EOF'
"""
Chat request and response schemas.
"""
from pydantic import BaseModel
from typing import Optional

class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None

class ChatResponse(BaseModel):
    success: bool
    message: str
    session_id: str
    user_id: str
EOF

echo "✅ Schema files created"
echo ""

# === Create security module files ===
echo "📝 Creating security module files..."

cat > $BASE_DIR/src/app/core/security/password_handler.py << 'EOF'
"""
Password hashing and verification using bcrypt.
"""
import bcrypt
from typing import Optional, Tuple

class PasswordManager:
    """Singleton for password operations."""
    
    _instance: Optional['PasswordManager'] = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not hasattr(self, '_initialized'):
            self._rounds = 12
            self._initialized = True
    
    def hash_password(self, password: str) -> str:
        """Hash a password using bcrypt."""
        if not password:
            raise ValueError("Password cannot be empty")
        password_bytes = password.encode('utf-8')
        hashed = bcrypt.hashpw(password_bytes, bcrypt.gensalt(rounds=self._rounds))
        return hashed.decode('utf-8')
    
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify a password against its hash."""
        if not plain_password or not hashed_password:
            return False
        try:
            password_bytes = plain_password.encode('utf-8')
            hashed_bytes = hashed_password.encode('utf-8')
            return bcrypt.checkpw(password_bytes, hashed_bytes)
        except Exception:
            return False
    
    def validate_password_strength(self, password: str) -> Tuple[bool, Optional[str]]:
        """Validate password meets strength requirements."""
        # TODO: Implement password strength validation
        if len(password) < 8:
            return False, "Password must be at least 8 characters"
        return True, None

password_manager = PasswordManager()
EOF

cat > $BASE_DIR/src/app/core/security/token_manager.py << 'EOF'
"""
JWT token creation and verification.
"""
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any
from jose import jwt, JWTError

class TokenManager:
    """Singleton for JWT operations."""
    
    _instance: Optional['TokenManager'] = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not hasattr(self, '_initialized'):
            self._secret_key = "your-secret-key-change-in-production"
            self._algorithm = "HS256"
            self._access_token_expire_minutes = 30
            self._initialized = True
    
    def create_access_token(
        self,
        user_id: str,
        email: str,
        username: Optional[str] = None,
        additional_claims: Optional[Dict[str, Any]] = None,
        expires_delta: Optional[timedelta] = None
    ) -> str:
        """Create a JWT access token."""
        to_encode = {
            "sub": user_id,
            "user_id": user_id,
            "email": email,
            "type": "access"
        }
        
        if username:
            to_encode["username"] = username
        
        if additional_claims:
            to_encode.update(additional_claims)
        
        if expires_delta:
            expire = datetime.now(timezone.utc) + expires_delta
        else:
            expire = datetime.now(timezone.utc) + timedelta(minutes=self._access_token_expire_minutes)
        
        to_encode["exp"] = expire
        to_encode["iat"] = datetime.now(timezone.utc)
        
        return jwt.encode(to_encode, self._secret_key, algorithm=self._algorithm)
    
    def verify_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Verify and decode a JWT token."""
        try:
            payload = jwt.decode(token, self._secret_key, algorithms=[self._algorithm])
            if payload.get("type") != "access":
                return None
            return payload
        except JWTError:
            return None
    
    def create_refresh_token(
        self,
        user_id: str,
        expires_delta: Optional[timedelta] = None
    ) -> str:
        """Create a JWT refresh token."""
        to_encode = {
            "sub": user_id,
            "user_id": user_id,
            "type": "refresh"
        }
        
        if expires_delta:
            expire = datetime.now(timezone.utc) + expires_delta
        else:
            expire = datetime.now(timezone.utc) + timedelta(days=7)
        
        to_encode["exp"] = expire
        to_encode["iat"] = datetime.now(timezone.utc)
        
        return jwt.encode(to_encode, self._secret_key, algorithm=self._algorithm)
    
    def verify_refresh_token(self, token: str) -> Optional[str]:
        """Verify a refresh token and return user_id."""
        try:
            payload = jwt.decode(token, self._secret_key, algorithms=[self._algorithm])
            if payload.get("type") != "refresh":
                return None
            return payload.get("user_id")
        except JWTError:
            return None

token_manager = TokenManager()
EOF

cat > $BASE_DIR/src/app/core/security/dependencies.py << 'EOF'
"""
FastAPI dependencies for JWT authentication.
"""
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional

from app.core.security.token_manager import token_manager
from app.db.repositories.user_repository import user_repository
from app.db.models.user import UserInDB

security = HTTPBearer()

async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> UserInDB:
    """Get current authenticated user from JWT token."""
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    token = credentials.credentials
    payload = token_manager.verify_token(token)
    
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token"
        )
    
    user_id = payload.get("user_id")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload"
        )
    
    user = await user_repository.get_user_by_id(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found"
        )
    
    return user

# Alias for clarity
require_auth = get_current_user
EOF

echo "✅ Security module files created"
echo ""

# === Create database model files ===
echo "📝 Creating database model files..."

cat > $BASE_DIR/src/app/db/models/user.py << 'EOF'
"""
User model for MongoDB.
"""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr, Field

class User(BaseModel):
    email: EmailStr
    username: str = Field(..., min_length=3, max_length=30)
    firstname: str = Field(..., min_length=2, max_length=50)
    lastname: str = Field(..., min_length=2, max_length=50)
    password_hash: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    is_active: bool = True
    
    class Config:
        populate_by_name = True

class UserInDB(User):
    id: Optional[str] = Field(None, alias="_id")
    
    class Config:
        populate_by_name = True
EOF

echo "✅ Database model files created"
echo ""

# === Create repository files ===
echo "📝 Creating repository files..."

cat > $BASE_DIR/src/app/db/repositories/user_repository.py << 'EOF'
"""
User repository for MongoDB operations.
"""
from typing import Optional
from datetime import datetime

from app.db.models.user import User, UserInDB

class UserRepository:
    """Repository for User model operations."""
    
    _instance: Optional['UserRepository'] = None
    
    def __init__(self):
        """Initialize repository."""
        self._collection = None  # TODO: Initialize MongoDB collection
    
    async def create_user(
        self,
        email: str,
        username: str,
        firstname: str,
        lastname: str,
        password_hash: str
    ) -> Optional[UserInDB]:
        """Create a new user."""
        # TODO: Implement MongoDB insertion
        pass
    
    async def get_user_by_email(self, email: str) -> Optional[UserInDB]:
        """Get user by email."""
        # TODO: Implement MongoDB query
        pass
    
    async def get_user_by_username(self, username: str) -> Optional[UserInDB]:
        """Get user by username."""
        # TODO: Implement MongoDB query
        pass
    
    async def get_user_by_id(self, user_id: str) -> Optional[UserInDB]:
        """Get user by ID."""
        # TODO: Implement MongoDB query
        pass

user_repository = UserRepository()
EOF

echo "✅ Repository files created"
echo ""

# === Create service files ===
echo "📝 Creating service files..."

cat > $BASE_DIR/src/app/services/auth_service.py << 'EOF'
"""
Authentication service for handling user authentication operations.
"""
from typing import Dict, Any

from app.db.repositories.user_repository import user_repository
from app.core.security.password_handler import password_manager
from app.core.security.token_manager import token_manager

class AuthService:
    """Service class for authentication operations."""
    
    def __init__(self):
        self.user_repository = user_repository
        self.password_manager = password_manager
        self.token_manager = token_manager
    
    async def signup(
        self,
        email: str,
        username: str,
        password: str,
        firstname: str,
        lastname: str
    ) -> Dict[str, Any]:
        """Register a new user."""
        # TODO: Implement signup logic with LangGraph workflow
        return {
            "success": False,
            "message": "Not implemented"
        }
    
    async def login(
        self,
        identifier: str,
        password: str
    ) -> Dict[str, Any]:
        """Authenticate a user."""
        # TODO: Implement login logic
        return {
            "success": False,
            "message": "Not implemented"
        }
    
    async def refresh_token(
        self,
        refresh_token: str
    ) -> Dict[str, Any]:
        """Refresh an access token."""
        # TODO: Implement token refresh logic
        return {
            "success": False,
            "message": "Not implemented"
        }

auth_service = AuthService()
EOF

echo "✅ Service files created"
echo ""

# === Create test files ===
echo "📝 Creating test structure..."

# Create test __init__.py files (already done above)

# Create a sample test file
cat > $BASE_DIR/tests/unit/test_example.py << 'EOF'
"""
Example test file.
"""
import pytest

def test_example():
    """Example test that always passes."""
    assert True

@pytest.mark.asyncio
async def test_async_example():
    """Example async test that always passes."""
    assert True
EOF

echo "✅ Test structure created"
echo ""

# === Create resources files ===
echo "📝 Creating resource configuration files..."

cat > $BASE_DIR/resources/application-defaults.yaml << 'EOF'
# Application default configuration
app:
  name: agenthub-be
  version: 1.0.0
  environment: development

database:
  postgres:
    host: localhost
    port: 5432
  mongodb:
    host: localhost
    port: 27017
  redis:
    host: localhost
    port: 6379

security:
  jwt_secret_key: your-secret-key-change-in-production
  jwt_algorithm: HS256
  access_token_expire_minutes: 30
EOF

echo "✅ Resource files created"
echo ""

# === Final summary ===
echo "========================================="
echo "✅ Project structure created successfully!"
echo "========================================="
echo ""
echo "📂 Project location: $BASE_DIR"
echo ""
echo "Next steps:"
echo "1. cd $BASE_DIR"
echo "2. Create and activate virtual environment:"
echo "   python -m venv .venv"
echo "   source .venv/bin/activate  # On Windows: .venv\\Scripts\\activate"
echo "3. Install dependencies:"
echo "   make install"
echo "4. Copy and configure environment:"
echo "   cp .env.example .env"
echo "5. Start services:"
echo "   make docker-up"
echo "6. Run the application:"
echo "   make run"
echo ""
echo "📚 Documentation: Check README.md for more details"
echo "🧪 Run tests: make test"
echo ""
echo "Happy coding! 🚀"
echo "========================================="
