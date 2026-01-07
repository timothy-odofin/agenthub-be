#!/bin/bash

# Script to generate a complete requirements.txt for deployment
# Combines Poetry dependencies with additional requirements

set -e

echo "🔄 Generating complete requirements.txt for deployment..."

# Check if poetry is installed
if ! command -v poetry &> /dev/null; then
    echo "❌ Poetry is not installed. Please install it first."
    exit 1
fi

# Export Poetry dependencies without hashes (for better compatibility)
echo "📦 Exporting Poetry dependencies..."
poetry export -f requirements.txt --output requirements-poetry.txt --without-hashes --without dev

# Backup original requirements.txt if it exists
if [ -f requirements.txt ]; then
    echo "💾 Backing up original requirements.txt..."
    cp requirements.txt requirements-original.txt
fi

# Check if we have additional requirements
if [ -f requirements-original.txt ]; then
    echo "🔗 Merging with existing requirements.txt..."
    # Remove duplicates and merge
    cat requirements-poetry.txt requirements-original.txt | sort -u > requirements-final.txt
else
    echo "📋 Using Poetry requirements only..."
    cp requirements-poetry.txt requirements-final.txt
fi

# Replace the main requirements.txt
mv requirements-final.txt requirements.txt

# Clean up temporary files
rm -f requirements-poetry.txt

echo "✅ Complete requirements.txt generated successfully!"
echo ""
echo "📄 Summary:"
wc -l requirements.txt
echo ""
echo "🚀 You can now deploy with this requirements.txt file"
