# Quick Start Guide

> ⚡ **Get AgentHub running in 5 minutes!**

## Table of Contents
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Configuration](#configuration)
- [First Run](#first-run)
- [Your First Query](#your-first-query)
- [Next Steps](#next-steps)

---

## Prerequisites

Before you begin, ensure you have:

- **Python 3.10+** installed
- **Docker & Docker Compose** (for databases)
- **Git** (to clone the repository)
- **OpenAI API Key** (or another LLM provider)

### Check Your Setup

```bash
# Check Python version
python --version
# Should show: Python 3.10.x or higher

# Check Docker
docker --version
docker-compose --version

# Check Git
git --version
```

---

## Installation

### 1. Clone the Repository

```bash
git clone https://github.com/timothy-odofin/agenthub-be.git
cd agenthub-be
```

### 2. Create Virtual Environment

```bash
# Create virtual environment
python -m venv venv

# Activate it
# On macOS/Linux:
source venv/bin/activate
# On Windows:
venv\Scripts\activate
```

### 3. Install Dependencies

```bash
# Install Python packages
pip install -r requirements.txt

# Verify installation
pip list | grep fastapi
# Should show: fastapi, langchain, etc.
```

### 4. Start Infrastructure

```bash
# Start PostgreSQL, MongoDB, Redis
docker-compose up -d

# Verify services are running
docker-compose ps
# Should show: postgres, mongodb, redis (all "Up")
```

---

## Configuration

### 1. Create Environment File

```bash
# Copy example environment file
cp .env.example .env

# Edit with your settings
nano .env  # or use your favorite editor
```

### 2. Essential Environment Variables

Add these to your `.env` file:

```bash
# LLM Provider (required)
DEFAULT_LLM_PROVIDER=openai
OPENAI_API_KEY=your-openai-api-key-here

# Database (default values work with Docker setup)
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=agenthub
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres

# MongoDB
MONGODB_HOST=localhost
MONGODB_PORT=27017
MONGODB_DB=agenthub

# Redis
REDIS_HOST=localhost
REDIS_PORT=6379

# Application
APP_ENV=development
LOG_LEVEL=INFO
```

### 3. Quick Configuration (Optional)

AgentHub uses YAML-based configuration for fine-grained control:

```bash
# View default LLM configuration
cat resources/application-llm.yaml
```

**Tip**: You can override any YAML setting with environment variables!

```bash
# Example: Change temperature
export OPENAI_TEMPERATURE=0.3
```

---

## First Run

### 1. Initialize Database

```bash
# Run migrations
python -m alembic upgrade head

# Verify tables were created
docker-compose exec postgres psql -U postgres -d agenthub -c "\dt"
```

### 2. Start the Application

```bash
# Start FastAPI server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

You should see:

```
INFO:     Uvicorn running on http://0.0.0.0:8000
INFO:     Application startup complete.
```

### 3. Verify Health

Open your browser to: **http://localhost:8000/health**

You should see:

```json
{
  "status": "healthy",
  "timestamp": "2026-01-08T22:30:00",
  "version": "1.0.0"
}
```

### 4. Explore API Docs

Visit: **http://localhost:8000/docs**

You'll see the interactive Swagger UI with all available endpoints!

---

## Your First Query

### Option 1: Using cURL

```bash
# Simple chat query
curl -X POST "http://localhost:8000/api/v1/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "What is machine learning?",
    "session_id": "test-session-1"
  }'
```

**Response:**
```json
{
  "response": "Machine learning is a subset of artificial intelligence...",
  "session_id": "test-session-1",
  "tokens_used": 45
}
```

### Option 2: Using Python

```python
import requests

# Query the chat endpoint
response = requests.post(
    "http://localhost:8000/api/v1/chat",
    json={
        "message": "What is Python?",
        "session_id": "test-session-2"
    }
)

print(response.json()["response"])
# Output: "Python is a high-level programming language..."
```

### Option 3: Using the Swagger UI

1. Go to **http://localhost:8000/docs**
2. Find `/api/v1/chat` endpoint
3. Click "Try it out"
4. Enter your message
5. Click "Execute"
6. See the response!

---

## Test RAG (Document Q&A)

### 1. Upload a Document

```bash
# Create a test document
echo "AgentHub is a production-grade LLM application framework. It supports multiple providers including OpenAI, Anthropic, and Google." > test-doc.txt

# Upload it
curl -X POST "http://localhost:8000/api/v1/documents/ingest" \
  -F "file=@test-doc.txt" \
  -F "collection_name=test-collection"
```

### 2. Query Your Document

```bash
curl -X POST "http://localhost:8000/api/v1/documents/query" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "What is AgentHub?",
    "collection_name": "test-collection"
  }'
```

**Response:**
```json
{
  "answer": "AgentHub is a production-grade LLM application framework that supports multiple providers including OpenAI, Anthropic, and Google.",
  "sources": ["test-doc.txt"]
}
```

---

## Common First-Run Issues

### Issue 1: "Module not found" Error

**Problem**: Python can't find the app module

**Solution**:
```bash
# Ensure you're in the project root
pwd  # Should show: .../agenthub-be

# Set PYTHONPATH
export PYTHONPATH="${PYTHONPATH}:$(pwd)/src"

# Or run with Python module syntax
python -m app.main
```

### Issue 2: Database Connection Error

**Problem**: Can't connect to PostgreSQL/MongoDB

**Solution**:
```bash
# Check if services are running
docker-compose ps

# If not running, start them
docker-compose up -d

# Check logs
docker-compose logs postgres
docker-compose logs mongodb
```

### Issue 3: "Invalid API Key" Error

**Problem**: LLM provider authentication fails

**Solution**:
```bash
# Verify API key is set
echo $OPENAI_API_KEY

# If empty, add to .env
echo "OPENAI_API_KEY=your-key-here" >> .env

# Restart the application
```

### Issue 4: Port Already in Use

**Problem**: Port 8000 is occupied

**Solution**:
```bash
# Use a different port
uvicorn app.main:app --reload --port 8080

# Or find what's using port 8000
lsof -i :8000
# Kill the process if needed
kill -9 <PID>
```

---

## Next Steps

### 🎓 Learn the Basics

- **[LLM Basics](../core-concepts/llm-basics.md)** - Understand how LLMs work
- **[RAG Pipeline](../core-concepts/rag-pipeline.md)** - Learn about document retrieval
- **[Architecture Overview](../architecture/overview.md)** - See how AgentHub is built

### 🛠️ Configuration

- **[LLM Providers](../guides/llm-providers/README.md)** - Configure different LLM providers
- **[Configuration System](../architecture/configuration-system.md)** - Master YAML configs
- **[Environment Variables](../deployment/environment-variables.md)** - All available settings

### 📚 Tutorials

- **[Build a RAG Chatbot](../tutorials/rag-chatbot.md)** - Step-by-step RAG tutorial
- **[Multi-LLM Routing](../tutorials/multi-llm-routing.md)** - Use multiple providers
- **[Custom Tools](../tutorials/custom-tools.md)** - Extend agent capabilities

### 🚀 Production

- **[Deployment Guide](../deployment/overview.md)** - Deploy to production
- **[Docker Setup](../deployment/docker.md)** - Containerize your app
- **[Monitoring](../guides/monitoring.md)** - Track performance

---

## Development Workflow

### Typical Day-to-Day Usage

```bash
# 1. Start infrastructure (once per session)
docker-compose up -d

# 2. Activate virtual environment
source venv/bin/activate

# 3. Start development server with auto-reload
uvicorn app.main:app --reload

# 4. Make code changes (server auto-restarts)

# 5. Run tests
pytest

# 6. Check logs
tail -f logs/$(date +%Y-%m-%d).log

# 7. Stop infrastructure (when done)
docker-compose down
```

### Running Tests

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/unit/test_llm_factory.py

# Run with coverage
pytest --cov=app tests/

# Run integration tests only
pytest tests/integration/
```

### Code Quality Checks

```bash
# Format code
black src/

# Check linting
flake8 src/

# Type checking
mypy src/

# Run all checks
make lint  # If Makefile is configured
```

---

## Useful Commands

### Database Management

```bash
# Access PostgreSQL
docker-compose exec postgres psql -U postgres -d agenthub

# Access MongoDB
docker-compose exec mongodb mongosh agenthub

# Access Redis CLI
docker-compose exec redis redis-cli

# Reset databases (⚠️ deletes all data!)
docker-compose down -v
docker-compose up -d
```

### View Logs

```bash
# Application logs
tail -f logs/$(date +%Y-%m-%d).log

# Docker service logs
docker-compose logs -f postgres
docker-compose logs -f mongodb
docker-compose logs -f redis

# All services
docker-compose logs -f
```

### Environment Management

```bash
# List all environment variables
printenv | grep -E "OPENAI|POSTGRES|MONGODB|REDIS"

# Load environment variables from .env
set -a && source .env && set +a

# Check which Python is being used
which python
# Should be: .../agenthub-be/venv/bin/python
```

---

## Quick Configuration Reference

### Minimal `.env` (Development)

```bash
# LLM
DEFAULT_LLM_PROVIDER=openai
OPENAI_API_KEY=sk-...

# Databases (defaults work with Docker)
POSTGRES_HOST=localhost
MONGODB_HOST=localhost
REDIS_HOST=localhost

# App
APP_ENV=development
LOG_LEVEL=DEBUG
```

### Minimal `.env` (Production)

```bash
# LLM
DEFAULT_LLM_PROVIDER=azure_openai
AZURE_OPENAI_API_KEY=...
AZURE_OPENAI_ENDPOINT=...

# Databases (use managed services)
POSTGRES_HOST=your-postgres-host
POSTGRES_SSL_MODE=require
MONGODB_URI=mongodb+srv://...
REDIS_URL=rediss://...

# App
APP_ENV=production
LOG_LEVEL=INFO
SECRET_KEY=your-secure-secret-key
```

---

## Health Checks

### Verify All Systems

```bash
# 1. Infrastructure
docker-compose ps
# All services should show "Up"

# 2. API health
curl http://localhost:8000/health
# Should return: {"status": "healthy"}

# 3. Database connections
curl http://localhost:8000/api/v1/system/health/db
# Should return: {"postgres": "ok", "mongodb": "ok", "redis": "ok"}

# 4. LLM provider
curl http://localhost:8000/api/v1/system/health/llm
# Should return: {"openai": "ok"}
```

### System Status Dashboard

Visit: **http://localhost:8000/api/v1/system/status**

```json
{
  "application": "healthy",
  "databases": {
    "postgres": "connected",
    "mongodb": "connected",
    "redis": "connected"
  },
  "llm_providers": {
    "openai": "available"
  },
  "uptime": "00:15:32"
}
```

---

## Getting Help

### Documentation

- **[Full Documentation](../README.md)** - Complete guide
- **[API Reference](../api-reference/README.md)** - Endpoint docs
- **[Troubleshooting](../guides/troubleshooting.md)** - Common issues

### Community

- **GitHub Issues**: [Report bugs](https://github.com/timothy-odofin/agenthub-be/issues)
- **Discussions**: [Ask questions](https://github.com/timothy-odofin/agenthub-be/discussions)
- **Architecture Docs**: [See more code examples](../architecture/design-patterns.md)

### Quick Links

| What | Where |
|------|-------|
| 📖 **Docs** | `docs/` directory |
| 🐛 **Issues** | GitHub Issues |
| 💡 **Code Examples** | Embedded in documentation |
| 🧪 **Tests** | `tests/` directory |
| ⚙️ **Config** | `resources/` directory |

---

## What You've Learned

✅ Installed AgentHub and its dependencies  
✅ Configured LLM providers and databases  
✅ Started the application  
✅ Made your first chat query  
✅ Tested RAG document retrieval  
✅ Know where to find help  

### You're Ready! 🎉

You now have AgentHub running locally. Time to build something amazing!

**Recommended Next Step**: Follow the [RAG Chatbot Tutorial](../tutorials/rag-chatbot.md) to build your first AI-powered application.

---

**Last Updated**: January 8, 2026  
**Version**: 1.0.0  
**Tested On**: macOS, Linux, Windows (WSL2)
