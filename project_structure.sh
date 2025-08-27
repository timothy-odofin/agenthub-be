#!/bin/bash

# === Settings ===
PROJECT_NAME="backend"
BASE_DIR=${1:-$(pwd)/$PROJECT_NAME}

echo "📂 Initializing project in: $BASE_DIR"

# === Directory structure ===
mkdir -p $BASE_DIR/{alembic,tests/{unit,integration,e2e}}
mkdir -p $BASE_DIR/app/{api/v1,core,db/{models,repositories},services/{agent/{tools,prompts},retriever},workers,schemas}

# === Base files ===
touch $BASE_DIR/.env.example
touch $BASE_DIR/README.md
touch $BASE_DIR/pyproject.toml
touch $BASE_DIR/alembic.ini
touch $BASE_DIR/Dockerfile
touch $BASE_DIR/docker-compose.yml

# === Python init files ===
find $BASE_DIR/app -type d -exec touch {}/__init__.py \;

# === Main FastAPI entrypoint ===
cat > $BASE_DIR/app/main.py << 'EOF'
from fastapi import FastAPI
from app.api.v1 import chat, health

app = FastAPI(title="Chatbot Backend")

# Routers
app.include_router(chat.router, prefix="/api/v1/chat", tags=["chat"])
app.include_router(health.router, prefix="/api/v1/health", tags=["health"])

@app.get("/")
def root():
    return {"status": "ok", "message": "Chatbot backend is running 🚀"}
EOF

# === Example health API ===
cat > $BASE_DIR/app/api/v1/health.py << 'EOF'
from fastapi import APIRouter

router = APIRouter()

@router.get("/livez")
def livez():
    return {"status": "alive"}

@router.get("/readyz")
def readyz():
    return {"status": "ready"}
EOF

# === Example chat API ===
cat > $BASE_DIR/app/api/v1/chat.py << 'EOF'
from fastapi import APIRouter
from app.schemas.chat import ChatRequest, ChatResponse

router = APIRRouter()

@router.post("/", response_model=ChatResponse)
async def chat(req: ChatRequest):
    # TODO: integrate agent + retriever here
    return ChatResponse(reply="This is a placeholder response.")
EOF

# === Example schema ===
cat > $BASE_DIR/app/schemas/chat.py << 'EOF'
from pydantic import BaseModel

class ChatRequest(BaseModel):
    session_id: str
    message: str

class ChatResponse(BaseModel):
    reply: str
EOF

# === Git ignore file ===
cat > $BASE_DIR/.gitignore << 'EOF'
__pycache__/
*.pyc
.env
.venv
postgres_data/
redis_data/
EOF

echo "✅ Project skeleton created successfully in $BASE_DIR"
