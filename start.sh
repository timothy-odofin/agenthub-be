#!/bin/bash
set -e

echo "🚀 Starting AgentHub Backend on Hugging Face Spaces..."

# Display environment info
echo "Python version: $(python --version)"
echo "Working directory: $(pwd)"
echo "Port: ${PORT:-7860}"

# Run database migrations if needed (optional, comment out if not using)
# cd src && alembic upgrade head

# Start the application
cd src && uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-7860} --workers 2 --log-level info
