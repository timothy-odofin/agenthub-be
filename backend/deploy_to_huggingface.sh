#!/bin/bash

# AgentHub Hugging Face Deployment Script
# This script helps you deploy to Hugging Face Spaces

set -e

echo "🤗 AgentHub Hugging Face Deployment Helper"
echo "=========================================="
echo ""

# Check if git is installed
if ! command -v git &> /dev/null; then
    echo "❌ Git is not installed. Please install git first."
    exit 1
fi

# Check if we're in a git repository
if ! git rev-parse --git-dir > /dev/null 2>&1; then
    echo "❌ Not a git repository. Please run this from your project root."
    exit 1
fi

echo "📋 Pre-deployment Checklist:"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "Step 1: Create Hugging Face Account (if you haven't)"
echo "   → Visit: https://huggingface.co/join"
echo ""
echo "Step 2: Create an Access Token"
echo "   → Visit: https://huggingface.co/settings/tokens"
echo "   → Click 'New token'"
echo "   → Name: 'agenthub-deployment'"
echo "   → Role: 'Write'"
echo "   → Copy the token (starts with 'hf_')"
echo ""
echo "Step 3: Create a Space"
echo "   → Visit: https://huggingface.co/new-space"
echo "   → Select 'Docker' as SDK"
echo "   → Choose a name (e.g., 'agenthub-backend')"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

read -p "Have you completed the above steps? (y/n): " READY

if [ "$READY" != "y" ] && [ "$READY" != "Y" ]; then
    echo ""
    echo "No problem! Complete the steps above and run this script again."
    echo "📚 See HUGGINGFACE_AUTHENTICATION.md for detailed instructions."
    exit 0
fi

echo ""
echo "🔐 Authentication Setup"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Check if huggingface-cli is installed
if command -v huggingface-cli &> /dev/null; then
    echo "✅ Hugging Face CLI is installed"

    # Check if already logged in
    if huggingface-cli whoami &> /dev/null; then
        CURRENT_USER=$(huggingface-cli whoami)
        echo "✅ Already logged in as: $CURRENT_USER"
        read -p "Use this account? (y/n): " USE_CURRENT

        if [ "$USE_CURRENT" != "y" ] && [ "$USE_CURRENT" != "Y" ]; then
            echo ""
            echo "Please login with your Hugging Face token:"
            huggingface-cli login
        fi
    else
        echo "Please login with your Hugging Face token:"
        echo "(Paste your token when prompted - it starts with 'hf_')"
        huggingface-cli login
    fi
else
    echo "📦 Hugging Face CLI not found. Installing..."
    pip install -q huggingface_hub

    if [ $? -eq 0 ]; then
        echo "✅ Hugging Face CLI installed"
        echo ""
        echo "Please login with your Hugging Face token:"
        echo "(Paste your token when prompted - it starts with 'hf_')"
        huggingface-cli login
    else
        echo "⚠️  Could not install Hugging Face CLI automatically."
        echo "You can still proceed with manual authentication."
    fi
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Get Hugging Face Space details
read -p "Enter your Hugging Face username: " HF_USERNAME
read -p "Enter your Space name (e.g., agenthub-backend): " HF_SPACE_NAME

if [ -z "$HF_USERNAME" ] || [ -z "$HF_SPACE_NAME" ]; then
    echo "❌ Username and Space name are required."
    exit 1
fi

HF_SPACE_URL="https://huggingface.co/spaces/$HF_USERNAME/$HF_SPACE_NAME"

echo ""
echo "🔗 Space URL: $HF_SPACE_URL"
echo ""

# Ask if they want to add the remote
read -p "Add Hugging Face as a git remote? (y/n): " ADD_REMOTE

if [ "$ADD_REMOTE" = "y" ] || [ "$ADD_REMOTE" = "Y" ]; then
    # Check if remote already exists
    if git remote get-url huggingface > /dev/null 2>&1; then
        echo "⚠️  Remote 'huggingface' already exists. Removing..."
        git remote remove huggingface
    fi

    git remote add huggingface "https://huggingface.co/spaces/$HF_USERNAME/$HF_SPACE_NAME"
    echo "✅ Added Hugging Face remote"

    # Show configured remotes
    echo ""
    echo "📡 Configured remotes:"
    git remote -v | grep huggingface
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📝 Next Steps to Complete Deployment"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "🔧 Step 1: Configure Environment Variables"
echo "   → Go to: $HF_SPACE_URL/settings"
echo "   → Click 'Repository secrets'"
echo "   → Add these secrets:"
echo ""
echo "   Required:"
echo "   • DATABASE_URL=postgresql://user:pass@host:port/db"
echo "   • MONGODB_URL=mongodb://user:pass@host:port/db"
echo "   • REDIS_URL=redis://host:port"
echo ""
echo "   LLM Providers (at least one):"
echo "   • OPENAI_API_KEY=sk-..."
echo "   • ANTHROPIC_API_KEY=sk-ant-..."
echo "   • GOOGLE_API_KEY=..."
echo ""
echo "   Optional:"
echo "   • JWT_SECRET_KEY=your-secret-key"
echo "   • ALLOWED_ORIGINS=https://your-frontend.com"
echo ""
echo "   💡 Need free databases? See QUICKSTART_HUGGINGFACE.md"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "🚀 Step 2: Deploy Your Code"
echo ""
echo "   Run these commands:"
echo "   ┌────────────────────────────────────────────────┐"
echo "   │ git add .                                      │"
echo "   │ git commit -m 'Deploy to Hugging Face'        │"
echo "   │ git push huggingface $(git branch --show-current):main             │"
echo "   └────────────────────────────────────────────────┘"
echo ""
echo "   ⏱️  Build takes 5-10 minutes"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "📊 Step 3: Monitor & Test"
echo ""
echo "   Space Dashboard: $HF_SPACE_URL"
echo "   API Docs:        https://$HF_USERNAME-$HF_SPACE_NAME.hf.space/docs"
echo "   Health Check:    https://$HF_USERNAME-$HF_SPACE_NAME.hf.space/health"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "📚 Additional Resources:"
echo "   • HUGGINGFACE_AUTHENTICATION.md - Authentication help"
echo "   • QUICKSTART_HUGGINGFACE.md - Quick reference"
echo "   • DEPLOYMENT_HUGGINGFACE.md - Complete guide"
echo ""
echo "🆘 Need help? Visit: https://discuss.huggingface.co"
echo ""
echo "✨ Happy deploying! 🚀"
