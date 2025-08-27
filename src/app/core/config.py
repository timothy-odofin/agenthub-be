import os
from pathlib import Path
from dotenv import load_dotenv

# Get the project root directory (two levels up from this file)
PROJECT_ROOT = Path(__file__).parent.parent.parent

# Load the .env file from the project root
load_dotenv(PROJECT_ROOT / '.env')

# Database Configuration
POSTGRES_USER = os.getenv('POSTGRES_USER', 'admin')
POSTGRES_PASSWORD = os.getenv('POSTGRES_PASSWORD', 'admin123')
POSTGRES_DB = os.getenv('POSTGRES_DB', 'polyagent')
POSTGRES_HOST = os.getenv('POSTGRES_HOST', 'localhost')
POSTGRES_PORT = int(os.getenv('POSTGRES_PORT', '5432'))

# Redis Configuration
REDIS_HOST = os.getenv('REDIS_HOST', 'localhost')
REDIS_PORT = int(os.getenv('REDIS_PORT', '6379'))

# Groq Configuration
GROQ_API_KEY = os.getenv('GROQ_API_KEY')

# App Configuration
APP_ENV = os.getenv('APP_ENV', 'development')
DEBUG = os.getenv('DEBUG', 'true').lower() == 'true'

# Database URL
DATABASE_URL = f"postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"

# Redis URL
REDIS_URL = f"redis://{REDIS_HOST}:{REDIS_PORT}"
