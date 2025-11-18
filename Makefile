.PHONY: install install-dev install-prod install-system-deps run-api run-worker run-infra stop-infra clean help test-redis

help:
	@echo "Available commands:"
	@echo "  make install-system-deps - Install system dependencies using Homebrew (macOS)"
	@echo "  make install-prod        - Install production dependencies (requirements.txt + poetry)"
	@echo "  make install-dev         - Install development dependencies (requirements-dev.txt + poetry)" 
	@echo "  make install             - Alias for install-prod"
	@echo "  make clean-install       - Clean installation (production)"
	@echo "  make clean-install-dev   - Clean installation (development)"
	@echo "  make run-api             - Run FastAPI application"
	@echo "  make run-worker          - Run Celery worker"
	@echo "  make run-infra           - Start infrastructure services (PostgreSQL, Redis, pgAdmin)"
	@echo "  make stop-infra          - Stop infrastructure services"
	@echo "  make clean               - Stop infrastructure and clean volumes"
	@echo "  make test-redis          - Test Redis connection"
	@echo "  make help                - Show this help message"

install-system-deps:
	@echo "Installing system dependencies..."
	brew install libmagic poppler tesseract libreoffice pandoc opencv

install-prod:
	@echo "Installing production dependencies..."
	pip install -r requirements.txt
	poetry install --only=main
	@echo "✅ Production dependencies installed successfully!"

install-dev: 
	@echo "Installing development dependencies..."
	pip install -r requirements.txt
	pip install -r requirements-dev.txt
	poetry install
	@echo "✅ Development dependencies installed successfully!"

install: install-prod

clean-install:
	@echo "Performing clean installation..."
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
	@echo "Performing clean development installation..."
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

run-api:
	poetry run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

run-worker:
	poetry run celery -A app.workers.celery_app worker --loglevel=info

run-infra:
	docker compose up -d postgres redis pgadmin

stop-infra:
	docker compose stop postgres redis pgadmin

clean:
	docker compose down -v

test-redis:
	@echo "Testing Redis connection..."
	@docker compose exec redis redis-cli ping
	@echo "Testing Redis connection with Python..."
	@poetry run python -c "import redis; r = redis.Redis(host='localhost', port=6379, db=0); print(f'Redis connection successful: {r.ping()}')"