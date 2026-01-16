---
title: AgentHub Backend API
emoji: 🤖
colorFrom: blue
colorTo: green
sdk: docker
pinned: false
app_port: 7860
---

# AgentHub Backend API

AI-powered agent hub with multi-provider LLM support built with FastAPI.

## Features

- 🤖 Multi-provider LLM support (OpenAI, Anthropic, Google, Ollama)
- 💬 Real-time chat with streaming responses
- 🔐 Authentication & Authorization
- 📊 Vector database integration (Chroma, Pinecone, Weaviate)
- 🔄 RAG (Retrieval Augmented Generation) pipeline
- 📁 Document ingestion (PDF, DOCX, TXT, etc.)
- 🧠 Conversation memory management
- 🛡️ Resilience patterns (retry, circuit breaker, rate limiting)

## API Documentation

Once deployed, visit:
- Interactive API docs: `https://your-space-name.hf.space/docs`
- Alternative docs: `https://your-space-name.hf.space/redoc`

## Environment Variables

Configure the following secrets in your Hugging Face Space settings:

### Required
- `DATABASE_URL` - PostgreSQL connection string
- `MONGODB_URL` - MongoDB connection string
- `REDIS_URL` - Redis connection string

### LLM Providers (at least one)
- `OPENAI_API_KEY` - OpenAI API key
- `ANTHROPIC_API_KEY` - Anthropic API key
- `GOOGLE_API_KEY` - Google AI API key

### Optional
- `PINECONE_API_KEY` - Pinecone vector database
- `WEAVIATE_URL` - Weaviate instance URL
- `JWT_SECRET_KEY` - JWT secret for authentication
- `ALLOWED_ORIGINS` - CORS allowed origins (comma-separated)

## Quick Start

1. Fork this repository
2. Create a new Space on Hugging Face
3. Select "Docker" as the SDK
4. Connect your forked repository
5. Configure environment variables in Space settings
6. Deploy!

## Local Development

```bash
# Install dependencies
pip install -r requirements.txt

# Run locally
cd src && uvicorn app.main:app --reload --port 8000
```

## Architecture

- **FastAPI**: Modern async web framework
- **SQLAlchemy**: ORM for PostgreSQL
- **MongoDB**: Document storage for conversations
- **Redis**: Caching and session management
- **Vector DBs**: Chroma, Pinecone, Weaviate for embeddings

## Documentation

For complete documentation, see the [main README](README.md) and [docs folder](docs/).
