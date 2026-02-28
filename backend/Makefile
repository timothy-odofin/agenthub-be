.PHONY: help install install-dev install-prod install-system-deps clean-install clean-install-dev \
        run-api run-api-dev run-api-staging run-api-prod run-worker run-infra stop-infra clean \
        test test-cov test-unit test-integration test-e2e \
        format lint typecheck check-all \
        docker-build docker-up docker-down docker-logs \
        test-redis

# ============================================================================
# Help
# ============================================================================

help:
	@echo "╔══════════════════════════════════════════════════════════════╗"
	@echo "║              AgentHub - Available Commands                   ║"
	@echo "╚══════════════════════════════════════════════════════════════╝"
	@echo ""
	@echo "📦 Installation:"
	@echo "  make install-system-deps - Install system dependencies (macOS only)"
	@echo "  make install-prod        - Install production dependencies"
	@echo "  make install-dev         - Install development dependencies"
	@echo "  make install             - Alias for install-prod"
	@echo "  make clean-install       - Clean installation (production)"
	@echo "  make clean-install-dev   - Clean installation (development)"
	@echo ""
	@echo "🚀 Running Services:"
	@echo "  make run-api             - Run FastAPI application (default .env)"
	@echo "  make run-api-dev         - Run with development environment (.env.dev)"
	@echo "  make run-api-staging     - Run with staging environment (.env.staging)"
	@echo "  make run-api-prod        - Run with production environment (.env.production)"
	@echo "  make run-worker          - Run Celery worker"
	@echo "  make run-infra           - Start infrastructure (PostgreSQL, Redis, MongoDB)"
	@echo "  make stop-infra          - Stop infrastructure services"
	@echo ""
	@echo "🧪 Testing:"
	@echo "  make test                - Run all tests"
	@echo "  make test-cov            - Run tests with coverage report"
	@echo "  make test-unit           - Run unit tests only"
	@echo "  make test-integration    - Run integration tests only"
	@echo "  make test-e2e            - Run end-to-end tests only"
	@echo ""
	@echo "🎨 Code Quality:"
	@echo "  make format              - Format code (black + isort)"
	@echo "  make lint                - Lint code (flake8)"
	@echo "  make typecheck           - Type check (mypy)"
	@echo "  make check-all           - Run format + lint + typecheck + test"
	@echo ""
	@echo "🐳 Docker:"
	@echo "  make docker-build        - Build Docker image"
	@echo "  make docker-up           - Start all services with Docker Compose"
	@echo "  make docker-down         - Stop all Docker services"
	@echo "  make docker-logs         - View Docker logs"
	@echo ""
	@echo "🧹 Cleanup:"
	@echo "  make clean               - Stop infrastructure and clean volumes"
	@echo "  make test-redis          - Test Redis connection"
	@echo ""
	@echo "❓ Help:"
	@echo "  make help                - Show this help message"
	@echo ""

# ============================================================================
# Installation Targets
# ============================================================================

install-system-deps:
	@echo "📦 Installing system dependencies (macOS only)..."
	@echo "⚠️  Note: This requires Homebrew. Skip if not on macOS."
	brew install libmagic poppler tesseract libreoffice pandoc opencv

install-prod:
	@echo "📦 Installing production dependencies..."
	pip install -r requirements.txt
	poetry install --only=main
	@echo "✅ Production dependencies installed successfully!"

install-dev:
	@echo "📦 Installing development dependencies..."
	pip install -r requirements.txt
	pip install -r requirements-dev.txt
	poetry install
	@echo "✅ Development dependencies installed successfully!"

install: install-prod

clean-install:
	@echo "🧹 Performing clean installation..."
	rm -rf .venv
	poetry env remove --all || true
	rm -f poetry.lock
	@echo "Creating new Poetry environment..."
	poetry env use python3
	@echo "Installing production dependencies..."
	poetry run pip install -r requirements.txt
	poetry install --only=main
	@echo "✅ Clean installation completed successfully!"

clean-install-dev:
	@echo "🧹 Performing clean development installation..."
	rm -rf .venv
	poetry env remove --all || true
	rm -f poetry.lock
	@echo "Creating new Poetry environment..."
	poetry env use python3
	@echo "Installing development dependencies..."
	poetry run pip install -r requirements.txt
	poetry run pip install -r requirements-dev.txt
	poetry install
	@echo "✅ Clean development installation completed successfully!"

# ============================================================================
# Running Services
# ============================================================================

run-api:
	@echo "🚀 Starting FastAPI application (default environment)..."
	poetry run uvicorn src.app.main:app --reload --host 0.0.0.0 --port 8000

run-api-dev:
	@echo "🚀 Starting FastAPI application (development environment)..."
	poetry run uvicorn src.app.main:app --env .env.dev --reload --host 0.0.0.0 --port 8000

run-api-staging:
	@echo "🚀 Starting FastAPI application (staging environment)..."
	poetry run uvicorn src.app.main:app --env .env.staging --host 0.0.0.0 --port 8000

run-api-prod:
	@echo "🚀 Starting FastAPI application (production environment)..."
	poetry run uvicorn src.app.main:app --env .env.production --host 0.0.0.0 --port 8000 --workers 4

run-worker:
	@echo "⚙️  Starting Celery worker..."
	poetry run celery -A src.app.workers.celery_app worker --loglevel=info

run-infra:
	@echo "🐳 Starting infrastructure services..."
	docker compose up -d postgres redis mongodb

stop-infra:
	@echo "🛑 Stopping infrastructure services..."
	docker compose stop postgres redis mongodb

clean:
	@echo "🧹 Cleaning up Docker volumes..."
	docker compose down -v

test-redis:
	@echo "🔍 Testing Redis connection..."
	@docker compose exec redis redis-cli ping
	@echo "Testing Redis connection with Python..."
	@poetry run python -c "import redis; r = redis.Redis(host='localhost', port=6379, db=0); print(f'Redis connection successful: {r.ping()}')"

# ============================================================================
# Testing Targets
# ============================================================================

test:
	@echo "🧪 Running all tests..."
	poetry run pytest tests/ -v

test-cov:
	@echo "📊 Running tests with coverage..."
	poetry run pytest tests/ --cov=src/app --cov-report=html --cov-report=term-missing -v
	@echo "✅ Coverage report generated in htmlcov/index.html"

test-unit:
	@echo "🧪 Running unit tests..."
	poetry run pytest tests/unit/ -v

test-integration:
	@echo "🔗 Running integration tests..."
	poetry run pytest tests/integration/ -v

test-e2e:
	@echo "🌐 Running end-to-end tests..."
	poetry run pytest tests/e2e/ -v

# ============================================================================
# Code Quality Targets
# ============================================================================

format:
	@echo "🎨 Formatting code with black and isort..."
	poetry run black src/ tests/
	poetry run isort src/ tests/
	@echo "✅ Code formatted successfully!"

lint:
	@echo "🔍 Linting code with flake8..."
	poetry run flake8 src/ tests/ --max-line-length=120 --exclude=__pycache__,.venv
	@echo "✅ Linting passed!"

typecheck:
	@echo "🔎 Type checking with mypy..."
	poetry run mypy src/ --ignore-missing-imports
	@echo "✅ Type checking passed!"

check-all: format lint typecheck test
	@echo "✅ All checks passed!"

# ============================================================================
# Docker Targets
# ============================================================================

docker-build:
	@echo "🐳 Building Docker image..."
	docker build -t agenthub-api:latest .

docker-up:
	@echo "🐳 Starting all services with Docker Compose..."
	docker compose up -d
	@echo "✅ All services started!"
	@echo "📊 View status: docker compose ps"
	@echo "📋 View logs: make docker-logs"

docker-down:
	@echo "🛑 Stopping all Docker services..."
	docker compose down
	@echo "✅ All services stopped!"

docker-logs:
	@echo "📋 Viewing Docker logs (Ctrl+C to exit)..."
	docker compose logs -f
