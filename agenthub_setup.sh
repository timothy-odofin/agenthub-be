#!/bin/bash

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}Setting up AgentHub Backend Development Environment...${NC}"

# Check if Python 3.12 is installed
if ! command -v python3.12 &> /dev/null; then
    echo "Python 3.12 is required but not installed. Please install it first."
    exit 1
fi

# Check if Poetry is installed
if ! command -v poetry &> /dev/null; then
    echo -e "${BLUE}Installing Poetry...${NC}"
    curl -sSL https://install.python-poetry.org | python3 -
    
    # Add Poetry to PATH for the current session
    export PATH="/Users/$(whoami)/.local/bin:$PATH"
    
    # Add Poetry to PATH permanently
    if [[ -f ~/.zshrc ]]; then
        echo 'export PATH="/Users/$(whoami)/.local/bin:$PATH"' >> ~/.zshrc
        source ~/.zshrc
    elif [[ -f ~/.bashrc ]]; then
        echo 'export PATH="/Users/$(whoami)/.local/bin:$PATH"' >> ~/.bashrc
        source ~/.bashrc
    fi
fi

# Verify Poetry is accessible
if ! command -v poetry &> /dev/null; then
    echo "Poetry installation failed or not in PATH. Please restart your terminal and try again."
    exit 1
fi

# Configure Poetry to create virtual environment in project directory
poetry config virtualenvs.in-project true

# Create virtual environment and install dependencies
echo -e "${BLUE}Creating virtual environment and installing dependencies...${NC}"
poetry env use python3.12
poetry install

# Create .env file if it doesn't exist
if [ ! -f .env ]; then
    echo -e "${BLUE}Creating .env file...${NC}"
    cat > .env << EOL
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
OPENAI_API_KEY=your-openai-api-key
GROQ_API_KEY=your-groq-api-key

# LangChain
LANGCHAIN_API_KEY=your-langchain-api-key
LANGCHAIN_PROJECT=agenthub
LANGCHAIN_TRACING_V2=true
LANGCHAIN_ENDPOINT=https://api.smith.langchain.com

# App
APP_ENV=development
DEBUG=true
APP_NAME=AgentHub
APP_VERSION=0.1.0

# Security
JWT_SECRET_KEY=your-jwt-secret-key
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
EOL

    echo -e "${GREEN}Created .env file with default values.${NC}"
    echo -e "${BLUE}Please update the API keys and secrets in .env with your actual values.${NC}"
fi

echo -e "${GREEN}Setup completed successfully!${NC}"
echo -e "${BLUE}To activate the virtual environment, run:${NC}"
echo -e "    source .venv/bin/activate"
echo -e "${BLUE}To start the development server:${NC}"
echo -e "    cd src && ../poetry run uvicorn app.main:app --reload"
