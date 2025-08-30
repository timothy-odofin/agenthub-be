import os
from pathlib import Path
from typing import Optional
import yaml
from dotenv import load_dotenv
from .schemas.ingestion_config import IngestionConfig


class AppConfig:
    """Application configuration manager implemented as a singleton"""
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            # Initialize the instance
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        # Only initialize once
        if self._initialized:
            return
            
        # Get the project root directory (two levels up from this file)
        self.project_root = Path(__file__).parent.parent.parent
        
        # Define resource paths
        self.resources_path = self.project_root / 'resources'
        self.ingestion_config_path = self.resources_path / 'application-data-sources.yaml'
        
        # Load environment variables
        self._load_env()
        self._load_database_config()
        self._load_redis_config()
        self._load_app_config()
        self._load_ingestion_config()

    def _load_env(self):
        """Load environment variables from .env file"""
        load_dotenv(self.project_root / '.env')
        self._initialized = True  # Mark initialization as complete

    def _load_database_config(self):
        """Load database configuration"""
        self.postgres_user = os.getenv('POSTGRES_USER', 'admin')
        self.postgres_password = os.getenv('POSTGRES_PASSWORD', 'admin123')
        self.postgres_db = os.getenv('POSTGRES_DB', 'polyagent')
        self.postgres_host = os.getenv('POSTGRES_HOST', 'localhost')
        self.postgres_port = int(os.getenv('POSTGRES_PORT', '5432'))
        self.database_url = (
            f"postgresql://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )

    def _load_redis_config(self):
        """Load Redis configuration"""
        self.redis_host = os.getenv('REDIS_HOST', 'localhost')
        self.redis_port = int(os.getenv('REDIS_PORT', '6379'))
        self.redis_url = f"redis://{self.redis_host}:{self.redis_port}"

    def _load_app_config(self):
        """Load application configuration"""
        self.app_env = os.getenv('APP_ENV', 'development')
        self.debug = os.getenv('DEBUG', 'true').lower() == 'true'
        self.groq_api_key = os.getenv('GROQ_API_KEY')

    def _load_ingestion_config(self) -> None:
        """Load the ingestion configuration from YAML"""
        try:
            if not self.ingestion_config_path.exists():
                self.ingestion_config = None
                return

            with open(self.ingestion_config_path, 'r') as f:
                config_dict = yaml.safe_load(f)
                self.ingestion_config = IngestionConfig(**config_dict)
        except Exception as e:
            print(f"Error loading ingestion config: {e}")
            self.ingestion_config = None

    def reload_ingestion_config(self) -> Optional[IngestionConfig]:
        """Reload the ingestion configuration from YAML"""
        self._load_ingestion_config()
        return self.ingestion_config

    @property
    def is_development(self) -> bool:
        """Check if the application is running in development mode"""
        return self.app_env.lower() == 'development'

    @property
    def is_production(self) -> bool:
        """Check if the application is running in production mode"""
        return self.app_env.lower() == 'production'


# Create a singleton instance
config = AppConfig()
