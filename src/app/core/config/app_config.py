"""
Core application configuration.
"""

import os
from pathlib import Path
from typing import Optional
import yaml
from dotenv import load_dotenv

from app.core.utils.single_ton import SingletonMeta
from app.core.schemas.ingestion_config import IngestionConfig


class AppConfig(metaclass=SingletonMeta):
    """Core application configuration only."""
    
    def __init__(self):
        # Get the project root directory (four levels up from this file)
        self.project_root = Path(__file__).parent.parent.parent.parent.parent
        
        # Define resource paths
        self.resources_path = self.project_root / 'resources'
        self.ingestion_config_path = self.resources_path / 'application-data-sources.yaml'
        
        # Load environment variables
        self._load_env()
        self._load_app_config()
        self._load_ingestion_config()
    
    def _load_env(self):
        """Load environment variables from .env file"""
        load_dotenv(self.project_root / '.env')
    
    def _load_app_config(self):
        """Load core application configuration only."""
        self.app_env = os.getenv('APP_ENV', 'development')
        self.debug = os.getenv('DEBUG', 'true').lower() == 'true'
        self.app_name = os.getenv('APP_NAME', 'AgentHub')
        self.app_version = os.getenv('APP_VERSION', '1.0.0')
        
        # Security
        self.jwt_secret_key = os.getenv('JWT_SECRET_KEY')
        self.jwt_algorithm = os.getenv('JWT_ALGORITHM', 'HS256')
        self.access_token_expire_minutes = int(os.getenv('ACCESS_TOKEN_EXPIRE_MINUTES', '30'))
        
        # API Configuration
        self.api_host = os.getenv('API_HOST', '0.0.0.0')
        self.api_port = int(os.getenv('API_PORT', '8000'))
        
        # Logging
        self.log_level = os.getenv('LOG_LEVEL', 'INFO')
    
    def _load_ingestion_config(self) -> None:
        """Load the ingestion configuration from YAML"""
        try:
            if not self.ingestion_config_path.exists():
                self.ingestion_config = None
                return

            with open(self.ingestion_config_path, 'r') as f:
                config_dict = yaml.safe_load(f)
                self.ingestion_config = IngestionConfig.model_validate(config_dict)
                print(f"Ingestion config loaded successfully, total config: {len(self.ingestion_config.data_sources)} data sources")
        except Exception as e:
            print(f"Error loading ingestion config: {e}")
            self.ingestion_config = None

    def reload_ingestion_config(self) -> Optional[IngestionConfig]:
        """Reload the ingestion configuration from YAML"""
        self._load_ingestion_config()
        return self.ingestion_config


# Create singleton instance
app_config = AppConfig()
