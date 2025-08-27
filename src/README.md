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
   - Create a default .env file in the project root

3. **Start the database, Redis, and pgAdmin**
   ```bash
   docker-compose up -d
   ```

   This will start:
   - PostgreSQL on port 5432
   - Redis on port 6379
   - pgAdmin on port 5050

   Access pgAdmin at http://localhost:5050
   - Email: admin@admin.com
   - Password: admin123

   To connect to PostgreSQL in pgAdmin:
   1. Add New Server
   2. Name: AgentHub
   3. Connection:
      - Host: postgres
      - Port: 5432
      - Database: polyagent
      - Username: admin
      - Password: admin123

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

The setup script will create a `.env` file in the project root with the following variables (you can also create it manually):

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

# API Keys
OPENAI_API_KEY=your-openai-api-key          # Required for OpenAI models
GROQ_API_KEY=your-groq-api-key              # Required for Groq models

# LangChain
LANGCHAIN_API_KEY=your-langchain-api-key    # Required for LangSmith monitoring
LANGCHAIN_PROJECT=agenthub                  # Project name in LangSmith
LANGCHAIN_TRACING_V2=true                   # Enable LangSmith tracing
LANGCHAIN_ENDPOINT=https://api.smith.langchain.com

# App
APP_ENV=development                         # development, staging, production
DEBUG=true
APP_NAME=AgentHub
APP_VERSION=0.1.0

# Security
JWT_SECRET_KEY=your-jwt-secret-key         # Required for JWT token generation
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
```

Make sure to replace the following values with your actual credentials:
- `OPENAI_API_KEY`: Get from [OpenAI Platform](https://platform.openai.com/api-keys)
- `GROQ_API_KEY`: Get from [Groq Cloud](https://console.groq.com)
- `LANGCHAIN_API_KEY`: Get from [LangSmith](https://smith.langchain.com)
- `JWT_SECRET_KEY`: Generate a secure random string for production

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
