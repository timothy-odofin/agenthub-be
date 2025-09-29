.PHONY: install install-brew-deps run-api run-worker run-infra stop-infra clean help test-redis

help:
	@echo "Available commands:"
	@echo "  make test-redis       - Test Redis connection"
	@echo "  make install           - Install Python dependencies using Poetry"
	@echo "  make install-brew-deps - Install system dependencies using Homebrew (macOS)"
	@echo "  make run-api          - Run FastAPI application"
	@echo "  make run-worker       - Run Celery worker"
	@echo "  make run-infra        - Start infrastructure services (PostgreSQL, Redis, pgAdmin)"
	@echo "  make stop-infra       - Stop infrastructure services"
	@echo "  make clean            - Stop infrastructure and clean volumes"
	@echo "  make help             - Show this help message"

install-system-deps:
	brew install libmagic poppler tesseract libreoffice pandoc opencv

install-pytorch:
	pip3 install torch torchvision --index-url https://download.pytorch.org/whl/cpu
	pip3 install "onnxruntime>=1.17.0" "unstructured-inference>=0.9.0" "unstructured-pytesseract>=0.3.12"

install:
	make install-pytorch
	poetry lock
	poetry install

clean-install:
	rm -rf .venv
	poetry env remove --all || true
	poetry cache clear . --all || true
	poetry install --no-cache
	make install-pytorch
	

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