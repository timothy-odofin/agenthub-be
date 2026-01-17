#!/bin/bash

# Hugging Face Space Log Viewer
# Note: This requires the Hugging Face CLI

echo "📊 Fetching Hugging Face Space logs..."
echo ""

# Check if huggingface-cli is installed
if ! command -v huggingface-cli &> /dev/null; then
    echo "❌ Hugging Face CLI not found. Installing..."
    pip install -q huggingface_hub
fi

# View logs (if supported by CLI)
echo "Note: Direct log streaming may not be available via CLI."
echo "Please use the web interface at:"
echo "https://huggingface.co/spaces/oyejidet/agenthub-backend"
echo ""
echo "Or use the Space API to check status:"

curl -s "https://huggingface.co/api/spaces/oyejidet/agenthub-backend" | python3 -m json.tool

echo ""
echo "For real-time logs, visit the Space dashboard in your browser."
