# AgentHub Backend

A modular AI assistant platform that acts as a central hub for knowledge retrieval and tool integration.

## Features

- Agent orchestration for intelligent tool selection
- RAG (Retrieval-Augmented Generation) with vector embeddings
- Integration with multiple knowledge sources
- Tool integrations (Jira, GitHub, Bitbucket, Confluence)
- Chat interface with streaming responses
- Session-based conversation management

## Tech Stack

- FastAPI
- PostgreSQL + pgvector
- Redis
- Celery
- LangChain + Groq
- Poetry for dependency management

## Prerequisites

- Python 3.12 or higher
- Docker and Docker Compose (for running PostgreSQL and Redis)
- Poetry (Python package manager)

## Quick Start

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/agenthub-be.git
   cd agenthub-be
   ```

2. **Run the setup script**
   ```bash
   chmod +x agenthub_setup.sh
   ./agenthub_setup.sh
   ```
   This will:
   - Create a Python virtual environment in the project root
   - Install all dependencies
   - Create a default .env file in the src directory

3. **Start the database and Redis**
   ```bash
   docker-compose up -d
   ```

4. **Activate the virtual environment**
   ```bash
   source .venv/bin/activate
   ```

5. **Run database migrations**
   ```bash
   alembic upgrade head
   ```

6. **Start the development server**
   ```bash
   poetry run uvicorn app.main:app --reload
   ```

The API will be available at http://localhost:8000
Swagger documentation: http://localhost:8000/docs

## Development Setup

### Install dependencies

```bash
poetry install
```

### Add new dependencies

```bash
poetry add package-name
```

### Run tests

```bash
poetry run pytest
```

### Code formatting

```bash
# Format code
poetry run black .

# Sort imports
poetry run isort .

# Type checking
poetry run mypy .
```

## Project Structure

```
src/
├── alembic/          # Database migrations
├── app/
│   ├── api/          # API endpoints
│   ├── core/         # Core functionality
│   ├── db/          # Database models and repositories
│   ├── schemas/     # Pydantic models
│   ├── services/    # Business logic
│   └── workers/     # Celery workers
└── tests/           # Test suite
```

## Environment Variables

Create a `.env` file in the project root with the following variables:

```env
# Database
POSTGRES_USER=admin
POSTGRES_PASSWORD=admin123
POSTGRES_DB=polyagent
POSTGRES_HOST=localhost
POSTGRES_PORT=5432

# Redis
REDIS_HOST=localhost
REDIS_PORT=6379

# Groq
GROQ_API_KEY=your-groq-api-key

# App
APP_ENV=development
DEBUG=true
```

## Docker Support

Build and run the entire stack using Docker Compose:

```bash
docker-compose up --build
```

## Contributing

1. Fork the repository
2. Create a new branch for your feature
3. Make your changes
4. Run tests and ensure they pass
5. Submit a pull request

## License

[MIT License](LICENSE)
