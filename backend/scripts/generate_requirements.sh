#!/bin/bash

# Script to install dependencies for deployment
# Installs Poetry dependencies and additional requirements

set -e

echo "🔄 Installing dependencies for deployment..."

# Check if poetry is installed
if ! command -v poetry &> /dev/null; then
    echo "❌ Poetry is not installed. Installing..."
    pip install poetry
fi

# Install Poetry dependencies (production only, no dev dependencies)
echo "📦 Installing Poetry dependencies..."
poetry install --no-dev --no-interaction --no-ansi

# Install additional requirements if requirements.txt exists
if [ -f requirements.txt ] && [ -s requirements.txt ]; then
    echo "📋 Installing additional requirements from requirements.txt..."
    pip install -r requirements.txt
else
    echo "ℹ️  No additional requirements.txt found, skipping..."
fi

echo "✅ All dependencies installed successfully!"
echo "� Ready to deploy!"
