#!/bin/bash

# Local Docker Test Script for Hugging Face Deployment

echo "🐳 Testing Docker build locally..."
echo ""

# Build the Docker image
echo "📦 Building Docker image..."
docker build -t agenthub-backend:test .

if [ $? -eq 0 ]; then
    echo "✅ Docker build successful!"
    echo ""
    echo "🧪 To test locally, run:"
    echo "docker run -p 7860:7860 -e DATABASE_URL=your_db_url -e MONGODB_URL=your_mongo_url -e REDIS_URL=your_redis_url agenthub-backend:test"
    echo ""
    echo "Then visit: http://localhost:7860/docs"
else
    echo "❌ Docker build failed. Please check the error messages above."
    exit 1
fi
